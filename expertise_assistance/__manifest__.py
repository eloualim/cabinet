# -*- coding: utf-8 -*-
{
    'name': "Assistance Expertise",
    'summary': """
        Module d'assistance pour l'expertise""",

    'description': """
        Module Odoo pour gérer l'assistance dans les processus d'expertise.
    """,

    'author': "Votre Entreprise",
    'website': "https://www.votreentreprise.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services',
    'version': '18.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
        'prt_report_attachment_preview',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/expertise_assistance_views.xml',
        'views/insurance_company_views.xml',
        'views/medecin_views.xml',
        'views/avocat_views.xml',
        'views/tribunal_views.xml',
        'views/ville_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}