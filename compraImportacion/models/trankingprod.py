from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class trackingprod(models.Model):
    _name = 'custom_purchase.trackingprod'
    _description = 'Tracking purchase product'

    name = fields.Char(string='Identifier', required=True)
    tracking_ids = fields.One2many(comodel_name='custom_purchase.tracking',
                                 inverse_name='nave_id',
                                 string='Seguimiento')
