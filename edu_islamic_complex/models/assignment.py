from datetime import timedelta

from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import ValidationError, UserError

WEEKDAY_MAP = {
    0: "meeting_monday",
    1: "meeting_tuesday",
    2: "meeting_wednesday",
    3: "meeting_thursday",
    4: "meeting_friday",
    5: "meeting_saturday",
    6: "meeting_sunday",
}


class EduAssignment(models.Model):
    _name = "edu_assignment"
    _description = "Teaching Assignment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    name = fields.Char(string="Assignment Reference", readonly=True, copy=False)
    teacher_id = fields.Many2one(
        "hr.employee",
        required=True,
        domain=[("is_teacher_effective", "=", True)],
        ondelete="restrict",
    )
    student_id = fields.Many2one("edu_student", ondelete="cascade")
    class_group_id = fields.Many2one("edu_class_group", ondelete="cascade")
    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date()
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("paused", "Paused"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    assignment_type = fields.Selection(
        [("student", "Student"), ("group", "Group")],
        compute="_compute_assignment_type",
    )
    meeting_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Meeting Day",
    )
    time_start = fields.Float(string="Start Time")
    time_end = fields.Float(string="End Time")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company_id",
        store=True,
    )
    load_units = fields.Integer(compute="_compute_load_units", store=True)

    session_ids = fields.One2many("edu_session", "assignment_id", string="Sessions")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("edu_assignment")
        records = super().create(vals_list)
        records.filtered(lambda a: a.status == "active")._generate_sessions()
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get("status") == "active":
            self._generate_sessions()
        return res

    @api.depends("student_id", "class_group_id")
    def _compute_assignment_type(self):
        for assignment in self:
            assignment.assignment_type = "group" if assignment.class_group_id else "student"

    @api.depends("student_id.company_id", "class_group_id.company_id")
    def _compute_company_id(self):
        for assignment in self:
            assignment.company_id = (
                    assignment.class_group_id.company_id
                    or assignment.student_id.company_id
                    or self.env.company
            )

    @api.depends("student_id", "class_group_id.active_student_count")
    def _compute_load_units(self):
        for assignment in self:
            if assignment.class_group_id:
                assignment.load_units = assignment.class_group_id.active_student_count
            elif assignment.student_id:
                assignment.load_units = 1
            else:
                assignment.load_units = 0

    @api.constrains("student_id", "class_group_id")
    def _check_target(self):
        for assignment in self:
            if not assignment.student_id and not assignment.class_group_id:
                raise ValidationError(_("Assignment must target a student or a class group."))
            if assignment.student_id and assignment.class_group_id:
                raise ValidationError(_("Assignment cannot target both a student and a class group."))

    @api.constrains("teacher_id", "status", "load_units")
    def _check_teacher_load(self):
        for assignment in self:
            if assignment.status != "active" or not assignment.teacher_id:
                continue
            if assignment.teacher_id.max_load and assignment.teacher_id.current_load > assignment.teacher_id.max_load:
                raise ValidationError(_("Teacher load exceeds maximum allowed."))

    @api.constrains("time_start", "time_end")
    def _check_time_range(self):
        for assignment in self:
            if assignment.time_start and assignment.time_end and assignment.time_end <= assignment.time_start:
                raise ValidationError(_("End time must be after start time."))

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for assignment in self:
            if assignment.start_date and assignment.end_date and assignment.end_date < assignment.start_date:
                raise ValidationError(_("End date must be after start date."))

    def action_generate_sessions(self):
        self._generate_sessions()
        return True

    def _generate_sessions(self):
        for assignment in self:
            if assignment.status != "active":
                continue
            if assignment.assignment_type == "student":
                assignment._generate_student_sessions()
            else:
                assignment._generate_group_sessions()

    def _generate_student_sessions(self):
        self.ensure_one()
        if not self.meeting_day:
            return
        if self._block_if_overdue(self.student_id):
            return
        weeks = int(self._get_param("edu_islamic_complex.default_recurrence_weeks", 4))
        session_duration = float(
            self._get_param("edu_islamic_complex.default_session_duration", 1.0)
        )
        start_time = self.time_start or 0.0
        end_time = self.time_end or (start_time + session_duration)
        self._create_sessions_for_weekday(int(self.meeting_day), weeks, start_time, end_time)

    def _generate_group_sessions(self):
        self.ensure_one()
        weeks = int(self._get_param("edu_islamic_complex.default_recurrence_weeks", 4))
        session_duration = float(
            self._get_param("edu_islamic_complex.default_session_duration", 1.0)
        )
        start_time = self.class_group_id.time_start or 0.0
        end_time = self.class_group_id.time_end or (start_time + session_duration)
        weekdays = [
            day for day, field_name in WEEKDAY_MAP.items() if getattr(self.class_group_id, field_name)
        ]
        for weekday in weekdays:
            self._create_sessions_for_weekday(weekday, weeks, start_time, end_time)

    def _create_sessions_for_weekday(self, weekday, weeks, start_time, end_time):
        self.ensure_one()
        start = self.start_date or fields.Date.context_today(self)
        if isinstance(start, str):
            start = fields.Date.from_string(start)
        # Find next weekday on or after start date
        days_ahead = (weekday - start.weekday()) % 7
        first_date = start + timedelta(days=days_ahead)
        existing = set(
            self.env["edu_session"].search(
                [("assignment_id", "=", self.id), ("date", ">=", first_date)]
            ).mapped("date")
        )
        for week in range(weeks):
            session_date = first_date + timedelta(days=7 * week)
            if session_date in existing:
                continue
            self.env["edu_session"].create(
                {
                    "assignment_id": self.id,
                    "teacher_id": self.teacher_id.id,
                    "class_group_id": self.class_group_id.id,
                    "student_id": self.student_id.id,
                    "date": session_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": self.class_group_id.location,
                }
            )

    def _block_if_overdue(self, student):
        if not student:
            return False
        param = self.env["ir.config_parameter"].sudo()
        if param.get_param("edu_islamic_complex.block_sessions_on_overdue") != "True":
            return False
        max_overdue = int(param.get_param("edu_islamic_complex.max_overdue_days", 0))
        if not max_overdue:
            return False
        enrollment = student.current_enrollment_id
        if enrollment and enrollment.overdue_days > max_overdue:
            raise UserError(_("Cannot schedule sessions: fees are overdue beyond the allowed threshold."))
        return False

    def _get_param(self, key, default):
        return self.env["ir.config_parameter"].sudo().get_param(key, default)
