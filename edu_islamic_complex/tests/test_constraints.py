from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestEduConstraints(TransactionCase):
    def setUp(self):
        super().setUp()
        self.level = self.env["edu_level"].create({"name": "Noorania", "sequence": 10})
        self.group = self.env["edu_class_group"].create(
            {"name": "Noorania A", "level_id": self.level.id, "capacity": 1}
        )
        self.student_1 = self.env["edu_student"].create({"name": "Student 1"})
        self.student_2 = self.env["edu_student"].create({"name": "Student 2"})
        self.teacher = self.env["hr.employee"].create(
            {"name": "Teacher 1", "is_teacher": True, "max_load": 1}
        )

    def test_group_capacity(self):
        self.env["edu_enrollment"].create(
            {
                "student_id": self.student_1.id,
                "level_id": self.level.id,
                "class_group_id": self.group.id,
                "status": "active",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["edu_enrollment"].create(
                {
                    "student_id": self.student_2.id,
                    "level_id": self.level.id,
                    "class_group_id": self.group.id,
                    "status": "active",
                }
            )

    def test_teacher_load(self):
        self.env["edu_assignment"].create(
            {
                "teacher_id": self.teacher.id,
                "student_id": self.student_1.id,
                "status": "active",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["edu_assignment"].create(
                {
                    "teacher_id": self.teacher.id,
                    "student_id": self.student_2.id,
                    "status": "active",
                }
            )

    def test_assignment_target(self):
        with self.assertRaises(ValidationError):
            self.env["edu_assignment"].create(
                {
                    "teacher_id": self.teacher.id,
                    "student_id": self.student_1.id,
                    "class_group_id": self.group.id,
                }
            )
