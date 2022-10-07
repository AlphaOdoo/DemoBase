# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class CrmLead(models.Model):

    _inherit = 'crm.lead'


    currency_USD= fields.Many2one('res.currency', string="Currency USD", required=True, default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    # sale_amount_total_USD = fields.Monetary('Sale Amount Total USD', currency_field='currency_USD', tracking=True)
  


  
    expected_revenue_1 = fields.Monetary('Expected Revenue_USD', currency_field='currency_USD', tracking=True)    
    prorated_revenue_1 = fields.Monetary('Prorated Revenue_USD', currency_field='currency_USD', store=True, compute="_compute_prorated_revenue_usd")
    recurring_revenue_1 = fields.Monetary('Recurring Revenues USD', currency_field='currency_USD', groups="crm.group_use_recurring_revenues")
    recurring_plan_1 = fields.Many2one('crm.recurring.plan', string="Recurring Plan USD", groups="crm.group_use_recurring_revenues")
    recurring_revenue_monthly_1 = fields.Monetary('Expected MRR in USD', currency_field='currency_USD', store=True,
                                               compute="_compute_recurring_revenue_monthly_usd",
                                               groups="crm.group_use_recurring_revenues")
    recurring_revenue_monthly_prorated_1 = fields.Monetary('Prorated MRR in USD', currency_field='currency_USD', store=True,
                                               compute="_compute_recurring_revenue_monthly_prorated_usd",
                                               groups="crm.group_use_recurring_revenues")

    

    cambioB = fields.Boolean(string='cambioB', default=False)
    cambioD = fields.Boolean(string='cambioD', default=False)

    def _prepare_data(self):
        USD = self.env['res.currency'].search([('name', '=', 'USD')])        
        _logger.debug("hello there people _prepare_data.............." )
        _logger.debug(USD.name)
        _logger.debug(USD.symbol)
        _logger.debug(USD.rate)
        BOB = self.env['res.currency'].search([('name', '=', 'BOB')])
        _logger.debug(BOB.name)
        _logger.debug(BOB.rate)
        _logger.debug("hello there people _prepare_data.............." )
        date = self._context.get('date') or fields.Date.today()        
        _logger.debug(date )
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company        
        return USD, BOB, company, date

    # @api.depends('sale_amount_total', 'sale_amount_total_USD', 'probability')
    # def _compute_sale_amount_total_USD(self):
    #     for lead in self:
    #         lead.sale_amount_total_USD = round( (lead.sale_amount_total or 0.0) * (self.env['res.currency'].search([('name', '=', 'USD')]).rate), 2)

    @api.depends('expected_revenue_1', 'probability')
    def _compute_prorated_revenue_usd(self):
        for lead in self:
            lead.prorated_revenue_1 = round((lead.expected_revenue or 0.0) * (lead.probability or 0) / 100.0, 2)\
                                      # @api.depends('expected_revenue_1', 'probability')


    @api.depends('recurring_revenue_1', 'recurring_plan.number_of_months')
    def _compute_recurring_revenue_monthly_usd(self):
        for lead in self:
            lead.recurring_revenue_monthly_1 = (lead.recurring_revenue or 0.0) / (lead.recurring_plan.number_of_months or 1)

    @api.depends('recurring_revenue_monthly_1', 'probability')
    def _compute_recurring_revenue_monthly_prorated_usd(self):
        
        for lead in self:
            lead.recurring_revenue_monthly_prorated_1 = (lead.recurring_revenue_monthly or 0.0) * (lead.probability or 0) / 100.0


    # aca van los bolivianos y si son modificados
    @api.onchange('expected_revenue')
    def _onchange_ganancia_bs(self):
        for record in self:
            
            if ((record.expected_revenue != '') or (record.expected_revenue != ' ')) and record.cambioD != True :
                USD, BOB, company, date = self._prepare_data()                
                record.expected_revenue_1 = BOB._convert(record.expected_revenue,USD,company,date)
                record.cambioB = True
                record.cambioD = False
            else :
                record.cambioD = False

    # aca van los dolares y si son modificados
    @api.onchange('expected_revenue_1')
    def _onchange_ganancia_dl(self):
        for record in self:
            if ((record.expected_revenue_1 != '') or (record.expected_revenue_1 != ' ')) and record.cambioB != True :
                USD, BOB, company, date = self._prepare_data()                
                record.expected_revenue = USD._convert(record.expected_revenue_1,BOB,company,date)
                record.cambioD = True
                record.cambioB = False
            else :
                record.cambioB = False

    def import_product(self):
        _logger.debug("iniciando wizard de importacion")
        return {
            'name': 'Importar productos',
            'type': 'ir.actions.act_window',
            'res_model': 'wizards.import.sale.order',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': self.env.context,  # estare mandando mal el contexto?
            #    'context': self.context,
        }

    # # para cargar proyectos
    # @api.onchange('stage_id')
    # def _create_project(self):
    #     if self.stage_id.is_won:            
    #         proj = self.env['project.project'].create({'name': self.name})
    #         proj.action_view_tasks()

    
    # project_count = fields.Integer(compute = 'compute_project_data', string= 'Number of Projects')
    # # project_ids = fields.One2many('project.project', 'project_id' string='Projects')

    # def get_project_project(self):
    #     self.ensure_one()
    #     return{
    #         'type': 'ir.actions.act_window',
    #         'name': 'Projects',
    #         'view_mode': 'tree',
    #         'res_model': 'project_project',
    #         'domain': [('name', '=', self.name)],
    #         'context': "{'create: False}"
    #     }    
    
    
    # def compute_project_data(self):
    #     for record in self:
    #         record.project_count = self.env['project.project'].search_count([('name', '=', self.name)])
            
