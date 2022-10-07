 #-*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Company(models.Model):
    _inherit="res.company"

    cod_patronal= fields.Char(string='Código Patronal')