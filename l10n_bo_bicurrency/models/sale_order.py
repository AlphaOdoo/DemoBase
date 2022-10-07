from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order BO Inherit'

    def _prepare_data(self):
        USD = self.env['res.currency'].search([('name', '=', 'USD')])
        BOB = self.env['res.currency'].search([('name', '=', 'BOB')])
        date = self._context.get('date') or fields.Date.today()
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
        return USD, BOB, company, date

    total_bs = fields.Float(string='Total Bs', compute="compute_total_bs", store=True)

    @api.depends('amount_total')
    def compute_total_bs(self):
        for rec in self:
            if 'USD' in rec.pricelist_id.name:
                USD, BOB, company, date = self._prepare_data()
                rec.total_bs = USD._convert(rec.amount_total, BOB, company, date)
                # rec.total_bs = rec.amount_total * 6.96
            else:
                rec.total_bs = rec.amount_total

    total_usd = fields.Float(string='Total USD', compute="compute_total_usd", store=True)
    
    @api.depends('amount_total')
    def compute_total_usd(self):
        for rec in self:
            if 'USD' not in rec.pricelist_id.name:
                USD, BOB, company, date = self._prepare_data()
                rec.total_usd = BOB._convert(rec.amount_total, USD, company, date)
                # rec.total_usd = rec.amount_total / 6.96
            else:
                rec.total_usd = rec.amount_total
            
    
