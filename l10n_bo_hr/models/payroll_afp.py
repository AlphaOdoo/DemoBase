import time
import json
import datetime
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
import pandas as pd
import numpy as np

try:
    from psycopg2 import sql
except ImportError:
    import sql
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PayrollAfp(models.TransientModel):

    _name = "payroll_afp"
    _description = "Payroll to AFP"
    start_date = fields.Date(
        # string="Start Date",  default=time.strftime('%Y-%m-01'), required=True)
        string="Start Date",  default=time.strftime('%Y-%m-%d'), required=True)

    end_date = fields.Date(
        # string="End Date",  default=datetime.datetime.now(), required=True)
        string="End Date",  default=time.strftime('%Y-%m-%d'), required=True)
    head_bank = ["EMPLEADO", "APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRES", 
                "COD. ASEGURADO", "NRO. CI", "EXTENSION", "CARGO", "DIAS TRABAJADOS", "INGRESO", "AÑOS", "PORCENTAJE",
                "BASICO", "BONO ANTIGUEDAD", "OTROS HABERES", "TOTAL GANADO", "RCIVA",
                "AFP-SIP", "APORTE SOLIDARIO", "AFP NACIONAL SOLIDARIO", "PRESTAMOS ANTICIPOS",
                "OTROS DESCUENTOS", "TOTAL DESCUENTOS", "LIQUIDO PAGABLE",
                "AFP's 4.71%", "CNS 10%", "2%_FONVIS", "INDEMNIZACION 8.33%", "AGUINALDO 8.33%", "PRIMA 8.33%",
                "COSTO MENSUAL BS.", "REGIONAL"
                 ]

    def print_xlsx(self):
        # Busqueda por fechas
        invoice_ids = self.env['hr.employee'].search(
            [])

        # valida que la fecha inicio sea inferior a fecha fin
        if self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

        # valida que hayan datos en la data
        if (len(invoice_ids) == 0):
            raise ValidationError(
                'There are no invoices in the selected range of dates')

        data = {}
        data['start_date'] = self.start_date
        data['end_date'] = self.end_date
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'payroll_afp',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'template afp',
                     },
            'report_type': 'xlsx',
        }

    def regla(self):
        return self.env.ref('l10n_bo_hr.consumo_regla').report_action(self)

    def get_xlsx_afp_report(self, data, response):

        row = 7
        lines = []
        fechaI = self.start_date
        fechaF = self.end_date
        account = 1
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('B2:I3', 'PLANILLA SUELDOS', head)
        sheet.write('B6', 'From:', cell_format)
        sheet.merge_range('C6:D6', data['start_date'], txt)
        sheet.write('F6', 'To:', cell_format)
        sheet.merge_range('G6:H6', data['end_date'], txt)

        row = self.head_BankBook(row, sheet)

        lines = self.get_payroll(data)

        self.body_bankbook(row, sheet, lines,
                           self.start_date, self.end_date, account)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # def get_payrollORIGINAL(self):

    #     lines = []
    #     sql_select = sql.SQL(
    #         """
    #     select
    #             emp.paternal_surname, emp.maternal_surname, emp.all_name, con.avc_number, emp.job_title, 0 as dias_trabajados, con.date_start,
    #             emp.birthday, '0.00%' as porc, con.wage, '0,00' as haber_basico, '0,00' as bono_antiguedad, '0,00' as otros_Haberes,
    #             '0,00' as total_ganado, '0,00' as rc_iva, '0,00' as sistema_integral, '0,00' as aporte_solidario, '0,00' as aporte_nai_solidario,
    #             '0,00' as prestamos_anticipos, '0,00' as otros_descuentos, '0,00' as total_descuentos, '0,00' as liquido_pagable, '0,00' as regional
    #             ,pl.name,pl.total
    #             from hr_payslip_line as pl
    #             left join hr_payslip as p
    #             on pl.slip_id = p.id
    #             left join hr_employee as emp
    #             on emp.id = p.employee_id
    #             left join resource_resource as r
    #             on r.id = emp.resource_id
    #             left join hr_contract as con on con.id = emp.contract_id
    #             where p.state = 'done'
    #             --and (pl.code like s)
    #             --and (to_char(p.date_to,'mm')=%s)
    #             --and (to_char(p.date_to,'yyyy')=%s)
    #             --group by r.name, p.date_to
    #     """)
    #     # % self.start_date % self.end_date
    #     # -- and aml.date >= % s
    #     # -- and aml.date <= % s AND rpb.id = %s % bank
    #     self._cr.execute(sql_select)
    #     lines = self._cr.fetchall()
    #     return lines

    def get_payroll(self, data):
        fechaI = data['start_date']
        fechaF = data['end_date']
        where = ' p.date_from >= ' + "'" + fechaI + \
            "'" + 'and p.date_to <=' + "'" + fechaF + "'"
        order = ' Order by emp.paternal_surname'
        lines_rciva = []
        sql_select = sql.SQL(
            """
            SELECT emp.id as Empleado, 
                    COALESCE(emp.paternal_surname,' ') as Paterno,
                    COALESCE(emp.maternal_surname,' ') as Materno, 
                    COALESCE(emp.all_name,' ') AS Nombres,                    
                    COALESCE(con.avc_number,' ') as CodAsegurado,
                    COALESCE(emp.identification_id,' ') as NroCi,
                    COALESCE(emp.ci_ext,' ') as Ext,
                    COALESCE(emp.job_title,' ') as Cargo,
                    COALESCE(cast((TO_CHAR(con.date_start, 'DD/MM/YYYY')) as TEXT), ' ') AS Ingreso,
                    COALESCE(emp.sucursal_id,' ') as Regional,
                    pl.code, COALESCE(pl.total, 0) as total
            FROM hr_payslip_line as pl
                    left join hr_payslip as p
                    on pl.slip_id = p.id
                    left join hr_employee as emp
                    on emp.id = p.employee_id
                    left join resource_resource as r
                    on r.id = emp.resource_id
                    left join hr_contract as con on con.id = emp.contract_id

            WHERE 
        """ + where + order
        )
        # % self.start_date % self.end_date
        # -- and aml.date >= % s
        # -- and aml.date <= % s AND rpb.id = %s % bank
        self._cr.execute(sql_select)
        lines_rciva = self._cr.fetchall()
        if(len(lines_rciva) > 0):
            df = pd.DataFrame(lines_rciva, columns=[
                'Empleado', 
                'Paterno', 
                'Materno', 
                'Nombres',
                'CodAsegurado',
                'NroCi',
                'Ext',
                'Cargo',
                'Ingreso',
                'Regional', 
                'name', 
                'total'])

            df = pd.crosstab(index=[df.Empleado, 
                                    df.Paterno, 
                                    df.Materno, 
                                    df.Nombres,
                                    df.CodAsegurado,
                                    df.NroCi,
                                    df.Ext,
                                    df.Cargo,
                                    df.Ingreso,
                                    df.Regional], columns=df.name,
                             values=df.total, aggfunc='mean')

            print(lines_rciva)
            print(df.fillna(0))

            df_oficial = df.fillna(0)
            dfi = df_oficial.reset_index()

            dfcont = dfi.filter(['Empleado', 'Paterno', 'Materno', 'Nombres', 'CodAsegurado', 'NroCi',
                                'Ext', 'Cargo', 'DiasTrabajados', 'Ingreso', 'AniosTrabajados', 'AniosPorcentaje', 'BASIC', 'BonoAntiguedad',
                                'OtrosIngresos', 'NET', 'ImpuestoRetenido', 'AporteAFP',
                                'AFP_SOL_0_5', 'AFP_SOL_MAY', 'PrestamoAnticipo', 'OtrosDescAFP', 'TotalDesc',
                                'LiquidoPagable', 'AFP_4_71', 'CNS', 'Fonvis_2',
                                'Indemnizacion_8_33', 'Aguinaldo_8_33', 'Prima', 'CostoMensual', 'Regional'])
            lines_rciva_list = dfcont.values.tolist()
            print(lines_rciva_list)
        else:
            lines_rciva_list = lines_rciva
        return lines_rciva_list

    def head_BankBook(self, row, sheet):

        column = 0
        # bold = sheet.add_format({'bold': True})
        for item in self.head_bank:
            sheet.write(row, column, item)
            column += 1
        row = row + 1
        return row

    def body_bankbook(self, row, sheet, body, fechaI, fechaF, account):
        # row es la fila donde comenzar
        # body es una lista de listas, body[0] es una lista con todo los valores que tiene head

        column = 8
        sumSaldo = 0
        # fechaI = self.start_date
        # fechaF = self.end_date
        # account = self.account

        # row, sumSaldo = self.sum_previous_balance(
        #     row, sheet, body, fechaI, fechaF, account)
        for item in body:
            # if (item[1] >= (datetime.datetime.strptime('2020-01-01 20:00:00', '%Y-%m-%d %H:%M:%S').date())) and (item[1] <= (datetime.datetime.strptime('2023-01-01 20:00:00', '%Y-%m-%d %H:%M:%S').date())):
            sheet.write_row(row, 0, item)
            # formula = '=G' + str(row) + '-H' + str(row) + 'I' + str(row-1)
            # sheet.write_formula(row, column, formula)
            row += 1
        return row


