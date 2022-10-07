import time
import json
import datetime
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import logging

_logger = logging.getLogger(__name__)


class PurchaseBookWizard(models.TransientModel):
    _name = "purchase_book_wizard"
    _description = "Purchase Book Report Fast Wizard"

    begin_date = fields.Date(
        string="Start Date",  default=time.strftime('%Y-%m-01'), required=True)
    end_date = fields.Date(
        string="End Date",  default=datetime.datetime.now(), required=True)
    # id = ''

    dui = fields.Text('DUI')
    auth_number = fields.Text('Authorization Number')
    control_code = fields.Text('Control Code')

    def _employee_get(self, name):
        record = self.env['expense_ids'].search(
            [('name', '=', name)])
        return record

    def _partner_get(self, name):
        record = self.env['res.partner'].search(
            [('name', '=', name)])
        return record

    def _partner_get_byID(self, id):
        record = self.env['res.partner'].search(
            [('id', '=', id)])
        return record

    def getDimfromline(self, tax_ids):
        resultado = False
        if (tax_ids):
            for tax in tax_ids:
                if tax.name.count('DIM') > 0 or tax.name.count('DUI') > 0:
                    resultado = True
        return resultado

    def getGrossfromline(self, tax_ids):
        resultado = False
        _logger.debug(f"entrando a getGrossfromline {tax_ids}")
        if (tax_ids):
            for tax in tax_ids:
                _logger.debug(f"es un impuesto: {tax.name}")
                if tax.name.find('Gross') >= 0:
                    _logger.debug(f"es una pinche GROSS {tax.name}")
                    resultado = True
        return resultado

    def getIvafromline(self, tax_ids):
        resultado = False
        _logger.debug(f"entrando a getIvafromline {tax_ids}")
        if (tax_ids):
            for tax in tax_ids:
                _logger.debug(f"es una pinche IVA {tax.name}")
                if tax.name.find('Iva') >= 0:
                    _logger.debug(f"es una pinche IVA {tax.name}")
                    resultado = True
        return resultado

    def itsbill(self, bill):
        resultado = False
        if not bill.with_tax:
            return False
        elif (len(str(bill.auth_number)) > 0 and len(str(bill.control_code)) > 0) or len(str(bill.dui)) > 1:
            if str(bill.l10n_bo_invoice_number) == '0' and len(str(bill.dui)) <= 1:
                resultado = False
            elif bill.control_code == '*':
                resultado = False
            elif self.getGrossfromline(bill.invoice_line_ids.tax_ids):
                resultado = False
            elif self.getIvafromline(bill.invoice_line_ids.tax_ids):
                resultado = True
            else:
                resultado = True
            # return True
        else:
            resultado = False
        return resultado

    def print_xlsx(self):
        print('ENTRA AL BOTON')
        # Busqueda por fechas
        invoice_ids = self.env['account.move'].search(
            ['&', ('invoice_date', '>=', self.begin_date),
             ('invoice_date', '<=', self.end_date),
             ('journal_id.type', '=', 'purchase'),
             ('state', '=', 'posted')
             ])
        expense_ids = self.env['hr.expense'].search(
            ['&', ('accounting_date', '>=', self.begin_date),
             ('accounting_date', '<=', self.end_date),
             ('state', 'in', ['done', 'approved'])
             ])

        # valida que la fecha inicio sea inferior a fecha fin
        if self.begin_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

        # valida que hayan dartos en la data
        if (len(invoice_ids) == 0):
            raise ValidationError(
                'There are no invoices in the selected range of dates')

        data = {}
        pos = 0
        # TODO iterar sobre cada objeto y mapear lo requerido
        for index, inv in enumerate(invoice_ids):
            porder_type = self.env['purchase.order'].search([('name', '=', inv.invoice_origin)]).requested_type_ncr or 'local'

            if ((porder_type.find('local') > -1) or (porder_type.find('interna') > -1)) and self.itsbill(inv):
                _logger.debug("********************* estas son las line")
                line_ids = inv.invoice_line_ids
                _logger.debug(line_ids)
                ice = 0
                gas = 0
                tasas = 0
                # factor = 1

                facturaDIM = False
                facturaGasto = False
                facturaTasa0 = False
                descuento = 0
                # if inv.currency_id.id == 2:
                #     factor = float('6.96')
                #     _logger.debug(f"********************* esto esta en DOLARES {factor}")
                _logger.debug("********************* entrando al for de las line")
                for line in line_ids:
                    linename = line.product_id.name
                    _logger.debug(f"es es un nombre del producto en la liena {linename}")
                    if (linename):
                        if linename.find("TASA") == 0:
                            tasas = tasas + line.price_total
                            _logger.debug(f" esta es la TASAS dentro del for {tasas}")
                        elif (linename.find("ICE") == 0):
                            ice = ice + line.price_total
                            _logger.debug(f" esta es la ICE dentro del for {ice}")
                        elif (linename.find("GASTOS BANCARIOS SIN/CF") == 0):
                            facturaGasto = True
                            _logger.debug(f" esta es la GASTOS BANCARIOS SIN/CF")
                        elif (linename.find("IMP. FLETE TERRESTE (TASA 0)") == 0):
                            facturaTasa0 = True
                            _logger.debug(f" esta es la IMP. FLETE TERRESTE (TASA 0)")
                        elif (linename.find("GASOLINA SIN CF") == 0):
                            gas = gas + line.price_total*0.30
                            _logger.debug(f" esta es la GASOLINA dentro del for {gas}")
                        elif (linename.find("IMP. DIM") == 0):
                            if self.getDimfromline(line.tax_ids):
                                facturaDIM = True
                                DIM_Credito_Fiscal = line.price_total
                                DIM_Importe_Total_Compra = line.price_total / 0.13
                                _logger.debug(f" esta es la DIM del for {DIM_Credito_Fiscal}")
                        elif linename.find("DESCUENTO") == 0:
                            descuento = round(descuento + abs(line.price_total), 2)
                        # descuento = descuento + line.price_total * (line.discount / 100)
                        _logger.debug(f" esta es la tasa dentro del for {descuento}")

                _logger.debug(f"********************* esto es la sumatoria la tasa {tasas}")
                _logger.debug(f"********************* esto es la sumatoria la descuento {descuento}")
                # search([('name', '=', line.get('Tag 1'))])
                _logger.debug(porder_type)
                _logger.debug(inv.invoice_origin)
                partnerData = self._partner_get(inv.partner_id.name)
                _logger.debug(inv.partner_id.name)
                invoice_content = {}
                if(partnerData.vat != False):
                    invoice_content['partner_id'] = partnerData.vat
                else:
                    invoice_content['partner_id'] = ' '
                invoice_content['partner'] = partnerData.name
                invoice_content['name'] = inv.ref
                invoice_content['bill_number'] = inv.l10n_bo_invoice_number or 0
                invoice_content['invoice_date'] = inv.invoice_date.strftime('%d/%m/%Y')
                if facturaDIM:
                    invoice_content['amount_total'] = DIM_Importe_Total_Compra
                else:
                    invoice_content['amount_total'] = inv.amount_total
                # Validar tasas de facturas especiales
                invoice_content['tasas'] = tasas
                invoice_content['amount_tax'] = inv.amount_tax
                invoice_content['amount_ICE'] = ice
                invoice_content['amount_IEHD'] = '0'
                invoice_content['amount_IPJ'] = '0'
                invoice_content['tax_ids'] = '0'
                if facturaGasto:
                    invoice_content['no_credit'] = inv.amount_total
                else:
                    invoice_content['no_credit'] = gas
                invoice_content['external_amounts'] = '0'
                invoice_content['excentos'] = '0'
                if facturaTasa0:
                    invoice_content['tasa_cero'] = inv.amount_total
                else:
                    invoice_content['tasa_cero'] = '0'

                invoice_content['external_purchases'] = '0'
                # =+I8 - J8 - K8 - L8 - M8 - N8 - O8 - P8
                if facturaDIM:
                    invoice_content['price_subtotal'] = DIM_Importe_Total_Compra - float(invoice_content['amount_ICE']) - float(invoice_content['amount_IEHD']) - float(invoice_content['amount_IPJ']) \
                                                        - float(invoice_content['tasas']) - float(invoice_content['no_credit']) \
                                                        - float(invoice_content['excentos']) - float(invoice_content['tasa_cero'])
                elif facturaGasto:
                    invoice_content['price_subtotal'] = 0
                else:
                    invoice_content['price_subtotal'] = invoice_content['amount_total'] - float(invoice_content['amount_ICE']) - float(invoice_content['amount_IEHD']) - float(invoice_content['amount_IPJ']) \
                                                        - float(invoice_content['tasas']) - float(invoice_content['no_credit']) \
                                                        - float(invoice_content['excentos']) - float(invoice_content['tasa_cero'])
                invoice_content['iva'] = '0,00'
                invoice_content['bon_al_iva'] = descuento
                invoice_content['gift_cart'] = '0'
                if facturaDIM:
                    _logger.debug(f"********************* Factura dim positivo")
                    invoice_content['base_cf'] = DIM_Importe_Total_Compra - float(invoice_content['bon_al_iva']) - float(invoice_content['gift_cart'])
                elif facturaGasto:
                    invoice_content['base_cf'] = 0
                else:
                    _logger.debug(f"********************* Factura dim negativo")
                    invoice_content['base_cf'] = invoice_content['price_subtotal'] + descuento - float(invoice_content['bon_al_iva']) - float(invoice_content['gift_cart'])
                    # invoice_content['base_cf'] = inv.amount_total + descuento - float(invoice_content['bon_al_iva']) - float(invoice_content['gift_cart'])
                invoice_content['credit'] = inv.amount_tax
                if facturaDIM:
                    invoice_content['puchase_type'] = '1'
                else:
                    invoice_content['puchase_type'] = '0,00'

                if(inv.auth_number != False):
                    invoice_content['auth_number'] = inv.auth_number
                else:
                    invoice_content['auth_number'] = 1
                if(inv.control_code != False):
                    invoice_content['control_code'] = inv.control_code
                else:
                    invoice_content['control_code'] = 0
                if(inv.dui != False):
                    invoice_content['dui'] = inv.dui
                else:
                    invoice_content['dui'] = 0
                # El descuento tiene que sumarse al total para mostrar
                invoice_content['amount_total'] = invoice_content['amount_total'] + descuento

                ## get currency:
                invoice_content['currency'] = inv.currency_id.id

                data[index] = invoice_content
                pos = index + 1
                _logger.debug(f' este es el pos {pos}')
            else:
                _logger.debug("********************este no era local o interna")
                _logger.debug(porder_type)

        _logger.debug("*********************  aca comienza gastos **************")
        for index, inv in enumerate(expense_ids):
            print(inv.invoice_number)
            print(inv.state)
            if (inv.control_code) or (inv.authorization_code):
                # factor = 1
                # if inv.currency_id.id == 2:
                #     factor = float('6.96')
                tax_ids = inv.tax_ids
                control_tasa = False
                control_gasolina = False
                total_amount = round(inv.unit_amount * inv.quantity, 2)
                for tax in tax_ids:
                    if tax:
                        if tax.name.find('Tasas') > -1:
                            control_tasa = True
                            _logger.debug('Es un TASAS gasto')

                if inv.product_id.name.find('COMBUSTIBLES') > -1:
                    control_gasolina = True
                    _logger.debug('Es un combustible gastop')

                _logger.debug(inv.control_code)
                _logger.debug(inv.authorization_code)
                _logger.debug(inv.name)
                # _logger.debug(inv.invoice_origin)
                partnerData = self._partner_get(inv.partner_id.name)
                _logger.debug(partnerData)
                _logger.debug(inv.partner_id.name)
                invoice_content = {}
                if(partnerData.vat):
                    invoice_content['partner_id'] = partnerData.vat or ' '
                else:
                    invoice_content['partner_id'] = ' '
                invoice_content['partner'] = partnerData.name or 'NONE'
                invoice_content['name'] = inv.reference
                invoice_content['bill_number'] = inv.invoice_number or 0
                invoice_content['invoice_date'] = inv.accounting_date.strftime('%d/%m/%Y')
                if control_tasa:
                    invoice_content['amount_total'] = 0
                else:
                    invoice_content['amount_total'] = total_amount
                # Validar tasas de facturas especiales
                if control_tasa:
                    invoice_content['tasas'] = total_amount
                    invoice_content['amount_tax'] = '0'
                else:
                    invoice_content['tasas'] = '0'
                    invoice_content['amount_tax'] = total_amount * 0.13
                # 2908 nuevo campo rate
                invoice_content['tasas'] = abs(inv.rate)
                invoice_content['amount_ICE'] = '0'
                invoice_content['amount_IEHD'] = '0'
                invoice_content['amount_IPJ'] = '0'
                invoice_content['tax_ids'] = '0'
                if inv.product_id.name.find('COMBUSTIBLES Y LUBRICANTES') > -1:
                    invoice_content['no_credit'] = total_amount * 0.3
                else:
                    invoice_content['no_credit'] = '0'
                    
                invoice_content['external_amounts'] = '0'
                invoice_content['excentos'] = '0'
                if inv.product_id.name.find('IMP. FLETE TERRESTE (TASA 0)') > -1:
                    invoice_content['tasa_cero'] = total_amount
                else:
                    invoice_content['tasa_cero'] = '0'

                invoice_content['external_purchases'] = '0'
                # =+I8 - J8 - K8 - L8 - M8 - N8 - O8 - P8
                if control_tasa:
                    invoice_content['price_subtotal'] = 0
                else:
                    invoice_content['price_subtotal'] = total_amount - float(invoice_content['amount_ICE']) - float(invoice_content['amount_IEHD']) - float(invoice_content['amount_IPJ']) \
                                                    - float(invoice_content['tasas']) - float(invoice_content['no_credit']) \
                                                    - float(invoice_content['excentos']) - float(invoice_content['tasa_cero'])
                invoice_content['iva'] = '0,00'
                invoice_content['bon_al_iva'] = '0'
                ## 2908 nuevo campo discount
                invoice_content['bon_al_iva'] = inv.discount
                invoice_content['gift_cart'] = '0'
                if control_tasa:
                    invoice_content['base_cf'] = 0
                    invoice_content['credit'] = 0
                else:
                    invoice_content['base_cf'] = invoice_content['price_subtotal'] - float(invoice_content['bon_al_iva']) - float(invoice_content['gift_cart'])
                    invoice_content['credit'] = invoice_content['base_cf'] * 0.13
                invoice_content['puchase_type'] = '0,00'

                if(inv.authorization_code != False):
                    invoice_content['auth_number'] = inv.authorization_code
                else:
                    invoice_content['auth_number'] = 1
                if(inv.control_code != False):
                    invoice_content['control_code'] = inv.control_code
                else:
                    invoice_content['control_code'] = 0

                invoice_content['dui'] = 0

                invoice_content['amount_total'] = float(total_amount) + float(invoice_content['tasas'])
                
                ## get currency:
                invoice_content['currency'] = inv.currency_id.id

                data[index+pos] = invoice_content
                _logger.debug(pos)
                _logger.debug(index)
                _logger.debug(index+pos)
            else:
                _logger.debug("********************este gasto no es factura")
                _logger.debug(inv.name)

        return {
            'type': 'ir.actions.report',
            'data': {'model': 'purchase_book_wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'template purchase',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        i = 8  # inicio de celdas a partir de la cabecera
        j = 1  # Nro
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
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
        sheet.merge_range('B2:I3', 'LIBRO DE COMPRAS', title)
        sheet.merge_range('B3:C3', '(Expresado en Bolivianos)', txt)
        sheet.write('A7', 'N°', head)
        sheet.write('B7', 'Especificación', head)
        sheet.write('C7', 'NIT Proveedor', head)
        sheet.write('D7', 'Razon Social Proveedor', head)
        sheet.write('E7', 'Código de Autorización', head)
        sheet.write('F7', 'Número de Factura', head)
        sheet.write('G7', 'Numero DUI/DIM', head)
        sheet.write('H7', 'Fecha de Factura', head)
        sheet.write('I7', 'Importe Total Compra', head)
        sheet.write('J7', 'Importe ICE', head)
        sheet.write('K7', 'Importe IEHD', head)
        sheet.write('L7', 'Importe IPJ', head)
        sheet.write('M7', 'Tasas', head)
        sheet.write('N7', 'Otro NO Sujeto a credito Fiscal', head)
        sheet.write('O7', 'Importes Excentos', head)
        sheet.write('P7', 'Importe Compras Grabadas a Tasa Cero', head)
        sheet.write('Q7', 'Subtotal', head)
        sheet.write(
            'R7', 'Descuentos Bonificaciones Rebajas Sujetas al IVA', head)
        sheet.write('S7', 'Importe GIFT CARD', head)
        sheet.write('T7', 'Importe Base CF', head)
        sheet.write('U7', 'Credito Fiscal', head)
        sheet.write('V7', 'Tipo Compra', head)
        sheet.write('W7', 'Código de Control', head)

        for index, inv in enumerate(data.items()):
            if inv[1]['currency'] == 2:
                factor = 6.96
            else:
                factor = 1
            sheet.write('A'+str(i), j, cell_format)
            sheet.write('B'+str(i), 1, txt)
            sheet.write('C'+str(i), inv[1]['partner_id'], txt)
            sheet.write('D'+str(i), inv[1]['partner'], txt)
            sheet.write('E'+str(i), inv[1]['auth_number'], txt)
            sheet.write('F'+str(i), inv[1]['bill_number'], txt)
            sheet.write('G'+str(i), inv[1]['dui'], txt)
            sheet.write('H'+str(i), inv[1]['invoice_date'], txt)
            sheet.write('I'+str(i), round(float(inv[1]['amount_total']) * factor, 2), txt)
            sheet.write('J'+str(i), round(float(inv[1]['amount_ICE']) * factor, 2), txt)
            sheet.write('K'+str(i), '0,00', txt)
            sheet.write('L'+str(i), '0,00', txt)
            # Validar tasas de facturas especiales
            sheet.write('M'+str(i), round(float(inv[1]['tasas']) * factor, 2), cell_format)
            sheet.write('N'+str(i), round(float(inv[1]['no_credit']) * factor, 2), txt)
            sheet.write('O'+str(i), '0,00', txt)
            sheet.write('P'+str(i), round(float(inv[1]['tasa_cero']) * factor, 2), txt)
            # if inv[1]['currency'] == 2:
            #     sheet.write('Q'+str(i), round(float(inv[1]['price_subtotal']) * 6.96, 2), cell_format)
            # else:
            sheet.write('Q'+str(i), round(float(inv[1]['price_subtotal']) * factor, 2), cell_format)
            sheet.write('R'+str(i), round(float(inv[1]['bon_al_iva']), 2) * factor, cell_format)
            sheet.write('S'+str(i), '0,00', txt)
            # if inv[1]['currency'] == 2:
            #     sheet.write('T'+str(i), round(float(inv[1]['base_cf']) * 6.96, 2), txt)
            # else:
            sheet.write('T'+str(i), round(float(inv[1]['base_cf']) * factor, 2), txt)
            sheet.write('U'+str(i), round(float(inv[1]['credit']) * factor, 2), cell_format)
            sheet.write('V'+str(i), '1,00', txt)
            sheet.write('W'+str(i), str(inv[1]['control_code']), txt)
            i = i + 1
            j = j + 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
