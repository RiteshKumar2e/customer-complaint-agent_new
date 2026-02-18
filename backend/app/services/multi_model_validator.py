"""
Multi-Model Validation Service
Validates agent solutions using multiple Groq LLM models for consensus-based quality assurance
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from app.agents.groq_client import groq_client
import json

class MultiModelValidator:
    """
    Multi-Model Validation Service for Agent Solutions
    Uses 5-10 different Groq models to validate solution quality
    """
    
    def __init__(self):
        self.groq_client = groq_client
        
        # Validation models (Only using confirmed working Groq models)
        self.validation_models = [
            "llama-3.3-70b-versatile",          # Top quality 70B
            "llama-3.1-8b-instant",             # Reliable 8B
            "deepseek-r1-distill-qwen-32b",     # Reasoning specialist
            "qwen-2.5-32b",                     # Balanced specialist
            "llama-3.2-3b-preview",             # Lightweight fast
            "llama-3.2-1b-preview"              # Ultra-fast
        ]
        
        self.min_models = 1  # Minimum models that must respond
        self.max_models = 4  # Reduced models to avoid rate limits
        self.confidence_threshold = 0.85  # Minimum confidence for approval
        
        # Validation criteria weights
        self.criteria_weights = {
            "correctness": 0.30,      # Is the solution technically correct?
            "completeness": 0.25,     # Does it address all aspects?
            "safety": 0.20,           # Is it safe and won't cause harm?
            "actionability": 0.15,    # Can the user actually implement it?
            "clarity": 0.10           # Is it clear and easy to understand?
        }
    
    async def validate_solution(
        self, 
        complaint: Dict, 
        draft_solution: str
    ) -> Dict:
        """
        Validates solution using multiple Groq models
        
        Args:
            complaint: Dict containing complaint details (category, description, etc.)
            draft_solution: The agent's proposed solution
        
        Returns:
            {
                "validation_results": [...],  # List of individual model results
                "confidence_score": 0.85,     # Overall confidence (0-1)
                "approval_status": "approved", # approved, needs_revision, rejected
                "model_agreement": {...},     # Consensus metrics
                "recommendations": [...]      # Suggestions for improvement
            }
        """
        print(f"🔍 Starting multi-model validation with {len(self.validation_models)} models...")
        
        # Run validation on multiple models in parallel
        validation_tasks = []
        for model_name in self.validation_models[:self.max_models]:
            task = self.validate_with_model(model_name, complaint, draft_solution)
            validation_tasks.append(task)
        
        # Wait for all validations to complete (with timeout)
        try:
            validation_results = await asyncio.wait_for(
                asyncio.gather(*validation_tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            print("⚠️  Validation timeout, using partial results...")
            validation_results = []
        
        # Filter out failed validations
        successful_validations = [
            result for result in validation_results 
            if result and not isinstance(result, Exception)
        ]
        
        print(f"✅ Received {len(successful_validations)} successful validations")
        
        # Check if we have minimum required validations
        if len(successful_validations) < self.min_models:
            return {
                "validation_results": successful_validations,
                "confidence_score": 0.0,
                "approval_status": "rejected",
                "model_agreement": {},
                "recommendations": [
                    f"Insufficient model responses ({len(successful_validations)}/{self.min_models} required)",
                    "Please try again or contact system administrator"
                ],
                "error": "Insufficient validation responses"
            }
        
        # Calculate consensus and confidence
        consensus_data = self.calculate_consensus(successful_validations)
        recommendations = self.generate_recommendations(successful_validations, consensus_data)
        
        # Determine approval status
        confidence_score = consensus_data["overall_confidence"]
        if confidence_score >= self.confidence_threshold:
            approval_status = "approved"
        elif confidence_score >= 0.60:
            approval_status = "needs_revision"
        else:
            approval_status = "rejected"
        
        return {
            "validation_results": successful_validations,
            "confidence_score": confidence_score,
            "approval_status": approval_status,
            "model_agreement": consensus_data,
            "recommendations": recommendations
        }
    
    async def validate_with_model(
        self, 
        model_name: str, 
        complaint: Dict, 
        solution: str
    ) -> Optional[Dict]:
        """
        Validates solution with a single model
        
        Returns:
            {
                "model": "llama-3.3-70b-versatile",
                "scores": {
                    "correctness": 0.9,
                    "completeness": 0.85,
                    "safety": 1.0,
                    "actionability": 0.8,
                    "clarity": 0.9
                },
                "overall_score": 0.89,
                "feedback": "...",
                "passed": true
            }
        """
        try:
            # Create validation prompt
            prompt = self._create_validation_prompt(complaint, solution)
            
            # Get validation from model
            if not self.groq_client.client:
                return None
            
            print(f"🤖 Validating with {model_name}...")
            
            response = self.groq_client.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert solution validator. Evaluate the proposed solution based on these criteria:
1. Correctness (0-1): Is the solution technically correct and will it actually solve the problem?
2. Completeness (0-1): Does it address all aspects of the complaint comprehensively?
3. Safety (0-1): Is it safe and won't cause any harm or additional problems?
4. Actionability (0-1): Can the user realistically implement this solution?
5. Clarity (0-1): Is it clear, well-explained, and easy to understand?

Respond ONLY with a valid JSON object in this exact format:
{
    "correctness": 0.9,
    "completeness": 0.85,
    "safety": 1.0,
    "actionability": 0.8,
    "clarity": 0.9,
    "feedback": "Brief explanation of your assessment"
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model_name,
                temperature=0.3,  # Lower temperature for more consistent validation
                max_tokens=500,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                scores = json.loads(result_text)
            except json.JSONDecodeError:
                print(f"⚠️  Failed to parse JSON from {model_name}")
                return None
            
            # Calculate overall score
            overall_score = sum(
                scores.get(criterion, 0) * weight 
                for criterion, weight in self.criteria_weights.items()
            )
            
            # Determine if passed
            passed = overall_score >= self.confidence_threshold
            
            validation_result = {
                "model": model_name,
                "scores": {
                    "correctness": scores.get("correctness", 0),
                    "completeness": scores.get("completeness", 0),
                    "safety": scores.get("safety", 0),
                    "actionability": scores.get("actionability", 0),
                    "clarity": scores.get("clarity", 0)
                },
                "overall_score": round(overall_score, 3),
                "feedback": scores.get("feedback", "No feedback provided"),
                "passed": passed
            }
            
            print(f"✅ {model_name}: {overall_score:.2f} ({'PASS' if passed else 'FAIL'})")
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Validation failed with {model_name}: {e}")
            return None
    
    def _create_validation_prompt(self, complaint: Dict, solution: str) -> str:
        """Creates the validation prompt for the model"""
        return f"""
