"""Strict task-plan contracts and checks independent of the model provider."""

from typing import Annotated, Literal, NotRequired, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

MIN_PLAN_DAYS = 1
MAX_PLAN_DAYS = 365
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ChatMessage(TypedDict):
    """Visible chat data, with an optional application-owned validation marker."""

    role: Literal["user", "assistant"]
    content: str
    schedule_checked: NotRequired[bool]
    evidence: NotRequired[dict | None]


class PlanValidationError(ValueError):
    """Describe a plan-rule failure without exposing model output or user data."""


class Task(BaseModel):
    # Strict mode rejects numeric strings and booleans where integers are needed.
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=1_500)
    start_day: int = Field(ge=1)
    end_day: int = Field(ge=1)
    reason: ShortText
    completion_criterion: ShortText

    @model_validator(mode="after")
    def check_day_order(self) -> Self:
        # A task cannot end before it starts, regardless of the plan's length.
        if self.end_day < self.start_day:
            raise ValueError("A task must end on or after its start day.")
        return self


class CareerPlan(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=1_500)
    assumptions: list[ShortText] = Field(max_length=8)
    duration_days: int = Field(ge=MIN_PLAN_DAYS, le=MAX_PLAN_DAYS)
    tasks: list[Task] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def check_schedule(self) -> Self:
        # These rules inspect real field values; a prompt cannot enforce them.
        if self.tasks[0].start_day != 1:
            raise ValueError("The first task must start on day 1.")
        if any(task.end_day > self.duration_days for task in self.tasks):
            raise ValueError("Every task must fit within the planning period.")
        starts = [task.start_day for task in self.tasks]
        if starts != sorted(starts):
            raise ValueError("Tasks must be ordered by start day.")
        # Overlap is allowed: independent tasks may be done in parallel.
        return self


def validate_duration(duration_days: int) -> None:
    """Check the person's selected duration before any paid request is made."""
    if type(duration_days) is not int or not MIN_PLAN_DAYS <= duration_days <= MAX_PLAN_DAYS:
        raise PlanValidationError("Choose a whole-number planning period from 1 to 365 days.")


def parse_plan(raw: str, *, expected_days: int) -> CareerPlan:
    """Accept only valid JSON whose plan matches the person's chosen duration."""
    validate_duration(expected_days)
    try:
        plan = CareerPlan.model_validate_json(raw)
    except ValidationError as error:
        # Pydantic's default exception text includes input values. Return only
        # fixed error categories so neither the UI nor correction hint leaks them.
        codes = sorted({item["type"] for item in error.errors(include_input=False, include_url=False)})
        raise PlanValidationError("Plan rules failed: " + ", ".join(codes)) from None
    # Check against the actual selection, not just a duration claimed by the model.
    if plan.duration_days != expected_days:
        raise PlanValidationError("The returned duration must equal the selected planning period.")
    return plan


def format_plan(plan: CareerPlan) -> str:
    """Turn an already checked plan into readable chat text."""
    lines = [f"## {plan.duration_days}-day action plan", "", plan.summary]
    if plan.assumptions:
        lines.extend(["", "**Assumptions**"])
        lines.extend(f"- {assumption}" for assumption in plan.assumptions)
    for number, task in enumerate(plan.tasks, 1):
        lines.extend([
            "", f"### Task {number} — {task.title}", "",
            f"- **Action:** {task.action}",
            f"- **Start day:** {task.start_day} — **End day:** {task.end_day}",
            f"- **Why it fits:** {task.reason}",
            f"- **Completion evidence:** {task.completion_criterion}",
        ])
    return "\n".join(lines)
