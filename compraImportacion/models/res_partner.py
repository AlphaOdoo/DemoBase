 #-*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Partner(models.Model):
    _inherit="res.partner"

    isforwarder= fields.Boolean(string='¿Es Forwarder?',default=False)
