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


class PayrollMinistry(models.TransientModel):
    _name = "payroll_ministry"
    _description = "Payroll to Ministery"
    start_date = fields.Date(
        # string="Start Date",  default=time.strftime('%Y-%m-01'), required=True)
        string="Start Date",  default=time.strftime('%Y-%m-%d'), required=True)

    end_date = fields.Date(
        # string="End Date",  default=datetime.datetime.now(), required=True)
        string="End Date",  default=time.strftime('%Y-%m-%d'), required=True)
    head_bank = ["NRO", "TIPO DE DOCUMENTO DE IDENTIDAD", "NRO DE DOCUMENTO DE IDENTIDAD",
                 "LUGAR DE EXPEDICION", "FECHA DE NACIMIENTO",
                 "APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRES",
                 "PAIS DE NACIONALIDAD", "SEXO", "JUBILADO", "APORTE AFP?",
                 "PERSONA CON DISCAPACIDAD?", "TUTOR DE PERSONA CON DISCAPACIDAD",
                 "FECHA INGRESO", "FECHA DE RETIRO", "MOTIVO RETIRO",
                 "CAJA DE SALUD", "AFP A LA QUE APORTA", "NUA/CUA", "SUCURSAL O UBICACION ADICIONAL",
                 "CLASIFICACION LABORAL", "CARGO", "MODALIDAD DE CONTRATO", "TIPOS CONTRATO", 
                 "DIAS PAGADOS", "HORAS PAGADAS", "HABER BASICO", "BONO ANTIGUEDAD", "HORAS EXTRA", 
                 "MONTO HORAS EXTRA", "HORAS RECARGO NOCTURNO", "MONTO HORAS EXTRA NOCTURNAS", 
                 "HORAS EXTRA DOMINICALES", "MONTO HORAS EXTRA DOMINICALES", "DOMINGOS TRABAJADOS",
                 "MONTO DOMINGOS TRABAJADOS", "NRO DOMINICALES", "SALARIO DOMINICAL", "BONO PRODUCCION",
                 "SUBSIDIO FRONTERA", "OTROS BONOS Y PAGOS", "RC-IVA", "APORTE CAJA DE SALUD",
                 "APORTE AFP", "OTROS DESCUENTOS"
                ]

    def _rule_get(self):
        record = self.env['hr.salary.rule'].search(
            [('code', '=', 'pay_ministery_001')])
        return record

    def print_xlsx(self):
        invoice_ids = self.env['hr.employee'].search(
            [])

        # valida que la fecha inicio sea inferior a fecha fin
        if self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

        # valida que hayan dartos en la data
        if (len(invoice_ids) == 0):
            raise ValidationError(
                'There are no invoices in the selected range of dates')

        data = {}
        data['start_date'] = self.start_date
        data['end_date'] = self.end_date
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'payroll_ministry',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'template ministry',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_ministry_report(self, data, response):

        row = 7
        lines = []
        account = 1
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('B2:I3', 'PLANILLA MINISTERIO', head)
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

    def get_payroll(self, data):
        fechaI = data['start_date']
        fechaF = data['end_date']
        where = ' p.date_from >= ' + "'" + fechaI + \
            "'" + 'and p.date_to <=' + "'" + fechaF + "'"
        # order = ' Order by emp.paternal_surname'
        lines = []
        sql_select = sql.SQL(
            """
        SELECT distinct emp.id as Empleado, 
            COALESCE(emp.doc_type,' ') as TipoDocIdentidad,
            COALESCE(emp.identification_id,' ') as NroDoc, 
            COALESCE(emp.ci_ext,' ') as LugarExpedicion,
			COALESCE(cast((TO_CHAR(emp.birthday, 'DD/MM/YYYY')) as TEXT), ' ') AS FechaNac,
            COALESCE(emp.paternal_surname,' ') as Paterno,
            COALESCE(emp.maternal_surname,' ') as Materno, 
            COALESCE(emp.all_name,' ') AS Nombres,
            COALESCE(cont.name,' ') as NombreCiudad, 
	    CASE 
	    WHEN emp.gender = 'female'
		THEN 'F'
	    WHEN emp.gender = 'male'
		THEN 'M'
	    WHEN emp.gender = 'other'
		THEN 'O'
	    ELSE
		' '
	    END AS gender,
        CASE
            WHEN
            con.retiree = 't'
		THEN 1
	    ELSE 
		0
	    END as retiree,
	    CASE
            WHEN
            con.contributes_afp = 't'
		THEN 1
	    ELSE 
		0
	    END as contributes_afp,
	    CASE
            WHEN
            con.disabled_person = 't'
		THEN 1
	    ELSE 
		0
	    END as disabled_person,
	    CASE
            WHEN
            con.disabled_person_tutor = 't'
		THEN 1
	    ELSE 
		0
	    END as disabled_person_tutor,
		COALESCE(cast((TO_CHAR(con.date_start, 'DD/MM/YYYY')) as TEXT), ' ') AS date_start,
		COALESCE(cast((TO_CHAR(con.date_end, 'DD/MM/YYYY')) as TEXT), ' ') AS date_end,
		COALESCE(con.retiree_reason, ' ') as Motivo,
		COALESCE(con.health_manager, ' ') as health_manager_id,
		COALESCE(con.afp_manager, ' ') as afp_manager_id,
		COALESCE(con.nua_cua, 0) as nua_cua,
		1 as address_home_id,
		COALESCE(con.job_classification, ' ') as ClasificacionLaboral,
		COALESCE(job.name, ' ') as Cargo,
		COALESCE(con.contract_modality, ' ') as contract_modality,
		COALESCE(con.contract_type_c, ' ') as contract_type,
		8 as HorasPagadas,
		pl.code as NombreRegla, 
		pl.total,
		0 as HorasExtra, 
		0 as MontoHorasExtra,
		0 as HorasRecargo,
		0 as MontoHorasExtraNocturnas,
		0 as HorasExtraDominicales, 
		0 as MontoHorasExtraDominicales,
		0 as DomingosTrabajados, 
		0 as MontoDomingosTrabajados, 
		0 as NroDominicales, 
		0 as SalarioDominical, 
		0 as BonoProduccion, 
		0 as SubsidioFrontera,
		0 as OtrosBonosPagos,
		0 as RC_IVA, 
		0 as AporteCajaSalud, 
		0 as AporteAFP1, 
		0 as OtrosDescuentos,
		0 as und1,
		0 as und2
        FROM hr_payslip_line as pl
                    left join hr_payslip as p
                    on pl.slip_id = p.id
                    left join hr_employee as emp
                    on emp.id = p.employee_id
                    left join resource_resource as r
                    on r.id = emp.resource_id
                    left join hr_contract as con on con.id = emp.contract_id
                    left join res_country as cont on cont.id = emp.country_id
                    left join hr_job as job on job.id = con.job_id
        WHERE 
    
        """
            + where
            # + order
        )

        self._cr.execute(sql_select)
        lines = self._cr.fetchall()

        if(len(lines) > 0):
            df = pd.DataFrame(lines, columns=[
                'Empleado',
                'TipoDocIdentidad',
                'NroDoc',
                'LugarExpedicion',
                'FechaNac',
                'Paterno',
                'Materno',
                'Nombres',
                'NombreCiudad',
                'gender',
                'retiree',
                'contributes_afp',
                'disabled_person',
                'disabled_person_tutor',
                'date_start',
                'date_end',
                'Motivo',
                'health_manager_id',
                'afp_manager_id',
                'nua_cua',
                'address_home_id',
                'ClasificacionLaboral',
                'Cargo',
                'contract_modality',
                'contract_type',
                'HorasPagadas',
                'NombreRegla',
                'total',
                'HorasExtra',
                'MontoHorasExtra',
                'HorasRecargo',
                'MontoHorasExtraNocturnas',
                'HorasExtraDominicales',
                'MontoHorasExtraDominicales',
                'DomingosTrabajados',
                'MontoDomingosTrabajados',
                'NroDominicales',
                'SalarioDominical',
                'BonoProduccion',
                'SubsidioFrontera',
                'OtrosBonosPagos',
                'RC_IVA',
                'AporteCajaSalud',
                'AporteAFP1',
                'OtrosDescuentos',
                'und1',
                'und2'])
            df = pd.crosstab(index=[df.Empleado,
                                    df.TipoDocIdentidad,
                                    df.NroDoc,
                                    df.LugarExpedicion,
                                    df.FechaNac,
                                    df.Paterno,
                                    df.Materno,
                                    df.Nombres,
                                    df.NombreCiudad,
                                    df.gender,
                                    df.retiree,
                                    df.contributes_afp,
                                    df.disabled_person,
                                    df.disabled_person_tutor,
                                    df.date_start,
                                    df.date_end,
                                    df.Motivo,
                                    df.health_manager_id,
                                    df.afp_manager_id,
                                    df.nua_cua,
                                    df.address_home_id,
                                    df.ClasificacionLaboral,
                                    df.Cargo,
                                    df.contract_modality,
                                    df.contract_type,
                                    df.HorasPagadas,
                                    df.HorasExtra,
                                    df.MontoHorasExtra,
                                    df.HorasRecargo,
                                    df.MontoHorasExtraNocturnas,
                                    df.HorasExtraDominicales,
                                    df.MontoHorasExtraDominicales,
                                    df.DomingosTrabajados,
                                    df.MontoDomingosTrabajados,
                                    df.NroDominicales,
                                    df.SalarioDominical,
                                    df.BonoProduccion,
                                    df.SubsidioFrontera,
                                    df.OtrosBonosPagos,
                                    df.RC_IVA,
                                    df.AporteCajaSalud,
                                    df.AporteAFP1,
                                    df.OtrosDescuentos,
                                    df.und1,
                                    df.und2
                                    ],
                             columns=df.NombreRegla,
                             values=df.total, aggfunc='mean')

            df_oficial = df.fillna(0)
            dfi = df_oficial.reset_index()

            dfcont = dfi.filter(['Empleado', 'TipoDocIdentidad', 'NroDoc', 'LugarExpedicion', 'FechaNac',
                                'Paterno', 'Materno', 'Nombres', 'NombreCiudad', 'gender',
                                 'retiree', 'contributes_afp', 'disabled_person', 'disabled_person_tutor',
                                 'date_start',
                                 'date_end', 'Motivo', 'health_manager_id', 'afp_manager_id', 'nua_cua',
                                 'address_home_id', 'ClasificacionLaboral', 'Cargo', 'contract_modality',
                                 'contract_type',
                                 'DiasTrabajados', 'HorasPagadas', 'BASIC', 'BonoAntiguedad', 'HorasExtra',
                                 'MontoHorasExtra', 'HorasRecargo', 'MontoHorasExtraNocturnas', 'HorasExtraDominicales', 'MontoHorasExtraDominicales',
                                 'DomingosTrabajados',
                                 'MontoDomingosTrabajados',
                                 'NroDominicales', 'SalarioDominical', 'BonoProduccion', 'SubsidioFrontera',
                                 'OtrosBonosPagos','ImpuestoRetenido', 'CNS', 'DescLey', 'OtrosDesc'])

            lines_rciva_list = dfcont.values.tolist()
        else:
            lines_rciva_list = lines
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
        column = 8
        bodyend = []
        for item in body:
            sheet.write_row(row, 0, item)
            row += 1
        return row


