from __future__ import annotations


REPORT_MODES = {
    "Standard Report": {
        "label": "Standard Report",
        "instruction": (
            "Write a balanced scouting report that covers current value, translatable strengths, "
            "development runway, and a realistic future projection."
        ),
    },
    "High-Upside Prospect": {
        "label": "High-Upside Prospect",
        "instruction": (
            "Emphasize long-term growth indicators, athletic tools, skill scalability, and why the player "
            "could outperform current production over time."
        ),
    },
    "Defensive Specialist": {
        "label": "Defensive Specialist",
        "instruction": (
            "Frame the evaluation through defensive impact, effort profile, versatility, anticipation, "
            "physical tools, and how the player can anchor winning possessions."
        ),
    },
    "Lead Guard Evaluation": {
        "label": "Lead Guard Evaluation",
        "instruction": (
            "Evaluate the player through lead-guard responsibilities such as decision-making, pace control, "
            "ball-screen utility, creation, communication, and late-game reliability."
        ),
    },
    "College Recruiter Version": {
        "label": "College Recruiter Version",
        "instruction": (
            "Write for a college recruiting audience. Prioritize role fit, recruitable traits, developmental "
            "ceiling, culture fit, and how the player may translate into a college program."
        ),
    },
}


def build_system_prompt() -> str:
    return (
        "You are an elite basketball scouting writer and evaluator. "
        "Write concise, professional scouting reports for evaluators and recruiters. "
        "Keep the tone developmental and constructive. "
        "Do not use harsh or dismissive language. "
        "Do not invent measurements, background details, or statistics that were not provided. "
        "Every report must be between 150 and 250 words."
    )


def build_user_prompt(player_record: dict[str, object], mode: str) -> str:
    mode_config = REPORT_MODES[mode]
    notable_moments = str(player_record.get("Notable Game Moments", "")).strip() or "No specific game moment notes were provided."

    return f"""
Create a basketball scouting report using the following requirements:

- Output length: 150-250 words.
- Tone: positive, developmental, and professional.
- Highlight strengths clearly.
- Frame growth opportunities as development areas without negative wording.
- Include a future projection.
- Mode emphasis: {mode_config['instruction']}

Player profile:
- Player Name: {player_record['Player Name']}
- Team: {player_record['Team']}
- Grade: {player_record['Grade']}
- Position: {player_record['Position']}
- Strengths: {player_record['Strengths']}
- Development Areas: {player_record['Development Areas']}
- Notable Game Moments: {notable_moments}
- Projection: {player_record['Projection']}
- Skill Score: {player_record['Skill Score']}
- Athleticism Score: {player_record['Athleticism Score']}
- Basketball IQ Score: {player_record['Basketball IQ Score']}
- Growth Upside Score: {player_record['Growth Upside Score']}

Formatting guidance:
- Write as 2 short paragraphs.
- Use specific basketball language.
- Mention the player's name in the opening sentence.
- End with a forward-looking projection statement.
""".strip()
