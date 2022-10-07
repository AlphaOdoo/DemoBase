 #-*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
#from . import purchase_order


class FacturaProveedor(models.Model):
    _inherit="stock.picking"


    nro_order = fields.Char(compute='_compute_nro_order', string='Número de Orden de Compra')


    def _compute_nro_order(self):
        for r in self:
            record = self.env['purchase.order'].search(
            [('name', '=', self.origin)])
            r.nro_order = record.nro_order