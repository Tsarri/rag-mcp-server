"""
Deadline Agent Wrapper
Integrates deadline extraction functionality into MCP server
Based on: https://github.com/dr-p1n/v2-demos-deadline.agent-agentta
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from anthropic import Anthropic
from supabase import create_client, Client
import holidays
import json


class DeadlineAgent:
    """
    Extract deadlines from text using Claude AI.
    Calculates working days and assigns risk levels.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, anthropic_key: str = None):
        """Initialize the deadline agent with API credentials"""
        print("Initializing Deadline Agent...")
        
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
        
        # Panama holidays calendar for working day calculations
        self.panama_holidays = holidays.Panama()
        
        print("✓ Deadline Agent ready")
    
    def calculate_working_days(self, target_date: datetime) -> int:
        """
        Calculate working days between today and target date.
        Excludes weekends and Panama public holidays.
        
        Args:
            target_date: The deadline date
            
        Returns:
            Number of working days (negative if overdue)
        """
        today = datetime.now().date()
        target = target_date.date() if isinstance(target_date, datetime) else target_date
        
        # Check if deadline has passed
        if target < today:
            return -1
        
        # Count working days
        working_days = 0
        current = today
        
        while current < target:
            current += timedelta(days=1)
            # Skip weekends (Mon=0, Tue=1, ..., Sat=5, Sun=6)
            # Skip Panama holidays
            if current.weekday() < 5 and current not in self.panama_holidays:
                working_days += 1
        
        return working_days
    
    def assess_risk_level(self, working_days: int) -> str:
        """
        Assess urgency based on working days remaining.
        
        Risk levels:
        - overdue: Past the deadline
        - critical: ≤ 2 working days
        - high: 3-5 working days
        - medium: 6-10 working days
        - low: > 10 working days
        
        Args:
            working_days: Number of working days until deadline
            
        Returns:
            Risk level string
        """
        if working_days < 0:
            return "overdue"
        elif working_days <= 2:
            return "critical"
        elif working_days <= 5:
            return "high"
        elif working_days <= 10:
            return "medium"
        else:
            return "low"
    
    async def extract_deadlines(self, text: str, source_id: str = None, client_id: str = None, gemini_context: Dict = None) -> Dict:
        """
        Extract all deadlines from text using Claude AI.
        
        This method:
        1. Sends text to Claude for deadline extraction
        2. Parses the response to get dates and descriptions
        3. Calculates working days for each deadline
        4. Assigns risk levels
        5. Stores everything in Supabase
        
        Args:
            text: Text to analyze (can be email, document, message, etc.)
            source_id: Optional identifier for tracking (e.g., "document:report.pdf")
            client_id: Optional client UUID to associate deadlines with a client
            
        Returns:
            Dict with:
                - extraction_id: UUID of the extraction record
                - deadlines: List of extracted deadlines with risk info
                - count: Number of deadlines found
        """
        try:
            # Construct the prompt for Claude with today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Build Gemini context hint if available
            gemini_hint = ""
            if gemini_context and gemini_context.get('dates_and_deadlines'):
                dates = gemini_context['dates_and_deadlines']
                if dates:
                    gemini_hint = "\nNOTE: Another AI model identified these dates in the document:\n"
                    for date_item in dates[:5]:  # Limit to 5 items
                        date_str = date_item.get('date', '')
                        desc = date_item.get('description', '')
                        importance = date_item.get('importance', '')
                        gemini_hint += f"- {date_str}: {desc} ({importance} importance)\n"
                    gemini_hint += "\nUse these as hints, but verify against the full text.\n\n"
            
            prompt = f"""You are analyzing a legal notification in Spanish. Today's date is {today}.
{gemini_hint}
Extract ALL deadlines, due dates, and time-sensitive legal obligations from the text below.

For each deadline:
1. Calculate the EXACT calendar date in YYYY-MM-DD format
2. If the text says "X días" (X days), calculate from today: {today}
3. If it says "días hábiles" (working days), still calculate calendar days (we'll adjust later)
4. Provide a brief description in Spanish of what is due

Text to analyze:
{text}

Respond with ONLY valid JSON in this exact format:
{{
    "deadlines": [
        {{"date": "YYYY-MM-DD", "description": "brief description in Spanish"}},
        {{"date": "YYYY-MM-DD", "description": "brief description in Spanish"}}
    ]
}}

If no deadlines found, respond with:
{{"deadlines": []}}

CRITICAL RULES:
- Calculate exact dates from "X días" relative to today ({today})
- "Tiene 20 días para..." means the deadline is {today} + 20 days
- "tiene 15 días hábiles" means {today} + 15 days (calendar)
- Always output YYYY-MM-DD format
- Return ONLY valid JSON, nothing else
- Descriptions in Spanish, under 100 characters

Examples:
- "Tiene 20 días para presentar" → date is 20 days from {today}
- "5 días hábiles contados desde hoy" → date is 5 days from {today}
- "30 días para aceptar o rechazar" → date is 30 days from {today}
"""

            # Call Claude API
            print(f"  → Calling Claude AI to extract deadlines...")
            
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Get the response text
            response_text = response.content[0].text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if "```" in response_text:
                # Extract content between ```json and ```
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                else:
                    response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                print(f"  Response was: {response_text[:300]}")
                result = {"deadlines": []}
            
            deadlines_data = result.get("deadlines", [])
            
            # Create extraction record in database
            extraction_record = {
                "source_id": source_id or f"manual-{int(datetime.now().timestamp())}",
                "text": text[:2000],  # Store first 2000 characters
                "extracted_count": len(deadlines_data),
                "extraction_timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            
            extraction_response = self.supabase.table('deadline_extractions').insert(extraction_record).execute()
            extraction_id = extraction_response.data[0]['id']
            
            print(f"  ✓ Created extraction record: {extraction_id}")
            
            # Process each deadline
            processed_deadlines = []
            
            for idx, deadline in enumerate(deadlines_data):
                try:
                    # Parse date
                    deadline_date = datetime.strptime(deadline['date'], '%Y-%m-%d')
                    
                    # Calculate working days and assess risk
                    working_days = self.calculate_working_days(deadline_date)
                    risk_level = self.assess_risk_level(working_days)
                    
                    # Prepare deadline record
                    deadline_record = {
                        "extraction_id": extraction_id,
                        "date": deadline['date'],
                        "description": deadline['description'],
                        "working_days_remaining": working_days,
                        "risk_level": risk_level,
                        "source_id": source_id,
                        "client_id": client_id
                    }
                    
                    # Insert into database and capture the response
                    response = self.supabase.table('deadlines').insert(deadline_record).execute()
                    
                    # Get the database-generated ID from the response
                    deadline_id = None
                    if response.data and len(response.data) > 0:
                        deadline_id = response.data[0]['id']
                    
                    # Add to results with the database ID
                    processed_deadlines.append({
                        "id": deadline_id,  # ✅ FIX: Include the database ID
                        "date": deadline['date'],
                        "description": deadline['description'],
                        "working_days_remaining": working_days,
                        "risk_level": risk_level
                    })
                    
                    if deadline_id:
                        print(f"  ✓ Deadline {idx + 1}: {deadline['date']} (ID: {deadline_id}) - {deadline['description'][:40]}... [{risk_level.upper()}]")
                    else:
                        print(f"  ⚠️ Deadline {idx + 1}: {deadline['date']} - {deadline['description'][:40]}... [{risk_level.upper()}] (ID not available)")
                
                except ValueError as e:
                    print(f"  ⚠️ Invalid date format '{deadline.get('date', 'N/A')}': {e}")
                    continue
                except KeyError as e:
                    print(f"  ⚠️ Missing field in deadline data: {e}")
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error processing deadline: {e}")
                    continue
            
            print(f"  ✓ Successfully processed {len(processed_deadlines)}/{len(deadlines_data)} deadlines")
            
            return {
                "extraction_id": extraction_id,
                "deadlines": processed_deadlines,
                "count": len(processed_deadlines)
            }
        
        except Exception as e:
            print(f"  ✗ Error in extract_deadlines: {e}")
            raise
    
    async def get_deadlines_by_risk(self, risk_level: str = None, client_id: str = None) -> List[Dict]:
        """
        Retrieve stored deadlines, optionally filtered by risk level and client.
        
        Args:
            risk_level: One of 'overdue', 'critical', 'high', 'medium', 'low', or None for all
            client_id: Optional client UUID to filter by
            
        Returns:
            List of deadline records from database
        """
        try:
            query = self.supabase.table('deadlines').select('*')
            
            if risk_level:
                query = query.eq('risk_level', risk_level.lower())
            
            if client_id:
                query = query.eq('client_id', client_id)
            
            # Order by date (soonest first)
            query = query.order('date', desc=False)
            
            response = query.execute()
            return response.data
        
        except Exception as e:
            print(f"Error fetching deadlines: {e}")
            raise
    
    async def get_upcoming_deadlines(self, days: int = 7, client_id: str = None) -> List[Dict]:
        """
        Get deadlines occurring within the next N days.
        
        Args:
            days: Number of days to look ahead
            client_id: Optional client UUID to filter by
            
        Returns:
            List of upcoming deadline records
        """
        try:
            today = datetime.now().date().isoformat()
            future_date = (datetime.now() + timedelta(days=days)).date().isoformat()
            
            query = self.supabase.table('deadlines')\
                .select('*')\
                .gte('date', today)\
                .lte('date', future_date)
            
            if client_id:
                query = query.eq('client_id', client_id)
            
            query = query.order('date', desc=False)
            
            response = query.execute()
            return response.data
        
        except Exception as e:
            print(f"Error fetching upcoming deadlines: {e}")
            raise
    
    async def get_stats(self, client_id: str = None) -> Dict:
        """
        Get statistics about stored deadlines.
        
        Args:
            client_id: Optional client UUID to filter by
        
        Returns:
            Dict with counts by risk level and total
        """
        try:
            # Get all deadlines
            query = self.supabase.table('deadlines').select('risk_level')
            
            if client_id:
                query = query.eq('client_id', client_id)
            
            all_deadlines = query.execute()
            
            # Count by risk level
            stats = {
                "total": len(all_deadlines.data),
                "overdue": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for deadline in all_deadlines.data:
                risk = deadline.get('risk_level', '').lower()
                if risk in stats:
                    stats[risk] += 1
            
            return stats
        
        except Exception as e:
            print(f"Error getting stats: {e}")
            raise