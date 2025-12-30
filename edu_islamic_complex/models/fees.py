from odoo import api, fields, models


class EduFeesPlan(models.Model):
    _name = "edu_fees.plan"
    _description = "Fees Plan"

    name = fields.Char(required=True)
    level_id = fields.Many2one("edu_level", ondelete="set null")
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    billing_period = fields.Selection(
        [("monthly", "Monthly"), ("one_time", "One-time")],
        default="monthly",
    )
    account_id = fields.Many2one(
        "ti_accounting_account_guide",
        string="Fee Account",
        ondelete="set null",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )


class EduInvoiceLink(models.Model):
    _name = "edu_invoice.link"
    _description = "Enrollment Invoice Link"

    enrollment_id = fields.Many2one("edu_enrollment", required=True, ondelete="cascade")
    entry_id = fields.Many2one("ti_accounting_je", required=True, ondelete="cascade")
    account_id = fields.Many2one(related="entry_id.account_id", store=True)
    partner_id = fields.Many2one(related="entry_id.partner_id", store=True)
    due_date = fields.Date(related="entry_id.due_date", store=True)
    debit = fields.Float(related="entry_id.debit", store=True)
    credit = fields.Float(related="entry_id.credit", store=True)
    explain = fields.Text(related="entry_id.explain", store=True)
    company_id = fields.Many2one(related="enrollment_id.company_id", store=True)
    overdue_days = fields.Integer(compute="_compute_overdue", store=True)
    is_overdue = fields.Boolean(compute="_compute_overdue", store=True)

    @api.depends("due_date", "debit", "credit")
    def _compute_overdue(self):
        today = fields.Date.context_today(self)
        for link in self:
            balance = (link.debit or 0.0) - (link.credit or 0.0)
            if link.due_date and balance > 0:
                delta = (today - link.due_date).days
                link.overdue_days = max(delta, 0)
                link.is_overdue = delta > 0
            else:
                link.overdue_days = 0
                link.is_overdue = False
