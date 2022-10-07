# -*- coding: utf-8 -*-
{
    'name': "Bolivia - RRHH",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Alpha Systems S.R.L.",
    'website': "http://www.alphasystems.com.bo",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.4.2',

    # any module necessary for this one to work correctly
    'depends': ['hr_payroll', 'hr_contract', 'hr_holidays', 'base', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/hr_employee_views_inherit.xml',
        'views/hr_contract_views_inherit.xml',
        # 'views/hr_payslip_run_view_inherit.xml',
        'views/payroll_ministry.xml',
        'views/payroll_afp.xml',
        'views/payroll_rciva.xml',
        'views/action_manager.xml',
        'views/consumo_regla.xml',
        'views/consumo_regla_template.xml',
        # 'views/rciva_form_view.xml',
        # 'reports/graphic_representation.xml',
        # 'reports/graphic_representation_templates.xml',
        'reports/paymentslip_report.xml',
        'reports/paymentslip_report_templates.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
