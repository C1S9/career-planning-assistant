"""Fictitious plans for local checks; no personal data or real API requests."""


def plan_data(days=3):
    return {
        "summary": "Explore career directions using business study and retail experience.",
        "assumptions": ["Some time is available outside work."],
        "duration_days": days,
        "tasks": [
            {
                "title": f"Exploration task {number}",
                "action": "Write a short comparison note.",
                "start_day": min(number, days),
                "end_day": min(number, days),
                "reason": "Uses the stated business and retail background.",
                "completion_criterion": "One written comparison note.",
            }
            for number in range(1, 4)
        ],
    }
