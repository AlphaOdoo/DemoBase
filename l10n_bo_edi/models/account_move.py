from ast import If
import base64
import code
from email.mime import base
from email.policy import default
from io import BytesIO
import logging
import itertools
import base64
import os
import random
import re
import readline
import shutil
from statistics import mode
import sys
import tarfile
from time import time
# from zipfile import ZipFile
# from click import echo
import pytz
import qrcode
import math

from datetime import datetime, timedelta
from odoo import fields, models, api
from pytz import timezone
import zeep
from zeep import client
from hashlib import sha256
from odoo.exceptions import UserError, Warning, ValidationError

# Digital Signature
# from html import unescape
# import xml.etree.ElementTree as ET
# import lxml.etree as etree
# import xml.dom.minidom
# import os

import gzip
import hashlib
# import asyncio
import time
import asyncio


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account move inherit'

    l10n_bo_cuf = fields.Text(
        string='CUF Code', help='(Código Unico de Facturación) Code referred to Point of Attention', readonly=True)

    l10n_bo_cufd = fields.Text(
        string='CUFD Code', help='(Código Unico de Facturación Diaria) Code provided by SIN, generated daily, identifies the invoice along with a number', readonly=True)

    efact_control_code = fields.Text(
        string='CUFD Control Code', help='Control Code, given along CUFD', readonly=True)

    l10n_bo_invoice_number = fields.Text(
        string='Invoice Number', help='Along with CUFD Code, helps in identifying the invoice', readonly=True)

    l10n_bo_selling_point = fields.Many2one(
        'selling_point', string='Selling Point', readonly=True)

    l10n_bo_branch_office = fields.Many2one(
        'branch_office', string='Branch Office', readonly=True)

    l10n_bo_emission_type = fields.Many2one(
        'emission_types', string='Emission Type Selection')

    qr_code = fields.Binary("QR Code", attachment=True, store=True)

    # def _default_state(self):
    #     return self.env['document_status']
    l10n_bo_document_status = fields.Many2one(
        'document_status', string='Document Status')

    # l10n_bo_cancellation_reason = fields.Many2one(
    #     'cancellation_reasons', string='Cancellation Reason')

    # Campos Provisionales Certificacion
    cafc = fields.Text(string='cafc', default='123')
    montoGiftCard = fields.Text(string='montoGiftCard', default='')
    ###

    # @api.depends('res.config.settings.l10n_bo_invoicing_type')
    def get_e_invoice_type(self):
        self.e_billing = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.l10n_bo_invoicing_type')
    e_billing = fields.Boolean(  # Electronic Invoicing Flag
        compute='get_e_invoice_type', default = False)  # default=_getInvoiceType # default=True

    representation_format = fields.Boolean('rep_format', default = False) # Graphic Representation Format flag
    representation_size = fields.Boolean('rep_size') # Graphic Representation Size flag

    is_drafted = fields.Boolean('is_drafted', default = False) # True if invoice has been drafted after confirmation
    is_cancelled = fields.Boolean('is_cancelled', default = False) # True if invoice has been cancelled
    is_confirmed = fields.Boolean(string='is_confirmed', default = False)

    def get_journal_type(self):
        self.journal_type = self.journal_id.type
    journal_type = fields.Char(compute='get_journal_type')


    # def get_invoice_type(self):
    #     if ("INV" not in self.name):
    #         self.inv_type = True
    #     else:
    #         self.inv_type = False
    def get_invoice_type(self):
        if (self.journal_id.type == 'sale'):
            self.inv_type = True
        else:
            self.inv_type = False
    inv_type = fields.Boolean(compute='get_invoice_type')  # Invoice/Bill Flag


    def get_total_converted(self):
        currency_name = self.invoice_line_ids.mapped('sale_line_ids').order_id.pricelist_id.currency_id.name
        # if type(currency_name) == str:
        #     if "USD" in currency_name:
        #         self.total_conv = self.amount_total * 6.96
        #     self.total_conv = 1.1
        # else:
        #     self.total_conv = 0.0
        if "USD" in str(currency_name):
            self.total_conv = round((self.amount_total * self.get_change_currency()), 2 )
        else:
            self.total_conv = 0.0
    total_conv = fields.Float(default= 0.0)

    # subtotal_conv = fields.Float(default= 0.0)

    def get_literal_number(self):
        print(self.total_conv)
        if self.total_conv == 0.0:
            self.total_lit = self.numero_to_letras(self.amount_total)
        else:
            self.total_lit = self.numero_to_letras(self.total_conv)
    total_lit = fields.Char(compute='get_literal_number')

    ##?? WORKAROUND DE DESCUENTO GLOBAL POR NUEVO CAMPO 
    # total_discount = fields.Float(string='Total discount', default=0.0)

    # @api.onchange('total_discount')
    # def _total_change(self):
    #     if self.total_discount and self.amount_total:
    #         if self.amount_total > self.total_discount: 
    #             self.amount_total = self.amount_total - self.total_discount
    #         else:
    #             raise Warning("Discount amount can't be higher than total amount")
                
    # @api.model
    # def create(self, values):
    #     if self.total_discount and self.amount_total:
    #         if self.amount_total > self.total_discount: 
    #             self.amount_total = self.amount_total - self.total_discount
    #         else:
    #             raise Warning("Discount amount can't be higher than total amount")
    #     res_id = super(AccountMove,self).create(values)
    #     #your code
    #     return res_id

    # @api.multi
    # def write(self, values):
    #     # if self.total_discount and self.amount_total:
    #     #     if self.amount_total > self.total_discount: 
    #     #         self.amount_total = self.amount_total - self.total_discount
    #     #     else:
    #     #         raise Warning("Discount amount can't be higher than total amount")
    #     if self.amount_total > self.total_discount:
    #         # self.amount_total = self.amount_total - self.total_discount
    #         self.write({'amount_total': self.amount_total - self.total_discount})
    #     return super(AccountMove,self).write(values)
    ##????????????????

    ##??  Variable para verificacion nit
    def get_nit_validation(self):
        self.valid_nit = self.check_nit()
        print(self.valid_nit)
    valid_nit = fields.Boolean(compute="get_nit_validation", default=1)

    def view_init(self, fields_list):  # Init method of lifecycle #
        self.valid_nit = self.check_nit()
        return super().view_init(fields_list)
    
    invoice_event_id = fields.Many2one(comodel_name='invoice_event', string='Invoice Event')
    event_begin_date = fields.Datetime(string='Event Begin date')
    event_end_date = fields.Datetime(string='Event End date')
    manual_invoice_date = fields.Datetime(string='Invoice Date & Time')
    is_manual = fields.Boolean('Manual Invoice', default = 0)

    invalid_nit = fields.Boolean('Invalid NIT', default=0)    

    total_discount = fields.Float(default=0.0)

    invoice_caption = fields.Char(string='Invoice Caption')
    
    is_offline = fields.Boolean('Is Offline', default=0)    

    # def get_discount_amount(self):
    #     self.disc_amount = self.amount_total * self.discount / 100
    # disc_amount = fields.Boolean(string='discount amount')

    ### Standard Billing Vars ###
    dui = fields.Text('DUI')
    auth_number = fields.Text('Authorization Number')
    control_code = fields.Text('Control Code')

    # @api.onchange('dosage_id')
    # def onchange_dosage_id(self):
        # if self.dosage_id:
        #     self.reversed_inv_id = self.env['cancelled_invoices'].search([('invoice_dosage_id', '=', self.dosage_id.id)])

    # @api.depends('dosage_id')
    # def _filter_cancelled(self):
    #     if self.dosage_id:
    #         self.reversed_inv_id = self.env['cancelled_invoices'].search([('invoice_dosage_id', '=', self.dosage_id.id)])
    #     else:
    #         self.reversed_inv_id = []
    dosage_id = fields.Many2one('invoice_dosage', string='Selected Dosage')
    reversed_inv_id = fields.Many2one('cancelled_invoices', string='Reversed Invoice:', help='Select only if you want to get the cancelled invoice number (reverse cancellation)')
    with_tax = fields.Boolean(string='With Tax', default=True)
    page_break = fields.Boolean(string='Page Break', default=0)

    # @api.onchange('manual_usd_edit')
    # def _manual_usd_message(self):
    #     if self.manual_usd_edit:
    #         raise Warning("La edición manual de montos está habilitada, verifique montos unitarios/cantidad/subtotal y total antes de emitir la factura")
    manual_usd_edit = fields.Boolean(string='Edición Manual USD', default=False)
    
    # def view_init(self, fields_list):  # Init method of lifecycle #
    #     print(self.getInvoiceType()["modality"])
    #     if self.getInvoiceType()["modality"] == 1:
    #         self.e_billing = True
    #     else:
    #         self.e_billing = False
    #     return super().view_init(fields_list)

    def get_dosage_config(self):
        self.dosage_data_edit = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.prov_dosage_edit')
    dosage_data_edit = fields.Boolean(compute='get_dosage_config')

    # @api.depends('partner_id.email')
    # def compute_partner_mail(self):
    #     self.invoice_mails = self.partner_id.email
    # def _inverse_partner_mail(self):
    #     self.invoice_mails = self.invoice_mails
    @api.onchange('partner_id')
    def _get_partner_mail(self):
        self.invoice_mails = self.partner_id.email
    invoice_mails = fields.Text(string='Correos a Enviar', readonly=False)

    # @api.model
    # def write(self, vals):
    #     self.invoice_mails = self.partner_id.email
    #     return super().create(vals)

    def _employee_get(self):
        record = self.env['res.users'].search(
            [('name', '=', self.env.user.name)])
        return record

    def get_name_sep(self, inv_line):
        idx_begin = inv_line.find(']') + 1
        return inv_line[idx_begin:]

    def get_code_sep(self, inv_line):
        idx_begin = inv_line.find('[')
        idx_end = inv_line.find(']') + 1
        return inv_line[idx_begin:idx_end]

    def check_usd_total(self):
        currency_name = self.invoice_line_ids.mapped('sale_line_ids').order_id.pricelist_id.currency_id.name
        if "USD" in currency_name:
            return True
        else:
            return False

    def get_change_currency(self):
        return float(self.env['bo_edi_params'].search([('name' ,'=', 'CHANGE_AMOUNT')]).value)

    
    def get_last_CUFD(self):
        try:
            last_cufd = self.env['cufd_log'].search([])[-1]
            if last_cufd:
                print(last_cufd)
                return last_cufd
            else:
                raise Warning("There is no CUFD registered yet")
        except:
            raise Warning("There is no CUFD registered yet")

    def get_CUFD_by_date(self, date_time):
        aux_date = datetime(date_time.year, date_time.month, date_time.day, date_time.hour + 4, date_time.minute, date_time.second)
        try:
            date_cufd = self.env['cufd_log'].search(['&', (
                    'begin_date',
                    '<=', aux_date),
                    ('end_date',
                    '>=', aux_date)])
            cufds = self.env['cufd_log'].search([])
            for c in cufds:
                print(str(c.id) + str(c.begin_date) + str(c.end_date))
            if date_cufd:
                print(date_cufd)
                return date_cufd
            else:
                raise Warning("There is no CUFD with related date")
        except:
            raise Warning("There is no CUFD with related date")

    async def create_new_CUFD(self):
        selling_point= self.getBranchOffice()[2]
        new_cufd = await asyncio.wait_for(asyncio.create_task(self._generate_cufd(3)), timeout= 60.0)
        new_cufd_obj = {
                # "id_cufd" : 1 ,
                "cufd" : new_cufd.codigo,
                "controlCode": new_cufd.codigoControl,
                "begin_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": new_cufd.fechaVigencia.strftime("%Y-%m-%d %H:%M:%S"),
                "invoice_number": 1,
                "selling_point": selling_point.id
        }
        print(new_cufd_obj)
        self.env['cufd_log'].create(new_cufd_obj)     
        return [new_cufd, new_cufd_obj]

    async def getCUFD(self, invoice_state = 1, date_time = datetime.now):
        now = datetime.now(
            timezone('America/Argentina/Buenos_Aires')) - timedelta(hours=1)

        if invoice_state == 2: ## Facturas manuales
            specific_cufd = self.get_CUFD_by_date(date_time)
            current_cafc_number = self.env['bo_edi_params'].search([('name' ,'=', 'CAFC_NUMBER')]).value

            cufd_data = [specific_cufd.cufd,
                            current_cafc_number, specific_cufd.controlCode, specific_cufd]
        else:
            if invoice_state: ## Facturas en lina

                status_obj = self.env['bo_edi_params'].search(
                    [('name', '=', 'ONLINE')])
                current_status = int(status_obj.value)

                if not current_status: ## Al retomar conexion se genera nuevo CUFD:
                    new_cufd = await asyncio.wait_for(asyncio.create_task(self.create_new_CUFD()), timeout= 60.0) # 1 min                               
                    cufd_data = [new_cufd[0].codigo,
                            1, new_cufd[0].codigoControl, new_cufd[1]]
                else: ## Caso contrario se usa el vigente

                    # current_cufd = self.env['cufd_log'].search(['&', (
                    #     'begin_date',
                    #     '<=', now.strftime("%Y-%m-%d %H:%M:%S")),
                    #     ('end_date',
                    #     '>=', now.strftime("%Y-%m-%d %H:%M:%S"))])
                        #  '>=', now), ('selling_point', '=', selling_point.id_selling_point)])

                    current_cufd = self.get_last_CUFD() ## Uso del ultimo debido a que pueden existir mas de un CUFD con el mismo rango de fechas
                    
                    if not current_cufd: ## si no encuentra genera nuevo
                        new_cufd = await asyncio.wait_for(asyncio.create_task(self.create_new_CUFD()), timeout= 60.0) # 1 min                               
                        cufd_data = [new_cufd[0].codigo,
                                1, new_cufd[0].codigoControl, new_cufd[1]]

                    else:
                        cufd_data = [current_cufd.cufd,
                                current_cufd.invoice_number, current_cufd.controlCode, current_cufd]

            else: ## Facturas fuera de linea
                last_cufd = self.get_last_CUFD()
                cufd_data = [last_cufd.cufd,
                            last_cufd.invoice_number, last_cufd.controlCode, last_cufd]

        return cufd_data

    def _getEmissionType(self):
        emission_type = self.env['ir.config_parameter'].get_param(
            'res.config.settings.l10n_bo_emission_type')
        return emission_type

    def getBranchOffice(self):
        branch_office_data = [self._employee_get().l10n_bo_is_seller,
                              self._employee_get().l10n_bo_branch_office_id,
                              self._employee_get().l10n_bo_selling_point_id
                              ]
        return branch_office_data

    def _getCompanyNIT(self):
        nit = self.env.company.vat
        return nit

    async def set_bo_edi_info(self, date_time, invoice_state = 1):

        cufd = await asyncio.wait_for(asyncio.create_task(self.getCUFD(invoice_state, date_time)), timeout= 60.0) # 1 min
        self.l10n_bo_cufd = cufd[0]
        self.efact_control_code = cufd[2]
        self.l10n_bo_invoice_number = cufd[1]
        self.l10n_bo_branch_office = self.getBranchOffice()[1]
        self.l10n_bo_selling_point = self.getBranchOffice()[2]

        if invoice_state == 2:
            date_time = date_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        self.write({'l10n_bo_cuf':self.getCuf(date_time)})

        if self.l10n_bo_cufd and self.l10n_bo_cuf:
            return True
        else:
            return False
        # raise Warning("CUFD not retrieved, cannot send invoice")
        # _logger.info(self._getEmissionType())
        # self.getheaderInvoiceData()

    def clean(self):
        self.l10n_bo_cufd = ""
        self.l10n_bo_invoice_number = 0
    
    def _convert_sin_time(self, date_time):
        year = date_time[:4]
        month = date_time[5:7]
        day = date_time[8:10]
        hour = date_time[11:13]
        mins = date_time[14:16]
        seg = date_time[17:19]
        ms = date_time[20:23]
        return year + month + day + hour + mins+ seg + ms

    def getCuf(self, date_time):
        nit = str(self._getCompanyNIT())
        if not nit:
            raise Warning("There is no VAT/NIT for the current company")

        # now = datetime.now(
        #     timezone('America/Argentina/Buenos_Aires')) - timedelta(hours=1)
        # time = now.strftime("%Y%m%d%H%M%S" + "000")
        time = self._convert_sin_time(date_time)
        branch_office = str(self._employee_get(
        ).l10n_bo_branch_office_id.id_branch_office)
        modality = str(1)
        emission_type = str(self.env['bo_edi_params'].search(
            [('name', '=', 'TIPOEMISION')]).value)
        invoice_type = str(1)
        document_type = str(1)
        # invoice_number = str(self.getCUFD()[1])
        invoice_number = str(self.l10n_bo_invoice_number)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)

        zero_str = str(str(self._addZeros('nit', nit)) + str(time[0:17]) + str(self._addZeros('branch_office', branch_office))
                       + str(modality) + str(emission_type) + str(invoice_type) + str(self._addZeros('document_type', document_type)) +
                       str(self._addZeros('invoice_number', invoice_number)) + str(self._addZeros('selling_point', selling_point)))
        mod11_str = str(self._Mod11(zero_str, 1, 9, False))
        base16_str = str(self._Base16(zero_str + mod11_str))
        cuf = base16_str + str(self.efact_control_code) ##//TODO Revisar codigocontrol mal obtenido al generar el primer cufd del dia
        # _logger.info('/////////////////////////////////////////')
        # print(zero_str)
        # print(mod11_str)
        # print(base16_str)
        # _logger.info('/////////////////////////////////////////')
        return cuf

    def _addZeros(self, field, value):
        if field == 'nit':
            if len(value) == 9:
                return '0000' + value
            elif len(value) == 10:
                return '000' + value
        elif field == 'branch_office':
            if len(value) == 1:
                return '000' + value
            elif len(value) == 2:
                return '00' + value
            elif len(value) == 3:
                return '0' + value
        elif field == 'document_type':
            if len(value) == 1:
                return '0' + value
            elif len(value) == 2:
                return value
        elif field == 'invoice_number':
            if len(value) == 1:
                return '000000000' + value
            elif len(value) == 2:
                return '00000000' + value
            elif len(value) == 3:
                return '0000000' + value
            elif len(value) == 4:
                return '0000000' + value
        elif field == 'selling_point':
            if len(value) == 1:
                return '000' + value
            elif len(value) == 2:
                return '00' + value
            elif len(value) == 3:
                return '0' + value

    # def _Mod11(self, cadena):
    #     factores = itertools.cycle((2, 3, 4, 5, 6, 7))
    #     suma = 0
    #     for digito, factor in zip(reversed(cadena), factores):
    #         suma += int(digito)*factor
    #     control = 11 - suma % 11
    #     if control == 10:
    #         return 1
    #     else:
    #         return control

    def _Mod11(self, cadena, numDig, limMult, x10):
        mult = None
        suma = None
        i = None
        n = None
        dig = None

        if not x10:
            numDig = 1

        n = 1
        while n <= numDig:
            suma = 0
            mult = 2
            for i in range(len(cadena) - 1, -1, -1):
                suma += (mult * int(cadena[i: i + 1]))
                mult += 1
                if mult > limMult:
                    mult = 2
            if x10:
                dig = math.fmod((math.fmod((suma * 10), 11)), 10)
            else:
                dig = math.fmod(suma, 11)
            if dig == 10:
                cadena += "1"
            if dig == 11:
                cadena += "0"
            if dig < 10:
                cadena += str(round(dig))
            n += 1
        result = cadena[len(cadena) - numDig : len(cadena)]
        return result

    def _Base16(self, cadena):
        hex_val = (hex(int(cadena))[2:]).upper()
        return hex_val

    def _Base16decode(self, cadena):
        print(int("0x" + cadena, 0))

    # def pruebaMod(self):
    #     stri = '00001234567892019011316372123100001110100000000010000'
    #     a = self._Mod11(stri)
    #     cadena = stri + str(a)
    #     _logger.info(cadena)
    #     _logger.info(str(self._Base16(cadena)))

    # def _getSiatToken(self, login, nit, password):
    #     client = zeep.Client(
    #         wsdl='https://pilotosiatservicios.impuestos.gob.bo/v1/ServicioAutenticacionSoap?wsdl')
    #     params = {'DatosUsuarioRequest': {
    #         'login': login,
    #         'nit': nit,
    #         'password': password
    #     }
    #     }
    #     result = client.service.token(**params)
    #     _logger.info(str(result['token']))
    #     return result['token']

    def getTime(self):
        now = datetime.now(
            timezone('America/Argentina/Buenos_Aires')) - timedelta(hours=1)
        return now

    # def log_method(self):
    #     _logger.info('///////////////////DFE INFO//////////////')
    #     _logger.info(self._employee_get().l10n_bo_branch_office_id)
    #     self.getCUFD()
    #     _logger.info(
    #         '/////////////////////////////////////////////////////////')

    def getheaderInvoiceData(self, invoice_state = 1, date_time = ''):
        # data_cufd = self.getCUFD() ##//TODO pendiente generacion dinamica CUFD async
        self.get_total_converted() ## Verificar factura en Dolares
        ## HEADER
        invoice_header = {
            'nit': self._getCompanyNIT(),
            'company_name': self.env.company.name,
            'city_name': self.env.company.city,
            'phone': self.env.company.phone,
            'invoice_number': self.l10n_bo_invoice_number,
            'cuf': self.l10n_bo_cuf,
            'cufd': self.l10n_bo_cufd,
            'branch_office_id': self._employee_get().l10n_bo_branch_office_id.id_branch_office,
            'company_address': self.env.company.street,
            'selling_point_id': self._employee_get().l10n_bo_selling_point_id.id_selling_point,
            # 'current_time': self.getTime().strftime("%Y-%m-%dT%H:%M:%S.000"),
            'current_time': date_time,
            'client_name': self.partner_id.name,
            'client_id_type': self.partner_id.l10n_bo_id_type.id_type_code if self.partner_id.l10n_bo_id_type else '1',
            'client_id': self.partner_id.vat,
            # 'payment_method': self.partner_id.property_payment_method_id,  # PEND
            'payment_method': '1',
            'total_untaxed': self.amount_untaxed,
            'total': self.amount_total if self.total_conv == 0.0 or self.manual_usd_edit else self.total_conv,
            # 'currency_type': self.env['ir.config_parameter'].get_param(
            #     'res.config.settings.currency_id')  # PEND
            'currency_type': '1',
            'complement': self.partner_id.complement
        }

        ## ITEMS
        invoiceItems = self.getInvoiceItemsData(0)
        ## Alternative data
        discount_item = {}
        for  idx, item in enumerate(invoiceItems):
            if "global_discount" in item.name:
                discount_item = item
        
        # global_discount = str(float(discount_item.price_unit) * -1) if discount_item else 0
        if discount_item:
            global_discount = str(float(discount_item.price_unit) * -1)
            if self.total_conv == 0.0:
                self.total_discount = float(global_discount)
            else:
                self.total_discount = round(float(global_discount) * self.get_change_currency())
            invoiceItems = self.getInvoiceItemsData(1)
        else:
            global_discount = 0
        ####

        ## Salto de pagina 
        break_item_number = int(self.env['bo_edi_params'].search(
                    [('name', '=', 'BREAKPAGE_ITEM_NUMBER')]).value)
        if len(invoiceItems) >= break_item_number:
             self.page_break = 1
        else:
            self.page_break = 0

        # Cambiar Parametro de Tipo Factura segun se requiera
        additional_data = self._getAdditionalData(0, invoice_state, global_discount)
        set_xml_res = self._setXML(invoice_header, invoiceItems,
                     additional_data, invoice_state)
        _logger.info('///////////////RESPUESTA FACTURA DEVUELTA///////////////////')
        _logger.info(set_xml_res[0])
        _logger.info('//////////////////////////////////')

        ##//?? VERIFICAR razón por la cual warnings no permiten guardar dato cuf (set_bo_edi_info)
        if set_xml_res[0]:
            if 'Contingencia' in set_xml_res[1]:
                last_cufd = self.get_last_CUFD()
                last_cufd.write({'invoice_number': int(last_cufd.invoice_number) + 1})
                return True
            elif 'Manual' in set_xml_res[1]:
                cafc_num = self.env['bo_edi_params'].search(
                    [('name', '=', 'CAFC_NUMBER')])
                cafc_num.write({'value': int(cafc_num.value) + 1})
                return True
            else:
                # now = self.getTime()
                # current_cufd = self.env['cufd_log'].search(['&', ( ##//TODO Pendiente obtencion de ultimo CUFD vigente
                # 'begin_date',
                # '<=', now),
                # ('end_date',
                # '>=', now)])
                current_cufd = self.get_last_CUFD() ## Obtener ultimo cufd debido a la posibilidad de generar eventos en el mismo dia y que hayan mas de un cufd
                current_cufd.write({'invoice_number': int(current_cufd.invoice_number) + 1})
                # raise Warning('SIN Invoice posted succesfully!')
                # self.trigger_popup(1)
                return True
        else :
            ## raise SIN error
            # raise Warning('Invoice rejected by SIN: ' + set_xml_res[1])
            # print("Invoice rejected", 'Invoice rejected by SIN: ' + set_xml_res[1])
            # self.trigger_popup(2)
            return False

    def getInvoiceItemsData(self, global_discount = 0):
        if global_discount:
            # items = self.invoice_line_ids.search(['&', ('name', '!=', 'global_discount'), ('move_name', '=', self.name), ('journal_id.type', '=', 'sale')])
            items = self.invoice_line_ids.filtered(lambda x: 'global_discount' not in x.name)
        else:
            items = self.invoice_line_ids
        for item in items:
            print(item.name)
        return items

    def _getAdditionalData(self, invoice_type, invoice_state = 1, global_discount = 0):
        cafc = self.env['bo_edi_params'].search(
            [('name', '=', 'CAFC')]).value
        header_start = ()
        additional_header_tags = (F"<montoGiftCard xsi:nil='true'/>")
        xml_end = ""
        if (invoice_type == 0):  # Factura Compra Venta
            header_start = ("<facturaElectronicaCompraVenta"
                            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
                            # "xmlns:xsd='http://www.w3.org/2001/XMLSchema'"
                            ' xsi:noNamespaceSchemaLocation="facturaElectronicaCompraVenta.xsd">')

            if global_discount:
                if self.total_discount != 0.0:
                    global_discount = self.total_discount
                additional_header_tags = additional_header_tags + (F"<descuentoAdicional>{global_discount}</descuentoAdicional>")
            else:
                additional_header_tags = additional_header_tags + (F"<descuentoAdicional xsi:nil='true'/>")
            
            if self.invalid_nit:
                additional_header_tags = additional_header_tags + (F"<codigoExcepcion>1</codigoExcepcion>")
            else:
                additional_header_tags = additional_header_tags + (F"<codigoExcepcion xsi:nil='true'/>")

            if invoice_state == 2:
                additional_header_tags = additional_header_tags + (F"<cafc>{cafc}</cafc>")
            else:
                additional_header_tags = additional_header_tags + (F"<cafc xsi:nil='true'/>")

            xml_end = "</facturaElectronicaCompraVenta>"
        # elif (invoice_type == 1): ## Factura Tasa Cero
        #     ## header_start = ...
        #     ## additional_tags = .....
        additional_data = {'start': header_start,
                           'additionalHeader': additional_header_tags,
                           'end': xml_end
                           }
        return additional_data

    def _setXML(self, headerInvoiceData, invoiceItems, additionalData, invoice_state = 1):
        xml = ''

        if not self.total_conv == 0.0 and not self.manual_usd_edit: ## Obtencion de total convertido por diferencia de centavos
            new_total_conv = 0.0
            for item in invoiceItems:
                new_total_conv = new_total_conv + round(round((item.price_unit * self.get_change_currency()), 2) * item.quantity, 2)

            if self.total_discount == 0.0:
                self.total_conv = round(new_total_conv, 2 )
            else:
                self.total_conv = round(new_total_conv - self.total_discount, 2)
            # self.subtotal_conv = new_total_conv
            # headerInvoiceData['total'] = round(new_total_conv, 2)
            headerInvoiceData['total'] = round(self.total_conv, 2)

        startHeader = additionalData['start']
        complement = F"<complemento>{headerInvoiceData['complement']}</complemento>" if headerInvoiceData['complement'] else "<complemento xsi:nil='true'/>"
        xmlHeader = ("<cabecera>"
                     F"<nitEmisor>{headerInvoiceData['nit']}</nitEmisor>"
                     F"<razonSocialEmisor>{headerInvoiceData['company_name']}</razonSocialEmisor>"
                     F"<municipio>{headerInvoiceData['city_name']}</municipio>"
                     F"<telefono>{headerInvoiceData['phone']}</telefono>"
                     F"<numeroFactura>{headerInvoiceData['invoice_number']}</numeroFactura>"
                     ##?? borrar
                    #  F"<numeroFactura>2</numeroFactura>"
                     F"<cuf>{headerInvoiceData['cuf']}</cuf>"
                     F"<cufd>{headerInvoiceData['cufd']}</cufd>"
                     F"<codigoSucursal>{headerInvoiceData['branch_office_id']}</codigoSucursal>"
                     F"<direccion>{headerInvoiceData['company_address']}</direccion>"
                     F"<codigoPuntoVenta>{headerInvoiceData['selling_point_id']}</codigoPuntoVenta>"
                     F"<fechaEmision>{headerInvoiceData['current_time']}</fechaEmision>"
                     F"<nombreRazonSocial>{headerInvoiceData['client_name']}</nombreRazonSocial>"
                     F"<codigoTipoDocumentoIdentidad>{headerInvoiceData['client_id_type']}</codigoTipoDocumentoIdentidad>"
                     F"<numeroDocumento>{headerInvoiceData['client_id']}</numeroDocumento>"
                    #  '<complemento xsi:nil="true"/>'
                     F"{complement}"
                    # F"<complemento>{headerInvoiceData['complement']}</complemento>" if headerInvoiceData['complement'] else '<complemento xsi:nil="true"/>'
                     F"<codigoCliente>{headerInvoiceData['client_id']}</codigoCliente>" # CI/NIT sin complemento
                     # PEND
                     F"<codigoMetodoPago>{headerInvoiceData['payment_method']}</codigoMetodoPago>"
                     "<numeroTarjeta xsi:nil='true'/>"
                    #  F"<montoTotal>{headerInvoiceData['total_untaxed']}</montoTotal>" # ERROR DE Impuestos, verificacion de montos
                     F"<montoTotal>{headerInvoiceData['total']}</montoTotal>"
                     F"<montoTotalSujetoIva>{headerInvoiceData['total']}</montoTotalSujetoIva>"
                     F"<codigoMoneda>1</codigoMoneda>"  # PEND
                     F"<tipoCambio>1</tipoCambio>"  # PEND
                     F"<montoTotalMoneda>{headerInvoiceData['total']}</montoTotalMoneda>"
                     )
        # xmlHeader = xmlHeader + complement
        xmlHeader = xmlHeader + additionalData['additionalHeader']
        invoice_caps = self.env["invoice_caption"].search([('activity_code', '=', invoiceItems[0].product_id.sin_item.activity_code.code)])
        rnd_cap = random.choice(invoice_caps)
        self.invoice_caption = rnd_cap.description
        xmlHeader = xmlHeader + (F"<leyenda>{rnd_cap.description}</leyenda>"  # PEND RND
                                 "<usuario>admin</usuario>"
                                 # PEND
                                 F"<codigoDocumentoSector>{headerInvoiceData['currency_type']}</codigoDocumentoSector>")
        endHeader = "</cabecera>"
        xml = xml + startHeader + xmlHeader + endHeader
        for item in invoiceItems:
            subtotal = F"<subTotal>{round(item.price_unit * item.quantity, 2)}</subTotal>" if self.total_conv == 0.0 or self.manual_usd_edit else F"<subTotal>{round(round((item.price_unit * self.get_change_currency()), 2) * item.quantity, 2)}</subTotal>"
            precioUnitario = F"<precioUnitario>{item.price_unit}</precioUnitario>" if self.total_conv == 0.0 or self.manual_usd_edit else F"<precioUnitario>{round(round(item.price_unit, 2) * self.get_change_currency(), 2)}</precioUnitario>"
            xmlItem = ("<detalle>"
                       F"<actividadEconomica>{item.product_id.sin_item.activity_code.code}</actividadEconomica>"
                       F"<codigoProductoSin>{item.product_id.sin_item.sin_code}</codigoProductoSin>"
                       F"<codigoProducto>{item.product_id.default_code}</codigoProducto>"
                      F"<descripcion>{item.name}</descripcion>"
                       F"<cantidad>{item.quantity}</cantidad>"
                       F"<unidadMedida>{item.product_id.measure_unit.measure_unit_code}</unidadMedida>"
                    #    F"<precioUnitario>{item.price_unit}</precioUnitario>"
                       F"{precioUnitario}"
                       "<montoDescuento xsi:nil='true'/>"
                    #    F"<subTotal>{item.price_subtotal}</subTotal>"
                    #    F"<subTotal>{headerInvoiceData['total']}</subTotal>" # ERROR DE Impuestos, verificacion de montos
                       F"{subtotal}"
                    #    F"<subTotal>{item.price_unit * item.quantity}</subTotal>"
                       '<numeroSerie xsi:nil="true"/>'
                       '<numeroImei xsi:nil="true"/>'
                       "</detalle>")
            xml = xml + xmlItem
        
        xml = xml + additionalData['end']

        # _logger.info(str(xmlHeader))
        xml_path = self.env['bo_edi_params'].search(
            [('name', '=', 'XML')]).value

        xml_signed_path = ''
        if invoice_state == 2:
            xml_signed_path = self.env['bo_edi_params'].search(
                [('name', '=', 'FACTMAN_NOPROC')]).value
        elif invoice_state:
            xml_signed_path = self.env['bo_edi_params'].search(
                [('name', '=', 'XMLSIGNED')]).value
        else:
            xml_signed_path = self.env['bo_edi_params'].search(
                [('name', '=', 'FACTPAQ_NOPROC')]).value

        xml_signed_server_path = self.env['bo_edi_params'].search(
            [('name', '=', 'XMLSIGNEDSERVER')]).value
        key_path = self.env['bo_edi_params'].search(
            [('name', '=', 'KEY')]).value
        cert_path = self.env['bo_edi_params'].search(
            [('name', '=', 'CERTIFICADO')]).value
        cred_path = self.env['bo_edi_params'].search(
            [('name', '=', 'CREDENTIALSPATH')]).value
        xsd_compraventa_path = self.env['bo_edi_params'].search(
            [('name', '=', 'XSDCompraVenta')]).value  ##?? borrar
        pwd_cert_path = self.env['bo_edi_params'].search(
            [('name', '=', 'PWDCERTIFICADO')]).value

        invoice_number = headerInvoiceData['invoice_number']
        ##?? borrar
        # invoice_number = "2"

        ## str(invoice_number).zfill(4) PREVIO NOMBRE
        # xml_name = self.name.replace('/', u"\u2215") ## Reemplazar barra de  nombre con codigo para que no se tome como ruta
        # date_time = self.getTime().strftime("%Y-%m-%dT%H:%M")
        # control_code = self.get_last_CUFD().controlCode ##TODO Agregar codigo control cufd a nombre para diferenciar facturas de un mismo dia por contingencia
        date_time = self.getTime().strftime("%Y-%m-%d")
        branch_office = self.getBranchOffice()[1].id_branch_office
        selling_point = self.getBranchOffice()[2].id_selling_point
        xml_name = str(date_time) + "_" + str(branch_office) + "_" + str(selling_point) + "_" + str(invoice_number).zfill(4)
        
        with open(xml_path + xml_name + '.xml', 'w') as xml_file:
            xml_file.write(xml)
            xml_file.close()

        xml_signed = self.env['sin_sync'].sign_xml(
            xml, cred_path, key_path, cert_path, xml_signed_server_path + xml_name)

        with open(xml_signed_path + xml_name + '.xml', 'w') as xml_signed_file:
            xml_signed_file.write(xml_signed)
            xml_signed_file.close()

        if invoice_state == 1:
            self._zip_xml(xml_signed_path + xml_name + '.xml', xml_signed_path + xml_name + '.gz')
            zip = open(xml_signed_path +
                    xml_name + '.gz', 'rb')
            zip_content = zip.read()

            hashed_xml = self._get_file_hash(xml_signed_path +
                                            xml_name + '.gz')


        if invoice_state == 2:
            ##?? generacion de factura manual
            return [True, "Factura XML Manual"]

        elif invoice_state:
            ##?? generacion de factura en línea
            send_invoice_res = self._req_send_invoice(self.l10n_bo_cufd, zip_content, hashed_xml, headerInvoiceData['current_time'])

            if send_invoice_res.codigoEstado == 908:
                return [True, send_invoice_res.codigoDescripcion]
            elif send_invoice_res.codigoEstado == 902:
                raise Warning("Invoice Rejected, Reason: " + send_invoice_res.mensajesList[0].descripcion + " Code: " + str(send_invoice_res.codigoEstado))
            else:
                _logger.info('///////////////RESPUESTA FACTURA///////////////////')
                _logger.info("Invoice Rejected, Reason: " + send_invoice_res.mensajesList[0].descripcion + " Code: " + str(send_invoice_res.codigoEstado))
                _logger.info('//////////////////////////////////')
                raise Warning("Invoice Rejected, Reason: " + send_invoice_res.mensajesList[0].descripcion + " Code: " + str(send_invoice_res.codigoEstado))
                return [False, send_invoice_res.codigoDescripcion]
        else :
            ##?? generacion de factura por contingencia
            return [True, "Factura XML Contingencia"]

    def _zip_xml(self, xml_path, output_path):
        with open(xml_path, 'rb') as f_input:
            with gzip.open(output_path, 'wb') as f_output:
                shutil.copyfileobj(f_input, f_output)

    ########### Digital Signature Algorithms ################

    def _NumberTobase64(self, cNumber):
        sResp = ""
        cCociente = 1

        while cCociente > 0:
            cCociente = 1
            cTemp = cNumber
            while cTemp >= 64:
                cTemp -= 64
                cCociente += 1
            cCociente -= 1
            cResiduo = cTemp
            sResp = self.dictionaryBase64[cResiduo] + sResp
            cNumber = cCociente
        return sResp

    def _XmlTobase64(self, xmlPath):
        with open(xmlPath, "rb") as file:
            encoded = base64.encodebytes(file.read()).decode("utf-8")
        return encoded

    def _StringTobase64(self, string):
        encodedString = base64.b64encode(bytes(string, 'utf-8'))
        return encodedString

    def _GetHashSha256(self, input):
        hash = sha256(input.encode('utf-8')).hexdigest()
        return hash

    def _get_file_hash(self, file_path):
        BLOCK_SIZE = 65536  # The size of each read from the file

        # Create the hash object, can use something other than `.sha256()` if you wish
        file_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:  # Open the file to read it's bytes
            # Read from the file. Take in the amount declared above
            fb = f.read(BLOCK_SIZE)
            while len(fb) > 0:  # While there is still data being read from the file
                file_hash.update(fb)  # Update the hash
                fb = f.read(BLOCK_SIZE)  # Read the next block from the file

        return file_hash.hexdigest()  # Get the digest of the hash

    def _read_private_key(self, private_key_pem, passphrase=None):
        """Reads a private key PEM block and returns a RSAPrivatekey

        :param private_key_pem: The private key PEM block
        :param passphrase: Optional passphrase needed to decrypt the private key
        :returns: a RSAPrivatekey object
        """
        if passphrase and isinstance(passphrase, str):
            passphrase = passphrase.encode("utf-8")
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode('utf-8')

        try:
            return serialization.load_pem_private_key(private_key_pem, passphrase,
                                                      backends.default_backend())
        except Exception:
            raise logging.exception.NeedsPassphrase

    ########### Report ################

    # def open_report_consume(self, context=None):
        # # if ids:
        # #     if not isinstance(ids, list):
        # #         ids = [ids]
        # #     context = dict(context or {}, active_ids=ids,
        # #                    active_model=self._name)
        # return {
        #     'type': 'ir.actions.report.xml',
        #     'report_name': 'l10n_bo_edi.graphic_representation_template',
        #     'context': context,
        # }

    def print_report(self):
        self.generate_qr_code()
        ##?? ADDON formato dinámico (no usado)
        # if not self.e_billing:
        #     currency_name = self.invoice_line_ids.mapped('sale_line_ids').order_id.pricelist_id.currency_id.name
        #     if "USD" in str(currency_name):
        #         self.total_conv = self.amount_total * 6.96
        #     else:
        #         self.total_conv = 0.0
        #     return self.env.ref('l10n_bo_edi.invoice_report').report_action(self)
        # else:
        #     if self.representation_format:
        #         return self.env.ref('l10n_bo_edi.graphic_representation').report_action(self)
        #     else:
        #         return self.env.ref('l10n_bo_edi.graphic_representation_pdf').report_action(self)
        ##????
        # currency_name = self.invoice_line_ids.mapped('sale_line_ids').order_id.pricelist_id.currency_id.name
        # if "USD" in str(currency_name):
        #     self.total_conv = self.amount_total * 6.96
        # else:
        #     self.total_conv = 0.0
        inv_lines = self.getInvoiceItemsData(1)
        break_item_number = int(self.env['bo_edi_params'].search(
                    [('name', '=', 'BREAKPAGE_ITEM_NUMBER')]).value)
        if len(inv_lines) >= break_item_number:
             self.page_break = 1
        else:
            self.page_break = 0
        return self.env.ref('l10n_bo_edi.invoice_report').report_action(self)


    def generate_qr_code(self):

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        if not self.e_billing:
            qr.add_data(str(self.env.company.vat) + '|' +
                        str(self.l10n_bo_invoice_number) + '|' +
                        str(self.auth_number) + '|' +
                        str(self.getTime().strftime("%d/%m/%Y")) + '|' +
                        str(round(self.amount_total)) + '|' +
                        str(round(self.amount_total)) + '|' +
                        str(self.control_code))
        else:
            qr_url = str(self.env['bo_edi_params'].search(
            [('name', '=', 'URL_QR')]).value)
            if self.representation_size:
                qr.add_data( qr_url + 'nit=' + str(self._getCompanyNIT()) + '&cuf='+ str(self.l10n_bo_cuf) + '&numero=' + str(self.l10n_bo_invoice_number) + '&t=2')
            else:
                qr.add_data(qr_url + 'nit=' + str(self._getCompanyNIT()) + '&cuf='+ str(self.l10n_bo_cuf) + '&numero=' + str(self.l10n_bo_invoice_number) + '&t=1')
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="JPEG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_code = qr_image
        # print(self.qr_code)

    ########### SIN Requests ################

    async def _generate_cufd(self, tipo_codigo):

        # self.env['sin_sync'].check_communication()
        ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        # selling_point = str(self.env['selling_point'].search(
        #     [('description', '=', 'PUNTO DE VENTA 0')]).id_selling_point)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        # branch_office = str(self.env['branch_office'].search(
        #     [('description', '=', 'CASA MATRIZ')]).id_branch_office)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        # cuis = str(self.env['bo_edi_params'].search(
        #     [('name', '=', 'CUIS-0')]).value)
        cuis = str(self.getBranchOffice()[2].cuis)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)

        return await asyncio.wait_for(asyncio.create_task(
          self.env['sin_sync'].get_cufd(
                ambience,
                modality,
                selling_point,
                system_code,
                branch_office,
                cuis,
                nit,
                tipo_codigo
            )
        ), timeout= 60.0)
        # return await (self.env['sin_sync'].get_cufd(
        #     ambience,
        #     modality,
        #     selling_point,
        #     system_code,
        #     branch_office,
        #     cuis,
        #     nit,
        #     tipo_codigo
        # ))

    def _req_send_invoice(self, cufd, zip_content, hashed_xml, date):

        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        cuis = str(self.getBranchOffice()[2].cuis)
        code_modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)
        emission_type = str(self.env['bo_edi_params'].search(
            [('name', '=', 'TIPOEMISION')]).value)
        # emission_type = 2 ##?? BORRAR

        return self.env['sin_sync'].send_invoice(emission_type, ambience, code_modality, selling_point, system_code, branch_office, cuis, nit,
            self.l10n_bo_cufd, zip_content, hashed_xml, date)

    def _req_cancel_invoice(self, cuf ,cufd , reason_code):
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        id_sector_type = str(self.env['sector_types'].search(
            [('description', '=', 'FACTURA COMPRA-VENTA')]).id_sector_type)
        id_emission = str(self.env['bo_edi_params'].search(
            [('name', '=', 'TIPOEMISION')]).value)
        id_modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        cuis = str(self.getBranchOffice()[2].cuis)

        return self.env['sin_sync'].cancel_invoice(cufd, cuf, reason_code, id_ambience, id_sector_type, id_emission, id_modality, selling_point, system_code, branch_office, cuis)

    def _req_send_event(self, reason_code, cufd_even, cufd, description, begin_date, end_date):
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        cuis = str(self.getBranchOffice()[2].cuis)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)

        return self.env['sin_sync'].send_invoice_event(id_ambience, selling_point, system_code,
                                                        branch_office, cuis, nit, cufd, reason_code,
                                                        description, begin_date, end_date, cufd_even)
        
    def req_sync_datetime(self):
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        cuis = str(self.getBranchOffice()[2].cuis)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)
        params = self.env['sin_sync'].sync_general(id_ambience, selling_point, 
                                                   system_code, branch_office,
                                                   cuis, nit)
        date_time = self.env['sin_sync'].sync_fecha_hora(params)
        if date_time.transaccion:
            print(date_time.fechaHora)
            print(str(date_time.fechaHora[:-6]) + '000'),
            return date_time.fechaHora
        else:
            raise Warning("There was an error trying to sync with SIN datetime")
    
    def req_verify_nit(self, nit_to_verify):
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        id_modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        cuis = str(self.getBranchOffice()[2].cuis)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)

        res_nit = self.env['sin_sync'].verifica_nit(id_ambience, id_modality, system_code,
                                                    branch_office, cuis, nit, nit_to_verify)
        if res_nit:
            return res_nit
        else:
            raise Warning("There was an error trying to verify NIT with SIN")
    
    def req_send_package(self, cufd, pack_content, pack_hash, cafc, inv_quantity , event_code):

        id_modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        cuis = str(self.getBranchOffice()[2].cuis)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)
        
        return self.env['sin_sync'].send_package(cufd, pack_content, pack_hash, cafc, inv_quantity, event_code,
                                          id_modality, id_ambience, selling_point, branch_office, system_code,
                                          cuis, nit)
    
    def req_verify_package(self, cufd, code_recept):

        id_modality = str(self.env['modalities'].search(
            [('description', '=', 'ELECTRONICA')]).id_modality)
        id_ambience = str(self.env['bo_edi_params'].search(
            [('name', '=', 'AMBIENTE')]).value)
        selling_point = str(self.getBranchOffice()[2].id_selling_point)
        branch_office = str(self.getBranchOffice()[1].id_branch_office)
        system_code = str(self.env['bo_edi_params'].search(
            [('name', '=', 'CODIGOSISTEMA')]).value)
        cuis = str(self.getBranchOffice()[2].cuis)
        nit = str(self.env['bo_edi_params'].search(
            [('name', '=', 'NIT')]).value)
        
        return self.env['sin_sync'].verify_package(id_ambience, selling_point, branch_office, id_modality,
                                                    system_code, cuis, nit, cufd, code_recept)
        

    def sync_activities(self):
        self.env['sin_sync'].cert_sync_catal(50, 0)
        # self.cert_invoices_cancellations(80)

    def cert_invoices_cancellations(self, iterations):
        for i in range(iterations):
            self.check_conectivity()
            # time.sleep(3)
            # self._req_cancel_invoice( self.l10n_bo_cufd, self.l10n_bo_cuf, 1)

    # def cert_invoices_generate(self, iterations):
    #     for i in range(iterations):

    ########### AUXILIARES ################

    # def create_notification(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Warning!',
    #             'message': 'You cannot do this action now',
    #             'sticky': True,
    #         }
    #     }

    ########### Anulaciones ################

    ##******************* Metodo previo para boton de cancelación
    # def button_cancel(self):
    #     if (self.e_billing):
    #         if (self.journal_id.type == 'sale' or self.journal_id.type == 'purchase'):
    #             self.is_cancelled = True
    #             super(AccountMove, self).button_cancel()
    #             return {
    #                 "type": "ir.actions.act_window",
    #                 "res_model": "invoice_cancel_reason_wizard",
    #                 "context": {'cuf':self.l10n_bo_cuf, 'cufd': self.l10n_bo_cufd },
    #                 "view_type": "form",
    #                 "view_mode": "form",
    #                 "target": "new",
    #             }
    #     else:
    #         new_cancel_inv = {
    #             "invoice_num" : self.l10n_bo_invoice_number,
    #             "inv_reversed": False,
    #             "date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
    #             "account_move_id": self.id,
    #             "invoice_dosage_id": self.dosage_id.id
    #         }
    #         self.env['cancelled_invoices'].create(new_cancel_inv)
    #         super(AccountMove, self).button_cancel()

    # def button_draft(self):
    #     print("Invoice Drafted")
    #     self.is_drafted = True
    #     super(AccountMove, self).button_draft()
    ##**************************************************************************

    def button_reverse(self):
        if self.invoice_mails == '':
            raise Warning("Field 'Correos a Enviar' must be filled")

        if self.journal_id.type == 'sale':
            # self.write({'auto_post': False, 'state': 'cancel'})
            if self.e_billing:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "account.move.reversal",
                    "context": {'inv_type': self.e_billing,
                                'cuf':self.l10n_bo_cuf,
                                # 'cufd': self.l10n_bo_cufd,
                                'cufd': self.get_last_CUFD().cufd,
                                'inv_number': self.l10n_bo_invoice_number,
                                'account_move_id': self.id,
                                'invoice_dosage_id': 0,
                                'email_to': self.invoice_mails
                                },
                    "view_type": "form",
                    "view_mode": "form",
                    "target": "new",
                }
            else:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "account.move.reversal",
                    "context": {'inv_type': self.e_billing,
                                'cuf': 0,
                                'cufd': 0,
                                'inv_number': self.l10n_bo_invoice_number,
                                'account_move_id': self.id,
                                'invoice_dosage_id': self.dosage_id.id},
                    "view_type": "form",
                    "view_mode": "form",
                    "target": "new",
                }



    def invoice_cancellation(self, inv_type, cuf=0, cufd=0, inv_number=0, account_move_id=0, invoice_dosage_id=0, reason_code = 0, email_to=''):
        if inv_type:
            res_cancel = self._req_cancel_invoice(cuf ,cufd , reason_code)
            if (res_cancel.codigoEstado != 905):
                _logger.info('///////////////RESPUESTA ANULACION FACTURA///////////////////')
                _logger.info('There was an error cancelling the invoice, Reason: ' + res_cancel.mensajesList[0].descripcion + " Code: " + str(res_cancel.codigoEstado))
                _logger.info('//////////////////////////////////')
                raise Warning('There was an error cancelling the invoice, Reason: ' + res_cancel.mensajesList[0].descripcion + " Code: " + str(res_cancel.codigoEstado))

        self.env['account.move'].search(
            [('id', '=', account_move_id)]).write({"is_cancelled" : True})

        new_cancel_inv = {
            "invoice_num" : inv_number,
            "inv_reversed": False,
            "date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
            "account_move_id": account_move_id,
            "invoice_dosage_id": invoice_dosage_id
        }

        self.env['cancelled_invoices'].create(new_cancel_inv)

        self.send_email(reason_code ,cufd, inv_number, email_to)

        # super(AccountMove, self).button_cancel()

        # if not reason_code:
        #     raise Warning('You must select an invoice cancelation reason')
        # else:
        #     res_cancel = self._req_cancel_invoice(cuf ,cufd , reason_code)
        #     if (res_cancel.codigoEstado != 905):
        #         _logger.info('///////////////RESPUESTA ANULACION FACTURA///////////////////')
        #         _logger.info('There was an error cancelling the invoice, Reason: ' + res_cancel.mensajesList[0].descripcion + " Code: " + str(res_cancel.codigoEstado))
        #         _logger.info('//////////////////////////////////')
        #         raise Warning('There was an error cancelling the invoice, Reason: ' + res_cancel.mensajesList[0].descripcion + " Code: " + str(res_cancel.codigoEstado))

            # self.is_cancelled = True
            # super(AccountMove, self).button_cancel() ##//TODO Averiguar la manera de llamar a metodo super origen desde otro metodo

    
    ########### MAIN ROAD ################
    def launch_warn_wizard(self):
        warn_wiz = {
                    "type": "ir.actions.act_window",
                    "res_model": "popup_warn_wizard",
                    "view_type": "form",
                    "view_mode": "form",
                    "target": "new",
                }
        return warn_wiz
    
    def launch_new_event_wizard(self):
        event_wiz = {
                    "type": "ir.actions.act_window",
                    "res_model": "invoice_event_wizard",
                    "view_type": "form",
                    "view_mode": "form",
                    "target": "new",
                }
        return event_wiz

    def check_nit(self):
        if self.partner_id.l10n_bo_id_type.id_type_code == 5:
            res_verif_nit = self.req_verify_nit(self.partner_id.vat)
            if res_verif_nit.mensajesList[0].codigo == 994:
                self.invalid_nit = True
                return False
            elif res_verif_nit.mensajesList[0].codigo == 986:
                return True
            else:
                return True
        else:
            return True
    
    def manual_inv(self):
        # if self.invoice_event_id and self.event_begin_date:
        #     if int(self.invoice_event_id.code) >= 4:
        #         self.check_conectivity(True)
        #     else:
        #         raise Warning('Manual invoices aren''t available for the current event, please change')
        # else:
        #     raise Warning('Fill in the invoice event & event date fields')

        cert_status = int(self.env['bo_edi_params'].search( ## Variable de certificacion para cambio de estado Online/Offline
            [('name', '=', 'CERTSTATUS')]).value)
        # if not cert_status:
        if self.manual_invoice_date:
            self.check_conectivity(True)
        else:
            raise Warning('Fill in the event date field')
        # else:
        #     raise Warning('You are currently online, there''s no need to create a manual invoice')

    async def send_package_settings(self):
        current_incident = self.env['invoice_incident'].search(
                                    [('sin_code', '=', "")])
        if current_incident :
            
            sin_date_time = self.getTime().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            new_cufd = await asyncio.wait_for(asyncio.create_task(self.create_new_CUFD()), timeout= 60.0) # 1 min
            current_incident.write({"end_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S")})
            res_incident_sent = self._req_send_event(current_incident.invoice_event_id.code, current_incident.cufd_log_id.cufd,
                                                                new_cufd[0].codigo, current_incident.description, current_incident.begin_date, current_incident.end_date )
            if(str(res_incident_sent).strip() != "None"):
                print(res_incident_sent)
                current_incident.write({"sin_code" : str(res_incident_sent)})
            else:
                raise Warning("There was an error sending the invoice event")
            no_proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTPAQ_NOPROC')]).value
            proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTPAQ_PROC')]).value
            xml_package_path = self.env['bo_edi_params'].search([('name', '=', 'EMPAQUETADO')]).value
            
            # params
            package_num = self.env['bo_edi_params'].search([('name', '=', 'CANTPAQUETES')])
            current_inv_num = self.env['bo_edi_params'].search([('name', '=', 'CANTACTUALFACTPAQ')])
            inv_num_limit = self.env['bo_edi_params'].search([('name', '=', 'CANTFAC_X_PAQUETE')]).value

            branch_office = self.getBranchOffice()[1].id_branch_office
            selling_point = self.getBranchOffice()[2].id_selling_point
            package_names = []

            first_pack_name = xml_package_path + "EMPAQUETADO_" + str(sin_date_time) + "_"+ str(branch_office) + "_" + str(selling_point) + ".tar.gz"
            package_names.append(first_pack_name)
            
            tar = tarfile.open(first_pack_name, 'w:gz')
            for root, dirs, files in os.walk(no_proc_invoices_path):
                for idx, file_name in enumerate(files, 1):
                    if current_inv_num.value <= inv_num_limit:
                        current_inv_num.write({"value" : int(current_inv_num.value) + 1}) 
                    else:
                        tar.close()
                        new_pack = xml_package_path + "EMPAQUETADO_" + self.req_sync_datetime() + "_"+ str(branch_office) + "_" + str(selling_point) + ".tar.gz"
                        tar = tarfile.open(new_pack, 'w:gz')
                        package_names.append(first_pack_name)
                        package_num.write({"value" : package_num.value + 1})
                        current_inv_num.write({"value" : '1'}) 
                    tar.add(os.path.join(root, file_name), arcname = "")
                    _logger.info("Ruta de No Proc Inv: " + no_proc_invoices_path + file_name)
                    _logger.info("Ruta de Proc Inv: " + proc_invoices_path + file_name)
                    os.replace(no_proc_invoices_path + file_name, proc_invoices_path + file_name)
            tar.close()
            current_inv_num.write({"value" : 1})                            
            
            # envío de paquete(s)
            for pack in package_names:
                zip = open(pack, 'rb')
                zip_content = zip.read()
                hashed_zip = self._get_file_hash(pack)
                zip.close()
                number_of_files = 0
                with tarfile.open(pack, "r") as tf:
                    number_of_files = len(tf.getmembers())

                send_package_res = self.req_send_package(
                    new_cufd[0].codigo, zip_content, hashed_zip, 0 , number_of_files , res_incident_sent)


                if send_package_res.codigoEstado != 901:
                    _logger.info("Package Rejected, Reason: " + send_package_res.mensajesList[0].descripcion + " Code: " + str(send_package_res.codigoEstado))
                    raise Warning("Package Rejected, Reason: " + send_package_res.mensajesList[0].descripcion + " Code: " + str(send_package_res.codigoEstado))
                else:
                    code_recept = send_package_res.codigoRecepcion
                    verify_package_res = self.req_verify_package(new_cufd[0].codigo, code_recept)

                    if verify_package_res.codigoEstado == 908:
                        print("PAQUETE ENVIADO")
                    else:
                        while verify_package_res.codigoEstado == 901:
                            time.sleep(30)
                            verify_package_res = self.req_verify_package(new_cufd[0].codigo, code_recept)
                        if verify_package_res.codigoEstado == 908:
                            print("PAQUETE ENVIADO")
                        else:
                            _logger.info("Package Verif Rejected, Reason: " + verify_package_res.mensajesList[0].descripcion + " Code: " + str(verify_package_res.codigoEstado))
                            raise Warning("Package Verif Rejected, Reason: " + verify_package_res.mensajesList[0].descripcion + " Code: " + str(verify_package_res.codigoEstado))
        
        else:
            print("Sin evento")

    def check_conectivity(self, manual = False):

        ###?? Validaciones generales

        self.total_discount = 0.0
        check_hom = 0
        check_internal = 0
        for item in self.invoice_line_ids: ##TODO parametrizar el nombre del item global_discount
            if (not item.product_id.measure_unit.measure_unit_code or not item.product_id.sin_item.sin_code or not item.product_id.sin_item.activity_code.code) and 'global_discount' not in item.product_id.name:
                check_hom = 1
        for item in self.invoice_line_ids: ##TODO parametrizar el nombre del item global_discount
            if (not item.product_id.default_code) and 'global_discount' not in item.product_id.name:
                check_internal = 1

        if check_hom: # Valida Homologacion de todos los productos
            raise Warning('One of the Invoice items is not homologated or does not have measure unit')
        if check_internal: # Valida Referencia interna
            raise Warning('One of the Invoice items does not have internal reference')
        if self.partner_id.l10n_bo_id_type.id_type_code != 1 and self.partner_id.complement:
            raise Warning('Complement field is only related to CI type ID, please change')
        if self.amount_total <= 0:
            raise Warning('Cannot send invoice with total amount 0')
        if self.invoice_mails == '':
            raise Warning("Field 'Correos a Enviar' must be filled")

        ###?? SET variables de comunicación

        sin_date_time = self.getTime().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

        emission_type_obj = self.env['bo_edi_params'].search(
            [('name', '=', 'TIPOEMISION')])

        status_obj = self.env['bo_edi_params'].search(
            [('name', '=', 'ONLINE')])
        current_status = int(status_obj.value)
        
        cert_status = int(self.env['bo_edi_params'].search( ## Variable de certificacion para cambio de estado Online/Offline
            [('name', '=', 'CERTSTATUS')]).value) 

        if cert_status:
            internet_status = self.env['sin_sync'].conexion()

            sin_ws_status = True
            if internet_status:

                sin_ws_status = self.env['sin_sync'].check_communication()

                if sin_ws_status.codigo == 926:
                    sin_ws_status = True
                    self.check_nit()
                    if self.getBranchOffice()[1] and self.getBranchOffice()[2]:
                        sin_date_time = self.req_sync_datetime()
                        if not manual: ## Validacion envío de paquete manuales
                            res_fill_codes = asyncio.run(self.set_bo_edi_info(sin_date_time, 1))
                            print(res_fill_codes)
                            if not res_fill_codes:
                                raise Warning("CUFD not retrieved, cannot send invoice")
                    else:
                        raise Warning('The current user doesn''t have branch office nor a selling point configured')
                else:
                    sin_ws_status = False
            else:
                sin_ws_status = False
        else:
            # internet_status = False
            # sin_ws_status = False
            internet_status = int(self.env['bo_edi_params'].search(
            [('name', '=', 'DEMO_INT_STATUS')]).value)
            sin_ws_status = int(self.env['bo_edi_params'].search(
            [('name', '=', 'DEMO_WS_STATUS')]).value)

        if sin_ws_status and internet_status:

            if current_status:

                ## FLUJO NORMAL
                return self.getheaderInvoiceData(1, sin_date_time)
                
            else:
                ## FIN DE SUCESO
                # current_status = True
                status_obj.write({"value" : 1})

                # Cambio de tipo de Emision
                emission_type_obj.write({"value" : 1})

                ##TODO Agregar condicion de misma fecha
                # current_incident = self.env['invoice_incident'].search(['&', (
                #                     'begin_date',
                #                     '=', 'end_date'),
                #                     ('sin_code',
                #                     '=', "")])
                # Busqueda de incidente
                current_incident = self.env['invoice_incident'].search(
                                    [('sin_code', '=', "")])

                if not manual:
                    current_incident.write({"end_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S")})

                # current_incident.write({"begin_date": "2022-06-13 15:00:05"})
                # current_incident.write({"end_date": "2022-06-13 15:05:10"})

                print(str(current_incident))

                if manual:
                    res_incident_sent = self._req_send_event(current_incident.invoice_event_id.code, current_incident.cufd_log_id.cufd,
                                                            self.get_last_CUFD().cufd , current_incident.description, current_incident.begin_date, current_incident.end_date )
                else:
                    res_incident_sent = self._req_send_event(current_incident.invoice_event_id.code, current_incident.cufd_log_id.cufd,
                                                            self.l10n_bo_cufd, current_incident.description, current_incident.begin_date, current_incident.end_date )

                if(str(res_incident_sent).strip() != "None"):
                    print(res_incident_sent)
                    current_incident.write({"sin_code" : str(res_incident_sent)})
                else:
                    raise Warning("There was an error sending the invoice event")

                ## ENVIO DE PAQUETE
                # rutas
                if manual:
                    no_proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTMAN_NOPROC')]).value
                    proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTMAN_PROC')]).value
                else:
                    no_proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTPAQ_NOPROC')]).value
                    proc_invoices_path = self.env['bo_edi_params'].search([('name', '=', 'FACTPAQ_PROC')]).value
                    
                xml_package_path = self.env['bo_edi_params'].search([('name', '=', 'EMPAQUETADO')]).value
                
                # params
                package_num = self.env['bo_edi_params'].search([('name', '=', 'CANTPAQUETES')])
                current_inv_num = self.env['bo_edi_params'].search([('name', '=', 'CANTACTUALFACTPAQ')])
                inv_num_limit = self.env['bo_edi_params'].search([('name', '=', 'CANTFAC_X_PAQUETE')]).value

                # if int(current_incident.invoice_event_id.code) >= 5:
                if manual:
                    cafc = self.env['bo_edi_params'].search([('name', '=', 'CAFC')]).value
                else:
                    cafc = 0

                # generación de paquete(s)
                branch_office = self.getBranchOffice()[1].id_branch_office
                selling_point = self.getBranchOffice()[2].id_selling_point
                package_names = []

                first_pack_name = xml_package_path + "EMPAQUETADO_" + str(sin_date_time) + "_"+ str(branch_office) + "_" + str(selling_point) + ".tar.gz"
                package_names.append(first_pack_name)
                
                tar = tarfile.open(first_pack_name, 'w:gz')
                for root, dirs, files in os.walk(no_proc_invoices_path):
                    for idx, file_name in enumerate(files, 1):
                        if current_inv_num.value <= inv_num_limit:
                            current_inv_num.write({"value" : int(current_inv_num.value) + 1}) 
                        else:
                            tar.close()
                            new_pack = xml_package_path + "EMPAQUETADO_" + self.req_sync_datetime() + "_"+ str(branch_office) + "_" + str(selling_point) + ".tar.gz"
                            tar = tarfile.open(new_pack, 'w:gz')
                            package_names.append(first_pack_name)
                            package_num.write({"value" : package_num.value + 1})
                            current_inv_num.write({"value" : '1'}) 
                        tar.add(os.path.join(root, file_name), arcname = "")
                        _logger.info("Ruta de No Proc Inv: " + no_proc_invoices_path + file_name)
                        _logger.info("Ruta de Proc Inv: " + proc_invoices_path + file_name)
                        os.replace(no_proc_invoices_path + file_name, proc_invoices_path + file_name)
                tar.close()
                current_inv_num.write({"value" : 1})                            
                
                # envío de paquete(s)
                for pack in package_names:
                    zip = open(pack, 'rb')
                    zip_content = zip.read()
                    hashed_zip = self._get_file_hash(pack)
                    zip.close()
                    number_of_files = 0
                    with tarfile.open(pack, "r") as tf:
                        number_of_files = len(tf.getmembers())

                    send_package_res = self.req_send_package(
                        self.l10n_bo_cufd, zip_content, hashed_zip, cafc , number_of_files , res_incident_sent)


                    if send_package_res.codigoEstado != 901:
                        _logger.info("Package Rejected, Reason: " + send_package_res.mensajesList[0].descripcion + " Code: " + str(send_package_res.codigoEstado))
                        raise Warning("Package Rejected, Reason: " + send_package_res.mensajesList[0].descripcion + " Code: " + str(send_package_res.codigoEstado))
                    else:
                        code_recept = send_package_res.codigoRecepcion
                        verify_package_res = self.req_verify_package(self.l10n_bo_cufd, code_recept)

                        if verify_package_res.codigoEstado == 908:
                            res_conectivity = self.check_conectivity()
                            if res_conectivity:
                                self.send_email_with_attachment(0)
                        else:
                            while verify_package_res.codigoEstado == 901:
                                time.sleep(30)
                                verify_package_res = self.req_verify_package(self.l10n_bo_cufd, code_recept)
                            if verify_package_res.codigoEstado == 908:
                                if manual:
                                    return True
                                else:
                                    res_conectivity = self.check_conectivity()
                                    if res_conectivity:
                                        self.send_email_with_attachment(0)
                            else:
                                _logger.info("Package Verif Rejected, Reason: " + verify_package_res.mensajesList[0].descripcion + " Code: " + str(verify_package_res.codigoEstado))
                                raise Warning("Package Verif Rejected, Reason: " + verify_package_res.mensajesList[0].descripcion + " Code: " + str(verify_package_res.codigoEstado))
                                
                    
        else:
            if self.partner_id.l10n_bo_id_type.id_type_code == 5:
                self.invalid_nit = True


            if manual:
                user_tz = pytz.timezone(self.env.context.get('tz' or self.env.user.tz))
                sin_date_time = pytz.utc.localize(self.manual_invoice_date).astimezone(user_tz)
                res_fill_codes = asyncio.run(self.set_bo_edi_info(sin_date_time, 2))
            else:
                res_fill_codes = asyncio.run(self.set_bo_edi_info(sin_date_time, 0))
                
            if not res_fill_codes:
                raise Warning("CUFD not retrieved, cannot send invoice")

            if current_status:
                ## INICIO DE SUCESO Y CREACION DE FACTURAS POR CONTINGENCIA

                # current_status = False ## Método para cambio de modo
                status_obj.write({"value" : 0})

                # Cambio de tipo de Emision
                emission_type_obj.write({"value" : 2})

                ## Creación suceso
                new_incident = {}
                # if not manual:
                if not internet_status:
                    new_incident = {
                        "invoice_event_id": 1,
                        "description": "Corte de Servicio de Internet",
                        "begin_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        "end_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        "selling_point_id": (self.getBranchOffice()[2]).id,
                        "incident_status_id": 1,
                        "sin_code": "",
                        "cufd_log_id": self.get_last_CUFD().id 
                    }
                elif not sin_ws_status:
                    new_incident = {
                        "invoice_event_id": 2,
                        "description": "Falla de Comunicación con Servicio Web de Impuestos",
                        "begin_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        "end_date": self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        "selling_point_id": (self.getBranchOffice()[2]).id,
                        "incident_status_id": 1,
                        "sin_code": "",
                        "cufd_log_id": self.get_last_CUFD().id 
                    }
                # else:
                #     new_incident = {
                #             "invoice_event_id": self.invoice_event_id.code,
                #             "description": self.invoice_event_id.description,
                #             "begin_date": self.event_begin_date.strftime("%Y-%m-%d %H:%M:%S"),
                #             "end_date": self.event_begin_date.strftime("%Y-%m-%d %H:%M:%S"),
                #             "selling_point_id": (self.getBranchOffice()[2]).id,
                #             "incident_status_id": 1,
                #             "sin_code": "",
                #             "cufd_log_id": self.get_last_CUFD().id 
                #         }
                self.env['invoice_incident'].create(new_incident)

            if not manual:
                self.is_offline = 1
                return self.getheaderInvoiceData(0, sin_date_time)
            else:
                self.is_manual = True
                return self.getheaderInvoiceData(2, sin_date_time)


    ########### EMAIL SEND W/ INVOICE XML & REPRESENTATION ################
    def send_email(self, reason_code, cuf, inv_number, email_to):
        ## set vars
        reason_name = self.env['cancellation_reasons'].search([('code', '=', reason_code)]).description
        
        ## Send Mail
        template = self.env['mail.template'].sudo().search([('name', '=', 'Anula Factura Electronica')], limit=1)
        if template:
            # email_values = {'email_to': email_to,
            #                 'email_from': 'noReply@alphasys.com.bo',
            #                 'reason_name': reason_name,
            #                 'cuf': cuf,
            #                 'inv_number': inv_number}

            email_values = {'email_to': email_to,
                            'email_from': 'noReply@alphasys.com.bo',
                            'subject': 'Factura Anulada',
                            'body_html': (F' <p>Su factura fue anulada correctamente</p>'
                                         F'<p>Detalles de Factura: </p>'
                                         F'<ul>'
                                            F'<li>FACTURA N°: {inv_number}</li>'
                                            F'<li>CÓD. AUTORIZACIÓN : {cuf}</li>'
                                            F'<li>RAZÓN SOCIAL: {reason_name}</li>'
                                        F'</ul>'
                                        F'<br/>'
                                        F'<p>------------------------------------------------------------</p>'
                                        F'<p>Recordarle que la presente cuenta no es administrada el correo fue enviado de manera'
                                        F'automática, favor de no responder al mismo.</p>')

                           }
            template.send_mail(self.id, email_values=email_values, force_send=True)
            return True


    def send_email_with_attachment(self, no_ws_inv = 0):
        ## set vars
        print("////////////////////////////////////////")
        print(self.page_break)
        self.generate_qr_code()
        if no_ws_inv:
            xml_path = self.env['bo_edi_params'].search(
                [('name', '=', 'FACTPAQ_NOPROC')]).value
        else:
            xml_path = self.env['bo_edi_params'].search(
                [('name', '=', 'XMLSIGNED')]).value
        # date_time = self.getTime().strftime("%Y-%m-%dT%H:%M")
        date_time = self.getTime().strftime("%Y-%m-%d")
        branch_office = self.getBranchOffice()[1].id_branch_office
        selling_point = self.getBranchOffice()[2].id_selling_point
        xml_name = str(date_time) + "_" + str(branch_office) + "_" + str(selling_point) + "_" + str(self.l10n_bo_invoice_number).zfill(4)
        report_template_id = self.env.ref(
            'l10n_bo_edi.invoice_report_pdf')._render_qweb_pdf(self.id)

        ## Attachments
        data_record_rep = base64.b64encode(report_template_id[0])
        ir_values_rep = {
            'name': "Factura Rep.pdf",
            'type': 'binary',
            'datas': data_record_rep,
            'store_fname': data_record_rep,
            'mimetype': 'application/x-pdf',
        }
        data_record_xml = self._XmlTobase64(xml_path + xml_name + '.xml')
        ir_values_xml = {
            'name': "Factura XML.xml",
            'type': 'binary',
            'datas': data_record_xml,
            'store_fname': data_record_xml,
            'mimetype': 'application/xml',
        }
        data_rep_id = self.env['ir.attachment'].create(ir_values_rep)
        data_xml_id = self.env['ir.attachment'].create(ir_values_xml)

        ## Send Mail
        template = self.env['mail.template'].sudo().search([('name', '=', 'Factura Electronica')], limit=1)
        if template:
            template.attachment_ids = [(6, 0, [data_rep_id.id, data_xml_id.id])]
            # email_values = {'email_to': self.partner_id.email,
            email_values = {'email_to': self.invoice_mails,
                            'email_from': 'noReply@alphasys.com.bo'}
            template.send_mail(self.id, email_values=email_values, force_send=True)
            # template.send_mail(self.id, force_send=True)
            template.attachment_ids = [(3, data_rep_id.id, data_xml_id.id)]
            return True

    ########### STANDARD BILLING ################

    def generate_control_code(self):
        if (self.journal_id.type == 'sale'):
            if self.dosage_id:
                auth_num = str(self.dosage_id['auth_number'])
                nit_client = str(self.partner_id.vat)
                inv_date = str(self.getTime().strftime("%Y%m%d"))
                total = str(round(self.amount_total))
                key = str(self.dosage_id['key'])
                inv_num = ''

                if self.reversed_inv_id:
                    inv_num = str(self.reversed_inv_id['invoice_num'])
                    self.reversed_inv_id['inv_reversed'] = True
                else:
                    inv_num = str(self.dosage_id['invoice_number'])
                    self.dosage_id['invoice_number'] += 1

                self.l10n_bo_invoice_number = inv_num
                self.auth_number = auth_num
                self.control_code = self.env['standard_billing'].controlCode(
                    auth_num, inv_num, nit_client, inv_date, total, key)
            else:
                raise Warning('You must select an invoice dosage')
        else:
            if self.with_tax:
                if not self.auth_number or not self.control_code or not self.l10n_bo_invoice_number:
                    raise Warning("You must fill the 'BO Information' fields")

    def action_post(self):
        if (self.journal_id.type == 'sale' or self.journal_id.type == 'purchase'):
            if self.inv_type: ## Si es factura de venta
                if self.e_billing: ## Si la modalidad es electronica...
                    # if self.is_drafted and not self.is_cancelled:
                    #     raise Warning("We cannot resend the current invoice, in order to resend it please cancel and confirm")
                    # else:
                    if not self.invoice_date:
                        raise Warning("The invoice date field is required")
                    if self.is_cancelled:
                        raise Warning("The current invoice has been cancelled, we cannot resend it to SIN")
                    else:
                        # if res_check_nit:
                        res_conectivity = self.check_conectivity()
                        if res_conectivity:
                            self.is_confirmed = True
                            current_status = int(self.env['bo_edi_params'].search(
                                    [('name', '=', 'ONLINE')]).value)
                            internet_status = int(self.env['bo_edi_params'].search(
                                    [('name', '=', 'DEMO_INT_STATUS')]).value)

                            if current_status:
                                self.send_email_with_attachment(0)
                            elif internet_status:
                                self.send_email_with_attachment(1)

                            self.print_report()
                        # else:
                        #     self.launch_warn_wizard()
                        #     print('test')
                            
                else: ## Si la modalidad es estandar
                    nit = self.partner_id.vat
                    currency_name = self.invoice_line_ids.mapped('sale_line_ids').order_id.pricelist_id.currency_id.name
                    if not nit:
                        raise Warning("There is no VAT/NIT for the client company")
                    else:
                        self.generate_control_code()
                        self.is_confirmed = True
                        self.print_report()
        super(AccountMove, self).action_post()

    ########### HELPERS ################

    def change_date_timezone(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz' or self.env.user.tz))
        return pytz.utc.localize(date_time).astimezone(user_tz)

    def parse_date(self, date_time):
        month = str(date_time.month) if len(str(date_time.month)) > 1 else '0' + str(date_time.month)
        day = str(date_time.day) if len(str(date_time.day)) > 1 else '0' + str(date_time.day)
        hour = str(date_time.hour) if len(str(date_time.hour)) > 1 else '0' + str(date_time.hour)
        minute = str(date_time.minute) if len(str(date_time.minute)) > 1 else '0' + str(date_time.minute)
        second = str(date_time.second) if len(str(date_time.second)) > 1 else '0' + str(date_time.second)
        return str(date_time.year) + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second

    def trigger_popup(self, type):
        print("entra")
        if type == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "popup_success_wizard",
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
            }
        else:
            return {
                "type": "ir.actions.act_window",
                "res_model": "popup_warn_wizard",
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
            }

    def numero_to_letras(self, numero):
        indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero)*100))
        contador = 0
        numero_letras = ""
        while entero >0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.convierte_cifra(a,1).strip()
            else :
                en_letras = self.convierte_cifra(a,0).strip()
            if a==0:
                numero_letras = en_letras+" "+numero_letras
            elif a==1:
                if contador in (1,3):
                    numero_letras = indicador[contador][0]+" "+numero_letras
                else:
                    numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
            else:
                numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)
        print(str(decimal))
        if len(str(decimal)) == 1:
            if str(decimal) == '0':
                numero_letras = numero_letras +" con " + str(decimal) + "0/100"
            else:
                numero_letras = numero_letras +" con 0" + str(decimal) + "/100"
        else:
            numero_letras = numero_letras +" con " + str(decimal) +"/100"
        print(numero_letras)
        return numero_letras

    def convierte_cifra(self,numero,sw):
        lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
        lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
                        ("VEINTE","VEINTI"),("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
                        ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
                        ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
                        ("NOVENTA" , "NOVENTA Y ")
                    ]
        lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
        centena = int (numero / 100)
        decena = int((numero -(centena * 100))/10)
        unidad = int(numero - (centena * 100 + decena * 10))
        #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
        texto_centena = ""
        texto_decena = ""
        texto_unidad = ""
        #Validad las centenas
        texto_centena = lista_centana[centena]
        if centena == 1:
            if (decena + unidad)!=0:
                texto_centena = texto_centena[1]
            else :
                texto_centena = texto_centena[0]
        #Valida las decenas
        texto_decena = lista_decena[decena]
        if decena == 1 :
            texto_decena = texto_decena[unidad]
        elif decena > 1 :
            if unidad != 0 :
                texto_decena = texto_decena[1]
            else:
                texto_decena = texto_decena[0]
        #Validar las unidades
        #print "texto_unidad: ",texto_unidad
        if decena != 1:
            texto_unidad = lista_unidad[unidad]
            if unidad == 1:
                texto_unidad = texto_unidad[sw]
        return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)

    def calculate_subtotal(self):
        inv_lines = self.getInvoiceItemsData(1)
        subtotal = 0
        if self.total_conv == 0.0 or self.manual_usd_edit:
            for i in inv_lines:
                item_subtotal = i.price_unit * i.quantity
                subtotal = subtotal + item_subtotal
            return [subtotal]
        else:
            subtotal_usd = 0
            for i in inv_lines:
                item_subtotal = round(i.price_unit * self.get_change_currency(), 2) * i.quantity
                subtotal = subtotal + item_subtotal
                item_subtotal_usd = i.price_unit * i.quantity
                subtotal_usd = subtotal_usd + item_subtotal_usd
            return [round(subtotal, 2), subtotal_usd ]

    def get_certstatus(self):
        record = int(self.env['bo_edi_params'].search( 
            [('name', '=', 'CERTSTATUS')]).value)
        return record


