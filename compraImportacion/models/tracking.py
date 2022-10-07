from odoo import models, fields, api
from datetime import datetime
from pytz import timezone
from odoo.exceptions import UserError, ValidationError


class tracking(models.Model):
    _name = 'custom_purchase.tracking'
    _description = 'Tracking purchase'

    name = fields.Char(string='Identifier', required=True)

    number_guide = fields.Char(string='Nro Doc. Embarque', required=True)

    type_shipment = fields.Selection(string='Tipo embarque',
                                     selection=[('aerea', 'Aereo'),
                                                ('maritimo', 'Maritimo'),
                                                ('carretera', 'Carretero'),
                                                ('bimodal', 'Bimodal')],
                                     copy=False)

    date_exit_manufacturer = fields.Date(string='Fecha Salida Fabrica')

    date_estimated_arrival = fields.Date(string='Fecha Estimada Llegada')

    date_pickup = fields.Date(string='Fecha Llegada')

    shipping_date = fields.Date(string='Fecha Embarque')

    registration_date = fields.Datetime.now()
    #fields.Date(string='Fecha Registro',default= fields.Date.context_today)

    incoterms = fields.Selection(string = 'Incoterms',
                                 selection = [ ('cif','CIF'),
                                               ('cifddp','CIF/DDP'),
                                               ('fcaexw','FCA/EXW')])

    channel_custom = fields.Selection(string = 'Canal aduana',
                                      selection=[('rojo','Rojo'),
                                                 ('verde', 'Verde'),
                                                 ('amarillo','Amarillo')], copy=False)
    
    customs_clearance = fields.Boolean(string ='Desaduanizacion',default=False)
    
    forwarder_id = fields.Many2one(comodel_name='res.partner', string='Forwarder',
                                   ondelete='cascade',
                                   required=True,
                                   domain="[('isforwarder','=', True)]")
    
    state_tracking = fields.Selection(string = 'Estado seguimiento',
                                      selection=[('pickupfab','Pickup Fabrica'),
                                                 ('embarque','Embarque'),
                                                 ('arriboaduana','Arribo Aduana'),
                                                 ('naciona','Nacionalizacion'),
                                                 ('entregadestino','Entrega Almacen')],
                                                  default='pickupfab')

    active = fields.Boolean(string='Active', required=True, default=True)

    productsorder_ids = fields.Many2many(comodel_name='purchase.order.line',
                                   string='Ordenes de Compra productos', required=True,
                                   domain="[('state','=', 'purchase')]")

    weight_number_boxes = fields.Char(string='Peso o Cantidad de cajas', required=True)

    customs_warehouse = fields.Selection(string = 'Almacen Aduana',
                                      selection=[('DAB','DAB'),
                                                 ('ALBO','ALBO')])

    reception_part = fields.Char(string='Parte de Recepción N°', required=True)

    # reception_part = fields.Char(string='Nro Doc. Embarque', required=True)