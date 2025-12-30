from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import ValidationError


class EduClassGroup(models.Model):
    _name = "edu_class_group"
    _description = "Class Group"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    level_id = fields.Many2one("edu_level", required=True, ondelete="restrict")
    capacity = fields.Integer(default=20)
    meeting_monday = fields.Boolean(string="Mon")
    meeting_tuesday = fields.Boolean(string="Tue")
    meeting_wednesday = fields.Boolean(string="Wed")
    meeting_thursday = fields.Boolean(string="Thu")
    meeting_friday = fields.Boolean(string="Fri")
    meeting_saturday = fields.Boolean(string="Sat")
    meeting_sunday = fields.Boolean(string="Sun")
    time_start = fields.Float(string="Start Time")
    time_end = fields.Float(string="End Time")
    location = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    enrollment_ids = fields.One2many("edu_enrollment", "class_group_id", string="Enrollments")
    assignment_ids = fields.One2many("edu_assignment", "class_group_id", string="Assignments")

    active_student_count = fields.Integer(
        string="Active Students",
        compute="_compute_student_counts",
        store=True,
    )
    total_student_count = fields.Integer(
        string="Total Students",
        compute="_compute_student_counts",
        store=True,
    )
    teacher_ids = fields.Many2many(
        "hr.employee",
        compute="_compute_teacher_ids",
        string="Teachers",
        store=True,
    )

    @api.depends("enrollment_ids.status")
    def _compute_student_counts(self):
        for group in self:
            group.total_student_count = len(group.enrollment_ids)
            group.active_student_count = len(group.enrollment_ids.filtered(lambda e: e.status == "active"))

    @api.depends("assignment_ids.teacher_id", "assignment_ids.status")
    def _compute_teacher_ids(self):
        for group in self:
            active_assignments = group.assignment_ids.filtered(lambda a: a.status == "active")
            group.teacher_ids = active_assignments.mapped("teacher_id")

    @api.constrains("capacity")
    def _check_capacity(self):
        for group in self:
            if group.capacity < 0:
                raise ValidationError(_("Capacity must be zero or greater."))
