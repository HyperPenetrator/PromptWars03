"""
Prompt builder for the EcoTrace Gemini agent.

Aggregates recent emission logs into a structured summary
that Gemini can reason over.
"""

from models import EmissionLog, EMISSION_FACTORS

SYSTEM_PROMPT = """\
You are EcoTrace, a friendly and knowledgeable carbon footprint coach.
You help individuals understand and reduce their environmental impact.

Rules:
- Be specific and data-driven. Always cite the CO₂e figures from the user's log.
- Rank suggestions by impact (high CO₂e savings first), then by ease.
- Never shame the user. Frame everything as opportunity, not failure.
- Keep responses under 250 words. Use bullet points for action items.
- If data is insufficient, ask 1 clarifying question — never more.

Respond in this JSON structure:
{
  "summary": "1–2 sentence overview of the user's week",
  "top_emission": {"category": "...", "co2e_kg": 0.0, "percentage": 0},
  "suggestions": [
    {"action": "...", "potential_saving_kg": 0.0, "difficulty": "easy|medium|hard"},
    ...
  ],
  "encouragement": "1 sentence motivational note"
}
"""


def build_user_prompt(logs: list[EmissionLog]) -> str:
    """
    Build a human-readable summary of the user's emission logs
    for the Gemini agent to analyze.
    """

    if not logs:
        return (
            "The user has no emission logs for this period. "
            "Ask them what activities they'd like to start tracking."
        )

    # Aggregate by category
    by_category: dict[str, float] = {}
    by_subtype: dict[str, float] = {}
    total = 0.0

    for log in logs:
        by_category[log.category] = by_category.get(log.category, 0) + log.co2e_kg
        label = f"{log.category}/{log.sub_type}"
        by_subtype[label] = by_subtype.get(label, 0) + log.co2e_kg
        total += log.co2e_kg

    # Build the prompt text
    lines = [
        f"## User Emission Summary ({len(logs)} entries, {round(total, 2)} kg CO₂e total)",
        "",
        "### By Category:",
    ]

    for cat, co2 in sorted(by_category.items(), key=lambda x: -x[1]):
        pct = round((co2 / total) * 100, 1) if total > 0 else 0
        lines.append(f"- {cat}: {round(co2, 2)} kg ({pct}%)")

    lines.append("")
    lines.append("### Detailed Breakdown:")

    for label, co2 in sorted(by_subtype.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- {label}: {round(co2, 2)} kg")

    lines.append("")
    lines.append(
        "Analyze this data and provide personalized suggestions "
        "to reduce the user's carbon footprint. Focus on the highest-impact areas."
    )

    return "\n".join(lines)


def build_weekly_prompt(logs: list[EmissionLog], previous_total: float | None = None) -> str:
    """
    Build a weekly summary prompt, optionally comparing to the previous week.
    """

    base = build_user_prompt(logs)

    if previous_total is not None:
        current_total = sum(log.co2e_kg for log in logs)
        delta = current_total - previous_total
        direction = "increase" if delta > 0 else "decrease"
        base += (
            f"\n\nCompared to last week ({round(previous_total, 2)} kg), "
            f"this is a {abs(round(delta, 2))} kg {direction}. "
            "Comment on this trend."
        )

    return base
