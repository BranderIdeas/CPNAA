# -*- coding: utf-8 -*-
{
    'name': "my_sample",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        App de Ejemplo
    """,

    'author': "Brander Ideas",
    'website': "http://www.branderideas.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/header_form_matricula.xml',
        'views/nav_bar_convenios.xml',
        'views/inicio_tramite.xml',
        'views/lista_tramites.xml',
        'views/inicio_convenios.xml',
        'views/convenios_archivo_csv.xml',
        'views/detalles_grado.xml',
        'views/form_convenio.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