COMPLAINT DETAILS:
Category: {complaint.get('category', 'Unknown')}
Priority: {complaint.get('priority', 'Unknown')}
Sentiment: {complaint.get('sentiment', 'Unknown')}
Subject: {complaint.get('subject', 'N/A')}
Description: {complaint.get('description', complaint.get('complaint_text', 'N/A'))}

PROPOSED SOLUTION:
{solution}

Please evaluate this solution based on the 5 criteria and provide scores (0-1) and feedback.
"""
    
    def calculate_consensus(self, validation_results: List[Dict]) -> Dict:
        """
        Calculates consensus score and agreement metrics
        
        Returns:
            {
                "overall_confidence": 0.85,
                "criteria_averages": {...},
                "agreement_rate": 0.80,
                "models_passed": 7,
                "models_failed": 1,
                "total_models": 8
            }
        """
        if not validation_results:
            return {
                "overall_confidence": 0.0,
                "criteria_averages": {},
                "agreement_rate": 0.0,
                "models_passed": 0,
                "models_failed": 0,
                "total_models": 0
            }
        
        # Calculate average scores for each criterion
        criteria_averages = {}
        for criterion in self.criteria_weights.keys():
            scores = [
                result["scores"].get(criterion, 0) 
                for result in validation_results
            ]
            criteria_averages[criterion] = round(sum(scores) / len(scores), 3)
        
        # Calculate overall confidence (weighted average)
        overall_confidence = sum(
            criteria_averages[criterion] * weight 
            for criterion, weight in self.criteria_weights.items()
        )
        
        # Calculate agreement rate (how many models passed)
        models_passed = sum(1 for result in validation_results if result.get("passed", False))
        models_failed = len(validation_results) - models_passed
        agreement_rate = models_passed / len(validation_results)
        
        return {
            "overall_confidence": round(overall_confidence, 3),
            "criteria_averages": criteria_averages,
            "agreement_rate": round(agreement_rate, 3),
            "models_passed": models_passed,
            "models_failed": models_failed,
            "total_models": len(validation_results)
        }
    
    def generate_recommendations(
        self, 
        validation_results: List[Dict], 
        consensus_data: Dict
    ) -> List[str]:
        """
        Generates recommendations for improvement based on validation results
        """
        recommendations = []
        
        # Check each criterion
        criteria_averages = consensus_data.get("criteria_averages", {})
        
        for criterion, avg_score in criteria_averages.items():
            if avg_score < 0.70:
                recommendations.append(
                    f"⚠️  {criterion.capitalize()}: Score is low ({avg_score:.2f}). "
                    f"Please improve this aspect of the solution."
                )
        
        # Check agreement rate
        agreement_rate = consensus_data.get("agreement_rate", 0)
        if agreement_rate < 0.60:
            recommendations.append(
                f"⚠️  Low model agreement ({agreement_rate:.0%}). "
                f"Consider revising the solution for better consensus."
            )
        
        # Add positive feedback if all good
        if not recommendations and consensus_data.get("overall_confidence", 0) >= 0.85:
            recommendations.append(
                "✅ Excellent solution! All validation criteria passed with high confidence."
            )
        
        return recommendations

# Global instance
multi_model_validator = MultiModelValidator()
