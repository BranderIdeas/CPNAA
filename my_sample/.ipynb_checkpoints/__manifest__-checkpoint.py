# -*- coding: utf-8 -*-
{
    'name': "CPNAA",

    'summary': """
        Modulo de la oficina virtual del CPNAA""",

    'description': """
        App del CPNAA
    """,

    'author': "Brander Ideas",
    'website': "http://www.branderideas.com",

    'category': 'Extra Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/textos_tramite.xml',
        'views/nav_bar_convenios.xml',
        'views/inicio_tramite.xml',
        'views/lista_tramites.xml',
        'views/inicio_convenios.xml',
        'views/convenios_archivo_csv.xml',
        'views/convenios_definitivo_pdf.xml',
        'views/convenios_grado_actas.xml',
        'views/detalles_grado.xml',
        'views/formulario_tramites.xml',
        'views/template_pdf.xml',
        'views/epayco.xml',
        'views/titulo_tramites.xml',
        'views/epayco_confirmacion.xml',
        'views/inicio_cert_vigencia.xml',
        'views/certificado_vigencia.xml',
        'views/consulta_registro.xml',
        'views/formulario_denuncia.xml',
        'views/formulario_pqrd.xml',
        'views/politica_datos.xml',
        'views/validacion_cert_de_vigencia.xml',
        'reports/cert_vigencia.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'application': True,
    
}
