
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Payslip(models.Model):
    _inherit = "hr.payslip"

    def print_report(self):
        # datas = {
        #     'inv': self,
        #     'items': self.invoice_line_ids
        # }
        # self.generate_qr_code()

        return self.env.ref('l10n_bo_hr.graphic_representation').report_action(self)


# falta trabajar
    # def print_report(self):
    #     # datas = {
    #     #     'inv': self,
    #     #     'items': self.invoice_line_ids
    #     # }
    #     #self.generate_qr_code()
    #     record = self.env['hr.employee'].search(
    #         [('name', '=', 'employee_id')])

    #     raise ValidationError((record.mobile_phone))

    #     # return self.env.ref('papeletapago.graphic_representation').report_action(self)


    def _employee_get(self):
        record = self.env['res.users'].search(
            [('name', '=', self.env.user.name)])
        return record
