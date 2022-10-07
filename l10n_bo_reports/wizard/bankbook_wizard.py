import time
import json
import datetime
import io
import logging
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from psycopg2 import sql
except ImportError:
    import sql
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


#  cuenta_bancaria, Fecha Documento, Tipo Transaccion, Numero de Doc, Datos, destinatario, Ingreso, Egreso
#   siempre comenzar en la columna A


class BankBookExcelWizard(models.TransientModel):
    _name = "bankbook_xlsx_report_wizard"
    _description = "Bankbook Report Fast Wizard"

    # cabcera
    head_bank = ["Cuenta Bancaria", "Fecha Documento", "Tipo Transaccion",
                 "Numero de Doc", "Datos", "destinatario", "Ingreso", "Egreso", "Saldo"]

    account = fields.Many2one('res.partner.bank', string='cuenta', required=True)
    start_date = fields.Date(
        string="Start Date", default=datetime.datetime.now().strftime('%Y-%m-01'), required=True)
    end_date = fields.Date(
        string="End Date", default=datetime.datetime.now().strftime('%Y-%m-%d'), required=True)

    def get_account (self, id):
        return self.env['res.partner.bank'].search([('id', '=', id)])

    def print_xlsx(self):
        if self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'account_id': self.account.id,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'bankbook_xlsx_report_wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Bank Book Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        _logger.debug("Entro a get xlsx report  ************************************")
        row = 7
        fechaI = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        fechaF = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        account_ids = self.get_account(data['account_id'])
        account_number = account_ids.acc_number
        account_id = account_ids.id
        _logger.debug(f"Cuenta ***************************** {account_ids}")
        _logger.debug(f"Cuenta ***************************** {account_id}")
        _logger.debug(f"Cuenta ***************************** {account_number}")
        _logger.debug(f"Cuenta ***************************** {fechaI}")
        _logger.debug(f"Cuenta ***************************** {fechaF}")
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('B2:I3', 'Reporte de Movientos de Cuentas', head)
        sheet.write('B6', 'From:', cell_format)
        sheet.merge_range('C6:D6', str(fechaI), txt)
        sheet.write('F6', 'To:', cell_format)
        sheet.merge_range('G6:H6', str(fechaF) , txt)
        _logger.debug("Praparando para entrar a head libreta Bancaria ************************")
        row = self.head_BankBook(row, sheet)
        _logger.debug("Praparando para entrar get move bank *****************************")
        lines = self.get_movebankdate(account_number, fechaI, fechaF)

        if not lines:
            raise ValidationError('No hay datos que mostrar')
        _logger.debug(f"lines1 *****************************{lines}")
        self.body_bankbook(row, sheet, lines, fechaI, account_number)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def head_BankBook(self, row, sheet):
        _logger.debug("Entro head libreta bancaria *****************************")
        _logger.debug(self.head_bank)
        column = 0
        # bold = sheet.add_format({'bold': True})
        for item in self.head_bank:
            sheet.write(row, column, item)
            column += 1
        row = row + 1
        return row

    def body_bankbook(self, row, sheet, body, fechaI, account):
        # row es la fila donde comenzar
        # body es una lista de listas, body[0] es una lista con todo los valores que tiene head
        _logger.debug("Entro body libreta bancaria *************************************")
        _logger.debug("Esto es body *************************************")
        _logger.debug(body)
        sumSaldo = self.get_movebank_Estado_Resutaldo_Date(account, fechaI)
        _logger.debug(sumSaldo)
        _logger.debug(row)
        sheet.write(row, 6, "Saldo Anterio")
        sheet.write(row, 8, sumSaldo)
        row += 1
        _logger.debug(row)
        primer = True
        for item in body:
            sheet.write_row(row, 0, item)
            sumSaldo = item[6] - abs(item[7]) + sumSaldo
            sheet.write(row, 8, sumSaldo)
            row += 1
        sheet.write(row, 6, "Saldo Actual")
        sheet.write(row, 8, sumSaldo)
        return row

    def get_movebankdate(self, bank, fechaI, fechaF):
        # La fecha tiene que llear en formato YYYY-MM-DD
        _logger.debug( "Entro a get move bank ejecutar el sql get_movebankdate*******************")
        _logger.debug( f"bank ******************* {bank}")
        _logger.debug( f"fecha Inicial ******************* {fechaI}")
        _logger.debug( f"fecha Final ******************* {fechaF}")

        sql_select = sql.SQL(
            """
        SELECT rpb.acc_number as numCuenta, aml.date as fecha , rb.name as banco, aml.move_name as numeroDocumento, aml.name as datos, rp.display_name as destinatario, CASE WHEN aml.amount_residual > 0 THEN aml.amount_residual ELSE '0' END AS Credito, CASE WHEN aml.amount_residual < 0 THEN aml.amount_residual ELSE '0' END AS Debito
        FROM public.account_journal AS aj
        LEFT JOIN public.account_move_line aml on aml.journal_id = aj.id
        LEFT JOIN public.res_partner as rp on aml.partner_id = rp.id
        LEFT JOIN public.res_partner_bank rpb on rpb.id = aj.bank_account_id 
        LEFT JOIN public.res_bank rb on rb.id = rpb.bank_id
        WHERE 
        aj.type like 'bank'
        AND aml.amount_residual != 0
        AND rpb.acc_number = """ + chr(39) + bank + chr(39) + """
		AND aml.date >= """ + chr(39) + str(fechaI) + """ 00:00:00""" + chr(39) + """
		AND aml.date <= """ + chr(39) + str(fechaF) + """ 23:59:59"""  + chr(39) + """	
                 
        """)
        self._cr.execute(sql_select)
        lines = self._cr.fetchall()
        _logger.debug(lines)

        return lines

    def get_movebank_Estado_Resutaldo_Date(self, bank, fecha):
        # La fecha tiene que llear en formato YYYY-MM-DD
        _logger.debug(
            "Entro a get move bank ejecutar el sql get_movebank_Estado_Resutaldo_Date******************************************")
        _logger.debug(f"bank ******************* {bank}")
        _logger.debug(f"fecha Inicial ******************* {fecha}")
        sql_select = sql.SQL(
            """
        
        select SUM(aml.amount_residual) AS ESTADO
        from public.account_journal AS aj
        LEFT JOIN public.account_move_line aml on aml.journal_id = aj.id
        LEFT JOIN public.res_partner as rp on aml.partner_id = rp.id
        LEFT JOIN public.res_partner_bank rpb on rpb.id = aj.bank_account_id 
        LEFT JOIN public.res_bank rb on rb.id = rpb.bank_id
        where 
        aj.type like 'bank'
        AND aml.amount_residual != 0
		AND rpb.acc_number = """ + chr(39) + bank + chr(39) + """
		AND aml.date < """ + chr(39) + str(fecha) + """ 23:59:59""" + chr(39) + """
                 
        """)
        self._cr.execute(sql_select)
        lines = self._cr.fetchall()
        _logger.debug(lines)
        _logger.debug(lines[0][0])

        return lines[0][0] or 0
