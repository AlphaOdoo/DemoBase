
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    previous_ufv = fields.Float(string='UFV Anterior',
                              required=False, default='')

    current_ufv = fields.Float(string='UFV Actual',
                              required=False, default='')
