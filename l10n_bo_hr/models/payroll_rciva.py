import time
import json
import datetime
import io
import pandas as pd
import numpy as np

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


class PayrollRciva(models.TransientModel):
    # _name = "excel_rciva_payroll"
    _name = "payroll_rciva"
    _description = "Payroll RCIVA"
    start_date = fields.Date(
        # string="Start Date",  default=time.strftime('%Y-%m-01'), required=True)
        string="Start Date",  default=time.strftime('%Y-%m-%d'), required=True)

    end_date = fields.Date(
        # string="End Date",  default=datetime.datetime.now(), required=True)
        string="End Date",  default=time.strftime('%Y-%m-%d'), required=True)

    head_RCIVA = ["EMPLEADO", "AÑO", "PERIODO", "CODIGO DEPENDIENTE", "APELLIDOS Y NOMBRES", "AP. PATERNO", "AP. MATERNO", "NOMBRES",
                  "NRO CI", "TIPO DOC.", "NOVEDADES","HABER BASICO", "BONO ANTIGUEDAD", "OTROS HABERES", "TOTAL GANADO", 
                  "DESCUENTOS DE LEY", "TOTAL SUELDO", "OTROS INGRESOS", "SUELDO NETO", "2 SMIN","DIF.SUJETA A IMPUESTO", 
                  "13% IMPUESTO", "13% 2MN", "IMPPAGAR", "FORM 110 DECL.JUR", "SALDO A/F FISCO", "SALDO A/F DEPENDT.","SALDO ANTERIOR", 
                  "ACTUALIZACION", "TOTAL ACTUALIZADO", "SALDO TOTAL DEP.", "SALDO UTILIZADO", "IMPUESTO RETENIDO","SALDO SIG.MES"
                  ]

    def print_xlsx_RCIVA(self):
        # Busqueda por fechas
        invoice_ids = self.env['hr.employee'].search(
            [])
        if (len(invoice_ids) == 0):
            raise ValidationError(
                'There are no invoices in the selected range of dates')
        data = {}
        data['start_date'] = self.start_date
        data['end_date'] = self.end_date
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'payroll_rciva',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'template rciva',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_rciva_report(self, data, response):

        row = 7
        lines_rciva = []

        account = 1
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('B2:I3', 'PLANILLA RC IVA', head)
        sheet.write('B6', 'From:', cell_format)
        sheet.merge_range('C6:D6', data['start_date'], txt)
        sheet.write('F6', 'To:', cell_format)
        sheet.merge_range('G6:H6', data['end_date'], txt)

        row = self.head_payroll_rciva(row, sheet)

        lines_rciva = self.get_payroll_RCIVA(data)

        self.body_payroll_rciva(row, sheet, lines_rciva,
                                self.start_date, self.end_date, account)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_payroll_RCIVA(self, data):
        fechaI = data['start_date']
        fechaF = data['end_date']

        where = ' p.date_from >= ' + "'" + fechaI + \
            "'" + 'and p.date_to <=' + "'" + fechaF + "'"
        order = ' Order by emp.paternal_surname'
        lines_rciva = []
        sql_select = sql.SQL(
            """
        SELECT emp.id as Empleado,
		EXTRACT(YEAR FROM p.date_to) AS Anio,
		EXTRACT(MONTH FROM p.date_to) AS Mes,
		emp.cod_dependent as CodDependiente,
		COALESCE(CONCAT(emp.paternal_surname , ' ',emp.maternal_surname, ' ',emp.all_name), ' ') AS ApellidosNombres,
		COALESCE(emp.paternal_surname,' ') as Paterno,
        COALESCE(emp.maternal_surname,' ') as Materno,
		emp.all_name as Nombres,
		emp.identification_id as NroCI,
		emp.doc_type as TipoDoc,
        con.novedades as Novedades,
		0 as OtrosIngresos,
        pl.code, COALESCE(pl.total, 0)
        FROM hr_payslip_line as pl
					left join hr_payslip as p on pl.slip_id = p.id
					left join hr_employee as emp on emp.id = p.employee_id
					left join resource_resource as r on r.id = emp.resource_id
					left join hr_contract as con on con.id = emp.contract_id
        WHERE 
        """ + where + order
        )
        self._cr.execute(sql_select)
        lines_rciva = self._cr.fetchall()
        if(len(lines_rciva) > 0):
            df = pd.DataFrame(lines_rciva, columns=[
                'Empleado', 
                'Anios',
                'Mes',
                'CodDependiente',
                'ApellidosNombres',
                'Paterno',
                'Materno',
                'Nombres',
                'NroCI',
                'TipoDoc',
                'Novedades',
                'OtrosIngresos',
                'name', 
                'total'])

            df = pd.crosstab(index=[df.Empleado, 
                                    df.Anios,
                                    df.Mes,
                                    df.CodDependiente,
                                    df.ApellidosNombres,
                                    df.Paterno,
                                    df.Materno,
                                    df.Nombres,
                                    df.NroCI,
                                    df.TipoDoc,
                                    df.Novedades], 
                                    columns=df.name,
                             values=df.total, aggfunc='mean')

            df_oficial = df.fillna(0)
            dfi = df_oficial.reset_index()

            dfcont = dfi.filter(['Empleado', 'Anios', 'Mes', 'CodDependiente',
                                 'ApellidosNombres', 'Paterno', 'Materno', 'Nombres',
                                 'NroCI','TipoDoc', 'Novedades' ,'BASIC', 'BonoAntiguedad',
                                 'OtrosHaberes', 'NET', 'DescLey', 'TotalSueldo','OtrosIngresos', 'SueldoNeto', 'MinimoNoImponible_',
                                 'Diff_Sujeta_Impuesto', 'RC13_IVA',
                                 'RC13_2Min', 'ImpPagar', 'Form110', 'Saldo_AF_Fisco', 'Saldo_AF_Dependt', 'SaldoAnterior', 'Actualizacion',
                                 'SaldoTotal', 'SaldoTotalDep', 'SaldoUtilizado', 'ImpuestoRetenido', 'Saldo_Sig_Mes'])
            lines_rciva_list = dfcont.values.tolist()
        else:
            lines_rciva_list = lines_rciva
        return lines_rciva_list

    def head_payroll_rciva(self, row, sheet):

        column = 0
        # bold = sheet.add_format({'bold': True})
        for item in self.head_RCIVA:
            sheet.write(row, column, item)
            column += 1
        row = row + 1
        return row

    def body_payroll_rciva(self, row, sheet, body, fechaI, fechaF, account):
        column = 8
        bodyend = []
        for item in body:
            sheet.write_row(row, 0, item)
            # formula = '=G' + str(row) + '-H' + str(row) + 'I' + str(row-1)
            # sheet.write_formula(row, column, formula)
            row += 1
        return row


