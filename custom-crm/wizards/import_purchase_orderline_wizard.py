# -*- coding: utf-8 -*-

import os
import csv
import tempfile
import xlrd, mmap, xlwt
import base64, binascii
from odoo import api, fields, models, _, SUPERUSER_ID
from io import BytesIO
from odoo.exceptions import UserError
import logging

try:
    from psycopg2 import sql
except ImportError:
    import sql

_logger = logging.getLogger(__name__)


#   Cabecera del EXCEL de importacion de ventas a cliente
#  Item, Producto, Descripción, Tiempo de Garantia (meses), Proveedor, Cant,
# Precio Lista Unitario, Total Proveedor, Total Venta, Discriminador 2 LINEA,
# 	Discriminador 3 SOLUCIONES, Discriminador 4 TIPO PRODUCTO]
#


class ImportPurchaseOrderlineWizard(models.TransientModel):
    _name = "import.purchase.orderline.wizard"
    _description = "import_purchase_orderline_wizard"

    file_data = fields.Binary('Archive', required=True, )
    file_name = fields.Char('File Name')

    def _default_order(self):
        return self.env['purchase.order'].browse(self._context.get('active_id'))

    def _default_company(self):
        return self.env['res.company'].browse(self._context.get('company_id')) or self.env.company

    def _takeOut_subtringEnd(self, cadena, sub):
        pcadena = str(cadena)
        pcadena = pcadena.strip().replace(chr(13), '')
        subcadena = str(sub)
        plon = len(pcadena)
        ubica = pcadena.find(subcadena)
        if ((ubica + len(subcadena)) < plon):
            _logger.debug(f"la sucadena {subcadena} nno esta al final de {pcadena}")
            return pcadena
        else:
            _logger.debug(f"la sucadena {subcadena} esta al final de {pcadena}")
            return pcadena.replace(".0", "")

    def import_fromxlsx(self):
        try:
            _logger.debug("********************************************")
            _logger.debug("sacar el purchase order original")
            origin_purchase_order = self._default_order()
            _logger.debug("********************************************")
            _logger.debug("validar el archivo")
            # if not self.csv_validator(self.file_data):
            #     raise UserError(_("The file must be an .xls/.xlsx extension"))
            _logger.debug("********************************************")
            _logger.debug("valido que archivo xls")
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file_data))  # self.xls_file is your binary field
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            worksheet = workbook.sheet_by_index(0)
            first_row = []  # The row where we stock the name of the column
            for col in range(worksheet.ncols):
                first_row.append(worksheet.cell_value(0, col))
            _logger.debug('Sacando el encabezado ****************')
            _logger.debug(first_row)

            # transform the workbook to a list of dictionaries
            archive_lines = []
            for row in range(1, worksheet.nrows):
                elm = {}
                for col in range(worksheet.ncols):
                    elm[first_row[col]] = self._takeOut_subtringEnd(worksheet.cell_value(row, col), ".0")

                _logger.debug('Sacando el cuerpo ****************')
                _logger.debug(elm)
                archive_lines.append(elm)

            # purchase_order_obj = self.env['purchase.order']
            product_obj = self.env['product.product']
            product_template_obj = self.env['product.template']
            purchase_order_line_obj = self.env['purchase.order.line']
            default_position_partner = self._default_order().partner_id.property_account_position_id


            # self.valid_columns_keys(archive_lines)
            self.valid_product_code(archive_lines, product_obj, product_template_obj)
            # self.valid_prices(archive_lines)

            cont = 0

            for line in archive_lines:
                cont += 1
                nro = str(line.get('Item', ""))
                code = str(line.get('Referencia Interna', ""))
                product_id = product_obj.search([('default_code', '=', code)])

                _logger.debug('Sacando el producto ****************')
                _logger.debug(code)
                _logger.debug(product_id)
                quantity = float(line.get(u'Cant.', 0))
                leadtime = line.get('Lead time', "")
                _logger.debug(quantity)
                _logger.debug('Lead Time ***********************')
                _logger.debug(leadtime)
                price_unit = line.get('Precio Lista Unitario', "")
                _logger.debug(price_unit)
                # product_uom = product_template_obj.search([('default_code', '=', code)])
                # _logger.debug(product_uom)
                if (default_position_partner.name == "Exterior"):
                    _logger.debug('entr a exterior')
                    # taxes = self.env['account.tax'].search(['name', '=', 'Tasa 0'])
                    taxes = self.env['account.tax'].search([('name', '=', 'Tasa 0')])
                    _logger.debug(taxes)
                else:
                    taxes = product_id.supplier_taxes_id.filtered(
                        lambda r: not product_id.company_id or r.company_id == product_id.company_id)
                    _logger.debug(taxes)
                tax_ids = default_position_partner.map_tax(taxes)
                _logger.debug(tax_ids)
                _logger.debug('ent al if paara crear al linea en prucase order line****************')
                _logger.debug(origin_purchase_order.id)
                _logger.debug(product_id.id)

                if origin_purchase_order and product_id:
                    _logger.debug('ent al if paara crear al linea puchase order****************')
                    vals1 = {
                        'nro_field': nro,
                        'order_id': origin_purchase_order.id,
                        'company_id': origin_purchase_order.company_id.id,
                        'product_id': product_id.id,
                        # 'date_planed' : '', se coloca automaticamnete
                        'product_qty': float(quantity),
                        'price_unit': price_unit,
                        # 'product_uom': product_id.product_tmpl_id.uom_po_id.id,
                        'name': product_id.name,
                        'taxes_id': [(6, 0, tax_ids.ids)],
                    }
                    purchase_order_line_id = purchase_order_line_obj.create(vals1).id
                    Tag1_id = self.env['account.analytic.tag'].search([('name', '=', line.get('Tag 1'))]).id
                    Tag2_id = self.env['account.analytic.tag'].search([('name', '=', line.get('Tag 2'))]).id
                    Tag3_id = self.env['account.analytic.tag'].search([('name', '=', line.get('Tag 3'))]).id
                    # valtag1 = {
                    #     'purchase_order_line_id': purchase_order_line_id,
                    #     'account_analytic_tag_id' : Tag1_id,
                    # }
                    # valtag2 = {
                    #     'purchase_order_line_id': purchase_order_line_id,
                    #     'account_analytic_tag_id' : Tag2_id,
                    # }
                    # valtag3 = {
                    #     'purchase_order_line_id': purchase_order_line_id,
                    #     'account_analytic_tag_id' : Tag3_id,
                    # }
                    sql_select = sql.SQL(
                        '''
                        INSERT INTO account_analytic_tag_purchase_order_line_rel (purchase_order_line_id,account_analytic_tag_id) VALUES 
                        ( ''' + chr(39) + str(purchase_order_line_id) + chr(39) + ''' , ''' + chr(39) + str(Tag1_id) + chr(39) + ''' ),    
                        ( ''' + chr(39) + str(purchase_order_line_id) + chr(39) + ''' , ''' + chr(39) + str(Tag2_id) + chr(39) + ''' ),    
                        ( ''' + chr(39) + str(purchase_order_line_id) + chr(39) + ''' , ''' + chr(39) + str(Tag3_id) + chr(39) + ''' )'''
                    )

                    self._cr.execute(sql_select)
                    self._cr.execute('commit')

                    # account_analytic_tag_sale_order_line_rel_obj.create(valtag1)
                    # account_analytic_tag_sale_order_line_rel_obj.create(valtag2)
                    # account_analytic_tag_sale_order_line_rel_obj.create(valtag3)

                    _logger.debug('se quedara aca ****************')
                    _logger.debug(purchase_order_line_id)
                    _logger.debug(Tag1_id)
                    _logger.debug(Tag2_id)
                    _logger.debug(Tag3_id)

            if self._context.get('open_order', False):
                return origin_purchase_order.action_view_order(origin_purchase_order.id)
            return {'type': 'ir.actions.act_window_close'}
        except Exception as e:
            raise UserError(_('error ' + str(e)))

    def find_parnert(self, record):
        return self.env['res.partner'].search([('name', '=', record.get('Proveedor'))])

    def create_parnert(self, record):
        _logger.debug("entro a crear partner en sale order")
        _logger.debug(record.get('Proveedor'))
        partner = record.get('Proveedor')
        comp_id = self.env.company.id
        _logger.debug(comp_id)
        # self.env['res.partner'].create({
        #     'name': partner,
        #     'company_id': comp_id,
        # })
        vals = {
            'name': partner,
            'customer_rank': 1,
            'supplier_rank': 0,
            'company_id': comp_id,
            'company_type': 'company',
            'type': 'contact',
        }
        return self.env['res.partner'].create(vals)

    def create_product(self, record):
        product_category_obj = self.env['product.category']
        partner = self.find_parnert(record)
        if partner:
            _logger.debug("hay partner huuuura")
        else:
            _logger.debug("no hay partner  chingaaaos")
            partner = self.create_parnert(record)
        _logger.debug("CREANDO PRODUCTO NUEVO")
        ventt = float(record.get('Venta Total'))
        _logger.debug(ventt)
        _logger.debug(record)
        _logger.debug(record.get('Producto'))
        _logger.debug(record.get('Cant.'))
        cant = float(record.get(u'Cant.', 0))
        leadtime = record.get('Lead time', "")
        product_code = record.get('Referencia Interna', "")
        std_price = float(ventt / cant)
        _logger.debug(f'Este es el precio standar {std_price}')
        cat_id = product_category_obj.search([('complete_name', '=', record.get('Sub Categoria'))]).id
        _logger.debug(f'Este es el precio standar {cat_id}')
        comp_id = self.env.company.id
        _logger.debug('Esta la compañiaaa')
        _logger.debug(comp_id)
        type_option = self.get_valid_type(record.get('Tipo'))
        _logger.debug(type_option)
        seller = self.env['product.supplierinfo'].create({
            'name': partner.id,
            'price': record.get('Precio Lista Unitario'),
            'delay': leadtime,
            'product_code': product_code,
        })
        sinit = record.get('SIN Items')
        measureu = record.get('Measure Items')
        sin_item = self.env['sin_items'].search([('sin_code', '=', sinit)]).id
        measure_unit = self.env['measure_unit'].search([('description', '=', measureu)]).id

        self.env['product.template'].create({
            'name': record.get('Producto'),
            'description_sale': record.get('Descripción'),
            'description_purchase': record.get('Descripción'),
            'standard_price': record.get('Precio Lista Unitario'),
            'list_price': std_price,
            'default_code': product_code,
            'categ_id': cat_id,
            'company_id': comp_id,
            'type': type_option,
            'invoice_policy': 'order',
            'tracking': 'serial',
            'sale_ok': 'true',
            'purchase_ok': 'true',
            'seller_ids': [seller.id],
            'sin_item': sin_item,
            'measure_unit': measure_unit,
        })

    # combertirlo todo en mayusculas
    def find_product(self, record):
        return self.env['product.template'].search([('default_code', '=', record.get('Referencia Interna'))])

    @api.model
    def valid_prices(self, archive_lines):
        cont = 0
        for line in archive_lines:
            cont += 1
            price = line.get('price', "")
            if price != "":
                price = str(price).replace("$", "").replace(",", ".")
            try:
                price_float = float(price)
            except:
                raise UserError(
                    "The price of the line item %s does not have an appropriate format, for example: '100.00' - '100'" % cont)
        return True

    @api.model
    def get_valid_price(self, price, cont):
        if price != "":
            price = str(price).replace("$", "")     #.replace(",", ".")
        try:
            price_float = float(price)
            _logger.debug('Calculando el price ***********************')
            _logger.debug(price_float)
            return price_float
        except:
            raise UserError(
                "The price of the line item %s does not have an appropriate format, for example: '100.00' - '100" % cont)
        return False

    @api.model
    def get_valid_type(self, typeA):
        cad = ''
        try:
            if typeA != "":
                if typeA == 'Consumible':
                    cad = 'consu'
                    _logger.debug('tipo consu ***********************' + cad)
                elif typeA == 'Servicio':
                    cad = 'service'
                    _logger.debug('tipo service ***********************' + cad)
                elif typeA == 'Almacenable':
                    cad = 'product'
                    _logger.debug('tipo product ***********************' + cad)
                else:
                    car = 'Error en el Type'
                    _logger.debug('tipo consu ***********************' + cad)
                    raise UserError('Error al crear el tipo de producto')
                    return ''
            return cad
        except:
            raise UserError(
                "The type of the line item %s does not have an appropriate format, Consumible, Servicio, Almacenable")
        return False

    @api.model
    def valid_product_code(self, archive_lines, product_obj, product_template_obj):
        cont = 0
        for line in archive_lines:
            cont += 1
            code = str(line.get('Referencia Interna', ""))
            product_id = product_template_obj.search([('default_code', '=', code)])
            if len(product_id) > 1:
                raise UserError("The product code of line %s is duplicated in the system." % cont)
            if not product_id:
                _logger.debug('Entro al If porque no hay producto ****************')
                self.create_product(line)
                # raise UserError("The product code of line %s can't be found in the system." % cont)

    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        # print "columns>>",columns
        text = "The file must contain the following columns: code, quantity, and price. \n The following columns are not in the file:";
        text2 = text
        # Item
        # Referencia Interna
        # Producto
        # Descripción
        # Sub Categoria
        # Lead time
        # Tipo
        # tracking
        # Tiempo de Garantia(meses)
        # Proveedor
        # Cant.
        # Precio Lista Unitario
        # Total Proveedor
        # Venta Total
        # Tag 1
        # Tag 2
        # Tag 3

        if not 'Item' in columns:
            text += "\n| Item |"
        if not 'Referencia Interna' in columns:
            text += "\n| Referencia Interna |"
        if not 'Producto' in columns:
            text += "\n| Producto |"
        if not 'Descripción' in columns:
            text += "\n| Descripción |"
        if not 'Sub Categoria' in columns:
            text += "\n| Sub Categoria |"
        if not 'Tipo' in columns:
            text += "\n| Tipo |"
        if not 'Lead time' in columns:
            text += "\n| Lead time |"
        if not 'Tiempo de Garantia(meses)' in columns:
            text += "\n| Tiempo de Garantia(meses) |"
        if not 'Proveedor' in columns:
            text += "\n| Proveedor |"
        if not u'Cant.' in columns:
            text += "\n| Cant. |"
        if not 'Precio Lista Unitario' in columns:
            text += "\n| Precio Lista Unitario |"
        if not 'Total Proveedor' in columns:
            text += "\n| Total Proveedor |"
        if not 'Venta Total' in columns:
            text += "\n| Venta Total |"
        if not 'Tag 1' in columns:
            text += "\n| Tag 1 |"
        if not 'Tag 2' in columns:
            text += "\n| Tag 2 |"
        if not 'Tag 3' in columns:
            text += "\n| Tag 3 |"
        if not 'SIN Items' in columns:
            text += "\n| SIN Items|"
        if not 'Measure Items' in columns:
            text += "\n| Measure Items |"
        if text != text2:
            raise UserError(text)
        return True

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.xls' or extension == '.xlsx' else False


