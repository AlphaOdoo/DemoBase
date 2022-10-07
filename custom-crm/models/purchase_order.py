# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    # Item	Producto	Descripción	Tiempo de Garantia (meses)	Proveedor	Cant.	Precio Lista  Unitario	Total Proveedor	Total  Venta	Discriminador 2 LINEA	Discriminador 3 SOLUCIONES	Discriminador 4 TIPO PRODUCTO

    # 0       1           2           3                           4           5       6                       7               8               9                      10                                           11

    _inherit = 'purchase.order'

    # Metodo para llamar al Wizar import_orderline_wizard y proceder con la importacion
    def import_product(self):
        _logger.debug("iniciando wizard de importacion")
        return {
            'name': 'Importar productos',
            'type': 'ir.actions.act_window',
            'res_model': 'import.purchase.orderline.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': self.env.context,  # estare mandando mal el contexto?
            #    'context': self.context,
        }
