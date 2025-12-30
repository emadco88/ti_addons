from odoo import api, fields, models


class EduStudent(models.Model):
    _name = "edu_student"
    _description = "Student"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    student_ref = fields.Char(string="Student Number", readonly=True, copy=False)
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        tracking=True,
    )
    birth_date = fields.Date(string="Date of Birth")
    national_id = fields.Char(string="National ID")
    address = fields.Text()
    phone = fields.Char()
    email = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Billing Partner")
    guardian_ids = fields.Many2many(
        "edu_guardian",
        "edu_guardian_student_rel",
        "student_id",
        "guardian_id",
        string="Guardians",
    )
    enrollment_date = fields.Date(default=fields.Date.context_today)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    enrollment_ids = fields.One2many("edu_enrollment", "student_id", string="Enrollments")
    assignment_ids = fields.One2many("edu_assignment", "student_id", string="Assignments")
    evaluation_ids = fields.One2many("edu_evaluation", "student_id", string="Evaluations")
    attendance_ids = fields.One2many("edu_attendance", "student_id", string="Attendance")

    enrollment_count = fields.Integer(compute="_compute_counts")
    assignment_count = fields.Integer(compute="_compute_counts")
    attendance_count = fields.Integer(compute="_compute_counts")
    evaluation_count = fields.Integer(compute="_compute_counts")
    invoice_count = fields.Integer(compute="_compute_counts")

    current_enrollment_id = fields.Many2one(
        "edu_enrollment",
        compute="_compute_current_enrollment",
        string="Current Enrollment",
    )
    current_level_id = fields.Many2one(
        "edu_level",
        compute="_compute_current_enrollment",
        string="Current Level",
    )

    attendance_rate = fields.Float(
        string="Attendance Rate",
        compute="_compute_attendance_rate",
        help="Percent of present attendance over total recorded sessions.",
    )
    evaluation_avg_score = fields.Float(
        string="Average Evaluation Score",
        compute="_compute_evaluation_avg",
    )

    teacher_ids = fields.Many2many(
        "hr.employee",
        compute="_compute_teacher_ids",
        string="Teachers",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("student_ref"):
                vals["student_ref"] = self.env["ir.sequence"].next_by_code("edu_student")
        return super().create(vals_list)

    def _compute_current_enrollment(self):
        for student in self:
            enrollment = student.enrollment_ids.filtered(lambda e: e.status == "active")
            student.current_enrollment_id = enrollment[:1]
            student.current_level_id = enrollment[:1].level_id

    def _compute_attendance_rate(self):
        Attendance = self.env["edu_attendance"]
        data = Attendance.read_group(
            [("student_id", "in", self.ids), ("person_type", "=", "student")],
            ["student_id", "status"],
            ["student_id", "status"],
        )
        total = {sid: 0 for sid in self.ids}
        present = {sid: 0 for sid in self.ids}
        for row in data:
            sid = row["student_id"][0]
            count = row["__count"]
            total[sid] += count
            if row["status"] == "present":
                present[sid] += count
        for student in self:
            if total.get(student.id):
                student.attendance_rate = (present.get(student.id, 0) / total[student.id]) * 100.0
            else:
                student.attendance_rate = 0.0

    def _compute_evaluation_avg(self):
        Evaluation = self.env["edu_evaluation"]
        data = Evaluation.read_group(
            [("student_id", "in", self.ids)],
            ["student_id", "total_score:avg"],
            ["student_id"],
        )
        mapped = {row["student_id"][0]: row["total_score"] for row in data}
        for student in self:
            student.evaluation_avg_score = mapped.get(student.id, 0.0)

    @api.depends(
        "assignment_ids.teacher_id",
        "assignment_ids.status",
        "enrollment_ids.class_group_id.assignment_ids.teacher_id",
        "enrollment_ids.class_group_id.assignment_ids.status",
    )
    def _compute_teacher_ids(self):
        for student in self:
            active_assignments = student.assignment_ids.filtered(lambda a: a.status == "active")
            teachers = active_assignments.mapped("teacher_id")
            groups = student.enrollment_ids.mapped("class_group_id")
            if groups:
                active_group_assignments = groups.mapped("assignment_ids").filtered(
                    lambda a: a.status == "active"
                )
                teachers |= active_group_assignments.mapped("teacher_id")
            student.teacher_ids = teachers

    def _compute_counts(self):
        for student in self:
            student.enrollment_count = len(student.enrollment_ids)
            student.assignment_count = len(student.assignment_ids)
            student.attendance_count = len(student.attendance_ids.filtered(lambda l: l.person_type == "student"))
            student.evaluation_count = len(student.evaluation_ids)
            invoices = student.enrollment_ids.mapped("invoice_link_ids.invoice_id")
            student.invoice_count = len(invoices)

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Enrollments",
            "res_model": "edu_enrollment",
            "view_mode": "list,form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }

    def action_view_assignments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Assignments",
            "res_model": "edu_assignment",
            "view_mode": "list,form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }

    def action_view_attendance(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Attendance",
            "res_model": "edu_attendance",
            "view_mode": "list,form,pivot,graph",
            "domain": [("student_id", "=", self.id), ("person_type", "=", "student")],
        }

    def action_view_evaluations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Evaluations",
            "res_model": "edu_evaluation",
            "view_mode": "list,form,graph,pivot",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.enrollment_ids.mapped("invoice_link_ids.invoice_id")
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        action["domain"] = [("id", "in", invoices.ids)]
        return action

    def action_open_placement_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Placement",
            "res_model": "edu_placement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_student_id": self.id},
        }
