"""Exercise runtime selection and broken-instruction stopping conditions."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import coaching_skills as skills
from mentors import MENTORS


class CoachingSkillTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        copied = Path(self.directory.name) / "skills"
        shutil.copytree(skills.SKILLS_DIR, copied)
        self.root = copied
        self.patcher = patch.object(skills, "SKILLS_DIR", copied)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_each_mentor_loads_common_evidence_and_only_its_own_workflow(self):
        mentor_document = skills._read_skill(skills.MENTOR_SKILL)
        for mentor_id in MENTORS:
            with self.subTest(mentor=mentor_id):
                instruction = skills.load_skill_instructions(mentor_id)
                self.assertIn(skills._read_skill(skills.EVIDENCE_SKILL), instruction)
                self.assertIn(skills._mentor_instructions(mentor_document, mentor_id), instruction)
                for other_id in set(MENTORS) - {mentor_id}:
                    other = skills._mentor_instructions(mentor_document, other_id).split("\n\n")[-1]
                    self.assertNotIn(other, instruction)

    def test_planning_instructions_are_loaded_only_for_plan_requests(self):
        plan = skills._read_skill(skills.PLANNING_SKILL)
        self.assertNotIn(plan, skills.load_skill_instructions("learning"))
        self.assertIn(plan, skills.load_skill_instructions("learning", planning=True))
        (self.root / skills.PLANNING_SKILL / "SKILL.md").unlink()
        skills.load_skill_instructions("learning")
        with self.assertRaises(skills.SkillLoadError):
            skills.load_skill_instructions("learning", planning=True)

    def test_missing_required_evidence_stops_instead_of_downgrading(self):
        (self.root / skills.EVIDENCE_SKILL / "SKILL.md").unlink()
        with self.assertRaises(skills.SkillLoadError):
            skills.load_skill_instructions("career")

    def test_invalid_metadata_and_empty_body_stop_loading(self):
        path = self.root / skills.EVIDENCE_SKILL / "SKILL.md"
        for content in (
            "No metadata", "---\nname: other-skill\ndescription: Coaching\n---\nBody",
            f"---name: {skills.EVIDENCE_SKILL}\ndescription: Coaching---Body",
            f"---\nname: {skills.EVIDENCE_SKILL}\n---\nBody",
            f"---\nname: {skills.EVIDENCE_SKILL}\ndescription: Coaching\n---\n",
            f"---\nname: {skills.EVIDENCE_SKILL}\nname: {skills.EVIDENCE_SKILL}\ndescription: Coaching\n---\nBody",
        ):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(skills.SkillLoadError):
                    skills.load_skill_instructions("career")

    def test_missing_or_duplicate_selected_workflow_stops_loading(self):
        path = self.root / skills.MENTOR_SKILL / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        for content in (original.replace("## career", "## unavailable"), original + "\n## career\nDuplicate workflow"):
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(skills.SkillLoadError):
                skills.load_skill_instructions("career")

    def test_unknown_mentor_rejects_before_reading_any_skill(self):
        with patch.object(skills, "_read_skill") as read:
            with self.assertRaises(ValueError):
                skills.load_skill_instructions("../../unexpected")
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
