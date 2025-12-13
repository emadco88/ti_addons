from odoo import fields, models


class TiHrEmployee(models.Model):
    _name = "ti.hr.employee"
    _description = "TI Employee"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    job_id = fields.Many2one("hr.job", string="Job Position")
    default_attendance_from = fields.Float(string="Default Attendance From", digits=(16, 2))
    default_attendance_to = fields.Float(string="Default Attendance To", digits=(16, 2))
    active = fields.Boolean(default=True)
