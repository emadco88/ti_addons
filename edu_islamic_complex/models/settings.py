from odoo import fields, models


class EduSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_gender_rules = fields.Boolean(
        string="Enable Gender Constraints",
        config_parameter="edu_islamic_complex.enable_gender_rules",
        company_dependent=True,
    )
    block_sessions_on_overdue = fields.Boolean(
        string="Block Sessions When Fees Overdue",
        config_parameter="edu_islamic_complex.block_sessions_on_overdue",
        company_dependent=True,
    )
    max_overdue_days = fields.Integer(
        string="Max Overdue Days",
        config_parameter="edu_islamic_complex.max_overdue_days",
        company_dependent=True,
        default=0,
    )
    session_duration_default = fields.Float(
        string="Default Session Duration (Hours)",
        config_parameter="edu_islamic_complex.default_session_duration",
        company_dependent=True,
        default=1.0,
    )
    recurrence_weeks_default = fields.Integer(
        string="Default Recurrence (Weeks)",
        config_parameter="edu_islamic_complex.default_recurrence_weeks",
        company_dependent=True,
        default=4,
    )
    fee_account_id_default = fields.Many2one(
        "ti_accounting_account_guide",
        string="Default Fee Account",
        config_parameter="edu_islamic_complex.default_fee_account_id",
        company_dependent=True,
    )
