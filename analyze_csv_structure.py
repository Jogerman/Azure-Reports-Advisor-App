#!/usr/bin/env python3
"""
Analyze Azure Advisor CSV structure for Saving Plans and Reservations.
This script examines how 1-year and 3-year terms are structured in the CSV.
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_csv_structure(csv_path):
    """Analyze the CSV structure for Saving Plans and Reservations."""

    print("=" * 80)
    print("AZURE ADVISOR CSV STRUCTURE ANALYSIS")
    print("=" * 80)

    # Read CSV
    print(f"\nReading CSV file: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    # Print all column names
    print("\n" + "=" * 80)
    print("COLUMN NAMES")
    print("=" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2}. {col}")

    # Filter for Saving Plans and Reservations
    print("\n" + "=" * 80)
    print("SAVING PLANS AND RESERVATIONS DETECTION")
    print("=" * 80)

    # Find Savings Plans
    savings_plan_mask = df['Recommendation'].str.contains(
        'savings plan',
        case=False,
        na=False
    )
    savings_plans = df[savings_plan_mask]

    print(f"\nSavings Plans found: {len(savings_plans)}")

    # Find Reserved Instances
    reserved_instance_mask = df['Recommendation'].str.contains(
        'reserved instance|reservation',
        case=False,
        na=False
    ) & ~savings_plan_mask  # Exclude savings plans

    reserved_instances = df[reserved_instance_mask]

    print(f"Reserved Instances found: {len(reserved_instances)}")

    # Analyze Savings Plans
    if len(savings_plans) > 0:
        print("\n" + "=" * 80)
        print("SAVINGS PLANS ANALYSIS")
        print("=" * 80)

        print("\nSample Savings Plan recommendations:")
        for idx, row in savings_plans.head(5).iterrows():
            print(f"\n--- Row {idx + 2} ---")
            print(f"Recommendation: {row['Recommendation']}")
            print(f"Potential Benefits: {row['Potential benefits']}")
            print(f"Annual Savings: {row['Potential Annual Cost Savings']}")
            print(f"Currency: {row['Potential Cost Savings Currency']}")

            # Check for year mentions in text
            full_text = f"{row['Recommendation']} {row['Potential benefits']}".lower()
            if '1-year' in full_text or 'one year' in full_text:
                print(">>> CONTAINS: 1-year term")
            if '3-year' in full_text or 'three year' in full_text:
                print(">>> CONTAINS: 3-year term")
            if '1 or 3 year' in full_text or 'one or three year' in full_text:
                print(">>> CONTAINS: 1 or 3 year options")

    # Analyze Reserved Instances
    if len(reserved_instances) > 0:
        print("\n" + "=" * 80)
        print("RESERVED INSTANCES ANALYSIS")
        print("=" * 80)

        print("\nSample Reserved Instance recommendations:")
        for idx, row in reserved_instances.head(5).iterrows():
            print(f"\n--- Row {idx + 2} ---")
            print(f"Recommendation: {row['Recommendation']}")
            print(f"Potential Benefits: {row['Potential benefits']}")
            print(f"Annual Savings: {row['Potential Annual Cost Savings']}")
            print(f"Currency: {row['Potential Cost Savings Currency']}")

            # Check for year mentions in text
            full_text = f"{row['Recommendation']} {row['Potential benefits']}".lower()
            if '1-year' in full_text or 'one year' in full_text:
                print(">>> CONTAINS: 1-year term")
            if '3-year' in full_text or 'three year' in full_text:
                print(">>> CONTAINS: 3-year term")
            if '1 or 3 year' in full_text or 'one or three year' in full_text:
                print(">>> CONTAINS: 1 or 3 year options")

    # Check if there are separate columns for 1-year vs 3-year savings
    print("\n" + "=" * 80)
    print("CHECKING FOR SEPARATE YEAR COLUMNS")
    print("=" * 80)

    year_related_cols = [col for col in df.columns if 'year' in col.lower() or '1' in col or '3' in col]
    if year_related_cols:
        print("\nPotential year-related columns found:")
        for col in year_related_cols:
            print(f"  - {col}")
    else:
        print("\nNo separate columns found for 1-year vs 3-year data")

    # Look for savings-related columns
    print("\n" + "=" * 80)
    print("SAVINGS-RELATED COLUMNS")
    print("=" * 80)

    savings_cols = [col for col in df.columns if 'saving' in col.lower() or 'cost' in col.lower()]
    print("\nSavings/Cost columns:")
    for col in savings_cols:
        print(f"  - {col}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    total_reservations = len(savings_plans) + len(reserved_instances)
    print(f"\nTotal Saving Plans: {len(savings_plans)}")
    print(f"Total Reserved Instances: {len(reserved_instances)}")
    print(f"Total Reservation Recommendations: {total_reservations}")
    print(f"Percentage of all recommendations: {total_reservations / len(df) * 100:.2f}%")

    # Calculate total savings
    sp_savings = savings_plans['Potential Annual Cost Savings'].sum()
    ri_savings = reserved_instances['Potential Annual Cost Savings'].sum()

    print(f"\nTotal Annual Savings from Saving Plans: ${sp_savings:,.2f}")
    print(f"Total Annual Savings from Reserved Instances: ${ri_savings:,.2f}")
    print(f"Total Annual Savings from Reservations: ${sp_savings + ri_savings:,.2f}")

    # Analyze unique recommendation types
    print("\n" + "=" * 80)
    print("UNIQUE RESERVATION RECOMMENDATION TYPES")
    print("=" * 80)

    all_reservations = pd.concat([savings_plans, reserved_instances])
    unique_recommendations = all_reservations['Recommendation'].unique()

    print(f"\nFound {len(unique_recommendations)} unique reservation recommendation types:\n")
    for i, rec in enumerate(unique_recommendations, 1):
        count = (all_reservations['Recommendation'] == rec).sum()
        total = all_reservations[all_reservations['Recommendation'] == rec]['Potential Annual Cost Savings'].sum()
        print(f"{i}. {rec}")
        print(f"   Count: {count}, Total Annual Savings: ${total:,.2f}\n")

    # CRITICAL: Check how Azure distinguishes 1-year vs 3-year
    print("\n" + "=" * 80)
    print("CRITICAL FINDING: HOW ARE 1-YEAR VS 3-YEAR DISTINGUISHED?")
    print("=" * 80)

    print("\nChecking if Azure Advisor CSV provides separate rows for different terms...")

    # Check if same resource appears multiple times with different terms
    if len(all_reservations) > 0:
        # Group by subscription to see if there are duplicates
        subscription_counts = all_reservations['Subscription ID'].value_counts()

        if any(subscription_counts > 1):
            print("\nFound subscriptions with multiple reservation recommendations:")
            for sub_id, count in subscription_counts.head(3).items():
                if count > 1:
                    print(f"\nSubscription: {sub_id} ({count} recommendations)")
                    sub_recs = all_reservations[all_reservations['Subscription ID'] == sub_id]
                    for idx, row in sub_recs.iterrows():
                        print(f"  - {row['Recommendation'][:80]}...")
        else:
            print("\nNo duplicates found - each subscription has unique recommendations")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    csv_path = "/Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/Context_docs/universal.csv"

    if not Path(csv_path).exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    analyze_csv_structure(csv_path)
