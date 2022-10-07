from email.policy import default
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit  = 'purchase.order.line'

    product_qty_import = fields.Float(string='Cantidad Importada', 
                                        digits='Product Unit of Measure', 
                                        required=False, 
                                        default=False)
