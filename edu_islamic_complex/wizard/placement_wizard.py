from odoo import api, fields, models
from odoo.tools.translate import _

from odoo.exceptions import UserError

DAY_FIELD_MAP = {
    "0": "available_monday",
    "1": "available_tuesday",
    "2": "available_wednesday",
    "3": "available_thursday",
    "4": "available_friday",
    "5": "available_saturday",
    "6": "available_sunday",
}


class EduPlacementWizard(models.TransientModel):
    _name = "edu_placement.wizard"
    _description = "Placement Wizard"

    student_id = fields.Many2one("edu_student", required=True)
    age_years = fields.Integer(compute="_compute_age")
    reading_level = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="basic",
    )
    memorization_juz = fields.Integer(string="Memorization (Ajza)", default=0)
    score = fields.Integer(compute="_compute_score", store=True)
    recommended_level_id = fields.Many2one(
        "edu_level",
        compute="_compute_recommended_level",
        store=True,
    )
    level_id = fields.Many2one("edu_level", string="Selected Level")
    class_group_id = fields.Many2one("edu_class_group", string="Class Group")
    suggested_teacher_ids = fields.Many2many(
        "hr.employee",
        compute="_compute_suggested_teachers",
        string="Suggested Teachers",
    )
    teacher_id = fields.Many2one(
        "hr.employee",
        domain="[(\"is_teacher_effective\", \"=\", True)]",
        string="Assigned Teacher",
    )
    create_assignment = fields.Boolean(default=True)
    meeting_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Meeting Day",
    )
    time_start = fields.Float(string="Start Time")
    time_end = fields.Float(string="End Time")

    @api.depends("student_id.birth_date")
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for wizard in self:
            if wizard.student_id.birth_date:
                delta = today - wizard.student_id.birth_date
                wizard.age_years = delta.days // 365
            else:
                wizard.age_years = 0

    @api.depends("reading_level", "memorization_juz", "age_years")
    def _compute_score(self):
        reading_score = {
            "none": 0,
            "basic": 10,
            "intermediate": 20,
            "advanced": 30,
        }
        for wizard in self:
            wizard.score = (
                    reading_score.get(wizard.reading_level, 0)
                    + wizard.memorization_juz * 2
                    + wizard.age_years
            )

    @api.depends("score")
    def _compute_recommended_level(self):
        Level = self.env["edu_level"]
        for wizard in self:
            level = Level.search(
                [
                    ("placement_min_score", "<=", wizard.score),
                    ("placement_max_score", ">=", wizard.score),
                ],
                order="sequence",
                limit=1,
            )
            if not level:
                level = Level.search([], order="sequence desc", limit=1)
            wizard.recommended_level_id = level
            if not wizard.level_id:
                wizard.level_id = level

    @api.depends("level_id", "student_id", "class_group_id", "meeting_day")
    def _compute_suggested_teachers(self):
        teachers = self.env["hr.employee"]
        for wizard in self:
            candidates = teachers.search(
                [
                    ("is_teacher_effective", "=", True),
                    ("company_id", "in", [wizard.student_id.company_id.id, False]),
                ]
            )
            scored = []
            for teacher in candidates:
                score = 0
                if wizard.level_id in teacher.teaching_specialization_ids:
                    score += 30
                if teacher.max_load:
                    score += max(0, teacher.max_load - teacher.current_load)
                else:
                    score += 5
                score -= teacher.current_load * 2
                if wizard._availability_match(teacher):
                    score += 5
                if self._gender_rule_enabled() and wizard.student_id.gender:
                    if teacher.gender == wizard.student_id.gender:
                        score += 10
                    else:
                        score -= 100
                scored.append((score, teacher.id))
            scored.sort(reverse=True)
            top_ids = [teacher_id for score, teacher_id in scored[:5] if score > -100]
            wizard.suggested_teacher_ids = [(6, 0, top_ids)]

    @api.onchange("recommended_level_id")
    def _onchange_recommended_level(self):
        if self.recommended_level_id:
            self.level_id = self.recommended_level_id

    def action_create_enrollment(self):
        self.ensure_one()
        if not self.level_id:
            raise UserError(_("Please select a level."))
        enrollment = self.env["edu_enrollment"].create(
            {
                "student_id": self.student_id.id,
                "level_id": self.level_id.id,
                "class_group_id": self.class_group_id.id,
                "status": "active",
                "placement_score": self.score,
                "placement_result": _("Placement via wizard"),
                "company_id": self.student_id.company_id.id,
            }
        )
        if self.create_assignment and self.teacher_id:
            assignment_vals = {
                "teacher_id": self.teacher_id.id,
                "student_id": self.student_id.id,
                "status": "active",
                "start_date": fields.Date.context_today(self),
                "company_id": self.student_id.company_id.id,
            }
            if self.class_group_id:
                assignment_vals["class_group_id"] = self.class_group_id.id
                assignment_vals.pop("student_id", None)
            else:
                assignment_vals.update(
                    {
                        "meeting_day": self.meeting_day,
                        "time_start": self.time_start,
                        "time_end": self.time_end,
                    }
                )
            self.env["edu_assignment"].create(assignment_vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "edu_enrollment",
            "res_id": enrollment.id,
            "view_mode": "form",
            "target": "current",
        }

    def _gender_rule_enabled(self):
        return (
                self.env["ir.config_parameter"].sudo().get_param(
                    "edu_islamic_complex.enable_gender_rules"
                )
                == "True"
        )

    def _availability_match(self, teacher):
        if self.class_group_id:
            days = [
                "0" if self.class_group_id.meeting_monday else None,
                "1" if self.class_group_id.meeting_tuesday else None,
                "2" if self.class_group_id.meeting_wednesday else None,
                "3" if self.class_group_id.meeting_thursday else None,
                "4" if self.class_group_id.meeting_friday else None,
                "5" if self.class_group_id.meeting_saturday else None,
                "6" if self.class_group_id.meeting_sunday else None,
            ]
            days = [day for day in days if day is not None]
            return any(getattr(teacher, DAY_FIELD_MAP.get(day), False) for day in days)
        if self.meeting_day:
            return getattr(teacher, DAY_FIELD_MAP.get(self.meeting_day), False)
        return False
