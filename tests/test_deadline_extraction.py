#!/usr/bin/env python3
"""
Test deadline extraction with legal notification emails
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from agents.deadline_agent import DeadlineAgent

load_dotenv()

async def test_single_email():
    """Test deadline extraction on a single legal notification"""
    
    # Initialize the agent
    print("Initializing Deadline Agent...")
    agent = DeadlineAgent()
    
    # Test email from your JSON
    test_email = """
    Asunto: Notificación de demanda - Juzgado XX de lo Civil
    De: notificaciones@juzgado3.gob.pa
    
    Se notifica que ha sido demandado en el proceso 2024-8013 iniciado por Juan Pérez. 
    Tiene 20 días para presentar su contestación de demanda.
    """
    
    print("\n" + "="*60)
    print("Testing deadline extraction...")
    print("="*60)
    print(f"\nEmail text:\n{test_email}\n")
    
    # Extract deadlines
    result = await agent.extract_deadlines(
        text=test_email,
        source_id="test-email-001"
    )
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Deadlines found: {result['count']}")
    print(f"Extraction ID: {result['extraction_id']}\n")
    
    if result['deadlines']:
        for i, deadline in enumerate(result['deadlines'], 1):
            print(f"Deadline {i}:")
            print(f"  Date: {deadline['date']}")
            print(f"  Description: {deadline['description']}")
            print(f"  Working days: {deadline['working_days_remaining']}")
            print(f"  Risk level: {deadline['risk_level']}")
            print()
    else:
        print("No deadlines extracted!")
    
    # Expected result from your JSON
    print("="*60)
    print("EXPECTED RESULT (from your JSON)")
    print("="*60)
    print("Date: 2025-12-12")
    print("Days: 20")
    print("Working days: false")
    print("Description: Period for settlement before trial")
    print("Risk: medio")

async def test_all_emails():
    """Test all emails from the JSON file"""
    
    # Load the JSON file
    json_path = '/mnt/user-data/uploads/test_deadline_agent.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        emails = json.load(f)
    
    print(f"Loaded {len(emails)} test emails")
    
    # Initialize agent
    agent = DeadlineAgent()
    
    # Test each email
    results = []
    
    for idx, email in enumerate(emails, 1):
        print(f"\n{'='*60}")
        print(f"Testing email {idx}/{len(emails)}: {email['subject']}")
        print(f"{'='*60}")
        
        # Extract deadlines
        result = await agent.extract_deadlines(
            text=f"Asunto: {email['subject']}\n\n{email['body']}",
            source_id=email['email_id']
        )
        
        # Compare with expected
        expected = email['expected_deadline']
        
        comparison = {
            'email_id': email['email_id'],
            'subject': email['subject'],
            'extracted_count': result['count'],
            'expected_date': expected['date'],
            'extracted_dates': [d['date'] for d in result['deadlines']],
            'match': expected['date'] in [d['date'] for d in result['deadlines']] if result['deadlines'] else False
        }
        
        results.append(comparison)
        
        # Print result
        if comparison['match']:
            print(f"✓ MATCH - Extracted correct deadline: {expected['date']}")
        else:
            print(f"✗ MISMATCH")
            print(f"  Expected: {expected['date']}")
            print(f"  Got: {comparison['extracted_dates']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    total = len(results)
    matches = sum(1 for r in results if r['match'])
    print(f"Total emails: {total}")
    print(f"Correct extractions: {matches}")
    print(f"Accuracy: {matches/total*100:.1f}%")

if __name__ == "__main__":
    # Choose which test to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        asyncio.run(test_all_emails())
    else:
        asyncio.run(test_single_email())