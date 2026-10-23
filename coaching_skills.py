"""Load the small instruction skills that the application actually uses."""

from pathlib import Path
import re
import sys

from mentors import get_mentor


SKILLS_DIR = (Path(sys._MEIPASS) / "application" / "skills"
              if getattr(sys, "frozen", False) else Path(__file__).resolve().parent / "skills")
EVIDENCE_SKILL = "evidence-informed-coaching"
MENTOR_SKILL = "mentor-decision-workflow"
PLANNING_SKILL = "realistic-action-planning"


class SkillLoadError(ValueError):
    """Stop a request when required coaching instructions are unavailable."""


def active_skill_names(mentor_id: str, *, planning: bool = False) -> tuple[str, ...]:
    """Expose the same selection used by the request builder to the interface."""
    get_mentor(mentor_id)
    return (EVIDENCE_SKILL, MENTOR_SKILL) + ((PLANNING_SKILL,) if planning else ())


def _read_skill(name: str) -> str:
    """Accept our intentionally small frontmatter format without a YAML dependency."""
    try:
        document = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise SkillLoadError("Required coaching skills could not be loaded. Repair the application files before retrying.") from None
    parts = re.fullmatch(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", document, re.DOTALL)
    if parts is None:
        raise SkillLoadError("A required coaching skill has invalid metadata.")
    metadata = {}
    for line in parts.group(1).strip().splitlines():
        key, separator, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not separator or key not in {"name", "description"} or key in metadata or not value:
            raise SkillLoadError("A required coaching skill has invalid metadata.")
        metadata[key] = value
    body = parts.group(2).strip()
    if metadata.get("name") != name or not metadata.get("description") or not body:
        raise SkillLoadError("A required coaching skill is incomplete.")
    return body


def _mentor_instructions(body: str, mentor_id: str) -> str:
    """Disclose the chosen mentor's workflow, keeping other specialties out."""
    sections = re.split(r"(?m)^## ([a-z]+)\s*$", body)
    selected = [sections[index + 1].strip() for index in range(1, len(sections), 2) if sections[index] == mentor_id]
    if len(selected) != 1 or not selected[0]:
        raise SkillLoadError("The selected mentor's coaching skill is incomplete.")
    return sections[0].strip() + "\n\n" + selected[0]


def load_skill_instructions(mentor_id: str, *, planning: bool = False) -> str:
    """Return evidence rules, one mentor workflow, and optional planning rules."""
    instructions = []
    for name in active_skill_names(mentor_id, planning=planning):
        body = _read_skill(name)
        if name == MENTOR_SKILL:
            body = _mentor_instructions(body, mentor_id)
        instructions.append(f"Applied skill: {name}\n{body}")
    return "\n\n".join(instructions)
