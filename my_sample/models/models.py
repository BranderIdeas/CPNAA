# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import http
from datetime import date, datetime, timedelta, timezone
from zeep import Client
from lxml import etree

import re
import base64
import requests
import logging
import json
    
_logger = logging.getLogger(__name__)

class my_sample(models.Model):
    _name = 'cpnaa.webservices'
    _description = 'WEBSERVICES CPNAA'
    
    x_name        = fields.Char('Nombre')
    x_url_service = fields.Char('Url del servicio')

    def endpoint_epayco(self, url, ref_payco):
        response = requests.get(url + ref_payco)
        if response.json():
            return response.json()
        else:
            return 'No existe información para referencia: %s' % ref_payco
        
        
    # SEVENET
    def sevenet_tramite(self, id_tramite, tipo_pago):
        ahora = datetime.now() - timedelta(hours=5)
        hoy   = ahora.date()
        tram_json = None
        n_folios  = 0
        url       = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','URL SERVICE ORFEO')]).x_value
        user      = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','USER ORFEO')]).x_value
        password  = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','PASS ORFEO')]).x_value
        key       = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','KEY ORFEO')]).x_value
        user_xml  = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','USER ORFEO XML')]).x_value
        cod_app   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','COD APP ORFEO')]).x_value
        auth_type = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','AUTH TYPE ORFEO')]).x_value
        
        headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'login': user,
        'password': password,
        'key': key
        }

        tramite = http.request.env['x_cpnaa_procedure'].browse(id_tramite)
        
        if tramite:
            tram_json = http.request.env['x_cpnaa_procedure'].sudo().search_read([('id','=',id_tramite)])[0]
            for key in tram_json:
                if type(tram_json[key]) == bytes and self.key_to_name(key):
                    n_folios += 1
    
        datos = """
            <cod_app>"""+cod_app+"""</cod_app>
            <authType>"""+auth_type+"""</authType>
            <userOrfeo>"""+user_xml+"""</userOrfeo>
            <TipoTercero>1</TipoTercero>
            #NombreTercero
            #PrimerApellidoTercero
            <SegundoApellidoTercero></SegundoApellidoTercero>
            #TipoIDTercero
            #NumeroIDTercero
            #CorreoElectronicoTercero
            #DireccionTercero
            #Internacionalizacion
            #Telefono
            <MedioRecep>3</MedioRecep>
            #AsuntoRadicado
            #FechaOficioRadicado
            #trd
            <dignatario></dignatario>
            #Folios
            <causal></causal>
            <tipo_radicado>2</tipo_radicado>
            <radi_desc_anex>Soporte anexo al tramite</radi_desc_anex>
            #cuenta_referencia
            #archivo
            #nombreArchivo
        """

        datos = datos.replace('#NombreTercero','<NombreTercero>%s</NombreTercero>' % tramite.x_studio_nombres)
        datos = datos.replace('#PrimerApellidoTercero','<PrimerApellidoTercero>%s</PrimerApellidoTercero>' % tramite.x_studio_apellidos)
        datos = datos.replace('#TipoIDTercero','<TipoIDTercero>%s</TipoIDTercero>' % tramite.x_studio_tipo_de_documento_1.x_orfeo_code)
        datos = datos.replace('#NumeroIDTercero','<NumeroIDTercero>%s</NumeroIDTercero>' % tramite.x_studio_documento_1)
        datos = datos.replace('#CorreoElectronicoTercero','<CorreoElectronicoTercero>%s</CorreoElectronicoTercero>' % tramite.x_studio_correo_electrnico)
        datos = datos.replace('#DireccionTercero','<DireccionTercero>%s</DireccionTercero>' % tramite.x_studio_direccin)
        datos = datos.replace('#Telefono','<Telefono>%s</Telefono>' % tramite.x_user_celular)
        datos = datos.replace('#Internacionalizacion', self.get_internacionalizacion(tramite))
        datos = datos.replace('#AsuntoRadicado','<AsuntoRadicado>Solicitud - %s - %s</AsuntoRadicado>' % (self.replace_tildes(tramite.x_service_ID.x_name), tipo_pago))
        datos = datos.replace('#FechaOficioRadicado','<FechaOficioRadicado>%s</FechaOficioRadicado>' % hoy.strftime('%Y-%m-%d'))
        datos = datos.replace('#trd','<trd>%s</trd>' % tramite.x_service_ID.x_orfeo_code)
        datos = datos.replace('#Folios','<folios>%s</folios>' % n_folios)
        datos = datos.replace('#cuenta_referencia','<cuenta_referencia>%s</cuenta_referencia>' % tramite.id)
        
        if type(tram_json['x_studio_documento']) == bytes and self.key_to_name('x_studio_documento'):
            nombreArchivo = '<nombreArchivo>%s%s.pdf</nombreArchivo>' % (self.key_to_name('x_studio_documento'), tramite.x_studio_documento_1)
            archivo       = '<archivo>%s</archivo>' % str(tram_json['x_studio_documento'])[2:-1]
            datos = datos.replace('#archivo', archivo)
            datos = datos.replace('#nombreArchivo', nombreArchivo)
        else:
            datos = datos.replace('#archivo', '<archivo>?</archivo>')
            datos = datos.replace('#nombreArchivo', '<nombreArchivo>?</nombreArchivo>')
            
        payload = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:Orfeo">
            <soapenv:Header/>
            <soapenv:Body>
                <urn:crearRadicado>"""+datos+"""
                </urn:crearRadicado>
            </soapenv:Body>
        </soapenv:Envelope>
        """
    
        encode_payload = payload.encode('UTF-8')
        _logger.info(encode_payload)

        response = requests.request("POST", url, headers=headers, data=encode_payload)
       
        _logger.info(response.status_code)
        _logger.info(response.text)
        
        radicado = 0  
        if response.status_code == 200:
            xmlResp = (response.text).replace('<?xml version="1.0" encoding="ISO-8859-1"?>','')
            root = etree.XML(xmlResp)
            contentResp = root.xpath("//text()")[0]
            _logger.info(contentResp)
            radicado = contentResp[17:31]
            _logger.info(radicado)
            radicado_valido = self.validar_radicado_orfeo(radicado)
            
            if not radicado_valido:
                radicado = 0
            
            if n_folios > 1 and radicado_valido:
                user_radicador = base64.b64decode(user).decode('utf-8')
                payload = """
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:Orfeo">
                    <soapenv:Header/>
                    <soapenv:Body>
                    <urn:anexarArchivosMasiva>
                    <cod_app>2</cod_app>
                    <authType>3</authType>
                    <nurad>"""+radicado+"""</nurad>
                    <usrRadicador>"""+user_radicador+"""</usrRadicador>
                    #adjuntos
                    </urn:anexarArchivosMasiva>
                    </soapenv:Body>
                </soapenv:Envelope>
                """

                adjuntosReplace = ''
                countFiles = 0
                for key in tram_json:
                    if type(tram_json[key]) == bytes and self.key_to_name(key) and key != 'x_studio_documento':
                        num = str(countFiles)
                        nombreArchivo = '<nombreArchivo%s>%s%s.pdf</nombreArchivo%s>' % (num, self.key_to_name(key), tramite.x_studio_documento_1, num)
                        archivo = '<archivo%s>%s</archivo%s>' % (num, str(tram_json[key])[2:-1], num)
                        adjuntosReplace += nombreArchivo+'\n'+archivo+'\n'
                        countFiles += 1

                maxFiles = 10
                numRange = maxFiles - (countFiles)
                for idx in range(numRange):
                    num = idx+(countFiles)
                    nombreArchivo = '<nombreArchivo%s></nombreArchivo%s>' % (num, num)
                    archivo = '<archivo%s></archivo%s>' % (num, num)
                    adjuntosReplace += nombreArchivo+'\n'+archivo+'\n'

                payload = payload.replace('#adjuntos',adjuntosReplace)
                _logger.info(payload)

                response = requests.request("POST", url, headers=headers, data=payload)
                if response.status_code == 200:
                    xmlResp = (response.text).replace('<?xml version="1.0" encoding="ISO-8859-1"?>','')
                    root = etree.XML(xmlResp)
                    contentResp = root.xpath("//text()")[0]
                    _logger.info(contentResp)
                else:
                    _logger.info('Error al tratar de anexar archivos masivamente, radicado nro %s' % radicado)

        return radicado

    def sevenet_denuncia(id_tramite):
        pruebas_pdf = None
        pruebas_img = None
        url = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','URL SERVICIO SEVENET')]).x_value
        tramite = http.request.env['x_cpnaa_complaint'].browse(id_tramite)
        if tramite:
            pruebas_pdf = http.request.env['x_evidence_files_pdf'].sudo().search_read([('x_complaint_ID','=',id_tramite)])
            pruebas_img = http.request.env['x_evidence_files_img'].sudo().search_read([('x_complaint_ID','=',id_tramite)])
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
        datos = datos.replace('#nombre','<nombre>%s</nombre>' % tramite.x_complainant_names)
        datos = datos.replace('#apellido','<apellido>%s</apellido>' % tramite.x_complainant_lastnames)
        datos = datos.replace('#numdocumento','<numdocumento>%s</numdocumento>' % tramite.x_complainant_document)
        datos = datos.replace('#ciudad','<ciudad>%s</ciudad>' % '')
        datos = datos.replace('#genero','<genero>%s</genero>' % '')
        datos = datos.replace('#tipoinst','<tipoinst>%s</tipoinst>' % '')
        datos = datos.replace('#nombrinst','<nombreinst>%s</nombreinst>' % '')
        datos = datos.replace('#profesion','<profesion>%s</profesion>' % '')
        datos = datos.replace('#fechagrado','<fechagrado>%s</fechagrado>' % '')
        datos = datos.replace('#docminis','<docminis>%s</docminis>' % '')
        datos = datos.replace('#residdirecc','<residdirecc>%s</residdirecc>' % tramite.x_complainant_address)
        datos = datos.replace('#residciudad','<residciudad>%s</residciudad>' % tramite.x_complainant_city_ID.id)
        datos = datos.replace('#residindica','<residindica>%s</residindica>' % '')
        datos = datos.replace('#residtelefo','<residtelefo>%s</residtelefo>' % tramite.x_complainant_phone)
        datos = datos.replace('#celular','<celular>%s</celular>' % tramite.x_complainant_celular)
        datos = datos.replace('#email','<email>%s</email>' % tramite.x_complainant_email)
        datos = datos.replace('#enviodirrec','<enviodirrec></enviodirrec>')
        datos = datos.replace('#enviocelula','<enviocelula></enviocelula>')
        datos = datos.replace('#envioindica','<envioindica></envioindica>')
        datos = datos.replace('#enviotelefo','<enviotelefo></enviotelefo>')
        datos = datos.replace('#enviociudad','<enviociudad></enviociudad>')
        datos = datos.replace('#enviotelefo','<enviotelefo></enviotelefo>')
        datos = datos.replace('#enviociudad','<enviociudad></enviociudad>')
        datos = datos.replace('#medioelectr','<medioelectr>%s</medioelectr>' % '')
        datos = datos.replace('#autornombre','<autornombre></autornombre>')
        datos = datos.replace('#adicionala','<adicionala>%s</adicionala>' % 'queja')
        datos = datos.replace('#adicionalb','<adicionalb>%s</adicionalb>' % 'pqrd')
        datos = datos.replace('#pqrdescrip','<pqrdescrip>%s</pqrdescrip>' % tramite.x_name)
        datos = datos.replace('#autordocume','<autordocume>%s</autordocume>' % '')
        datos = datos.replace('#tdepago','<tipodepago>%s</tipodepago>' % '')

        docs = []
        for prueba in pruebas_pdf:
            _logger.info(prueba['x_file'])
            documento = '<documento> #documento </documento>'
            nombre_original = '<nombreoriginal>%s.pdf</nombreoriginal>' % prueba['x_name']
            cuerpo = '<cuerpo>%s</cuerpo>' % str(prueba['x_file'])[2:-1]
            documento = documento.replace('#documento','%s %s' % (nombre_original, cuerpo))
            docs.append(documento)
        for prueba in pruebas_img:
            documento = '<documento> #documento </documento>'
            nombre_original = '<nombreoriginal>%s.%s</nombreoriginal>' % (prueba['x_name'], prueba['x_extention'])
            cuerpo = '<cuerpo>%s</cuerpo>' % str(prueba['x_file'])[2:-1]
            documento = documento.replace('#documento','%s %s' % (nombre_original, cuerpo))
            _logger.info(cuerpo)
            docs.append(documento)

        adjuntos = '<adjuntos> #documentos </adjuntos>'
        adjuntos = adjuntos.replace('#documentos',' '.join(docs))

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
    def key_to_name(self, key):
        names = {
            'x_studio_documento': 'DOCUMENTO-',
            'x_studio_imagen_diploma': 'DIPLOMA-',
            'x_min_convalidation_pdf': 'DOC-MIN-EDUC-',
            'x_studio_acreditacin_de_profesin_en_el_extranjero': 'ACRED-PROF-EXTR-',
            'x_studio_certificado_de_existencia_empresa_contratante': 'CERT-EXIS-EMPR-CONT-',
            'x_studio_experiencia_profesional_acreditada': 'EXP-PROF-ACRED-',
            'x_studio_imgen_de_diploma_apostillado': 'IMG-DIPLOMA-APOST-',
            'x_studio_solicitud_empresa_contratante': 'SOLIC-EMPR-CONT-',
        }
        return names.get(key, False)
    
    # Realiza la petición del token
    def epayco_login(self, url, payload, headers):
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()['token']
    
    # Realiza la petición de las transacciones aceptadas
    def epayco_aceptadas(self, url, payload, headers):
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.json()
    
    # Realiza la petición de las transacciones aceptadas en las ultimas 24 horas
    def epayco_detalle(self, url, payload, headers):  
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.json()
    
    # Realiza el envio del certificado con vigencia con destino al exterior por email 
    def enviar_certificado_email(self, certificado):
        _logger.info(certificado)
        template_obj = http.request.env['mail.template'].sudo().search_read([('name','=','x_cpnaa_template_certificate_exterior_attachment')])[0]
        cert_at = http.request.env['ir.attachment'].sudo().create({
            'name': 'cert-vig-prof-dest-ext-%s.pdf' % certificado.x_document_number,
            'type': 'binary',
            'datas': certificado.x_signed_document,
            'mimetype': 'application/x-pdf'
        })
        if template_obj:
            body = template_obj['body_html']
            mail_values = {
                'subject': template_obj['subject'],
                'attachment_ids': [cert_at.id],
                'body_html': body,
                'email_to': certificado.x_email,
                'email_from': template_obj['email_from'],
           }
        try:
            http.request.env['mail.mail'].sudo().create(mail_values).send()
            return {'ok': True, 'mensaje': 'Certificado enviado exitosamente'}
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'mensaje': 'No se podido completar su solicitud'}

    def validar_radicado_orfeo(self, radicado):
        regex = '^[0-9]*$'
        if(re.search(regex, radicado)) and len(radicado) == 14:  
            return True
        else:
            return False
        
    def get_internacionalizacion(self, tramite):
        city = tramite.x_studio_ciudad_1.x_name
        dpto = tramite.x_studio_departamento_estado.x_name
        is_bogota = dpto == 'CUNDINAMARCA' and city == 'BOGOTA D.C.'
        city_orfeo = tramite.x_studio_ciudad_1.x_orfeo_code
        dpto_orfeo = '11' if is_bogota else tramite.x_studio_departamento_estado.x_orfeo_code
        return '<Internacionalizacion>1-170-%s-%s</Internacionalizacion>' % (dpto_orfeo, city_orfeo)

    def replace_tildes(self, cadena):
        a,b = 'áéíóúüÁÉÍÓÚÜ','aeiouuAEIOUU'
        trans = str.maketrans(a,b)
        return cadena.translate(trans)