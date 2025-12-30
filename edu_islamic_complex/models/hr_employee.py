from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_teacher = fields.Boolean(string="Is Teacher")
    is_teacher_effective = fields.Boolean(
        string="Is Teacher (Effective)",
        compute="_compute_is_teacher_effective",
        store=True,
    )
    teaching_specialization_ids = fields.Many2many(
        "edu_level",
        "edu_teacher_level_rel",
        "employee_id",
        "level_id",
        string="Teaching Specializations",
    )
    max_load = fields.Integer(string="Max Teaching Load", default=0)
    availability_notes = fields.Text(string="Availability Notes")
    available_monday = fields.Boolean(string="Monday")
    available_tuesday = fields.Boolean(string="Tuesday")
    available_wednesday = fields.Boolean(string="Wednesday")
    available_thursday = fields.Boolean(string="Thursday")
    available_friday = fields.Boolean(string="Friday")
    available_saturday = fields.Boolean(string="Saturday")
    available_sunday = fields.Boolean(string="Sunday")

    current_load = fields.Integer(string="Current Load", compute="_compute_current_load")
    assigned_student_ids = fields.Many2many(
        "edu_student",
        compute="_compute_assigned_records",
        string="Assigned Students",
    )
    assigned_group_ids = fields.Many2many(
        "edu_class_group",
        compute="_compute_assigned_records",
        string="Assigned Groups",
    )

    @api.depends("is_teacher", "job_id.name")
    def _compute_is_teacher_effective(self):
        for employee in self:
            job_name = (employee.job_id.name or "").lower()
            auto = "teacher" in job_name or "معلم" in job_name
            employee.is_teacher_effective = bool(employee.is_teacher or auto)

    def _compute_current_load(self):
        assignment_model = self.env["edu_assignment"]
        data = assignment_model.read_group(
            [("teacher_id", "in", self.ids), ("status", "=", "active")],
            ["load_units:sum"],
            ["teacher_id"],
        )
        mapped = {item["teacher_id"][0]: int(item["load_units"]) for item in data}
        for employee in self:
            employee.current_load = mapped.get(employee.id, 0)

    def _compute_assigned_records(self):
        assignment_model = self.env["edu_assignment"]
        for employee in self:
            assignments = assignment_model.search(
                [("teacher_id", "=", employee.id), ("status", "=", "active")]
            )
            students = assignments.mapped("student_id")
            groups = assignments.mapped("class_group_id")
            if groups:
                students |= groups.mapped("enrollment_ids.student_id")
            employee.assigned_student_ids = students
            employee.assigned_group_ids = groups
