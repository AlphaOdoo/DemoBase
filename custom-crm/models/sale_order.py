# -*- coding: utf-8 -*-

from odoo import models, fields, api

# from odoo import models, fields,_
# from odoo.api import constrains, returns
import logging

_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError

class SaleOrder(models.Model):

# Item	Producto	Descripción	Tiempo de Garantia (meses)	Proveedor	Cant.	Precio Lista  Unitario	Total Proveedor	Total  Venta	Discriminador 2 LINEA	Discriminador 3 SOLUCIONES	Discriminador 4 TIPO PRODUCTO

# 0       1           2           3                           4           5       6                       7               8               9                      10                                           11                       




    _inherit = 'sale.order'

    # Metodo para llamar al Wizar import_orderline_wizard y proceder con la importacion
    def import_product(self):
        _logger.debug("iniciando wizard de importacion")
        return {
            'name': 'Importar productos',
            'type': 'ir.actions.act_window',
            'res_model': 'import.orderline.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': self.env.context,  # estare mandando mal el contexto?
            #    'context': self.context,
        }

    # Motodos para desde una de saler.order de compra aprobada se puede generar varias purchase order segun
    # cantidad de proveedores

    def action_view_purchase_orders_inherit(self):
        self.ensure_one()

        # Leer el Order Line y ponerlo en lo lista
        # ordenar por proveedor
        # generar lista de lista 
        # lista de dupla, proveedor y lista de productos

        # purchase_order_ids = (self.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id | self.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id).ids
        # action = {
        #     'res_model': 'purchase.order',
        #     'type': 'ir.actions.act_window',
        # }
        # if len(purchase_order_ids) == 1:
        #     action.update({
        #         'view_mode': 'form',
        #         'res_id': purchase_order_ids[0],
        #     })
        # else:
        #     action.update({
        #         'name': ("Purchase Order generated from %s", self.name),
        #         'domain': [('id', 'in', purchase_order_ids)],
        #         'view_mode': 'tree,form',
        #     })

        listOrderLine = []
        listPartnerOrderLine = []
        listProduct = []

        listOrderLine = self.getListOrderInline(self)

        listPartnerOrderLine = self.getListParnerOderInLine(self, listOrderLine)

        for partner in listPartnerOrderLine:
            listProduct = self.built_list_product(self, listOrderLine, partner)
            self.built_purchase_ordel_line(self, listProduct, partner)

        return action

    def _get_new_sale_line(self, orig_sale, orig_sale_line):
        res = {
            'order_id': orig_sale.id,
            'product_id': orig_sale_line.product.id,
            'name': orig_sale_line.name,
            'sequence': orig_sale_line.sequence,
            'price_unit': orig_sale_line.price_unit,
            'product_uom': orig_sale_line.product_uom.id,
            'product_uom_qty': orig_sale_line.qty or 1,
            'product_uos_qty': orig_sale_line.qty or 1,
        }
        self.env['sale.order.line'].create(res)

        return res

    def _get_order_lines(self, sale):
        res = []
        line_env = self.env['sale.order.line']
        res = self._get_new_sale_line(sale, line_env)
        for line in sale.order_line:
            wizard_line = False
            for wzline in self.wizard_lines:
                if wzline.product == line.product_id:
                    wizard_line = wzline
                    break
            if wizard_line:
                res.append((0, 0, self._get_new_sale_line(sale, line, wizard_line)))
        return res

    def getListOrderInline(self):
        lines = []
        lines = self.order_line
        return lines
    
    def getListParnerOderInLine(self, listOrder):
        listpartner = []
        for line in listOrder:
            if line[4] not in listpartner:
                listpartner.append(line[3])
        return listpartner

    def built_list_product(self, ListOrder, partner):
        listline = []
        for line in ListOrder:
            if line[4] == partner:
                listline.append(line)

        return listline

    def built_purchase_ordel_line(self, listproduct, partner):

        purchase_order_values = {
            'order_line' : listproduct
        }
        # if len(record) != 0:
            
        #     purchase_order = self.env['sale.order'].search([('name', '=', self.env.context.get('active_id'))])
        #     purchase_order_view = purchase_order.write(purchase_order_values)
        
        # if purchase_order_view:
        #     return {
        #             'type': 'ir.actions.act_window',
        #             'res_model': 'purchase.order',
        #             'view_mode': 'form',
        #             'res_id': purchase_order_view.id,
        #             'views': [(False, 'form')],
        #         }

        sale_vals = {
            'user_id': self.order.user_id.id,
            'partner_id': self.order.partner_id.id,
            'parent_id': self.order.id,
            'date_order': self.order_date,
            'client_order_ref': self.order.client_order_ref,
            'company_id': self.order.company_id.id,
            'is_sample': True,
            'order_line': self._get_order_lines(self.order)
        }
        self.env['purchase.order'].create(sale_vals)
        return action



    def create_product(self, record):

        self.env['product.template'].create({
               'name': record[1],
               'description_sale': record[2],
               'standard_price': record[6],
                })
   
    def create_line_for_orderline(self, record):
        search = self.env['product.template'].search([('name', '=', record[1]),])
        if not search: 
            print('{record} no existe *********************')      
        lines_ids = {
            # 'id': record[0],
            'name': record[1],
            'description': record[2],
            'supplier': record[4],
            'warranty': record[3],
            'cant':  record[5],
            'cost':  record[6],
            'tot_supplier':  record[7],
            'tot_sale':  record[8],
            'Linea':  record[9],
            'Soluciones':  record[10],
            'Tipo':  record[11],
        }
        return lines_ids


    def import_in_orderLine(self, record):

        sale_order_values = {
            'order_line' : record
        }
        if len(record) != 0:
            
            sale_order = self.env['sale.order'].search([('name', '=', self.env.context.get('active_id'))])
            sale_order_view = sale_order.write(sale_order_values)
        
        if sale_order_view:
            return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    'res_id': sale_order_view.id,
                    'views': [(False, 'form')],
            }


