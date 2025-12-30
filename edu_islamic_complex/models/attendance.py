from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class EduAttendance(models.Model):
    _name = "edu_attendance"
    _description = "Attendance"
    _order = "date desc"

    session_id = fields.Many2one("edu_session", required=True, ondelete="cascade")
    person_type = fields.Selection(
        [("student", "Student"), ("teacher", "Teacher")],
        required=True,
        default="student",
    )
    student_id = fields.Many2one("edu_student", ondelete="cascade")
    teacher_id = fields.Many2one("hr.employee", ondelete="cascade")
    date = fields.Date(related="session_id.date", store=True)
    status = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
        ],
        default="absent",
    )
    notes = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="session_id.company_id",
        store=True,
    )

    _sql_constraints = [
        (
            "unique_attendance",
            "unique(session_id, person_type, student_id, teacher_id)",
            "Attendance already exists for this session.",
        )
    ]

    @api.constrains("person_type", "student_id", "teacher_id")
    def _check_person(self):
        for line in self:
            if line.person_type == "student" and not line.student_id:
                raise ValidationError(_("Student attendance requires a student."))
            if line.person_type == "student" and line.teacher_id:
                raise ValidationError(_("Teacher must be empty for student attendance."))
            if line.person_type == "teacher" and not line.teacher_id:
                raise ValidationError(_("Teacher attendance requires a teacher."))
            if line.person_type == "teacher" and line.student_id:
                raise ValidationError(_("Student must be empty for teacher attendance."))