# def get_payroll_RCIVA_crosstabpostgress(self):

    #     lines_rciva = []
    #     sql_select = sql.SQL(
    #         """
    #     select *
    #         FROM crosstab( '
    #             SELECT emp.id, CONCAT(emp.paternal_surname , '' '',emp.maternal_surname, '' '',emp.all_name) AS apellidos_nombres,
    #             0 as OtrosIngresos,
    #             pl.name, pl.total
    #             FROM hr_payslip_line as pl
    #                                 left join hr_payslip as p
    #                                 on pl.slip_id = p.id
    #                                 left join hr_employee as emp
    #                                 on emp.id = p.employee_id
    #                                 left join resource_resource as r
    #                                 on r.id = emp.resource_id
    #                                 left join hr_contract as con on con.id = emp.contract_id
    #                     WHERE p.state = ''done''
    #                     ORDER BY 1,2
    #                     '
    #                     ,$$VALUES ('Basico'::text), ('BonoAntiguedad'::text), ('OtrosHaberes'::text),
    #                     ('TotalGanado'::text), ('AFP_12_21'::text), ('AFP_SOL_10_5'::text), ('AFP_JUB_2_21'::text)
    #                     , ('AFP_JUB_0_5'::text), ('AFP_SOL_0_5'::text)
    #                     , ('AFP_SOL_MAY'::text)
    #                     , ('SueldoNeto'::text), ('MinimoNoImponible'::text), ('Diff_Sujeta_Impuesto'::text)
    #                     , ('13_Iva'::text), ('Form110_Decljur'::text), ('13_2Min'::text), ('Saldo_AF_Fisco'::text)
    #                     , ('Saldo_AF_Dependt'::text), ('SaldoAnterior'::text), ('Actualizacion'::text)
    #                     , ('SaldoTotal'::text), ('SaldoTotalDep'::text), ('SaldoUtilizado'::text)
    #                     , ('ImpuestoRetenido'::text), ('SaldoSigMes'::text)$$)

    #         AS payrollAFP ("id" text,"apellidos_nombres"text,
    #         "OtrosIngresos"text,"Basico" text, "BonoAntiguedad" text,
    #         "OtrosHaberes" text, "TotalGanado" text , "AFP_12_21" text, "AFP_SOL_10_5" text, "AFP_JUB_2_21" text
    #         , "AFP_JUB_0_5" text, "AFP_SOL_0_5" text, "AFP_SOL_MAY" text
    #         , "SueldoNeto" text, "MinimoNoImponible" text, "Diff_Sujeta_Impuesto" text, "13_Iva" text
    #         , "Form110_Decljur"text,"13_2Min" text, "Saldo_AF_Fisco" text, "Saldo_AF_Dependt" text
    #         , "SaldoAnterior" text, "Actualizacion" text, "SaldoTotal" text, "SaldoTotalDep" text, "SaldoUtilizado" text
    #         , "ImpuestoRetenido" text, "Saldo_Sig_Mes" text);
    #     """)
    #     # % self.start_date % self.end_date
    #     # -- and aml.date >= % s
    #     # -- and aml.date <= % s AND rpb.id = %s % bank
    #     self._cr.execute(sql_select)
    #     lines_rciva = self._cr.fetchall()
    #     print('LIINES______________________________________________________POSTGRES')
    #     print(lines_rciva)
    #     return lines_rciva