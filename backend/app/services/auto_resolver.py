from app.db.database import get_ist_time, SessionLocal
from app.db.models import Complaint, AgentResolution, ModelValidation, User
from app.services.multi_model_validator import multi_model_validator
from app.services.email_service import email_service
import asyncio

class AutoResolver:
    """
    Automatic Resolution Service
    Orchestrates the autonomous validation and delivery of AI solutions
    """
    
    async def process_complaint(self, complaint_id: int):
        \"\"\"
        Runs the full autonomous resolution pipeline for a complaint
        \"\"\"
        db = SessionLocal()
        try:
            print(f"🚀 Starting Auto-Resolution Pipeline for Complaint ID: {complaint_id}")
            
            # 1. Get complaint
            complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if not complaint:
                print(f"❌ Complaint {complaint_id} not found")
                return
            
            # Check if already resolved or has resolution
            existing_res = db.query(AgentResolution).filter(AgentResolution.complaint_id == complaint_id).first()
            if existing_res:
                print(f"ℹ️ Complaint {complaint_id} already has a resolution record")
                return

            # 2. Extract solution from AI analysis
            solution = complaint.solution
            if not solution:
                print(f"❌ No solution found for Complaint {complaint_id}")
                return
            
            # 3. Prepare data for validation
            complaint_data = {
                "category": complaint.category,
                "priority": complaint.priority,
                "sentiment": complaint.sentiment,
                "subject": complaint.subject,
                "description": complaint.description or complaint.complaint_text
            }
            
            # 4. Run multi-model validation (Consensus building)
            print(f"🔍 Validating solution for {complaint.ticket_id}...")
            validation_result = await multi_model_validator.validate_solution(
                complaint_data,
                solution
            )
            
            # 5. Create AgentResolution record (QuickFix AI as the agent)
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
            if validation_result.get("validation_results"):
                for model_result in validation_result["validation_results"]:
                    # Handle nested scores dict
                    scores = model_result.get("scores", {})
                    for criterion, score in scores.items():
                        model_validation = ModelValidation(
                            resolution_id=resolution.id,
                            model_name=model_result["model"],
                            validation_type=criterion,
                            score=score,
                            feedback=model_result.get("feedback", ""),
                            passed=score >= 0.70,
                            created_at=get_ist_time()
                        )
                        db.add(model_validation)
                db.commit()

            # 6. Deliver automatically if confidence is very high (>= 85%)
            # This implements the "Automatic Mail" requirement
            confidence = validation_result.get("confidence_score", 0)
            status = validation_result.get("approval_status")
            
            if status == "approved" and confidence >= 0.85:
                print(f"✨ High confidence ({confidence:.2f}) detected. Sending automatic resolution...")
                
                try:
                    email_service.send_agent_resolution(
                        user_email=complaint.email,
                        user_name=complaint.name,
                        ticket_id=complaint.ticket_id,
                        complaint_subject=complaint.subject or "Your Complaint",
                        agent_solution=solution,
                        agent_name=agent_name
                    )
                    
                    # Update status to delivered
                    resolution.status = "delivered"
                    resolution.resolution_timestamp = get_ist_time()
                    
                    # Mark complaint as resolved in main table
                    complaint.is_resolved = True
                    complaint.updated_at = get_ist_time()
                    
                    db.commit()
                    print(f"✅ Auto-Resolution DELIVERED safely for {complaint.ticket_id}")
                except Exception as e:
                    print(f"❌ Auto-Resolution Delivery Failed: {e}")
                    db.rollback()
            else:
                print(f"⏳ Auto-Resolution held for manual review. Confidence: {confidence:.2f}, Status: {status}")
                
        except Exception as e:
            print(f"❌ Auto-Resolution Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

auto_resolver = AutoResolver()
