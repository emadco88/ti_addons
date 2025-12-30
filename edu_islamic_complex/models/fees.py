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
    product_id = fields.Many2one("product.product", string="Invoice Product")
    journal_id = fields.Many2one("account.journal", string="Sales Journal")
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
    invoice_id = fields.Many2one("account.move", required=True, ondelete="cascade")
    state = fields.Selection(related="invoice_id.state", store=True)
    payment_state = fields.Selection(related="invoice_id.payment_state", store=True)
    invoice_date_due = fields.Date(related="invoice_id.invoice_date_due", store=True)
    amount_total = fields.Monetary(related="invoice_id.amount_total", store=True)
    amount_residual = fields.Monetary(related="invoice_id.amount_residual", store=True)
    currency_id = fields.Many2one(related="invoice_id.currency_id", store=True)
    company_id = fields.Many2one(related="invoice_id.company_id", store=True)
    overdue_days = fields.Integer(compute="_compute_overdue", store=True)
    is_overdue = fields.Boolean(compute="_compute_overdue", store=True)

    @api.depends("invoice_date_due", "payment_state")
    def _compute_overdue(self):
        today = fields.Date.context_today(self)
        for link in self:
            if link.invoice_date_due and link.payment_state not in ("paid", "in_payment"):
                delta = (today - link.invoice_date_due).days
                link.overdue_days = max(delta, 0)
                link.is_overdue = delta > 0
            else:
                link.overdue_days = 0
                link.is_overdue = False
