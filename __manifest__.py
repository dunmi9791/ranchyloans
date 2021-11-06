# -*- coding: utf-8 -*-
{
    'name': "ranchyloans",

    'summary': """
        This module is developed to manage the day to day activities of the ranchy co-operative society""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Secteur Networks",
    'website': "http://www.secteurnetworks.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'kpi_dashboard', 'hr',],

    # always loaded
    'data': [
        'wizard/collection.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/first_actions.xml',
        'views/views.xml',
        'views/menus.xml',
        'data/subtypes.xml',
        'views/templates.xml',
        'data/automation.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
