from odoo import http
import logging
from zeep import Client
from lxml import etree
import requests

_logger = logging.getLogger(__name__)

def sevenet_consulta(id_tramite, tipo_pago):
    tram_json = None
    url = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','URL SERVICIO SEVENET')]).x_value
    tramite = http.request.env['x_cpnaa_procedure'].browse(id_tramite)
    if tramite:
        tram_json = http.request.env['x_cpnaa_procedure'].sudo().search_read([('id','=',id_tramite)])[0]
    datos = """ 
            <datos>
            #tramite #nombre #apellido #numdocumento #ciudad #genero 
            #tipoinst #nombrinst #profesion #fechagrado #docminis 
            #residdirecc #residciudad #residindica #residtelefo #celular 
            #email #enviodirrec #enviocelula #envioindica #enviotelefo 
            #enviociudad #enviotelefo #enviociudad #medioelectr #autornombre 
            #adicionala #adicionalb #pqrdescrip #autordocume #tdepago #adjuntos
            </datos>
            """

    datos = datos.replace('#tramite','<tramite>%s</tramite>' % tramite.x_service_ID.x_abbreviation_name)
    datos = datos.replace('#nombre','<nombre>%s</nombre>' % tramite.x_studio_nombres)
    datos = datos.replace('#apellido','<apellido>%s</apellido>' % tramite.x_studio_apellidos)
    datos = datos.replace('#numdocumento','<numdocumento>%s</numdocumento>' % tramite.x_studio_documento_1)
    datos = datos.replace('#ciudad','<ciudad>%s</ciudad>' % tramite.x_studio_ciudad_1.id)
    datos = datos.replace('#genero','<genero>%s</genero>' % tramite.x_studio_gnero.x_name)
    datos = datos.replace('#tipoinst','<tipoinst>%s</tipoinst>' % tramite.x_studio_universidad_5.x_institution_type_ID.x_name)
    datos = datos.replace('#nombrinst','<nombreinst>%s</nombreinst>' % tramite.x_studio_universidad_5.x_name)
    datos = datos.replace('#profesion','<profesion>%s</profesion>' % tramite.x_studio_carrera_1.x_name)
    datos = datos.replace('#fechagrado','<fechagrado>%s</fechagrado>' % tramite.x_studio_fecha_de_grado_2.strftime('%Y%m%d'))
    datos = datos.replace('#docminis','<docminis>%s</docminis>' % '')
    datos = datos.replace('#residdirecc','<residdirecc>%s</residdirecc>' % tramite.x_studio_direccin)
    datos = datos.replace('#residciudad','<residciudad>%s</residciudad>' % tramite.x_studio_ciudad_1.id)
    datos = datos.replace('#residindica','<residindica>%s</residindica>' % '')
    datos = datos.replace('#residtelefo','<residtelefo>%s</residtelefo>' % tramite.x_studio_telfono)
    datos = datos.replace('#celular','<celular>%s</celular>' % tramite.x_user_celular)
    datos = datos.replace('#email','<email>%s</email>' % tramite.x_studio_correo_electrnico)
    datos = datos.replace('#enviodirrec','<enviodirrec></enviodirrec>')
    datos = datos.replace('#enviocelula','<enviocelula></enviocelula>')
    datos = datos.replace('#envioindica','<envioindica></envioindica>')
    datos = datos.replace('#enviotelefo','<enviotelefo></enviotelefo>')
    datos = datos.replace('#enviociudad','<enviociudad></enviociudad>')
    datos = datos.replace('#enviotelefo','<enviotelefo></enviotelefo>')
    datos = datos.replace('#enviociudad','<enviociudad></enviociudad>')
    datos = datos.replace('#medioelectr','<medioelectr>%s</medioelectr>' % tramite.x_elec_autorization)
    datos = datos.replace('#autornombre','<autornombre></autornombre>')
    datos = datos.replace('#adicionala','<adicionala></adicionala>')
    datos = datos.replace('#adicionalb','<adicionalb>%s</adicionalb>' % '')
    datos = datos.replace('#pqrdescrip','<pqrdescrip>%s</pqrdescrip>' % '')
    datos = datos.replace('#autordocume','<autordocume>%s</autordocume>' % '')
    datos = datos.replace('#tdepago','<tipodepago>%s</tipodepago>' % tipo_pago)
    
    docs_pdf = []
    for key in tram_json:
        if type(tram_json[key]) == bytes and key_to_name(key):
            documento = '<documento> #documento </documento>'
            nombre_original = '<nombreoriginal>%s%s.pdf</nombreoriginal>' % (key_to_name(key), tramite.x_studio_documento_1)
            cuerpo = '<cuerpo>%s</cuerpo>' % str(tram_json[key])[2:-1]
            documento = documento.replace('#documento','%s %s' % (nombre_original, cuerpo))
            docs_pdf.append(documento)
    
    adjuntos = '<adjuntos> #documentos </adjuntos>'
    adjuntos = adjuntos.replace('#documentos',' '.join(docs_pdf))
    
    datos = datos.replace('#adjuntos',adjuntos)
    client = Client(url)
    resp = client.service.Registrar(datos)
    _logger.info(datos)

    root = etree.XML(resp)
    body = etree.SubElement(root, "textoRespuesta")

    radicado = 0
    mensaje_respuesta = root.xpath("//text()")[1]
    codigo_respuesta  = int(root.xpath("//text()")[0])
    if codigo_respuesta == 0:
        radicado = int(mensaje_respuesta[10:].split('-')[0])
    else:
        _logger.info('Error al radicar en sevenet: %s' % mensaje_respuesta)
    return radicado


# Reemplaza la key del diccionario por el nombre que se va a guardar en sevenet
def key_to_name(key):
    names = {
        'x_studio_documento': 'DOCUMENTO-',
        'x_studio_imagen_diploma': 'DIPLOMA-',
        'x_min_convalidation_pdf': 'DOC-MIN-EDUC-',
#         'x_studio_acreditacin_de_profesin_en_el_extranjero': 'ACRED-PROF-EXTR-',
#         'x_studio_certificado_de_existencia_empresa_contratante': 'CERT-EXIS-EMPR-CONT-',
#         'x_studio_experiencia_profesional_acreditada': 'EXP-PROF-ACRED-',
#         'x_studio_imgen_de_diploma_apostillado': 'IMG-DIPLOMA-APOST-',
#         'x_studio_solicitud_empresa_contratante': 'SOLIC-EMPR-CONT-',
    }
    return names.get(key, False)
