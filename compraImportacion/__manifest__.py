# -*- coding: utf-8 -*-
{
    'name': "compraImportacion",

    'summary': """
        Módulo para compraImportacion""",

    'description': """
        Mostrar las capacidades de Odoo para crear nuevos
        modelos y sus vistas
    """,

    'author': "Company",
    'website': "http://www.mycompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'compraImportacion',
    'version': '0.6.0.1',

    # any module necessary for this one to work correctly
    'depends': ['contacts','product','account','purchase', 'stock'],

    # always loaded
    'data': [

        'security/ir.model.access.csv',
        'views/purchase_order_view_inherit.xml',
        'views/purchase_order_tree_view_inherit.xml',
        'views/purchase_order_kanban_view_inherit.xml',
        #'views/purchase_order_report_inherit.xml',
        'views/res_partners_view_inherit.xml',
        'views/templates.xml',
        'views/purchaseOL_view_inherit.xml',
        'views/custom_purchase_menu_items.xml',
        'views/tracking_views.xml',
        'views/stock_picking_view_inherit.xml',
        #'views/stock_picking_vpicktree_view_inherit.xml',
        #'report/mission_report_templates.xml'
    ],

    # only loaded in demonstration mode
    #'demo': [
    #   'demo/demo.xml',
    #],
    'installable': True,
    'application': True,
    'auto_install': False,
}
