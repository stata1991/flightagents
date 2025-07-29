#!/usr/bin/env python3

import re

def test_budget_extraction():
    """Test budget extraction patterns directly"""
    
    # Test queries
    test_queries = [
        "from New York to Orlando on August 10th for 5 days with 2 adults budget $1000",
        "I want to go to Disney World from New York on August 10th for 5 days with 3 adults and 1 child, budget $1000",
        "budget $1000",
        "1000 dollars",
        "1000$",
        "1000 usd",
        "budget 1000",
        "1000 budget"
    ]
    
    # Budget patterns from the code
    budget_patterns = [
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1000, $1,000, $1000.50
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1000 dollars, 1,000 dollar
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1000$, 1,000$
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*usd',  # 1000 usd, 1,000 USD
        r'budget\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # budget 1000
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*budget'  # 1000 budget
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print(f"Query length: {len(query)}")
        
        query_lower = query.lower()
        print(f"Query lower: '{query_lower}'")
        
        for i, pattern in enumerate(budget_patterns):
            match = re.search(pattern, query_lower)
            print(f"Pattern {i}: {pattern} - Match: {match}")
            if match:
                budget_str = match.group(1).replace(',', '')
                try:
                    budget_amount = float(budget_str)
                    print(f"✅ Found budget amount: ${budget_amount}")
                    break
                except ValueError:
                    print(f"❌ Failed to parse budget string: {budget_str}")
                    continue
        else:
            print("❌ No budget amount found")

if __name__ == "__main__":
    test_budget_extraction() 