import os
import asyncio
import traceback
from datetime import timedelta

from app.db.database import get_ist_time, SessionLocal
from app.db.models import Complaint, AgentResolution, ModelValidation, User
from app.services.multi_model_validator import multi_model_validator
from app.services.email_service import email_service
from app.agents.groq_client import groq_client
from app.agents.solution_suggester import suggest_solution

# Seconds to wait after a complaint is filed before auto-resolving it
AUTO_RESOLVE_DELAY = int(os.getenv("AUTO_RESOLVE_DELAY_SECONDS", "300"))
# Minimum consensus confidence for the AI to mail a resolution on its own.
# Anything below stays a draft in the agent queue for a human to finish.
AUTO_RESOLVE_MIN_CONFIDENCE = float(os.getenv("AUTO_RESOLVE_MIN_CONFIDENCE", "0.75"))
# How far back to look for complaints a restart left unprocessed
RECOVERY_WINDOW = timedelta(days=3)


class AutoResolver:
    """
    Automatic Resolution Service
    Orchestrates the autonomous validation and delivery of AI solutions
    """

    def __init__(self):
        # Complaint ids currently scheduled/running, so startup recovery and the
        # request's background task never process the same complaint twice.
        self._in_flight = set()

    async def process_complaint(self, complaint_id: int, delay: int = None):
        """
        Runs the full autonomous resolution pipeline for a complaint after a
        short delay (so a human agent can step in first).
        """
        if complaint_id in self._in_flight:
            return
        self._in_flight.add(complaint_id)
        try:
            delay = AUTO_RESOLVE_DELAY if delay is None else max(0, delay)
            print(f"⏳ Complaint {complaint_id} received. Auto-resolution in {delay}s...")
            await asyncio.sleep(delay)
            await self._resolve(complaint_id)
        finally:
            self._in_flight.discard(complaint_id)

    async def resume_pending(self):
        """
        Background tasks live in memory, so a restart/redeploy (or Render's idle
        spin-down) drops every complaint still waiting out its delay. Re-queue
        unresolved complaints that never got a resolution record.
        """
        db = SessionLocal()
        try:
            now = get_ist_time()
            pending = (
                db.query(Complaint.id, Complaint.created_at)
                .outerjoin(AgentResolution, AgentResolution.complaint_id == Complaint.id)
                .filter(
                    AgentResolution.id.is_(None),
                    Complaint.is_resolved.isnot(True),
                    Complaint.created_at >= now - RECOVERY_WINDOW,
                )
                .all()
            )
        except Exception as e:
            print(f"❌ Auto-Resolution recovery query failed: {e}")
            return
        finally:
            db.close()

        if pending:
            print(f"🔁 Re-queueing {len(pending)} complaint(s) for auto-resolution")
        for complaint_id, created_at in pending:
            elapsed = (now - created_at).total_seconds() if created_at else AUTO_RESOLVE_DELAY
            asyncio.create_task(
                self.process_complaint(complaint_id, delay=int(AUTO_RESOLVE_DELAY - elapsed))
            )

    async def _resolve(self, complaint_id: int):
        db = SessionLocal()
        try:
            print(f"🚀 Starting Auto-Resolution Pipeline for Complaint ID: {complaint_id}")

            complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if not complaint:
                print(f"❌ Complaint {complaint_id} not found")
                return

            # A human agent may have handled it during the delay
            if complaint.is_resolved:
                print(f"ℹ️ Complaint {complaint_id} already resolved")
                return
            existing_res = db.query(AgentResolution).filter(AgentResolution.complaint_id == complaint_id).first()
            if existing_res:
                print(f"ℹ️ Complaint {complaint_id} already has a resolution record")
                return

            complaint_data = {
                "category": complaint.category,
                "priority": complaint.priority,
                "sentiment": complaint.sentiment,
                "subject": complaint.subject,
                "description": complaint.description or complaint.complaint_text
            }

            # The AI pipeline can come back with an empty solution when the LLMs
            # were unavailable at submit time - generate one now instead of giving up.
            solution = (complaint.solution or "").strip()
            if not solution:
                solution = (await suggest_solution(
                    complaint.category or "Other",
                    f"Subject: {complaint.subject}\nDescription: {complaint_data['description']}"
                ) or "").strip()
            if not solution:
                print(f"❌ No solution could be produced for Complaint {complaint_id}")
                return

            print(f"🔍 Validating solution for {complaint.ticket_id}...")
            validation_result = await multi_model_validator.validate_solution(complaint_data, solution)

            # Below the auto-send bar: rewrite the solution using the validators'
            # feedback and keep whichever version scores higher.
            if validation_result.get("confidence_score", 0) < multi_model_validator.confidence_threshold \
                    and validation_result.get("validation_results"):
                improved = await self._improve_solution(complaint_data, solution, validation_result)
                if improved:
                    improved_result = await multi_model_validator.validate_solution(complaint_data, improved)
                    if improved_result.get("confidence_score", 0) > validation_result.get("confidence_score", 0):
                        print(f"✨ Improved solution scored {improved_result['confidence_score']:.2f} "
                              f"(was {validation_result.get('confidence_score', 0):.2f})")
                        solution, validation_result = improved, improved_result

            admin = db.query(User).filter(User.role == 'Admin').first()
            agent_id = admin.id if admin else 1
            agent_name = "QuickFix AI (System)"

            resolution = AgentResolution(
                complaint_id=complaint.id,
                ticket_id=complaint.ticket_id,
                agent_id=agent_id,
                agent_name=agent_name,
                draft_solution=solution,
                final_solution=solution,
                validation_results=validation_result.get("validation_results"),
                confidence_score=validation_result.get("confidence_score"),
                validation_status=validation_result.get("approval_status"),
                model_agreement_metrics=validation_result.get("model_agreement"),
                status="draft",
                created_at=get_ist_time()
            )
            db.add(resolution)
            db.commit()
            db.refresh(resolution)

            # Store individual model validations for transparency
            for model_result in validation_result.get("validation_results") or []:
                for criterion, score in model_result.get("scores", {}).items():
                    db.add(ModelValidation(
                        resolution_id=resolution.id,
                        model_name=model_result["model"],
                        validation_type=criterion,
                        score=score,
                        feedback=model_result.get("feedback", ""),
                        passed=score >= 0.70,
                        created_at=get_ist_time()
                    ))
            db.commit()

            confidence = validation_result.get("confidence_score", 0)
            if confidence < AUTO_RESOLVE_MIN_CONFIDENCE:
                print(f"⏳ Auto-Resolution held for manual review. Confidence: {confidence:.2f}, "
                      f"Status: {validation_result.get('approval_status')}")
                return

            print(f"✨ Confidence {confidence:.2f} - sending automatic resolution...")
            email_service.send_agent_resolution(
                user_email=complaint.email,
                user_name=complaint.name,
                ticket_id=complaint.ticket_id,
                complaint_subject=complaint.subject or "Your Complaint",
                agent_solution=solution,
                agent_name=agent_name
            )

            now = get_ist_time()
            resolution.status = "delivered"
            resolution.resolution_timestamp = now
            complaint.is_resolved = True
            complaint.solution = solution
            complaint.updated_at = now
            db.commit()
            print(f"✅ Auto-Resolution DELIVERED for {complaint.ticket_id}")

        except Exception as e:
            print(f"❌ Auto-Resolution Error: {e}")
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()

    async def _improve_solution(self, complaint_data: dict, solution: str, validation_result: dict):
        feedback = "\n".join(
            f"- {r.get('feedback', '')}" for r in validation_result.get("validation_results", []) if r.get("feedback")
        )
        recommendations = "\n".join(f"- {r}" for r in validation_result.get("recommendations", []))
        prompt = f"""Rewrite the customer support solution below so it fully resolves the complaint.

COMPLAINT
Category: {complaint_data.get('category')}
Priority: {complaint_data.get('priority')}
Subject: {complaint_data.get('subject')}
Description: {complaint_data.get('description')}

CURRENT SOLUTION
{solution}

REVIEWER FEEDBACK
{feedback or '- (none)'}
{recommendations}

Requirements:
- Address every issue raised in the complaint and every point of reviewer feedback.
- Give clear, numbered, actionable steps with realistic timelines.
- Be empathetic and professional; do not promise anything unsafe or impossible.
- Write in the same language as the current solution.
- Output only the rewritten solution text, with no preamble or headings about the rewrite."""
        try:
            improved = await groq_client.generate(prompt, max_tokens=1200)
        except Exception as e:
            print(f"⚠️ Solution improvement failed: {e}")
            return None
        return improved.strip() if improved else None


auto_resolver = AutoResolver()
