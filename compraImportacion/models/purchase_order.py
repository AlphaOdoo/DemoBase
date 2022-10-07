from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import stripped_sys_argv


class OrdenCompra(models.Model):
    _inherit="purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    nro_order = fields.Char(string='Número de Orden de Compra', required=False,index=True, copy=False, states=READONLY_STATES)
                   
    # partner_forwarder = fields.Many2one('res.partner', 
    #                                 string='Forwarder', 
    #                                 required=False, 
    #                                 change_default=True, 
    #                                 tracking=True, 
    #                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", 
    #                                 help="You can find a Forwarder by its Name, TIN, Email or Internal Reference.")
    
    partner_forwarder = fields.Many2one(comodel_name='res.partner', string='Forwarder',
                                   ondelete='cascade',
    #                               required=True,
                                   domain="[('isforwarder','=', True)]")

    requested_type_ncr = fields.Selection(string= 'Tipo de Orden de Compra',
                                    selection=[('NCR equipos','NCR Equipos'),
                                                ('NCR software','NCR Software'),
                                                ('otros','Importacion'),
                                                ('local','Local'),
                                                ('interna','Interna')],
                                    copy=False, default='interna',
                                    states=READONLY_STATES)

    active = fields.Boolean(string='Active', required=True, 
                              default=True)

    sale_order = fields.Many2one(comodel_name='sale.order', string='Orden de Venta',
                                   ondelete='cascade',
                                   states=READONLY_STATES
    #                               required=True,
    #                               domain="[('isforwarder','=', True)]"
                                   )


    # @api.onchange('requested_type_ncr')
    # def _onchange_partner(self):
    #     # if(self.requested_type_ncr == 'NCR equipos'):
    #     #     orders = self.env['purchase.order'].search([('requested_type_ncr', '=', 'NCR equipos'),('nro_order', 'not like', '-5')], order='nro_order desc',limit=1,)
    #     # elif(self.requested_type_ncr == 'NCR software'):
    #     #     orders = self.env['purchase.order'].search([('requested_type_ncr', '=', 'NCR software'),('nro_order', 'like', '-5')], order='nro_order desc',limit=1,)
    #     # elif(self.requested_type_ncr == 'local'):
    #     #     orders = self.env['purchase.order'].search([('requested_type_ncr', '=', 'local'),('nro_order', 'like', 'OL')], order='nro_order desc',limit=1,)
    #     # elif(self.requested_type_ncr == 'interna'):
    #     #     orders = self.env['purchase.order'].search([('requested_type_ncr', '=', 'interna'),('nro_order', 'like', 'OI')], order='nro_order desc',limit=1,)
    #     # else:
    #     #     orders = self.env['purchase.order'].search([('requested_type_ncr', '=', 'otros'),('nro_order', 'not like', '7115'),('nro_order', 'not like', 'OL'),('nro_order', 'not like', 'OI')], order='nro_order desc',limit=1,)
        


    #     #el orders es el que obtiene el ultimo valor registrado, ese hay que reemplazarlo por el codigo quemado
        


    #     # self.nro_order = orders.nro_order
    #     # orders = self.env['purchase.order'].search([], order='nro_order desc',limit=1)
    #     if (orders.requested_type_ncr == 'NCR equipos'):
    #         if(orders.nro_order != False):
    #             num=orders.nro_order[10:14]
    #         else:
    #             num='0000'
    #     elif (orders.requested_type_ncr == 'NCR software'):
    #         if(orders.nro_order != False):
    #             num=orders.nro_order[11:14]
    #         else:
    #             num='000'
    #     elif (orders.requested_type_ncr == 'local'):
    #         if(orders.nro_order != False):
    #             num=orders.nro_order[8:12]
    #         else:
    #             num='000'
    #     elif (orders.requested_type_ncr == 'interna'):
    #         if(orders.nro_order != False):
    #             num=orders.nro_order[8:12]
    #         else:
    #             num='000'
    #     else:
    #         if(orders.nro_order != False):
    #             num=orders.nro_order[5:9]
    #         else:
    #             num='0000'
    #     #     #num='001'
    #     #self.nro_order = num
    #     sequence = int(num)
    #     #self.nro_order = num

    #     # Obtiene Codigo prefijo segun tipo compra
    #     if self.requested_type_ncr == 'NCR equipos':
    #         initvalue = sequence
    #         incrementedSufix = initvalue + 1
    #         prefixinitnum = '0'
    #         #Genera año
    #         from datetime import datetime
    #         now = datetime.now()
    #     # Obtiene Codigo prefijo segun proveedorime.now()
    #         year = now.year
    #         if incrementedSufix < 10:
    #             prefixnumber = prefixinitnum +'00' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(10,99):
    #             prefixnumber = prefixinitnum + '0' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(100,999):
    #             prefixnumber = prefixinitnum 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(1000,9999):
    #             incrementedSufix = str(incrementedSufix)
    #         # if incrementedSufix in range(10000,99999):
    #         #     prefixnumber = prefixinitnum + '00'
    #         #     incrementedSufix = prefixnumber+str(incrementedSufix)
    #         # if incrementedSufix in range(100000,999999):
    #         #     prefixnumber = prefixinitnum + '0'
    #         #     incrementedSufix = prefixnumber+str(incrementedSufix)
    #         # if incrementedSufix in range(1000000,9999999):
    #         #     prefixnumber = prefixinitnum 
    #         #     incrementedSufix = prefixnumber+str(incrementedSufix)
    #         #Genera prefijo NCR 
    #         NCRPrefix = '7115'
    #         self.nro_order = NCRPrefix + '-' + str(year) + '-' + str(incrementedSufix)
    #     elif self.requested_type_ncr == 'NCR software':
    #         initvalue = sequence
    #         incrementedSufix = initvalue + 1
    #         prefixinitnum = '0'
    #         #Genera año
    #         from datetime import datetime
    #         now = datetime.now()
    #         year = now.year
    #         if incrementedSufix < 10:
    #             prefixnumber = prefixinitnum +'0' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(10,99):
    #             prefixnumber = prefixinitnum 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         # if incrementedSufix in range(100,999):
    #         #     prefixnumber = prefixinitnum 
    #         #     incrementedSufix = prefixnumber+str(incrementedSufix)
    #         #Genera prefijo NCR 
    #         NCRPrefix = '7115'
    #         self.nro_order = NCRPrefix + '-' + str(year) + '-5' + str(incrementedSufix)
    #     elif self.requested_type_ncr == 'local':
    #         initvalue = sequence
    #         incrementedSufix = initvalue + 1
    #         prefixinitnum = '0'
    #         #Genera año
    #         from datetime import datetime
    #         now = datetime.now()
    #         year = now.year
    #         if incrementedSufix < 10:
    #             prefixnumber = prefixinitnum +'00' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(10,99):
    #             prefixnumber = prefixinitnum + '0' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(100,999):
    #             prefixnumber = prefixinitnum 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(1000,9999):
    #             incrementedSufix = str(incrementedSufix)
    #         #Genera prefijo NCR 
    #         NCRPrefix = 'OL'
    #         self.nro_order = NCRPrefix + '-' + str(year) + '-' + str(incrementedSufix)
    #     elif self.requested_type_ncr == 'interna':
    #         initvalue = sequence
    #         incrementedSufix = initvalue + 1
    #         prefixinitnum = '0'
    #         #Genera año
    #         from datetime import datetime
    #         now = datetime.now()
    #         year = now.year
    #         if incrementedSufix < 10:
    #             prefixnumber = prefixinitnum +'00' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(10,99):
    #             prefixnumber = prefixinitnum + '0' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(100,999):
    #             prefixnumber = prefixinitnum 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(1000,9999):
    #             incrementedSufix = str(incrementedSufix)
    #         #Genera prefijo NCR 
    #         NCRPrefix = 'OI'
    #         self.nro_order = NCRPrefix + '-' + str(year) + '-' + str(incrementedSufix)
    #     else:
    #         initvalue = sequence
    #         #Genera año
    #         from datetime import datetime
    #         now = datetime.now()
    #         year = now.year
    #         #Genera sufijo autoincremental
    #         incrementedSufix = initvalue + 1
    #         prefixinitnum = '0'
    #         if incrementedSufix < 10:
    #             prefixnumber = prefixinitnum +'00' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(10,99):
    #             prefixnumber = prefixinitnum + '0' 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(100,999):
    #             prefixnumber = prefixinitnum 
    #             incrementedSufix = prefixnumber+str(incrementedSufix)
    #         if incrementedSufix in range(1000,9999):
    #             incrementedSufix = str(incrementedSufix)
    #         self.nro_order = str(year) + '-' + incrementedSufix
    