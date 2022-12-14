# -*- coding:utf-8 -*-

from datetime import date, datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import date_utils


import logging
import json
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


_logger = logging.getLogger(__name__)


class SalesBookWizard(models.TransientModel):
    _name = "sales.book.wizard"
    _description = "SIN Sales Book Report Fast Wizard"

    begin_date = fields.Date(string='Begin Date', required=True)

    end_date = fields.Date(string='End Date', required=True)

    report_types = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'EXCEL')
    ], string='Report Types')

    # def trigger_report(self):

    #     invoice_ids = self.env['account.move'].search(
    #         ['&', ('invoice_date', '>=', self.begin_date),
    #          ('invoice_date', '<=', self.end_date)])

    #     # _logger.info(str(invoice_ids[0].amount_total))
    #     # PENDIENTE FILTRO POR FECHAS
    #     # return self.env.ref('l10n_bo_edi.sales_book').report_action(self, data=invoice_ids)
    #     return self.env.ref('l10n_bo_edi.sales_book').report_action(self)

    def trigger_report(self):

        invoice_ids = self.env['account.move'].search(
            ['&', ('invoice_date', '>=', self.begin_date),
             ('invoice_date', '<=', self.end_date)])

        _logger.info(str(invoice_ids))
        _logger.info(str(len(invoice_ids)))

        if (len(invoice_ids) == 0):
            self.notify('No Invoices',
                        'There are no invoices in the selected range of dates', 'info')
        else:
            return self.env.ref('l10n_bo_edi.sales_book').report_action(self)

        # PENDIENTE FILTRO POR FECHAS
        # return self.env.ref('l10n_bo_edi.sales_book').report_action(self, data=invoice_ids)

    def notify(self, title, description, type):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': (title),
                'message': description,
                'type': type,  # types: success,warning,danger,info
                'sticky': True,  # True/False will display for few seconds if false
            },
        }
        return notification

    def print_xlsx(self):
        invoice_type = self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.l10n_bo_invoicing_type')

        if self.begin_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

        ## GET ALL INVOICES
        invoice_ids = self.env['account.move'].search(
            ['&', ('invoice_date', '>=', self.begin_date),
             ('invoice_date', '<=', self.end_date),
             ('journal_id.type', '=', 'sale'),
             ('state', '!=', 'draft')])
        
        ## GET ALL REVERSED INVOICES
        rev_invoices = invoice_ids.filtered(lambda inv: inv.amount_total_signed < 0)
        invoice_ids = invoice_ids.filtered(lambda inv: inv.amount_total_signed > 0)

        _logger.info(str(invoice_ids))

        if (len(invoice_ids) == 0):
            raise ValidationError(
                'There are no invoices in the selected range of dates')

        data = {}
        # TODO iterar sobre cada objeto y mapear lo requerido
        for index, inv in enumerate(invoice_ids):
            invoice_content = {}
            if (inv.currency_id.name == 'USD'):
                exchange = 6.96
            else:
                exchange = 1
            _logger.debug("********************* entrando al for de las line")
            line_ids = inv.invoice_line_ids
            descuento = 0
            for line in line_ids:
                linename = line.product_id.name
                _logger.debug(f"es es un nombre de producto de la liena {linename}")
                if (linename):
                    if linename.find("DESCUENTO") == 0:
                        descuento = round(descuento + (-1 * line.price_total), 2)
                        _logger.debug(f" esta es la tasa de descuento dentro del for {descuento}")

            invoice_content['invoice_date'] = inv.invoice_date.strftime(
                '%d/%m/%Y')
            invoice_content['l10n_bo_invoice_number'] = inv.l10n_bo_invoice_number
            _logger.debug(f"cargando el invoice:  {inv.l10n_bo_invoice_number}")
            invoice_content['client_vat'] = inv.partner_id.vat
            invoice_content['client_name'] = inv.partner_id.name
            invoice_content['amount_total'] = inv.amount_total_signed + round((descuento * exchange), 2)
            invoice_content['amount_by_group'] = inv.amount_by_group
            invoice_content['amount_untaxed'] = inv.amount_untaxed_signed + round((descuento * exchange), 2)
            invoice_content['amount_tax'] = inv.amount_tax_signed
            invoice_content['BaseDebitoFiscal'] = inv.amount_total_signed
            # invoice_content['discount'] = round(descuento * exchange, 2)
            # Facturaci??n Electr??nica
            invoice_content['l10n_bo_cuf'] = inv.l10n_bo_cuf
            invoice_content['efact_control_code'] = inv.efact_control_code
            # Facturaci??n Est??ndar
            invoice_content['auth_number'] = inv.auth_number
            invoice_content['control_code'] = inv.control_code
            # invoice_content['state'] = 'V' if inv.state == 'posted' else 'A'
            invoice_content['state'] = 'A' if inv.payment_state == 'reversed' else 'V' ## SET CANCELED INVOICES
            invoice_content['discount'] =  inv.total_discount if inv.total_discount != 0.0 else '0.00'
            data[index] = invoice_content

        return {
            'type': 'ir.actions.report',
            'data': {'model': 'sales.book.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):

        invoice_type = self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.l10n_bo_invoicing_type')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # Cell Format
        sheet = workbook.add_worksheet()
        sheet.set_column('A:X', 25)
        cell_format = workbook.add_format({'font_size': '12px'})
        title = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '16px'})
        title.set_font_color('blue')
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '12px'})
        head.set_pattern(2)
        head.set_bg_color('blue')
        head.set_font_color('white')
        txt = workbook.add_format({'font_size': '10px'})
        # Headers
        sheet.merge_range('A1:D2', 'Registro de Ventas Estandar', title)
        sheet.merge_range('A3:B3', '(Expresado en Bolivianos)', txt)
        sheet.write('A4', 'N??', head)
        sheet.write('B4', 'Especificaci??n', head)
        sheet.write('C4', 'Fecha de la Factura', head)
        sheet.write('D4', 'N?? de la Factura', head)
        sheet.write('E4', 'C??digo de Autorizaci??n', head)
        sheet.write('F4', 'NIT/CI Cliente', head)
        sheet.write('G4', 'Complemento', head)
        sheet.write('H4', 'Nombre o Raz??n Social', head)
        sheet.write('I4', 'Importe Total de la Venta', head)
        sheet.write('J4', 'Importe ICE', head)
        sheet.write('K4', 'Importe IEHD', head)
        sheet.write('L4', 'Importe IPJ', head)
        sheet.write('M4', 'Tasas', head)
        sheet.write('N4', 'Otros No Sujetos al IVA', head)
        sheet.write('O4', 'Exportaciones y Operaciones Exentas', head)
        sheet.write('P4', 'Ventas Gravadas a Tasa Cero', head)
        sheet.write('Q4', 'Subtotal', head)
        sheet.write(
            'R4', 'Descuentos, Bonificaciones y Rebajas Sujetas al IVA', head)
        sheet.write('S4', 'Importe Gift Card', head)
        sheet.write('T4', 'Importe Base para D??bito Fiscal', head)
        sheet.write('U4', 'Debito Fiscal', head)
        sheet.write('V4', 'Estado', head)
        sheet.write('W4', 'C??digo de Control', head)
        sheet.write('X4', 'Tipo de Venta', head)
        # Data Iteration
        for index, inv in enumerate(data.items()):
            # print(index % 2)
            # if(index % 2 == 0):
            #     print('entra')
            #     txt.set_bg_color('#97c5db')
            sheet.write('A' + str(int(inv[0]) + 5), str(int(inv[0]) + 1), txt)
            sheet.write('B' + str(int(inv[0]) + 5), '2', txt)
            sheet.write('C' + str(int(inv[0]) + 5),
                        inv[1]['invoice_date'], txt)
            sheet.write('D' + str(int(inv[0]) + 5),
                        inv[1]['l10n_bo_invoice_number'], txt)
            _logger.debug(f"cargando el excel1:  {inv[1]['l10n_bo_invoice_number']}")
            _logger.debug(f"cargando el excel2:  {str(int(inv[0])+5)}")
            if invoice_type:
                sheet.write('E' + str(int(inv[0]) + 5),
                            inv[1]['l10n_bo_cuf'], txt)
            else:
                sheet.write('E' + str(int(inv[0]) + 5),
                            inv[1]['auth_number'], txt)
            sheet.write('F' + str(int(inv[0]) + 5), inv[1]['client_vat'], txt)
            sheet.write('G' + str(int(inv[0]) + 5), '', txt)
            sheet.write('H' + str(int(inv[0]) + 5), inv[1]['client_name'], txt)
            sheet.write('I' + str(int(inv[0]) + 5),
                        inv[1]['amount_total'], txt)
            sheet.write('J' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('K' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('L' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('M' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('N' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('O' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('P' + str(int(inv[0]) + 5), '0.00', txt)
            sheet.write('Q' + str(int(inv[0]) + 5),
                        inv[1]['amount_total'], txt)
            # sheet.write('R' + str(int(inv[0]) + 5),
            #             inv[1]['amount_by_group'], txt)
            sheet.write('R' + str(int(inv[0]) + 5), inv[1]['discount'], txt)
            sheet.write('S' + str(int(inv[0]) + 5), '0.00', txt)
            # sheet.write('T' + str(int(inv[0]) + 5),
            #             inv[1]['amount_untaxed'], txt)
            sheet.write('T' + str(int(inv[0]) + 5),
                        inv[1]['BaseDebitoFiscal'], txt)
            # deb_fiscal = int(inv[1]['amount_tax'])
            sheet.write('U' + str(int(inv[0]) + 5),
                        str(round(float(inv[1]['amount_tax']), 2)), txt)
            sheet.write('V' + str(int(inv[0]) + 5), inv[1]['state'], txt)
            if invoice_type:
                sheet.write('W' + str(int(inv[0]) + 5),
                            inv[1]['efact_control_code'], txt)
            else:
                sheet.write('W' + str(int(inv[0]) + 5),
                            inv[1]['control_code'], txt)
            sheet.write('X' + str(int(inv[0]) + 5), '0', txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
