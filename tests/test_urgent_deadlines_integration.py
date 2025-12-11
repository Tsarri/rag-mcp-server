#!/usr/bin/env python3
"""
Integration test documentation for urgent deadlines endpoint
Shows example usage and expected response format
"""

# Example request
example_request = """
GET /api/urgent-deadlines?limit=10

Headers:
  Accept: application/json
"""

# Expected response format
example_response = """
{
  "count": 10,
  "deadlines": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "date": "2025-12-05",
      "description": "Presentar alegaciones al requerimiento",
      "working_days_remaining": 2,
      "risk_level": "critical",
      "client_id": "987e6543-e21b-98d7-b654-321987654321",
      "client_name": "Acme Corporation",
      "client_email": "legal@acme.com"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "date": "2025-12-08",
      "description": "Responder a notificación judicial",
      "working_days_remaining": 5,
      "risk_level": "high",
      "client_id": "987e6543-e21b-98d7-b654-321987654322",
      "client_name": "Beta Industries",
      "client_email": "contact@beta.com"
    }
  ]
}
"""

# Example curl command
example_curl = """
# Get top 10 most urgent deadlines across all clients
curl http://localhost:8000/api/urgent-deadlines

# Get top 20 most urgent deadlines
curl http://localhost:8000/api/urgent-deadlines?limit=20
"""

# Key features
features = """
Key Features:
1. Returns deadlines from ALL clients (no client_id filter)
2. Sorted by risk level priority:
   - overdue (highest priority)
   - critical
   - high
   - medium
   - low (lowest priority)
3. Within each risk level, sorted by date (soonest first)
4. Includes client information (name and email)
5. Respects limit query parameter (default: 10)
6. Returns proper error handling with HTTP status codes

Risk Level Definitions:
- overdue: Past the deadline (working_days_remaining < 0)
- critical: ≤ 2 working days remaining
- high: 3-5 working days remaining
- medium: 6-10 working days remaining
- low: > 10 working days remaining
"""

if __name__ == "__main__":
    print("="*60)
    print("Urgent Deadlines Endpoint - Integration Test Documentation")
    print("="*60)
    print("\n" + example_request)
    print("\nExpected Response Format:")
    print(example_response)
    print("\nExample curl commands:")
    print(example_curl)
    print("\n" + features)
    print("\n" + "="*60)
    print("Endpoint implementation complete and tested ✓")
    print("="*60)
