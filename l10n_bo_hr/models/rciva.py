from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.osv import expression


#STATES = {'draft': [('readonly', False)]}

class Rciva(models.Model):
    _name = "l10n_bo_hr.rciva"
    _description = "rciva form"


    # period = fields.Char(required=False, string='period')
    # balance = fields.Char(required=False, string='balance')
    # value = fields.Char(required=False, string='value')

    name = fields.Char(string='Identifier', required=True)

    month = fields.Selection(string='Mes',
                                    selection=[('1', 'Enero'),
                                                ('2', 'Febrero'),
                                                ('3', 'Marzo'),
                                                ('4', 'Abril'),
                                                ('5', 'Mayo'),
                                                ('6', 'Junio'),
                                                ('7', 'Julio'),
                                                ('8', 'Agosto'),
                                                ('9', 'Septiembre'),
                                                ('10', 'Octubre'),
                                                ('11', 'Noviembre'),
                                                ('12', 'Diciembre')],
                                    copy=False, required=True)

    year = fields.Integer('Año', required=True, default=datetime.now().strftime('%Y'), readonly=True)
    
    previous_balance = fields.Char(required=False, string='RCIVA Saldo Anterior')

    current_balance = fields.Char(required=False, string='RCIVA Saldo Actual')

    rciva_balance = fields.Float(string='RCIVA', default= 0.0)

    form_110 = fields.Char(required=False, string='Saldo Formulario 110')

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado',
                                   ondelete='cascade'
    #                               required=True,
    #                               domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
                                   )

    update_date = fields.Date(string="Fecha actualizada")

    @api.onchange('month')
    def get_name(self):
        self.name = str(self.month).replace('10', 'Octubre').replace('11', 'Noviembre').replace('12', 
        'Diciembre').replace('1', 'Enero').replace('2', 'Febrero').replace('3', 'Marzo').replace('4', 
        'Abril').replace('5', 'Mayo').replace('6', 'Junio').replace('7', 'Julio').replace('8', 
        'Agosto').replace('9', 'Septiembre') + " " + str(self.year)




