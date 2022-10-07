# -*- coding: utf-8 -*-
{
    'name': "custom-crm",

    'summary': """
        Modulo que permite la personalización:
        -	Uso de doble moneda Bs principal y secundaria Dólar en CRM
        -	Crear un Sale Order en Oportuniad en base a ur archivo excel

        """,

    "description": """
        Modulo que permite la personalización del CRM y formulario de Oportunidad:
        -	Habilita en Pantalla la doble moneda dentro de CRM moneda Bs como principal y secundaria Dólar.
        -	Desde la pantalla de oportunidad se habilita un botón para creación de un Sale Order en base a un archivo EXCEL (XLSX)
        -   Desde pantalla de orden venta (Sale Oder) habilita boton para importar productos
    """,

    'author': "ALPHA SYSTEMS - Indasoge",
    'website': "http://www.alphasys.com.bo",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': "CRM",
    'version': '14.0.0.22.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'sale_management', 'web', 'crm', 'account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views_inherit.xml',
        'views/sale_order_line_views_inherit.xml',
        'views/purchase_order_line_views_inherit.xml',
        'views/purchase_order_views_inherit.xml',
        'views/crm_lead_views_inherit.xml',
        'views/import_bc.xml',
        'wizards/import_orderline_wizard.xml',
        'wizards/import_purchase_orderline_wizard.xml',
        'wizards/import_purchase_order.xml',
        'wizards/import_sale_order.xml',
    ],
    'qweb': ['static/src/xml/import_cmd.xml'],
    'images': ['static/description/banner.jpg'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
