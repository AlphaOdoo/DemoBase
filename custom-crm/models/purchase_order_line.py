# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    nro_field = fields.Integer()




