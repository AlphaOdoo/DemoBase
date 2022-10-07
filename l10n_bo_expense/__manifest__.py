# -*- coding: utf-8 -*-
{
    'name': "Bolivia - Expenses",


    'description': """
        Long description of module's purpose
    """,

    'author': "Alphasys-Indasoge",
    'website': "http://www.alphasys.com.bo",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'expense',
    'version': '14.0.2.6',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense', 'contacts'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/hr_expense_views_inherit.xml',
        'views/hr_expense_views_tree_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
