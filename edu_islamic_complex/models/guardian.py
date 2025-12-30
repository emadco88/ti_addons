from odoo import fields, models


class EduGuardian(models.Model):
    _name = "edu_guardian"
    _description = "Guardian"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    relation = fields.Selection(
        [
            ("father", "Father"),
            ("mother", "Mother"),
            ("guardian", "Guardian"),
        ],
        default="guardian",
    )
    phone = fields.Char()
    email = fields.Char()
    address = fields.Text()
    national_id = fields.Char(string="National ID")
    partner_id = fields.Many2one("res.partner", string="Related Partner")
    user_id = fields.Many2one("res.users", string="Portal User")
    student_ids = fields.Many2many(
        "edu_student",
        "edu_guardian_student_rel",
        "guardian_id",
        "student_id",
        string="Students",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
