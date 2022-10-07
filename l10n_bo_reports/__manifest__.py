# -*- coding: utf-8 -*-
{
    'name': """Bolivia - Accounting Reports""",

    'description': """
        This code allows to generate all reports related to Bolivian
        accounting
    """,

    'author': "Indasoge-Alphasys",
    'website': "http://www.alphasys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations',

    'version': '14.0.7.8',


    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_bo_edi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/action_manager.xml',
        'wizard/sales_book_wizard_view.xml',
        'wizard/purchase_book_wizard_view.xml',
        'wizard/sales_banking_wizard_view.xml',
        'wizard/bankbook_wizard_view.xml',
        'views/account_report_menuitems.xml',
        'reports/sales_book.xml',
        'reports/sales_book_templates.xml',
        'reports/accountentry_report.xml',
        'reports/accountentry_report_templates.xml',
        #'views/account_move_view_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
