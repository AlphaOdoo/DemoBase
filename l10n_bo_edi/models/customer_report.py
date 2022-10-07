from odoo import api, fields, models

class CustomerReport(models.Model):
    _name = 'customer.report'
    _description = "Customer Report"
    partner_id = fields.Many2one('res.partner', string="Customer")
    template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model','=','customer.report')]",
                                 required=True)
    line_ids = fields.One2many('account.move', 'report_id', string="Invoices")