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


class BankingWizard(models.TransientModel):
    _name = "sales.banking.wizard"
    _description = "SIN Banking Report Fast Wizard"

    begin_date = fields.Date(string='Begin Date', required=True)

    end_date = fields.Date(string='End Date', required=True)

    report_types = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'EXCEL')
    ], string='Report Types')

    # def trigger_report(self):

    #     invoice_ids = self.env['account.move'].search(
    #         ['&', ('invoice_date_due', '>=', self.begin_date),
    #          ('invoice_date_due', '<=', self.end_date)])

    #     # _logger.info(str(invoice_ids[0].amount_total))
    #     # PENDIENTE FILTRO POR FECHAS
    #     # return self.env.ref('l10n_bo_edi.sales_book').report_action(self, data=invoice_ids)
    #     return self.env.ref('l10n_bo_edi.sales_book').report_action(self)

    def trigger_report(self):

        account_payment_ids = self.env['account.payment'].search(
            ['&', ('date', '>=', self.begin_date),
             ('date', '<=', self.end_date)])

        _logger.info(str(account_payment_ids))
        _logger.info(str(len(account_payment_ids)))

        if (len(invoice_ids) == 0):
            self.notify('No Payment',
                        'There are no payments in the selected range of dates', 'info')
        else:
            return self.env.ref('l10n_bo_edi.sales_banking').report_action(self)

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
        
        stored_payments = ['1']
        self._cr.execute('''
            SELECT
                payment.id,
                --ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
				invoice.id as invid,
                invoice.move_type
            FROM account_payment payment
            JOIN account_move move ON move.id = payment.move_id
            JOIN account_move_line line ON line.move_id = move.id
            JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
            JOIN account_move invoice ON invoice.id = counterpart_line.move_id
            JOIN account_account account ON account.id = line.account_id
            WHERE account.internal_type IN ('receivable', 'payable')
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
				AND move.date BETWEEN ''' + chr(39) + str(self.begin_date) + chr(39) + ''' AND ''' + chr(39) + str(self.end_date) + chr(39) + '''
            GROUP BY payment.id, invoice.move_type, invoice.id
        ''')
        data = {}
        query_res = self._cr.dictfetchall()
        if self.begin_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

        #if (len(invoicquery_rese_ids) == 0):
        #    raise ValidationError(
        #        'There are no invoices in the selected range of dates')
        index = 0
        for res in query_res:
            pay = self.env['account.payment'].browse(res['id'])
            inv = self.env['account.move'].browse(res['invid'])
            if (inv.amount_total>=50000):
                invoice_content = {}
                invoice_content['invoice_date_due'] = inv.invoice_date_due.strftime('%d/%m/%Y')
                invoice_content['l10n_bo_cuf'] = inv.l10n_bo_cuf
                invoice_content['l10n_bo_invoice_number'] = inv.l10n_bo_invoice_number
                invoice_content['client_vat'] = inv.partner_id.vat
                invoice_content['client_name'] = inv.partner_id.name
                invoice_content['amount_total'] = inv.amount_total
                invoice_content['amount_payment'] = pay.amount
                invoice_content['amount_by_group'] = inv.amount_by_group
                invoice_content['amount_untaxed'] = inv.amount_untaxed
                invoice_content['invoice_number'] = inv.l10n_bo_invoice_number
                invoice_content['payment_ref'] = pay.ref
                invoice_content['account_num'] = pay.move_id.journal_id.bank_account_id.acc_number
                invoice_content['bank_vat'] = pay.move_id.journal_id.bank_account_id.bank_id.vat
                invoice_content['payment_method'] = pay.payment_method_id.name
                invoice_content['auth_number'] = inv.auth_number
                invoice_content['payment_date'] = pay.date.strftime('%d/%m/%Y')
                data[index] = invoice_content
                index = index + 1


        return {
            'type': 'ir.actions.report',
            'data': {'model': 'sales.banking.wizard',
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
        sheet.merge_range('A1:D2', 'Reporte de bancarización', title)
        sheet.merge_range('A3:B3', '(Expresado en Bolivianos)', txt)
        sheet.write('A4', 'N°', head)
        sheet.write('B4', 'Modalidad Transacción', head)
        sheet.write('C4', 'Fecha Fact/Doc', head)
        sheet.write('D4', 'Tipo Transacción', head)
        sheet.write('E4', 'NIT CI proveedor', head)
        sheet.write('F4', 'Nombre/Razón Social Proveedor', head)
        sheet.write('G4', 'Nro fac/doc', head)
        sheet.write('H4', 'Nro de contrato', head)
        sheet.write('I4', 'Importe Factura/Doc', head)
        sheet.write('J4', 'Nro autoriz fac/doc', head)
        sheet.write('K4', 'Nro cta del doc del pago', head)
        sheet.write('L4', 'Montos en documento del pago', head)
        sheet.write('M4', 'Monto acumulado2', head)
        sheet.write('N4', 'NIT entidad financiera', head)
        sheet.write('O4', 'Nro doc de pago o (Nº transacción u operación)', head)
        sheet.write('P4', 'Tipo doc de pago', head)
        sheet.write('Q4', 'Fecha del doc de pago', head)
        # Data Iteration
        for index, inv in enumerate(data.items()):
            # print(index % 2)
            # if(index % 2 == 0):
            #     print('entra')
            #     txt.set_bg_color('#97c5db')
            #inv[1]['l10n_bo_cuf'], txt)
            print(inv[1]['amount_by_group'])
            sheet.write('A' + str(int(inv[0]) + 5), str(int(inv[0]) + 1), txt)
            sheet.write('B' + str(int(inv[0]) + 5), '2', txt)
            sheet.write('C' + str(int(inv[0]) + 5),
                        inv[1]['invoice_date_due'], txt)
            sheet.write('D' + str(int(inv[0]) + 5), '1', txt)
            sheet.write('E' + str(int(inv[0]) + 5), inv[1]['client_vat'], txt)
            sheet.write('F' + str(int(inv[0]) + 5), inv[1]['client_name'], txt)
            sheet.write('G' + str(int(inv[0]) + 5), inv[1]['invoice_number'], txt)
            sheet.write('H' + str(int(inv[0]) + 5), '0', txt)
            sheet.write('I' + str(int(inv[0]) + 5), inv[1]['amount_total'], txt)
            if invoice_type:
                sheet.write('J' + str(int(inv[0]) + 5),
                            inv[1]['l10n_bo_cuf'], txt)
            else:
                sheet.write('J' + str(int(inv[0]) + 5),
                            inv[1]['auth_number'], txt)            
            sheet.write('K' + str(int(inv[0]) + 5), inv[1]['account_num'], txt)
            sheet.write('L' + str(int(inv[0]) + 5), inv[1]['amount_payment'], txt)
            sheet.write('M' + str(int(inv[0]) + 5), inv[1]['amount_payment'], txt)
            sheet.write('N' + str(int(inv[0]) + 5), inv[1]['bank_vat'], txt)
            sheet.write('O' + str(int(inv[0]) + 5), inv[1]['payment_ref'], txt)
            sheet.write('P' + str(int(inv[0]) + 5), inv[1]['payment_method'], txt)
            sheet.write('Q' + str(int(inv[0]) + 5), inv[1]['payment_date'], txt)


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
