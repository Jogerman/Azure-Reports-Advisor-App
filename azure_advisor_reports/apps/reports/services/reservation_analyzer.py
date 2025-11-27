"""
Service for analyzing Azure Advisor recommendations to identify and classify
Saving Plans and Reserved Instances.

Version 2.0 - Enhanced Multi-Dimensional Analysis

This service analyzes recommendation text to:
1. Detect if a recommendation is related to reservations/savings plans
2. Classify the type of reservation (Reserved Instance, Savings Plan, etc.)
3. Extract commitment term duration (1 or 3 years)
4. Distinguish between Savings Plans and traditional reservations (NEW)
5. Detect combined commitments (Savings Plans + Reservations) (NEW)
6. Auto-categorize into granular taxonomy (NEW)
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ReservationAnalyzer:
    """
    Analyzes Azure Advisor recommendations to identify and extract
    information about Reserved Instances and Savings Plans.

    Version 2.0 - Enhanced with multi-dimensional categorization
    """

    # Savings Plan specific keywords (distinct from traditional reservations)
    SAVINGS_PLAN_KEYWORDS = [
        'savings plan',
        'compute savings',
        'azure savings plan',
        'savings commitment',
        'purchasing a savings plan',  # NEW - Azure Advisor format
        'purchase a savings plan',     # NEW - variation
        'buy a savings plan',          # NEW - variation
        'consider purchasing a savings plan',  # NEW - full phrase from Azure Advisor
    ]

    # Traditional reservation keywords (excluding savings plans)
    TRADITIONAL_RESERVATION_KEYWORDS = [
        'reserved instance',
        'reserved vm instance',
        'reserved capacity',
        'reservation',
        'commit',
        'commitment',
        'reserve',
        'ri ',  # Abbreviation for Reserved Instance
        'reserved',
        # NEW - Azure Advisor specific phrases
        'consider virtual machine reserved instance',
        'consider cosmos db reserved instance',
        'consider sql paas db reserved instance',
        'consider app service reserved instance',
        'consider database for mysql reserved instance',
        'consider blob storage reserved instance',
        'consider suselinux reserved instance',
        'consider azure synapse analytics',
        'purchasing reserved instance',
        'purchase reserved instance',
        'buy reserved instance',
    ]

    # Combined list for general reservation detection
    RESERVATION_KEYWORDS = SAVINGS_PLAN_KEYWORDS + TRADITIONAL_RESERVATION_KEYWORDS

    # Combined commitment patterns
    COMBINED_COMMITMENT_PATTERNS = [
        r'savings\s+plan.*(?:and|with|combined).*reservation',
        r'reservation.*(?:and|with|combined).*savings\s+plan',
        r'savings\s+plan.*\+.*reservation',
        r'reservation.*\+.*savings\s+plan',
    ]

    # Patterns for extracting commitment terms
    COMMITMENT_PATTERNS = [
        r'(?:one|1)[\s-]*year',  # "one year", "1 year", "1-year"
        r'(?:three|3)[\s-]*year',  # "three year", "3 year", "3-year"
        r'(?:one|1)\s*or\s*(?:three|3)[\s-]*year',  # "one or three year"
        r'1\s*or\s*3[\s-]*year',  # "1 or 3 year"
        r'(?:12|36)[\s-]*month',  # "12 month", "36 month"
    ]

    # Reservation type patterns
    TYPE_PATTERNS = {
        'reserved_instance': [
            r'reserved\s+(?:vm\s+)?instance',
            r'\bri\b',  # Abbreviation
            r'vm\s+reservation',
        ],
        'savings_plan': [
            r'savings?\s+plan',
            r'compute\s+savings',
        ],
        'reserved_capacity': [
            r'reserved\s+capacity',
            r'database\s+reservation',
            r'cosmos\s+db\s+reservation',
            r'storage\s+reservation',
        ],
    }

    @staticmethod
    def is_reservation_recommendation(recommendation_text: str, potential_benefits: str = '') -> bool:
        """
        Determine if a recommendation is related to reservations or savings plans.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text (optional)

        Returns:
            bool: True if this is a reservation recommendation
        """
        if not recommendation_text:
            logger.debug("No recommendation text provided, returning False")
            return False

        # Combine all text for analysis
        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Check for reservation keywords
        for keyword in ReservationAnalyzer.RESERVATION_KEYWORDS:
            if keyword in full_text:
                logger.info(f"✓ DETECTED RESERVATION: keyword '{keyword}' in: {recommendation_text[:100]}")
                return True

        # Log when we DON'T detect a reservation (for debugging)
        # Only log if the text contains cost-related terms to reduce noise
        if any(term in full_text for term in ['cost', 'saving', 'price', 'purchase', 'buy']):
            logger.debug(f"✗ NOT DETECTED as reservation (cost-related): {recommendation_text[:100]}")

        return False

    @staticmethod
    def extract_reservation_type(recommendation_text: str, potential_benefits: str = '') -> Optional[str]:
        """
        Extract the type of reservation from the recommendation text.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text (optional)

        Returns:
            str: One of 'reserved_instance', 'savings_plan', 'reserved_capacity', or 'other'
        """
        if not recommendation_text:
            return None

        # Combine all text for analysis
        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Check each type pattern
        for reservation_type, patterns in ReservationAnalyzer.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    logger.debug(f"Matched reservation type: {reservation_type} with pattern: {pattern}")
                    return reservation_type

        # If we know it's a reservation but can't classify it specifically
        if ReservationAnalyzer.is_reservation_recommendation(recommendation_text, potential_benefits):
            return 'other'

        return None

    @staticmethod
    def extract_commitment_term(recommendation_text: str, potential_benefits: str = '') -> Optional[int]:
        """
        Extract the commitment term (1 or 3 years) from the recommendation text.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text (optional)

        Returns:
            int: 1 or 3 (years), or None if no commitment term found
        """
        if not recommendation_text:
            return None

        # Combine all text for analysis
        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Track which terms we find
        found_one_year = False
        found_three_year = False

        # Check for "one or three year" pattern first (most common in Azure Advisor)
        if re.search(r'(?:one|1)\s*or\s*(?:three|3)[\s-]*year', full_text, re.IGNORECASE):
            # FIXED: This means both options are available but CSV doesn't specify which
            # Return None to indicate the term is a user choice, not specified in data
            logger.debug("Found 'one or three year' pattern - term is user choice, returning None")
            return None

        # Check for specific year mentions
        if re.search(r'(?:three|3)[\s-]*year|36[\s-]*month', full_text, re.IGNORECASE):
            found_three_year = True

        if re.search(r'(?:one|1)[\s-]*year|12[\s-]*month', full_text, re.IGNORECASE):
            found_one_year = True

        # If we found both (but not in "or" pattern), prefer 3 years
        if found_three_year:
            logger.debug("Found 3-year commitment term")
            return 3
        elif found_one_year:
            logger.debug("Found 1-year commitment term")
            return 1

        # FIXED: Don't default to any term if unknown - Azure CSV doesn't provide this info
        # Return None to indicate term is not specified in the recommendation
        if ReservationAnalyzer.is_reservation_recommendation(recommendation_text, potential_benefits):
            logger.debug("Reservation detected but no specific term found - returning None (term unknown)")
            return None

        return None

    @classmethod
    def is_savings_plan(cls, recommendation_text: str, potential_benefits: str = '') -> bool:
        """
        Determine if recommendation is specifically for Azure Savings Plan.

        Savings Plans are flexible, compute-focused commitments that provide
        discounts across VM families, sizes, and regions.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text

        Returns:
            bool: True if this is a Savings Plan recommendation
        """
        if not recommendation_text:
            return False

        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Check for Savings Plan specific keywords
        for keyword in cls.SAVINGS_PLAN_KEYWORDS:
            if keyword in full_text:
                logger.debug(f"Identified as Savings Plan: keyword '{keyword}'")
                return True

        return False

    @classmethod
    def is_traditional_reservation(cls, recommendation_text: str, potential_benefits: str = '') -> bool:
        """
        Determine if recommendation is for traditional reservation (RI, RC).

        Traditional reservations are resource-specific commitments for
        specific VM SKUs, databases, or capacity.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text

        Returns:
            bool: True if traditional reservation (NOT Savings Plan)
        """
        if not recommendation_text:
            return False

        # First check if it's a Savings Plan (takes precedence)
        if cls.is_savings_plan(recommendation_text, potential_benefits):
            return False

        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Check for traditional reservation keywords
        for keyword in cls.TRADITIONAL_RESERVATION_KEYWORDS:
            if keyword in full_text:
                logger.debug(f"Identified as traditional reservation: keyword '{keyword}'")
                return True

        return False

    @classmethod
    def is_combined_commitment(cls, recommendation_text: str, potential_benefits: str = '') -> bool:
        """
        Detect if recommendation involves BOTH Savings Plans AND Reservations.

        Some Azure Advisor recommendations suggest combining Savings Plans
        with specific Reservations for optimal savings.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text

        Returns:
            bool: True if recommendation involves both types
        """
        if not recommendation_text:
            return False

        full_text = f"{recommendation_text} {potential_benefits}".lower()

        # Check for combined commitment patterns
        for pattern in cls.COMBINED_COMMITMENT_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                logger.debug(f"Identified as combined commitment: pattern '{pattern}'")
                return True

        # Alternative detection: has both SP and Reservation keywords
        has_sp = any(kw in full_text for kw in cls.SAVINGS_PLAN_KEYWORDS)
        has_reservation = any(kw in full_text for kw in cls.TRADITIONAL_RESERVATION_KEYWORDS)

        if has_sp and has_reservation:
            logger.debug("Identified as combined commitment: contains both SP and Reservation keywords")
            return True

        return False

    @classmethod
    def categorize_commitment(
        cls,
        recommendation_text: str,
        potential_benefits: str = '',
        commitment_term_years: Optional[int] = None,
    ) -> str:
        """
        Categorize recommendation into granular commitment category.

        Returns one of:
        - 'pure_reservation_1y': Traditional reservation, 1 year
        - 'pure_reservation_3y': Traditional reservation, 3 years
        - 'pure_savings_plan': Savings Plan only
        - 'combined_sp_1y': Savings Plan + 1-year reservation
        - 'combined_sp_3y': Savings Plan + 3-year reservation
        - 'uncategorized': Cannot determine

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text
            commitment_term_years: Extracted commitment term

        Returns:
            str: Category identifier
        """
        # Check for combined commitments first
        if cls.is_combined_commitment(recommendation_text, potential_benefits):
            if commitment_term_years == 1:
                return 'combined_sp_1y'
            elif commitment_term_years == 3:
                return 'combined_sp_3y'
            else:
                # FIXED: Don't default - term is unknown
                return 'combined_sp_unknown_term'

        # Check for pure Savings Plan
        if cls.is_savings_plan(recommendation_text, potential_benefits):
            return 'pure_savings_plan'

        # Check for traditional reservations
        if cls.is_traditional_reservation(recommendation_text, potential_benefits):
            if commitment_term_years == 1:
                return 'pure_reservation_1y'
            elif commitment_term_years == 3:
                return 'pure_reservation_3y'
            else:
                # FIXED: Don't default - term is unknown
                return 'pure_reservation_unknown_term'

        return 'uncategorized'

    @classmethod
    def analyze_recommendation(
        cls,
        recommendation_text: str,
        potential_benefits: str = ''
    ) -> Dict[str, any]:
        """
        Perform complete multi-dimensional analysis of a recommendation.

        Enhanced to include Savings Plan detection and categorization.

        Args:
            recommendation_text: The recommendation description
            potential_benefits: Additional benefits text (optional)

        Returns:
            dict: Analysis results with keys:
                - is_reservation: bool
                - reservation_type: str or None
                - commitment_term_years: int or None
                - is_savings_plan: bool (NEW)
                - commitment_category: str (NEW)
        """
        is_reservation = cls.is_reservation_recommendation(recommendation_text, potential_benefits)

        result = {
            'is_reservation': is_reservation,
            'reservation_type': None,
            'commitment_term_years': None,
            'is_savings_plan': False,
            'commitment_category': 'uncategorized',
        }

        # Only extract additional details if it's a reservation
        if is_reservation:
            result['reservation_type'] = cls.extract_reservation_type(
                recommendation_text, potential_benefits
            )
            result['commitment_term_years'] = cls.extract_commitment_term(
                recommendation_text, potential_benefits
            )

            # NEW: Determine if Savings Plan
            result['is_savings_plan'] = cls.is_savings_plan(
                recommendation_text, potential_benefits
            )

            # NEW: Categorize into granular taxonomy
            result['commitment_category'] = cls.categorize_commitment(
                recommendation_text,
                potential_benefits,
                result['commitment_term_years']
            )

        logger.info(
            f"Enhanced reservation analysis: "
            f"is_reservation={result['is_reservation']}, "
            f"type={result['reservation_type']}, "
            f"term={result['commitment_term_years']} years, "
            f"is_savings_plan={result['is_savings_plan']}, "
            f"category={result['commitment_category']}"
        )

        return result

    @staticmethod
    def calculate_total_commitment_savings(
        annual_savings: float,
        commitment_term_years: Optional[int]
    ) -> float:
        """
        Calculate total savings over the commitment period.

        Args:
            annual_savings: Annual cost savings
            commitment_term_years: Commitment term (1 or 3 years)

        Returns:
            float: Total savings over commitment period
        """
        if commitment_term_years and annual_savings:
            return annual_savings * commitment_term_years
        return annual_savings or 0

    @staticmethod
    def format_reservation_summary(
        reservation_type: Optional[str],
        commitment_term_years: Optional[int],
        annual_savings: float,
        currency: str = 'USD'
    ) -> str:
        """
        Format a human-readable summary of reservation savings.

        Args:
            reservation_type: Type of reservation
            commitment_term_years: Commitment term in years
            annual_savings: Annual cost savings
            currency: Currency code

        Returns:
            str: Formatted summary text
        """
        if not reservation_type:
            return f"Annual savings: {currency} {annual_savings:,.2f}"

        type_display = {
            'reserved_instance': 'Reserved VM Instance',
            'savings_plan': 'Savings Plan',
            'reserved_capacity': 'Reserved Capacity',
            'other': 'Reservation',
        }.get(reservation_type, 'Reservation')

        total_savings = ReservationAnalyzer.calculate_total_commitment_savings(
            annual_savings, commitment_term_years
        )

        if commitment_term_years:
            return (
                f"{type_display} ({commitment_term_years}-year commitment): "
                f"{currency} {annual_savings:,.2f}/year "
                f"({currency} {total_savings:,.2f} total commitment savings)"
            )
        else:
            return f"{type_display}: {currency} {annual_savings:,.2f}/year"
