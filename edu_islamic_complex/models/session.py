from datetime import datetime, time

from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import ValidationError


class EduSession(models.Model):
    _name = "edu_session"
    _description = "Teaching Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, start_time"

    name = fields.Char(string="Session Reference", readonly=True, copy=False)
    assignment_id = fields.Many2one("edu_assignment", ondelete="set null")
    class_group_id = fields.Many2one("edu_class_group", ondelete="set null")
    student_id = fields.Many2one("edu_student", ondelete="set null")
    teacher_id = fields.Many2one("hr.employee", ondelete="set null")
    date = fields.Date(required=True, default=fields.Date.context_today)
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    start_datetime = fields.Datetime(compute="_compute_datetimes", store=True)
    end_datetime = fields.Datetime(compute="_compute_datetimes", store=True)
    location = fields.Char()
    state = fields.Selection(
        [("scheduled", "Scheduled"), ("done", "Done"), ("cancelled", "Cancelled")],
        default="scheduled",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company_id",
        store=True,
    )

    attendance_ids = fields.One2many("edu_attendance", "session_id", string="Attendance")
    attendance_count = fields.Integer(compute="_compute_attendance_counts")
    present_count = fields.Integer(compute="_compute_attendance_counts")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("edu_session")
        records = super().create(vals_list)
        records._create_attendance_lines()
        return records

    @api.depends("date", "start_time", "end_time")
    def _compute_datetimes(self):
        for session in self:
            if not session.date:
                session.start_datetime = False
                session.end_datetime = False
                continue
            start_hour = int(session.start_time or 0.0)
            start_minute = int(round((session.start_time % 1) * 60))
            end_hour = int(session.end_time or 0.0)
            end_minute = int(round((session.end_time % 1) * 60))
            session.start_datetime = datetime.combine(
                session.date, time(start_hour, start_minute)
            )
            session.end_datetime = datetime.combine(session.date, time(end_hour, end_minute))

    @api.depends(
        "assignment_id.company_id",
        "class_group_id.company_id",
        "student_id.company_id",
    )
    def _compute_company_id(self):
        for session in self:
            session.company_id = (
                    session.assignment_id.company_id
                    or session.class_group_id.company_id
                    or session.student_id.company_id
                    or self.env.company
            )

    def _compute_attendance_counts(self):
        for session in self:
            student_lines = session.attendance_ids.filtered(lambda l: l.person_type == "student")
            session.attendance_count = len(student_lines)
            session.present_count = len(student_lines.filtered(lambda l: l.status == "present"))

    def _create_attendance_lines(self):
        Attendance = self.env["edu_attendance"]
        for session in self:
            existing_students = session.attendance_ids.filtered(
                lambda l: l.person_type == "student"
            ).mapped("student_id")
            if session.class_group_id:
                students = session.class_group_id.enrollment_ids.filtered(
                    lambda e: e.status == "active"
                ).mapped("student_id")
            else:
                students = session.student_id
            for student in students:
                if student in existing_students:
                    continue
                Attendance.create(
                    {
                        "session_id": session.id,
                        "person_type": "student",
                        "student_id": student.id,
                        "status": "absent",
                    }
                )
            if session.teacher_id and not session.attendance_ids.filtered(
                    lambda l: l.person_type == "teacher" and l.teacher_id == session.teacher_id
            ):
                Attendance.create(
                    {
                        "session_id": session.id,
                        "person_type": "teacher",
                        "teacher_id": session.teacher_id.id,
                        "status": "present",
                    }
                )

    @api.constrains("start_time", "end_time")
    def _check_time_range(self):
        for session in self:
            if session.start_time and session.end_time and session.end_time <= session.start_time:
                raise ValidationError(_("End time must be after start time."))

    @api.onchange("assignment_id")
    def _onchange_assignment_id(self):
        if self.assignment_id:
            self.teacher_id = self.assignment_id.teacher_id
            self.class_group_id = self.assignment_id.class_group_id
            self.student_id = self.assignment_id.student_id
