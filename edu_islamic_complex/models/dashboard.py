from odoo import api, fields, models


class EduDashboard(models.Model):
    _name = "edu_dashboard"
    _description = "Education Dashboard"

    name = fields.Char(default="Education Dashboard")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    active_students = fields.Integer(compute="_compute_metrics")
    attendance_rate = fields.Float(compute="_compute_metrics")
    overdue_fees = fields.Integer(compute="_compute_metrics")
    teacher_load = fields.Float(compute="_compute_metrics")

    @api.depends("company_id")
    def _compute_metrics(self):
        Student = self.env["edu_student"]
        Attendance = self.env["edu_attendance"]
        InvoiceLink = self.env["edu_invoice.link"]
        Employee = self.env["hr.employee"]

        for dashboard in self:
            students = Student.search_count(
                [("active", "=", True), ("company_id", "=", dashboard.company_id.id)]
            )
            att_data = Attendance.read_group(
                [
                    ("person_type", "=", "student"),
                    ("company_id", "=", dashboard.company_id.id),
                ],
                ["status"],
                ["status"],
            )
            total = sum(row["__count"] for row in att_data)
            present = sum(row["__count"] for row in att_data if row["status"] == "present")
            overdue = InvoiceLink.search_count(
                [("company_id", "=", dashboard.company_id.id), ("is_overdue", "=", True)]
            )
            teachers = Employee.search(
                [
                    ("is_teacher_effective", "=", True),
                    ("company_id", "in", [dashboard.company_id.id, False]),
                ]
            )
            load_total = sum(teachers.mapped("current_load"))
            dashboard.active_students = students
            dashboard.attendance_rate = (present / total) * 100.0 if total else 0.0
            dashboard.overdue_fees = overdue
            dashboard.teacher_load = load_total / len(teachers) if teachers else 0.0

    @api.model
    def get_dashboard(self):
        dashboard = self.search([("company_id", "=", self.env.company.id)], limit=1)
        if not dashboard:
            dashboard = self.create({"company_id": self.env.company.id})
        return dashboard
