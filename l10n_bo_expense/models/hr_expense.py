from odoo import models, fields, api
from odoo.exceptions import UserError, Warning , ValidationError


class hrexpense(models.Model):
    _inherit = 'hr.expense'

    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Proveedor',
                                 ondelete='set null', required=False)

    control_code = fields.Char(string='Código de Control', required=False)

    authorization_code = fields.Char(string='Código Autorización', required=False)

    fixed_background = fields.Selection(string= 'Fondos Fijos',
                                    selection=[('lpz','CHLPZ'),
                                                ('scz','CHSCZ'),
                                                ('sczatm','CHSCZATMs'),
                                                ('cbba','CHCBBA'),
                                                ('oru','CHORU'),
                                                ('tja','CHTJA'),
                                                ('pts','CHPTS'),
                                                ('scr','CHSCR')],
                                    copy=False, default='lpz')

    invoice_number = fields.Char(string='Número de Factura', required=False)

    @api.onchange('partner_id')
    def _get_partner_nit(self):
        self.write({'partner_nit' : self.partner_id.vat}) 
    partner_nit = fields.Char(string='NIT',required=False)

    discount = fields.Float(string='Descuento', required=False)

    rate = fields.Float(string='Tasas', required=False)

    # def get_global_total(self):
    #     self.global_total = self.total_amount - self.discount + self.rate

    @api.onchange('rate')
    def _get_subtotal_from_discount(self):
        # if self.discount >= (self.unit_amount * self.quantity):
        #     raise Warning("Descuento no puede sobrepasar el subtotal")
        # else:
        #     self.write({'subtotal': (self.unit_amount * self.quantity) - self.discount})
        self.write({'subtotal': (self.unit_amount * self.quantity) - self.rate})
    @api.onchange('discount')
    def _get_subtotal_from_rate(self):
        # if self.rate >= self.total_amount:
        #     raise Warning("Tasas no pueden sobrepasar el total")
        # else:
        #     self.write({'total_amount': self.subtotal - self.rate})
        self.write({'total_amount': self.subtotal - self.discount})
    
    @api.onchange('unit_amount')
    def _get_subtotal_from_unit_amount(self):
        self.write({'subtotal': (self.unit_amount * self.quantity) - self.rate})
    
    @api.onchange('quantity')
    def _get_subtotal_from_quantity(self):
        self.write({'subtotal': (self.unit_amount * self.quantity) - self.rate})

    @api.onchange('subtotal')
    def _get_total_from_subtotal(self):
        self.write({'total_amount':self.subtotal - self.discount})
    subtotal = fields.Float(string='Subtotal', required=False)

    total_amount = fields.Monetary(string="Total", readonly=False)

    
    
    
    

