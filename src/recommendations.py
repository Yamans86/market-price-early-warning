from __future__ import annotations


def generate_recommendation(alert_level: str) -> dict[str, object]:
    """Map alert levels to humanitarian cash programming recommendations."""
    recommendations = {
        "Normal": {
            "action": "Continue routine market monitoring.",
            "rationale": "Prices are within the expected range based on recent market history.",
            "checks": [
                "Maintain monthly price monitoring for minimum expenditure basket items.",
                "Review transfer values during the normal program cycle.",
                "Keep triangulating with trader and household feedback.",
            ],
        },
        "Watch": {
            "action": "Increase monitoring frequency and validate the price signal.",
            "rationale": "Prices are moving above normal levels but do not yet require an immediate response change.",
            "checks": [
                "Check whether the increase is seasonal or linked to a temporary supply disruption.",
                "Compare with nearby markets and secondary price sources.",
                "Prepare transfer-value scenarios in case prices continue rising.",
            ],
        },
        "Alert": {
            "action": "Prepare transfer-value adjustment options.",
            "rationale": "Price stress is high enough to threaten purchasing power if the trend persists.",
            "checks": [
                "Estimate basket affordability under 10%, 20%, and 30% price increases.",
                "Consult traders on stock levels, restocking constraints, and payment liquidity.",
                "Coordinate with cash working group partners before changing transfer values.",
            ],
        },
        "Critical": {
            "action": "Trigger urgent market review and transfer-value recalculation.",
            "rationale": "Prices show severe stress that may undermine cash assistance adequacy.",
            "checks": [
                "Run a rapid market assessment within 72 hours.",
                "Consider temporary top-ups, split payments, or mixed assistance.",
                "Review whether markets remain functional and accessible for targeted households.",
            ],
        },
    }

    return recommendations.get(alert_level, recommendations["Normal"])
