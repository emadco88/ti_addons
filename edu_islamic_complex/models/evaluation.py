from odoo import api, fields, models


class EduEvaluation(models.Model):
    _name = "edu_evaluation"
    _description = "Evaluation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Evaluation Reference", readonly=True, copy=False)
    student_id = fields.Many2one("edu_student", required=True, ondelete="cascade")
    teacher_id = fields.Many2one("hr.employee", required=True, ondelete="restrict")
    enrollment_id = fields.Many2one("edu_enrollment", ondelete="set null")
    date = fields.Date(default=fields.Date.context_today)
    period = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("term", "Term"),
        ],
        default="monthly",
    )
    memorization_score = fields.Float(string="Memorization")
    recitation_score = fields.Float(string="Recitation")
    behavior_score = fields.Float(string="Behavior")
    homework_score = fields.Float(string="Homework")
    total_score = fields.Float(compute="_compute_total_score", store=True)
    notes = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="student_id.company_id",
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("edu_evaluation")
        return super().create(vals_list)

    @api.depends(
        "memorization_score",
        "recitation_score",
        "behavior_score",
        "homework_score",
    )
    def _compute_total_score(self):
        for evaluation in self:
            evaluation.total_score = sum(
                [
                    evaluation.memorization_score,
                    evaluation.recitation_score,
                    evaluation.behavior_score,
                    evaluation.homework_score,
                ]
            )