# def get_xlsx_ministry_report_ORIGINAL(self, data, response):
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
#         sheet.merge_range(
#             'B2:I3', 'PLANILLA PARA MINISTERIO DE TRABAJO', title)
#         # sheet.write('B6', 'From:', cell_format)
#         # sheet.merge_range('C6:D6', data['start_date'], txt)
#         # sheet.write('F6', 'To:', cell_format)
#         # sheet.merge_range('G6:H6', data['end_date'], txt)
#         sheet.write('B7', 'Nro', head)
#         sheet.write('C7', 'Tipo de Documento de Identidad', head)
#         sheet.write('D7', 'Numero de Documento de Identidad', head)
#         sheet.write('E7', 'Fecha de Nacimiento', head)
#         sheet.write('F7', 'Apellido Paterno', head)
#         sheet.write('G7', 'Apellido Materno', head)
#         sheet.write('H7', 'Nombre', head)
#         sheet.write('I7', 'Pais', head)
#         sheet.write('J7', 'Sexo', head)
#         sheet.write('K7', 'Jubilado', head)
#         sheet.write('L7', 'Aporta a la AFP?', head)
#         sheet.write('M7', 'Persona con Discapacidad?', head)
#         sheet.write('N7', 'Tutor de persona con discapacidad', head)
#         sheet.write('O7', 'Fecha Ingreso', head)
#         sheet.write('P7', 'Fecha Retiro', head)
#         sheet.write('Q7', 'Motivo Retiro', head)
#         sheet.write('R7', 'Caja de Salud', head)
#         sheet.write('S7', 'AFP a la que aporta', head)
#         sheet.write('T7', 'NUA/CUA', head)
#         sheet.write('U7', 'Sucursal o ubicacion adicional', head)
#         sheet.write('V7', 'Clasificacion laboral', head)
#         sheet.write('W7', 'Cargo', head)
#         sheet.write('X7', 'Modalidad de contrato', head)
#         sheet.write('Y7', 'Tipo Contrato', head)
#         sheet.write('Z7', 'Días pagados', head)
#         sheet.write('AA7', 'Horas Pagadas', head)
#         sheet.write('AB7', 'Haber BAsico', head)
#         sheet.write('AC7', 'Bono de antiguedad', head)
#         sheet.write('AD7', 'Horas extra', head)
#         sheet.write('AE7', 'Monto Horas extra', head)
#         sheet.write('AF7', 'Horas recargo nocturno', head)
#         sheet.write('AG7', 'Monto horas extra nocturnas', head)
#         sheet.write('AH7', 'Horas extra dominicales', head)
#         sheet.write('AI7', 'Monto Horas extra dominicales', head)
#         sheet.write('AJ7', 'Domingos Trabajados', head)
#         sheet.write('AK7', 'Monto Domingo Trabajado', head)
#         sheet.write('AL7', 'Nro. Dominicales', head)
#         sheet.write('AM7', 'SAlario Dominical', head)
#         sheet.write('AN7', 'Bono produccion', head)
#         sheet.write('AO7', 'Subsidio Frontera', head)
#         sheet.write('AP7', 'Otros bonos y pagos', head)
#         sheet.write('AQ7', 'RC-IVA', head)
#         sheet.write('AR7', 'aporte a caja de salud', head)
#         sheet.write('AS7', 'otros descuentos', head)
#         for index, inv in enumerate(data.items()):
#             sheet.write('B'+str(i), j, cell_format)
#             sheet.write('E'+str(i), str(inv[1]['identification_id']), txt)
#             sheet.write('E'+str(i), str(inv[1]['birthday']), txt)
#             sheet.write('F'+str(i), str(inv[1]['name']), txt)
#             sheet.write('G'+str(i), str(inv[1]['name']), txt)
#             sheet.write('H'+str(i), str(inv[1]['name']), txt)
#             sheet.write('I'+str(i), str(inv[1]['country_of_birth']), txt)
#             sheet.write('J'+str(i), str(inv[1]['gender']), txt)

