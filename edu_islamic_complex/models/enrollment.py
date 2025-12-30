from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import ValidationError


class EduEnrollment(models.Model):
    _name = "edu_enrollment"
    _description = "Enrollment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    name = fields.Char(string="Enrollment Reference", readonly=True, copy=False)
    student_id = fields.Many2one("edu_student", required=True, ondelete="cascade")
    level_id = fields.Many2one("edu_level", required=True, ondelete="restrict")
    class_group_id = fields.Many2one("edu_class_group", ondelete="set null")
    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date()
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("paused", "Paused"),
            ("graduated", "Graduated"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    placement_score = fields.Integer(string="Placement Score")
    placement_result = fields.Text(string="Placement Result")
    fee_plan_id = fields.Many2one("edu_fees.plan", string="Fees Plan")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="student_id.company_id",
        store=True,
        readonly=True,
    )

    invoice_link_ids = fields.One2many("edu_invoice.link", "enrollment_id", string="Invoices")
    invoice_count = fields.Integer(compute="_compute_invoice_count")
    overdue_days = fields.Integer(compute="_compute_overdue")
    has_overdue = fields.Boolean(compute="_compute_overdue")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("edu_enrollment")
        return super().create(vals_list)

    @api.constrains("class_group_id", "level_id")
    def _check_group_level(self):
        for enrollment in self:
            if enrollment.class_group_id and enrollment.level_id != enrollment.class_group_id.level_id:
                raise ValidationError(_("Class group level must match enrollment level."))

    @api.constrains("status", "class_group_id")
    def _check_capacity(self):
        for enrollment in self:
            if enrollment.status != "active" or not enrollment.class_group_id:
                continue
            group = enrollment.class_group_id
            if group.capacity and self.search_count(
                    [("class_group_id", "=", group.id), ("status", "=", "active")]
            ) > group.capacity:
                raise ValidationError(_("Class group capacity exceeded."))

    @api.constrains("student_id", "level_id", "status")
    def _check_unique_active(self):
        for enrollment in self:
            if enrollment.status not in ("active", "paused"):
                continue
            domain = [
                ("student_id", "=", enrollment.student_id.id),
                ("level_id", "=", enrollment.level_id.id),
                ("status", "in", ("active", "paused")),
                ("id", "!=", enrollment.id),
            ]
            if self.search_count(domain):
                raise ValidationError(_("Student already has an active enrollment for this level."))

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for enrollment in self:
            if enrollment.start_date and enrollment.end_date and enrollment.end_date < enrollment.start_date:
                raise ValidationError(_("End date must be after start date."))

    def _compute_invoice_count(self):
        for enrollment in self:
            enrollment.invoice_count = len(enrollment.invoice_link_ids)

    def _compute_overdue(self):
        # today = fields.Date.context_today(self)
        for enrollment in self:
            overdue_days = 0
            has_overdue = False
            for link in enrollment.invoice_link_ids:
                if link.is_overdue and link.overdue_days > overdue_days:
                    overdue_days = link.overdue_days
                    has_overdue = True
            enrollment.overdue_days = overdue_days
            enrollment.has_overdue = has_overdue

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref("edu_islamic_complex.action_edu_invoice_links").read()[0]
        action["domain"] = [("enrollment_id", "=", self.id)]
        return action

    def action_create_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "edu_create.invoice.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_enrollment_id": self.id},
        }

    @api.onchange("level_id")
    def _onchange_level_id(self):
        if self.level_id and not self.fee_plan_id:
            plan = self.env["edu_fees.plan"].search(
                [("level_id", "=", self.level_id.id), ("active", "=", True)], limit=1
            )
            if plan:
                self.fee_plan_id = plan
