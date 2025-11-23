#!/usr/bin/env python3
"""
Standalone test to analyze reservation categorization logic without Django dependencies.
"""

import re

# Sample recommendation from actual CSV
recommendation_text = "Consider using Azure Reserved VM Instances to save money on virtual machines"
potential_benefits = "Reduce virtual machine costs by committing to one or three-year terms"

print("=" * 80)
print("TESTING RESERVATION CATEGORIZATION LOGIC")
print("=" * 80)
print(f"\nRecommendation: {recommendation_text}")
print(f"Benefits: {potential_benefits}")
print()

full_text = f"{recommendation_text} {potential_benefits}".lower()

# Step 1: Check for savings plan keywords
SAVINGS_PLAN_KEYWORDS = [
    'savings plan',
    'compute savings',
    'azure savings plan',
    'savings commitment',
]

is_savings_plan = any(kw in full_text for kw in SAVINGS_PLAN_KEYWORDS)
print(f"Step 1 - Is Savings Plan: {is_savings_plan}")
print(f"  Reason: Checking for keywords {SAVINGS_PLAN_KEYWORDS}")
print()

# Step 2: Check for traditional reservation keywords
TRADITIONAL_RESERVATION_KEYWORDS = [
    'reserved instance',
    'reserved vm instance',
    'reserved capacity',
    'reservation',
    'commit',
    'commitment',
    'reserve',
    'ri ',
    'reserved',
]

# Only check if NOT savings plan
if not is_savings_plan:
    is_traditional_reservation = any(kw in full_text for kw in TRADITIONAL_RESERVATION_KEYWORDS)
    print(f"Step 2 - Is Traditional Reservation: {is_traditional_reservation}")
    print(f"  Keywords found in text:")
    for kw in TRADITIONAL_RESERVATION_KEYWORDS:
        if kw in full_text:
            print(f"    ✓ '{kw}' found")
    print()
else:
    is_traditional_reservation = False
    print("Step 2 - Skipped (already identified as Savings Plan)")
    print()

# Step 3: Extract commitment term
print("Step 3 - Extract Commitment Term:")

# Check for "one or three year" pattern first
if re.search(r'(?:one|1)\s*or\s*(?:three|3)[\s-]*year', full_text, re.IGNORECASE):
    commitment_term = 3
    print(f"  Found 'one or three year' pattern -> defaulting to 3 years")
else:
    found_three_year = bool(re.search(r'(?:three|3)[\s-]*year|36[\s-]*month', full_text, re.IGNORECASE))
    found_one_year = bool(re.search(r'(?:one|1)[\s-]*year|12[\s-]*month', full_text, re.IGNORECASE))

    print(f"  Found 3-year pattern: {found_three_year}")
    print(f"  Found 1-year pattern: {found_one_year}")

    if found_three_year:
        commitment_term = 3
    elif found_one_year:
        commitment_term = 1
    else:
        commitment_term = 3  # Default for reservations
        print(f"  No specific term found -> defaulting to 3 years")

print(f"  Result: {commitment_term} years")
print()

# Step 4: Check for combined commitments
COMBINED_PATTERNS = [
    r'savings\s+plan.*(?:and|with|combined).*reservation',
    r'reservation.*(?:and|with|combined).*savings\s+plan',
    r'savings\s+plan.*\+.*reservation',
    r'reservation.*\+.*savings\s+plan',
]

is_combined = any(re.search(pattern, full_text, re.IGNORECASE) for pattern in COMBINED_PATTERNS)
has_sp = any(kw in full_text for kw in SAVINGS_PLAN_KEYWORDS)
has_reservation = any(kw in full_text for kw in TRADITIONAL_RESERVATION_KEYWORDS)

if has_sp and has_reservation:
    is_combined = True

print(f"Step 4 - Is Combined Commitment: {is_combined}")
print(f"  Has Savings Plan keywords: {has_sp}")
print(f"  Has Reservation keywords: {has_reservation}")
print()

# Step 5: Categorize
print("Step 5 - Final Categorization:")

if is_combined:
    if commitment_term == 1:
        category = 'combined_sp_1y'
    else:
        category = 'combined_sp_3y'
    print(f"  Combined commitment detected")
elif is_savings_plan:
    category = 'pure_savings_plan'
    print(f"  Pure Savings Plan detected")
elif is_traditional_reservation:
    if commitment_term == 1:
        category = 'pure_reservation_1y'
    else:
        category = 'pure_reservation_3y'
    print(f"  Pure traditional reservation detected")
else:
    category = 'uncategorized'
    print(f"  Cannot categorize")

print(f"\n  FINAL CATEGORY: {category}")
print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print("\nSummary:")
print(f"  is_savings_plan: {is_savings_plan}")
print(f"  is_traditional_reservation: {is_traditional_reservation}")
print(f"  commitment_term_years: {commitment_term}")
print(f"  commitment_category: {category}")
print()

if category in ['pure_reservation_1y', 'pure_reservation_3y']:
    print("✓ SUCCESS: This recommendation WOULD appear in pure reservation tables")
    print(f"  Would appear in table: Pure Reserved Instances - {commitment_term} Year")
else:
    print("✗ PROBLEM: This recommendation would NOT appear in pure reservation tables")
    print(f"  Current category: {category}")
