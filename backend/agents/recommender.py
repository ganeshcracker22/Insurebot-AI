"""
Insurance recommendation engine.

Takes user profile (age, income, dependents, has_vehicle, has_house)
and returns recommended insurance products with Ollama-enhanced explanations.
"""

import logging
from typing import List, Dict, Any

from backend.lib.ollama import generate, is_available

logger = logging.getLogger(__name__)

RECOMMENDATION_RULES = [
    {
        "id": "life",
        "type": "Life Insurance",
        "condition": lambda p: p.get("dependents", 0) > 0,
        "reason": "You have dependents who rely on your income.",
        "priority": 1,
    },
    {
        "id": "motor",
        "type": "Motor Insurance",
        "condition": lambda p: p.get("has_vehicle", False),
        "reason": "You own a vehicle that needs protection.",
        "priority": 2,
    },
    {
        "id": "home",
        "type": "Home Insurance",
        "condition": lambda p: p.get("has_house", False),
        "reason": "Your home is a valuable asset requiring coverage.",
        "priority": 2,
    },
    {
        "id": "health",
        "type": "Health Insurance",
        "condition": lambda p: True,
        "reason": "Medical coverage is essential for everyone.",
        "priority": 3,
    },
    {
        "id": "investment",
        "type": "Investment Plan (ULIP)",
        "condition": lambda p: p.get("income", 0) > 1_000_000,
        "reason": "Your high income makes wealth-building investment plans beneficial.",
        "priority": 4,
    },
    {
        "id": "term",
        "type": "Term Life Insurance",
        "condition": lambda p: p.get("age", 0) < 45 and p.get("dependents", 0) > 0,
        "reason": "A term plan offers high coverage at low cost during your earning years.",
        "priority": 1,
    },
    {
        "id": "senior_health",
        "type": "Senior Citizen Health Insurance",
        "condition": lambda p: p.get("age", 0) >= 60,
        "reason": "Specialized health coverage designed for senior citizens.",
        "priority": 2,
    },
]


def get_rule_based_recommendations(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return sorted list of applicable recommendations based on rules."""
    recommendations = []

    for rule in RECOMMENDATION_RULES:
        try:
            if rule["condition"](profile):
                recommendations.append(
                    {
                        "type": rule["type"],
                        "reason": rule["reason"],
                        "priority": rule["priority"],
                    }
                )
        except Exception:
            continue

    recommendations.sort(key=lambda r: r["priority"])
    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec["type"] not in seen:
            seen.add(rec["type"])
            unique_recs.append(rec)

    return unique_recs


def build_explanation_prompt(profile: Dict[str, Any], recommendations: List[Dict]) -> str:
    """Build an Ollama prompt for personalized explanation."""
    rec_list = "\n".join(
        f"- {r['type']}: {r['reason']}" for r in recommendations
    )

    prompt = f"""You are InsureBot, an insurance advisor. A user has provided their profile:

Age: {profile.get('age', 'unknown')}
Annual Income: ₹{profile.get('income', 0):,}
Number of Dependents: {profile.get('dependents', 0)}
Owns Vehicle: {'Yes' if profile.get('has_vehicle') else 'No'}
Owns House: {'Yes' if profile.get('has_house') else 'No'}

Based on this profile, the following insurance products are recommended:
{rec_list}

Please provide a brief, friendly, personalized explanation (3–5 sentences) of why these \
insurance products are suitable for this person. Be conversational and helpful."""

    return prompt


def recommend(profile: Dict[str, Any], model: str = "mistral") -> Dict[str, Any]:
    """
    Generate insurance recommendations for a user profile.

    Args:
        profile: Dict with keys: age, income, dependents, has_vehicle, has_house
        model: Ollama model for explanation generation.

    Returns:
        Dict with 'recommendations' list and 'explanation' string.
    """
    recommendations = get_rule_based_recommendations(profile)

    explanation = ""
    if recommendations and is_available():
        try:
            prompt = build_explanation_prompt(profile, recommendations)
            explanation = generate(prompt, model=model)
        except RuntimeError as exc:
            logger.warning(f"Ollama unavailable for explanation: {exc}")
            explanation = (
                "Based on your profile, we've identified the most suitable insurance "
                "products for you. Please review the recommendations above."
            )
    elif not is_available():
        explanation = (
            "Based on your profile, we've identified the most suitable insurance "
            "products for you. Please review the recommendations above."
        )

    return {
        "profile": profile,
        "recommendations": recommendations,
        "explanation": explanation,
    }
