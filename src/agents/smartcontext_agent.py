"""
SmartContext Agent Wrapper
Integrates strategic analytics functionality into MCP server
Based on: https://github.com/dr-p1n/v2-demos-SmartContext.agent-agentta
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic
from supabase import create_client, Client


class SmartContextAgent:
    """
    Strategic analytics agent that aggregates data and generates insights.
    Performs business intelligence analysis using Claude AI.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, anthropic_key: str = None):
        """Initialize the SmartContext agent with API credentials"""
        print("Initializing SmartContext Agent...")
        
        # Get credentials from parameters or environment
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        self.anthropic_key = anthropic_key or os.getenv('ANTHROPIC_API_KEY')
        
        # Validate credentials
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials (SUPABASE_URL, SUPABASE_KEY)")
        
        if not self.anthropic_key:
            raise ValueError("Missing Anthropic API key (ANTHROPIC_API_KEY)")
        
        # Initialize API clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.anthropic = Anthropic(api_key=self.anthropic_key)
        
        print("✓ SmartContext Agent ready")
    
    async def analyze_deadline_risk(self, firm_id: str, deadline_data: Dict) -> Dict:
        """
        Analyze deadline risk based on deadline statistics.
        
        Args:
            firm_id: Identifier for the firm/user
            deadline_data: Dict with:
                - upcoming_deadlines: Total count
                - overdue_tasks: Count of overdue
                - deadlines_next_7_days: Count in next week
                - critical_deadlines: Count of critical priority
                - high_deadlines: Count of high priority
                
        Returns:
            Strategic analysis with insights and recommendations
        """
        return await self._perform_analysis(
            firm_id=firm_id,
            analysis_type="deadline_risk",
            data=deadline_data
        )
    
    async def analyze_caseload_health(self, firm_id: str, caseload_data: Dict) -> Dict:
        """
        Analyze workload distribution and capacity.
        
        Args:
            firm_id: Identifier for the firm/user
            caseload_data: Dict with:
                - total_cases: Total active cases
                - active_attorneys: Number of attorneys
                - avg_case_duration_days: Average duration
                - cases_by_status: Dict of status counts
                
        Returns:
            Strategic analysis with capacity insights
        """
        return await self._perform_analysis(
            firm_id=firm_id,
            analysis_type="caseload_health",
            data=caseload_data
        )
    
    async def analyze_profitability_trends(self, firm_id: str, financial_data: Dict) -> Dict:
        """
        Analyze financial performance and trends.
        
        Args:
            firm_id: Identifier for the firm/user
            financial_data: Dict with:
                - monthly_revenue: Total revenue
                - billable_hours: Hours billed
                - realization_rate: Collection rate
                - revenue_by_practice: Dict by practice area
                
        Returns:
            Strategic financial analysis
        """
        return await self._perform_analysis(
            firm_id=firm_id,
            analysis_type="profitability_trends",
            data=financial_data
        )
    
    async def _perform_analysis(self, firm_id: str, analysis_type: str, data: Dict) -> Dict:
        """
        Core analysis function that sends data to Claude for strategic insights.
        
        Args:
            firm_id: Identifier for the firm/user
            analysis_type: Type of analysis (deadline_risk, caseload_health, profitability_trends)
            data: Input data for analysis
            
        Returns:
            Dict with analysis results
        """
        try:
            print(f"  → Performing {analysis_type} analysis...")
            
            # Build analysis-specific prompt
            if analysis_type == "deadline_risk":
                prompt = self._build_deadline_risk_prompt(data)
            elif analysis_type == "caseload_health":
                prompt = self._build_caseload_health_prompt(data)
            elif analysis_type == "profitability_trends":
                prompt = self._build_profitability_prompt(data)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # Call Claude API
            print(f"  → Calling Claude AI for strategic analysis...")
            
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Get the response text
            response_text = response.content[0].text.strip()
            
            # Clean up response
            if "```" in response_text:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                else:
                    response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                print(f"  Response was: {response_text[:500]}")
                # Fallback result
                analysis_result = {
                    "key_insights": ["Analysis could not be completed"],
                    "action_items": [],
                    "metrics": {},
                    "summary": "Error processing analysis",
                    "risk_level": "unknown",
                    "confidence": 0.0
                }
            
            # Store in database
            db_record = {
                "firm_id": firm_id,
                "analysis_type": analysis_type,
                "input_data": data,
                "key_insights": analysis_result.get("key_insights", []),
                "action_items": analysis_result.get("action_items", []),
                "metrics": analysis_result.get("metrics", {}),
                "summary": analysis_result.get("summary", ""),
                "risk_level": analysis_result.get("risk_level", "unknown"),
                "confidence": analysis_result.get("confidence", 0.0)
            }
            
            result = self.supabase.table('analyses').insert(db_record).execute()
            analysis_id = result.data[0]['id']
            
            print(f"  ✓ Analysis complete: {analysis_result.get('summary', 'No summary')[:60]}...")
            print(f"  ✓ Risk level: {analysis_result.get('risk_level', 'unknown')}")
            print(f"  ✓ Confidence: {analysis_result.get('confidence', 0):.0%}")
            
            return {
                "analysis_id": analysis_id,
                "firm_id": firm_id,
                "analysis_type": analysis_type,
                "result": analysis_result
            }
        
        except Exception as e:
            print(f"  ✗ Error performing analysis: {e}")
            raise
    
    def _build_deadline_risk_prompt(self, data: Dict) -> str:
        """Build prompt for deadline risk analysis"""
        return f"""You are a strategic business analyst for a law firm. Analyze the following deadline data and provide strategic insights.

Data:
{json.dumps(data, indent=2)}

Provide a strategic analysis in ONLY valid JSON format:
{{
    "key_insights": [
        "First major insight about deadline patterns",
        "Second insight about risk exposure",
        "Third insight about capacity"
    ],
    "action_items": [
        "Specific action to mitigate risk",
        "Resource allocation recommendation",
        "Process improvement suggestion"
    ],
    "metrics": {{
        "overall_risk_score": 0.75,
        "capacity_utilization": 0.85,
        "deadline_adherence_rate": 0.92
    }},
    "summary": "One sentence executive summary of the situation",
    "risk_level": "one of: low, medium, high, critical",
    "confidence": 0.95
}}

Focus on:
- Deadline concentration and distribution patterns
- Capacity vs demand assessment
- Risk mitigation strategies
- Resource allocation recommendations

Return ONLY the JSON, no other text."""

    def _build_caseload_health_prompt(self, data: Dict) -> str:
        """Build prompt for caseload health analysis"""
        return f"""You are a strategic business analyst for a law firm. Analyze the following caseload data and provide strategic insights.

Data:
{json.dumps(data, indent=2)}

Provide a strategic analysis in ONLY valid JSON format:
{{
    "key_insights": [
        "Major insight about workload distribution",
        "Capacity utilization finding",
        "Efficiency or bottleneck observation"
    ],
    "action_items": [
        "Workload rebalancing recommendation",
        "Resource allocation suggestion",
        "Process optimization step"
    ],
    "metrics": {{
        "capacity_utilization": 0.87,
        "workload_balance_score": 0.65,
        "efficiency_trend": 0.15
    }},
    "summary": "One sentence executive summary",
    "risk_level": "one of: low, medium, high, critical",
    "confidence": 0.95
}}

Focus on:
- Attorney workload distribution
- Capacity vs caseload assessment
- Efficiency opportunities
- Resource optimization strategies

Return ONLY the JSON, no other text."""

    def _build_profitability_prompt(self, data: Dict) -> str:
        """Build prompt for profitability analysis"""
        return f"""You are a strategic financial analyst for a law firm. Analyze the following financial data and provide strategic insights.

Data:
{json.dumps(data, indent=2)}

Provide a strategic analysis in ONLY valid JSON format:
{{
    "key_insights": [
        "Major financial performance insight",
        "Revenue trend observation",
        "Profitability driver finding"
    ],
    "action_items": [
        "Revenue optimization recommendation",
        "Cost management suggestion",
        "Practice area strategy"
    ],
    "metrics": {{
        "revenue_growth_rate": 0.12,
        "profit_margin": 0.35,
        "efficiency_ratio": 0.78
    }},
    "summary": "One sentence executive summary",
    "risk_level": "one of: low, medium, high, critical",
    "confidence": 0.95
}}

Focus on:
- Revenue trends and patterns
- Profitability by practice area
- Realization rate optimization
- Financial health indicators

Return ONLY the JSON, no other text."""

    async def get_recent_analyses(self, firm_id: str, analysis_type: str = None, limit: int = 10) -> List[Dict]:
        """
        Get recent analyses for a firm.
        
        Args:
            firm_id: Identifier for the firm/user
            analysis_type: Optional filter by analysis type
            limit: Maximum number of results
            
        Returns:
            List of analysis records
        """
        try:
            query = self.supabase.table('analyses').select('*').eq('firm_id', firm_id)
            
            if analysis_type:
                query = query.eq('analysis_type', analysis_type)
            
            query = query.order('created_at', desc=True).limit(limit)
            
            response = query.execute()
            return response.data
        
        except Exception as e:
            print(f"Error fetching analyses: {e}")
            raise
    
    async def get_analysis_stats(self, firm_id: str) -> Dict:
        """
        Get statistics about analyses performed.
        
        Args:
            firm_id: Identifier for the firm/user
            
        Returns:
            Dict with analysis statistics
        """
        try:
            # Get all analyses for firm
            all_analyses = self.supabase.table('analyses').select('analysis_type, risk_level').eq('firm_id', firm_id).execute()
            
            stats = {
                "total": len(all_analyses.data),
                "by_type": {
                    "deadline_risk": 0,
                    "caseload_health": 0,
                    "profitability_trends": 0
                },
                "by_risk": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0,
                    "unknown": 0
                }
            }
            
            for analysis in all_analyses.data:
                analysis_type = analysis.get('analysis_type', '')
                risk_level = analysis.get('risk_level', 'unknown')
                
                if analysis_type in stats['by_type']:
                    stats['by_type'][analysis_type] += 1
                
                if risk_level in stats['by_risk']:
                    stats['by_risk'][risk_level] += 1
            
            return stats
        
        except Exception as e:
            print(f"Error getting analysis stats: {e}")
            raise