#             sheet.write('C'+str(i), '0,00', txt)
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
#             sheet.write('Y'+str(i), '0,00', txt)
#             sheet.write('Z'+str(i), '0,00', txt)
#             sheet.write('AA'+str(i), '0,00', txt)
#             sheet.write('AB'+str(i), '0,00', txt)
#             sheet.write('AC'+str(i), '0,00', txt)
#             sheet.write('AD'+str(i), '0,00', txt)
#             sheet.write('AE'+str(i), '0,00', txt)
#             sheet.write('AF'+str(i), '0,00', txt)
#             sheet.write('AG'+str(i), '0,00', txt)
#             sheet.write('AH'+str(i), '0,00', txt)
#             sheet.write('AI'+str(i), '0,00', txt)
#             sheet.write('AJ'+str(i), '0,00', txt)
#             sheet.write('AK'+str(i), '0,00', txt)
#             sheet.write('AL'+str(i), '0,00', txt)
#             sheet.write('AM'+str(i), '0,00', txt)
#             sheet.write('AN'+str(i), '0,00', txt)
#             sheet.write('AO'+str(i), '0,00', txt)
#             sheet.write('AP'+str(i), '0,00', txt)
#             sheet.write('AQ'+str(i), '0,00', txt)
#             sheet.write('AR'+str(i), '0,00', txt)
#             sheet.write('AS'+str(i), '0,00', txt)

#             i = i + 1
#             j = j + 1

#         workbook.close()
#         output.seek(0)
#         response.stream.write(output.read())
#         output.close()
