from odoo import fields, models


class EduLevel(models.Model):
    _name = "edu_level"
    _description = "Educational Level"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    curriculum_notes = fields.Text(string="Curriculum Notes")
    prerequisite_ids = fields.Many2many(
        "edu_level",
        "edu_level_prereq_rel",
        "level_id",
        "prereq_id",
        string="Prerequisites",
    )
    placement_min_score = fields.Integer(string="Placement Min Score", default=0)
    placement_max_score = fields.Integer(string="Placement Max Score", default=100)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
