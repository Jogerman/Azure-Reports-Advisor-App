#!/usr/bin/env python3
"""
Test script to analyze how ReservationAnalyzer categorizes the sample recommendation.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sample recommendation from CSV
recommendation_text = "Consider using Azure Reserved VM Instances to save money on virtual machines"
potential_benefits = "Reduce virtual machine costs by committing to one or three-year terms"

print("=" * 80)
print("TESTING RESERVATION ANALYZER")
print("=" * 80)
print(f"\nRecommendation: {recommendation_text}")
print(f"Benefits: {potential_benefits}")
print()

# Import after path setup
from apps.reports.services.reservation_analyzer import ReservationAnalyzer

# Analyze the recommendation
result = ReservationAnalyzer.analyze_recommendation(recommendation_text, potential_benefits)

print("ANALYSIS RESULT:")
print("-" * 80)
for key, value in result.items():
    print(f"{key:30}: {value}")

print("\n" + "=" * 80)
print("EXPECTED vs ACTUAL")
print("=" * 80)
print(f"Expected commitment_category: pure_reservation_3y (default when '1 or 3 year' found)")
print(f"Actual commitment_category:   {result['commitment_category']}")
print()
print(f"Expected commitment_term_years: 3 (default for '1 or 3 year')")
print(f"Actual commitment_term_years:   {result['commitment_term_years']}")
print()
print(f"Expected is_savings_plan: False")
print(f"Actual is_savings_plan:   {result['is_savings_plan']}")
print()

# Test individual methods
print("\n" + "=" * 80)
print("DETAILED BREAKDOWN")
print("=" * 80)

print(f"\n1. is_reservation_recommendation(): {ReservationAnalyzer.is_reservation_recommendation(recommendation_text, potential_benefits)}")
print(f"2. is_savings_plan(): {ReservationAnalyzer.is_savings_plan(recommendation_text, potential_benefits)}")
print(f"3. is_traditional_reservation(): {ReservationAnalyzer.is_traditional_reservation(recommendation_text, potential_benefits)}")
print(f"4. is_combined_commitment(): {ReservationAnalyzer.is_combined_commitment(recommendation_text, potential_benefits)}")
print(f"5. extract_reservation_type(): {ReservationAnalyzer.extract_reservation_type(recommendation_text, potential_benefits)}")
print(f"6. extract_commitment_term(): {ReservationAnalyzer.extract_commitment_term(recommendation_text, potential_benefits)}")
print(f"7. categorize_commitment(): {ReservationAnalyzer.categorize_commitment(recommendation_text, potential_benefits, result['commitment_term_years'])}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if result['commitment_category'] in ['pure_reservation_1y', 'pure_reservation_3y']:
    print("✓ SUCCESS: Recommendation would be categorized for display in pure reservation tables")
else:
    print("✗ PROBLEM: Recommendation NOT categorized for pure reservation tables")
    print(f"  Current category: {result['commitment_category']}")
    print(f"  This is why the tables are empty!")
