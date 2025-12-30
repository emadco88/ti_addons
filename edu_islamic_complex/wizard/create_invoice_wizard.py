from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import UserError


class EduCreateInvoiceWizard(models.TransientModel):
    _name = "edu_create.invoice.wizard"
    _description = "Create Enrollment Invoice"

    enrollment_id = fields.Many2one("edu_enrollment", required=True)
    plan_id = fields.Many2one("edu_fees.plan", string="Fees Plan")
    invoice_date = fields.Date(default=fields.Date.context_today)
    period_start = fields.Date()
    period_end = fields.Date()
    amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )
    account_id = fields.Many2one("ti_accounting_account_guide", string="Account")

    @api.onchange("enrollment_id")
    def _onchange_enrollment(self):
        if self.enrollment_id:
            self.plan_id = self.enrollment_id.fee_plan_id
            self._apply_plan_defaults()

    @api.onchange("plan_id")
    def _onchange_plan(self):
        self._apply_plan_defaults()

    def _apply_plan_defaults(self):
        if self.plan_id:
            self.amount = self.plan_id.amount
            self.account_id = self.plan_id.account_id
            self.currency_id = self.plan_id.currency_id

    def action_create_invoice(self):
        self.ensure_one()
        enrollment = self.enrollment_id
        if not enrollment:
            raise UserError(_("Enrollment is required."))
        account = self.account_id or self._get_default_account()
        if not account:
            raise UserError(_("Please configure a fee account."))
        partner = self._get_billing_partner(enrollment)
        if not partner:
            raise UserError(_("Please define a billing partner."))
        amount = self.amount or enrollment.fee_plan_id.amount
        if not amount:
            raise UserError(_("Please set a fee amount."))
        entry_vals = {
            "account_id": account.id,
            "partner_id": partner.id,
            "due_date": self.period_end or self.invoice_date,
            "debit": amount or 0.0,
            "credit": 0.0,
            "explain": self._entry_explain(enrollment),
        }
        entry = self.env["ti_accounting_je"].create(entry_vals)
        self.env["edu_invoice.link"].create(
            {"enrollment_id": enrollment.id, "entry_id": entry.id}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ti_accounting_je",
            "res_id": entry.id,
            "view_mode": "form",
            "target": "current",
        }

    def _entry_explain(self, enrollment):
        name = enrollment.level_id.name or ""
        if self.period_start and self.period_end:
            name = _("%s (%s - %s)") % (name, self.period_start, self.period_end)
        return name or _("Education Fees")

    def _get_default_account(self):
        param = self.env["ir.config_parameter"].sudo()
        account_id = int(param.get_param("edu_islamic_complex.default_fee_account_id", 0))
        return self.env["ti_accounting_account_guide"].browse(account_id) if account_id else False

    def _get_billing_partner(self, enrollment):
        student = enrollment.student_id
        if student.partner_id:
            return student.partner_id
        guardian = student.guardian_ids.filtered("partner_id")[:1]
        if guardian:
            return guardian.partner_id
        if student.guardian_ids:
            guardian = student.guardian_ids[0]
            partner = self.env["res.partner"].create(
                {
                    "name": guardian.name,
                    "phone": guardian.phone,
                    "email": guardian.email,
                }
            )
            guardian.partner_id = partner
            return partner
        partner = self.env["res.partner"].create(
            {"name": student.name, "phone": student.phone, "email": student.email}
        )
        student.partner_id = partner
        return partner
