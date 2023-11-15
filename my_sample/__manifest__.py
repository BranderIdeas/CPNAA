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
        'views/inicio_tramite_beneficio.xml',
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
        'views/inicio_mat_virtual.xml',
        'views/inicio_correccion.xml',
        'views/inicio_pactos.xml',
        'views/preguntas_mat_virtual.xml',
        'views/certificado_vigencia.xml',
        'views/consulta_registro.xml',
        'views/formulario_denuncia.xml',
        'views/formulario_pqrs.xml',
        'views/formulario_solicitud_correccion.xml',
        'views/detalle_denuncia.xml',
        'views/politica_datos.xml',
        'views/validacion_cert_de_vigencia.xml',
        'views/validacion_cert_de_vigencia_exterior.xml',
        'views/texto_advertencia_tramites.xml',
        'views/profile.xml',
        'views/calculadora.xml',
        'reports/cert_vigencia.xml',
        'reports/cert_vigencia_exterior.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'application': True,
    
}
