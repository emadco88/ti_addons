from odoo import fields, models


class TiAccountingAccountGuide(models.Model):
    _name = "ti_accounting_account_guide"
    _description = "Account Guide"
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)


class TiAccountingJe(models.Model):
    _name = "ti_accounting_je"
    _description = "Journal Entry"
    _order = "due_date desc, id desc"

    debit = fields.Float(default=0.0)
    credit = fields.Float(default=0.0)
    account_id = fields.Many2one(
        "ti_accounting_account_guide",
        required=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one("res.partner", ondelete="set null")
    due_date = fields.Date()
    explain = fields.Text()
