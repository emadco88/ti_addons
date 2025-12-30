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
    product_id = fields.Many2one("product.product", string="Invoice Product")
    journal_id = fields.Many2one("account.journal", string="Journal")

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
            self.product_id = self.plan_id.product_id
            self.journal_id = self.plan_id.journal_id
            self.currency_id = self.plan_id.currency_id

    def action_create_invoice(self):
        self.ensure_one()
        enrollment = self.enrollment_id
        if not enrollment:
            raise UserError(_("Enrollment is required."))
        product = self.product_id or self._get_default_product()
        if not product:
            raise UserError(_("Please configure an invoice product."))
        partner = self._get_billing_partner(enrollment)
        if not partner:
            raise UserError(_("Please define a billing partner."))
        journal = self.journal_id or self._get_default_journal()
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_date": self.invoice_date,
            "invoice_date_due": self.period_end or self.invoice_date,
            "journal_id": journal.id if journal else False,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": self._invoice_line_name(enrollment),
                        "quantity": 1.0,
                        "price_unit": self.amount or enrollment.fee_plan_id.amount,
                    },
                )
            ],
        }
        invoice = self.env["account.move"].create(invoice_vals)
        self.env["edu_invoice.link"].create(
            {"enrollment_id": enrollment.id, "invoice_id": invoice.id}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def _invoice_line_name(self, enrollment):
        name = enrollment.level_id.name or ""
        if self.period_start and self.period_end:
            name = _("%s (%s - %s)") % (name, self.period_start, self.period_end)
        return name or _("Education Fees")

    def _get_default_product(self):
        param = self.env["ir.config_parameter"].sudo()
        product_id = int(param.get_param("edu_islamic_complex.default_invoice_product_id", 0))
        return self.env["product.product"].browse(product_id) if product_id else False

    def _get_default_journal(self):
        param = self.env["ir.config_parameter"].sudo()
        journal_id = int(param.get_param("edu_islamic_complex.default_fee_journal_id", 0))
        return self.env["account.journal"].browse(journal_id) if journal_id else False

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