# def get_xlsx_afp_report_ORIGINAL(self, data, response):
#         i = 8  # inicio de celdas a partir de la cabecera
#         j = 1  # Nro
#         output = io.BytesIO()
#         workbook = xlsxwriter.Workbook(output, {'in_memory': True})
#         sheet = workbook.add_worksheet()
#         cell_format = workbook.add_format({'font_size': '12px'})
#         # head = workbook.add_format(
#         #     {'align': 'center', 'bold': True, 'font_size': '20px'})
#         sheet.set_column('A:X', 25)
#         cell_format = workbook.add_format({'font_size': '12px'})
#         title = workbook.add_format(
#             {'align': 'left', 'bold': True, 'font_size': '16px'})
#         title.set_font_color('blue')
#         head = workbook.add_format(
#             {'align': 'center', 'bold': True, 'font_size': '12px'})
#         head.set_pattern(2)
#         head.set_bg_color('blue')
#         head.set_font_color('white')
#         txt = workbook.add_format({'font_size': '10px'})
#         sheet.merge_range('B2:I3', 'PLANILLA AFP', title)
#         # sheet.write('B6', 'From:', cell_format)
#         # sheet.merge_range('C6:D6', data['start_date'], txt)
#         # sheet.write('F6', 'To:', cell_format)
#         # sheet.merge_range('G6:H6', data['end_date'], txt)
#         sheet.write('B7', 'Nro', head)
#         sheet.write('C7', 'Apellido Paterno', head)
#         sheet.write('D7', 'Apellido Materno', head)
#         sheet.write('E7', 'Nombres', head)
#         sheet.write('F7', 'Codigo de Asegurado', head)
#         sheet.write('G7', 'Cargo', head)
#         sheet.write('H7', 'Días del mes trabajado', head)
#         sheet.write('I7', 'Fecha Ingreso', head)
#         sheet.write('J7', 'Años', head)
#         sheet.write('K7', '%', head)
#         sheet.write('L7', 'Haber Basico', head)
#         sheet.write('M7', 'Bono de antiguedad', head)
#         sheet.write('N7', 'Otros haberes', head)
#         sheet.write('O7', 'Total GAnado', head)
#         sheet.write('P7', 'RC-IVA', head)
#         sheet.write('Q7', 'Sistema Integral de Pensiones', head)
#         sheet.write('R7', 'Aporte Solidario', head)
#         sheet.write('S7', 'Aporte NAl. Solidario', head)
#         sheet.write('T7', 'Prestamos Anticipos', head)
#         sheet.write('U7', 'Otros descuentos', head)
#         sheet.write('V7', 'TOTAL DESCUENTOS', head)
#         sheet.write('W7', 'LIQUIDO PAGABLE', head)
#         sheet.write('X7', 'REGIONAL', head)
#         for index, inv in enumerate(data.items()):
#             sheet.write('B'+str(i), j, txt)
#             #sheet.write('E'+str(i), str(inv[1]['identification_id']), txt)
#             #sheet.write('E'+str(i), str(inv[1]['birthday']), txt)
#             sheet.write('C'+str(i), str(inv[1]['name']), txt)
#             sheet.write('D'+str(i), str(inv[1]['name']), txt)
#             sheet.write('E'+str(i), str(inv[1]['name']), txt)
#             #sheet.write('I'+str(i), str(inv[1]['country_of_birth']), txt)
#             sheet.write('J'+str(i), str(inv[1]['gender']), txt)

#             sheet.write('F'+str(i), '0,00', txt)
#             sheet.write('G'+str(i), '0,00', txt)
#             sheet.write('H'+str(i), '0,00', txt)
#             sheet.write('I'+str(i), '0,00', txt)
#             sheet.write('K'+str(i), '0,00', txt)
#             sheet.write('L'+str(i), '0,00', txt)
#             sheet.write('M'+str(i), '0,00', txt)
#             sheet.write('N'+str(i), '0,00', txt)
#             sheet.write('O'+str(i), '0,00', txt)
#             sheet.write('P'+str(i), '0,00', txt)
#             sheet.write('Q'+str(i), '0,00', txt)
#             sheet.write('R'+str(i), '0,00', txt)
#             sheet.write('S'+str(i), '0,00', txt)
#             sheet.write('T'+str(i), '0,00', txt)
#             sheet.write('U'+str(i), '0,00', txt)
#             sheet.write('V'+str(i), '0,00', txt)
#             sheet.write('W'+str(i), '0,00', txt)
#             sheet.write('X'+str(i), '0,00', txt)
#             i = i + 1
#             j = j + 1
#         workbook.close()
#         output.seek(0)
#         response.stream.write(output.read())
#         output.close()
