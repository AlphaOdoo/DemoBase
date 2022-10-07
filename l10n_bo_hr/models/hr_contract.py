from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class custom_contract(models.Model):
    _inherit = 'hr.contract'

    salary_advance = fields.Monetary(string='Adelanto de sueldo')

    transport_assignment = fields.Monetary(string='Asignación Transporte')

    allowance_periods = fields.Monetary(string='Asignación Viaticos')

    premium_bonus = fields.Monetary(string='Prima')

    bonus = fields.Monetary(string='Aguinaldo')

    health_manager_id = fields.Many2one(comodel_name='res.partner', string='Ente gestor de salud',
                                        ondelete='cascade',
                                        required=False,
                                        default=False,
                                        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    health_manager = fields.Selection(string='Ente gestor de salud',
                              selection=[('1', 'Caja Nacional de Salud (C.N.S.)'),
                                         ('2', 'Caja Petrolera de Salud (C.P.S.)'),
                                         ('3', 'Caja de Salud de Caminos'),
                                         ('4', 'Caja Bancaria Estatal de Salud (C.B.E.S.)'),
                                         ('5', 'Caja de Salud de la Banca Privada (C.S.B.P.)'),
                                         ('6', 'Caja de Salud Cordes'),
                                         ('7', 'Seguro Social Universitario (S.I.S.S.U.B.)'),
                                         ('8', 'Corporación del Seguro Social Militar (COOSMIL)'),
                                         ('9', 'Seguro Integral de Salud (SINEC)')],
                              copy=False, default='1')

    avc_number = fields.Char(required=False, string='AVC-04')

    insured_code = fields.Char(string='Codigo Asegurado')
    
    nua_cua = fields.Integer(string='NUA/CUA')
    
    contributes_afp = fields.Boolean(
        string='Aporta AFP', required=False, default=False)
    
    disabled_person = fields.Boolean(
        string='Persona con Discapacidad', required=False, default=False)
    
    disabled_person_tutor = fields.Boolean(
        string='Tutor Persona con Discapacidad', required=False, default=False)
    
    retiree = fields.Boolean(
        string='ES Jubilado', required=False, default=False)

    other_discounts = fields.Monetary(string='Otros Descuentos')
    
    fine = fields.Monetary(string='Multas')

    afp_manager_id = fields.Many2one(comodel_name='res.partner', string='Gestor AFP',
                                     ondelete='cascade',
                                     required=False,
                                     default=False,
                                     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    afp_manager = fields.Selection(string='Gestor AFP',
                              selection=[('1', 'AFP Previsión'),
                                         ('2', 'AFP Futuro')],
                              copy=False, default='1')

    divisa = fields.Selection(string='Divisa',
                              selection=[('bolivianos', 'BOB'),
                                         ('dolares', 'USD'),
                                         ('euros', 'EUR')],
                              copy=False, default='bolivianos')

    contract_type_c = fields.Selection(string='Tipo de contrato',
                              selection=[('1', 'Escrito'),
                                         ('2', 'Verbal')],
                              copy=False, default='1')

    previous_rciva = fields.Monetary(string='Saldo Mes Anterior')

    current_rciva = fields.Monetary(string='Saldo Actual')
    
    form_110 = fields.Monetary(string='Saldo Formulario 110')

    previous_ufv = fields.Float(string='UFV Anterior',
                              required=False, default='')

    current_ufv = fields.Float(string='UFV Actual',
                              required=False, default='')

    retiree_reason = fields.Selection(string='Motivo de Retiro',
                              selection=[('1', 'Retiro voluntario del trabajador'),
                                         ('2', 'Vencimiento de contrato'),
                                         ('3', 'Conclusión de obra'),
                                         ('4', 'Perjuicio material causado con intención en los instrumentos de trabajo'),
                                         ('5', 'Revelación de secretos industriales'),
                                         ('6', 'Omisiones o imprudencias que afecten a la seguridad o higiene industrial'),
                                         ('7', 'Inasistencia injustificada de más de seis días continuos'),
                                         ('8', 'Incumplimiento total o parcial del convenio'),
                                         ('9', 'Robo o hurto por el trabajador'),
                                         ('10', 'Retiro forzoso')],
                              copy=False, default='1')

    job_classification = fields.Selection(string='Clasificación Laboral',
                              selection=[('1', 'Ocupaciones de dirección en la administración pública y empresas'),
                                         ('2', 'Ocupaciones de profesionales científicos e intelectuales'),
                                         ('3', 'Ocupaciones de técnicos y profesionales de apoyo'),
                                         ('4', 'Empleados de oficina'),
                                         ('5', 'Trabajadores de los servicios y vendedores del comercio'),
                                         ('6', 'Productores y trabajadores en la agricultura, pecuaria, agropecuaria y pesca'),
                                         ('7', 'Trabajadores de la industria extractiva, construcción, industria manufacturera y otros oficios'),
                                         ('8', 'Operadores de instalaciones y maquinarias'),
                                         ('9', 'Trabajadores no calificados'),
                                         ('10', 'Fuerzas armadas')],
                              copy=False, default='4')                       

    contract_modality = fields.Selection(string='Modalidad de Contrato',
                              selection=[('1', 'Tiempo indefinido'),
                                         ('2', 'A plazo fijo'),
                                         ('3', 'Por temporada'),
                                         ('4', 'Por realización de obra o servicio'),
                                         ('5', 'Condicional o eventual')],
                              copy=False, default='1') 

    loan = fields.Monetary(string='Préstamos')

    novedades = fields.Selection(string='Estado del Contrato',
                              selection=[('V', 'VIGENTE'),
                                         ('I', 'INGRESO'),
                                         ('D', 'DESVINCULACION')],
                              copy=False, default='V')
    


    # Campos Sandra Omonte
    contract_modality_2 = fields.Selection(string='Modalidad Contrato',
                                         selection=[('tiempoindef', 'Tiempo indefinido'),
                                                    ('plazofijo', 'A plazo fijo'),
                                                    ('eventual',
                                                     'Condicional o Eventual'),
                                                    ('temporada', 'Por Temporada'),
                                                    ('servicio', 'Por realizacion de Servicio')],
                                         copy=False, default='tiempoindef')
    contract_type_expiration = fields.Date(
        string='Vencimiento tipo de contratacion')
    calculate_overtime = fields.Boolean(
        string='Calcula Horas Extras', default=False)
    cbu = fields.Integer(string='CBU')
    settlement_start_date = fields.Date('Fecha Inicio Finiquito')
    dismissal_date = fields.Date('Fecha retiro')
    dismissal_reason = fields.Text('Motivo Retiro')
    # bank_company =  fields.Many2one(comodel_name='res.bank', string='Banco')
    # cta_bank =  fields.Many2one(comodel_name='res.partner.bank', string='Cuenta Banco',
    #                          domain="[('id_bank','=',bank_company')")
    #Campos Erick

    #contract_modality_c = fields.Selection(string='Modalida de contrato',
                              #selection=[ ('euros', 'EUR')],
                              #copy=False, default='bolivianos')
