#!/usr/bin/env python3

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.budget_allocation_service import BudgetAllocationService

def test_budget_allocation():
    """Test the budget allocation system with different scenarios."""
    
    print("💰 Testing Budget Allocation System (30-35% for Hotels)")
    print("=" * 60)
    
    service = BudgetAllocationService()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Budget Trip (5 days, 2 people, $2000)",
            "total_budget": 2000,
            "duration": 5,
            "travelers": 2
        },
        {
            "name": "Mid-Range Trip (7 days, 2 people, $4000)",
            "total_budget": 4000,
            "duration": 7,
            "travelers": 2
        },
        {
            "name": "Luxury Trip (10 days, 2 people, $8000)",
            "total_budget": 8000,
            "duration": 10,
            "travelers": 2
        },
        {
            "name": "Family Trip (7 days, 4 people, $5000)",
            "total_budget": 5000,
            "duration": 7,
            "travelers": 4
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 {scenario['name']}")
        print("-" * 40)
        
        # Calculate budget allocation
        allocation = service.calculate_budget_allocation(
            scenario['total_budget'],
            scenario['duration'],
            scenario['travelers']
        )
        
        if allocation:
            print(f"💰 Total Budget: {allocation['total_estimated_cost']}")
            print(f"\n📊 Budget Breakdown:")
            for category, amount in allocation['budget_breakdown'].items():
                percentage = allocation['budget_percentages'][category]
                print(f"   {category.title()}: {amount} ({percentage})")
            
            print(f"\n🏨 Hotel Budget Allocation:")
            hotel_info = allocation['hotel_budget_allocation']
            print(f"   Allocated Amount: {hotel_info['allocated_amount']} ({hotel_info['percentage']})")
            print(f"   Per Night: {hotel_info['per_night']}")
            print(f"   Per Person Per Night: {hotel_info['per_person_per_night']}")
            print(f"   Recommendation: {hotel_info['recommendation']}")
            
            # Get hotel price range
            price_range = service.get_hotel_price_range(
                scenario['total_budget'],
                scenario['duration'],
                scenario['travelers']
            )
            
            if price_range:
                print(f"\n🏨 Hotel Price Range:")
                budget_range = price_range['budget_range']
                print(f"   Target Price: {budget_range['target_price']}/night")
                print(f"   Recommended Range: {budget_range['min_price']} - {budget_range['max_price']}/night")
                
                recommendations = price_range['hotel_recommendations']
                print(f"   Budget Tier: {recommendations['budget_tier']}")
                print(f"   Suggested Types: {', '.join(recommendations['suggested_types'])}")
                print(f"   Booking Tips:")
                for tip in recommendations['booking_tips'][:3]:  # Show first 3 tips
                    print(f"     • {tip}")
        
        print("\n" + "=" * 60)

def test_hotel_validation():
    """Test hotel validation against budget allocation."""
    
    print("\n🏨 Testing Hotel Validation Against Budget")
    print("=" * 60)
    
    service = BudgetAllocationService()
    
    # Sample hotel data (mock)
    mock_hotels = [
        {"name": "Budget Hotel", "price": 80},
        {"name": "Mid-Range Hotel", "price": 150},
        {"name": "Upscale Hotel", "price": 250},
        {"name": "Luxury Hotel", "price": 400}
    ]
    
    # Test with $3000 budget, 7 days, 2 people
    budget_range = service.get_hotel_price_range(3000, 7, 2)
    
    if budget_range:
        validation = service.validate_hotel_recommendations(mock_hotels, budget_range)
        
        print(f"💰 Budget: $3000 for 7 days, 2 people")
        print(f"🏨 Target Hotel Budget: {budget_range['budget_range']['target_price']}/night")
        print(f"📊 Validation Results:")
        print(f"   Budget-Friendly Hotels: {validation['budget_friendly_count']}")
        print(f"   Over-Budget Hotels: {validation['over_budget_count']}")
        print(f"   Compliance: {validation['budget_compliance']}")
        
        print(f"\n✅ Budget-Friendly Hotels:")
        for hotel in validation['budget_friendly_hotels']:
            print(f"   • {hotel['name']}: ${hotel['price']}/night")
        
        if validation['over_budget_hotels']:
            print(f"\n❌ Over-Budget Hotels:")
            for hotel in validation['over_budget_hotels']:
                print(f"   • {hotel['name']}: ${hotel['price']}/night")

def test_comprehensive_report():
    """Test comprehensive budget report generation."""
    
    print("\n📋 Testing Comprehensive Budget Report")
    print("=" * 60)
    
    service = BudgetAllocationService()
    
    # Generate comprehensive report
    report = service.generate_budget_report(
        total_budget=5000,
        trip_duration=7,
        travelers=2
    )
    
    if report:
        print(f"💰 Budget Report for $5000 Trip (7 days, 2 people)")
        print(f"\n📊 Budget Allocation:")
        allocation = report['budget_allocation']
        for category, amount in allocation['budget_breakdown'].items():
            percentage = allocation['budget_percentages'][category]
            print(f"   {category.title()}: {amount} ({percentage})")
        
        print(f"\n🏨 Hotel Recommendations:")
        price_range = report['hotel_price_range']
        if price_range:
            budget_range = price_range['budget_range']
            print(f"   Target: {budget_range['target_price']}/night")
            print(f"   Range: {budget_range['min_price']} - {budget_range['max_price']}/night")
        
        print(f"\n💡 Cost-Saving Tips:")
        for tip in report['cost_saving_tips']:
            print(f"   • {tip}")

if __name__ == "__main__":
    test_budget_allocation()
    test_hotel_validation()
    test_comprehensive_report()
    
    print("\n🎉 Budget Allocation System Testing Complete!")
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ 30-35% automatic hotel budget allocation")
    print("   ✅ Smart budget breakdown by category")
    print("   ✅ Hotel price range recommendations")
    print("   ✅ Budget validation for hotel recommendations")
    print("   ✅ Comprehensive budget reports")
    print("   ✅ Cost-saving tips based on budget tier") 