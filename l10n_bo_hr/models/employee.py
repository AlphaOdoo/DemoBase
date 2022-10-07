from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class employee(models.Model):
    _inherit = 'hr.employee'

    sucursal_id = fields.Selection(string='Sucursal',
                                   selection=[('lpz', 'La Paz'),
                                              ('cbba', 'Cochabamba'),
                                              ('scz', 'Santa Cruz')],
                                   copy=False, default='lpz')

    # CAmpos Adicionados

    all_name = fields.Char(string='Nombres', required=True, default='')

    paternal_surname = fields.Char(
        string='Apellido Paterno', required=False, default='')

    maternal_surname = fields.Char(
        string='Apellido Materno', required=False, default='')

    maried_surname = fields.Char(
        string='Apellido de Casada 1', required=False, default='')

    afp_affiliate = fields.Char(
        string='AFP Afiliada', required=False, default='')

    blood_type = fields.Char(string='Tipo de Sangre',
                             required=False, default='')
                             
    cod_laboral = fields.Char(string='Cod. Laboral',
                              required=False, default='')

    cod_dependent = fields.Char(string='Cod. Dependiente',
                                required=False, default='')
    
    ci_ext = fields.Char(string='Ext. CI',
                                required=False, default='')

    doc_type = fields.Selection(string='Tipo Doc.',
                                   selection=[('CI', 'Carnet de Identidad'),
                                              ('PASAPORTE', 'Pasaporte')],
                                   copy=False, default='CI')
    
    employee_address = fields.Char(string='Dirección',
                                required=False, default='')
    
    @api.onchange('name')
    def _onchange_name(self):
        complete_name = ''

        complete_name = str(self.paternal_surname) + ' ' + \
            str(self.maternal_surname) + ' ' + str(self.all_name)
        self.name = complete_name

    @api.onchange('all_name')
    def _onchange_allname(self):
        complete_name = ''

        complete_name = str(self.paternal_surname) + ' ' + \
            str(self.maternal_surname) + ' ' + str(self.all_name)
        self.name = complete_name

    @api.onchange('paternal_surname')
    def _onchange_pat(self):
        complete_name = ''

        complete_name = str(self.paternal_surname) + ' ' + \
            str(self.maternal_surname) + ' ' + str(self.all_name)
        self.name = complete_name

    @api.onchange('maternal_surname')
    def _onchange_mat(self):
        complete_name = ''

        complete_name = str(self.paternal_surname) + ' ' + \
            str(self.maternal_surname) + ' ' + str(self.paternal_surname)
        self.name = complete_name
