from odoo import http
from datetime import date, datetime, timedelta, timezone
from random import choice
import logging
import unicodedata
import re
import io
import base64
import json
import sys
import requests
import dateutil.relativedelta

from . import sevenet as Sevenet
# Instancia de logging para imprimir por consola
_logger = logging.getLogger(__name__)

meses = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

class MySample(http.Controller):
    @http.route('/', auth='public', website=True)
    def redirect_login(self):
        _logger.info(http.request.session)
        if http.request.session.uid == None:
            return http.request.redirect('/web/login')
        else:
            return http.request.redirect('/my/home')

#             user = http.request.env['res.users'].search([('login','=',http.request.session.login)])
#             if len(user.groups_id) == 2 and user.groups_id[0].id == 43 and user.groups_id[1].id == 43:
#                 return http.request.redirect('/convenios')
#                 return http.request.redirect('/historial-tramites')
#             else:
#                 return http.request.redirect('/my/home')
            
#     @http.route('/my', website=True)
#     def redirect_home(self):
#         user = http.request.env['res.users'].search([('login','=',http.request.session.login)])
#         if len(user.groups_id) == 2 and user.groups_id[0].id == 43 and user.groups_id[1].id == 43:
#             return http.request.redirect('/convenios')
#         elif len(user.groups_id) == 2 and user.groups_id[0].id == 45 and user.groups_id[1].id == 45:
#             return http.request.redirect('/historial-tramites')
    
    # Crea un usuario tipo persona desde el formulario del website
    # Activa la automatización para la creación y seguimiento del trámite
    @http.route('/create_user', methods=["POST"], auth='public', website=True)
    def create_user(self, **kw):
        resp = {}
        _logger.info(kw)
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
        try:
            user = http.request.env['x_cpnaa_user'].sudo().create(kw)
            resp = { 'ok': True, 'message': 'Usuario creado con exito',
                     'data_user': {'tipo_doc': kw['x_document_type_ID'], 'documento': kw['x_document']} }
        except:
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    # Actualiza el registro desde el formulario del website cuando el el trámite tiene un rechazo
    @http.route('/update_tramite', methods=["POST"], auth='public', website=True)
    def update_tramite(self, **kw):
        resp = {}
        data_user = False
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
        try:
            user = http.request.env['x_cpnaa_user'].search([('x_document_type_ID.id','=',kw.get('x_document_type_ID')),
                                                               ('x_document','=',kw.get('x_document'))])
            tramite = http.request.env['x_cpnaa_procedure'].search([('x_user_ID','=',user.id)])[0]
            update = {'x_studio_carrera_1':kw.get('x_institute_career'),'x_studio_universidad_5': kw.get('x_institution_ID'),
                      'x_full_name': kw.get('x_name')+' '+kw.get('x_last_name'), 'x_validation_refuse': False,
                      'x_name': tramite.x_service_ID.x_name+'-'+kw.get('x_name')+'-'+kw.get('x_last_name')}
            rechazos = http.request.env['x_cpnaa_refuse_procedure'].sudo().search([('x_procedure_ID','=',tramite.id)])
            if len(rechazos) > 0:
                id_rechazo = rechazos[-1].id
            if tramite.x_cycle_ID.x_order == 0:
                data_user = {'tipo_doc': kw['x_document_type_ID'], 'documento': kw['x_document']}
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).sudo().write(update)
            http.request.env['x_cpnaa_user'].browse(user.id).sudo().write(kw)
            # Escribe en el mailthread que el trámite ha sido actualizado
            subject = 'Trámite actualizado por ' + kw.get('x_name')+' '+kw.get('x_last_name')
            body = kw.get('x_name')+' '+kw.get('x_last_name') + ' ha actualizado la información del trámite'
            self.mailthread_tramite(tramite.id, kw.get('x_name'), kw.get('x_last_name'), subject, body, user.x_partner_ID.id)
            if len(rechazos) > 0:
                # Marca el rechazo como corregido
                http.request.env['x_cpnaa_refuse_procedure'].browse(id_rechazo).sudo().write({'x_corrected':True})
            resp = { 'ok': True, 'message': 'Usuario y trámite actualizados con exito', 'id_user': user.id, 'data_user': data_user}
        except:
            _logger.info(sys.exc_info())
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
        return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    # Ruta que renderiza pagina de pagos, si no existe un trámite por pagar lo redirige al inicio del trámite
    @http.route('/pagos/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def epayco(self, tipo_doc, documento):
        campos = ['id','x_studio_tipo_de_documento_1','x_studio_documento_1','x_service_ID','x_rate']
        tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                      ('x_studio_documento_1','=',documento),
                                                                      ('x_cycle_ID.x_order','=',0)],campos)
        if (tramites):
            return http.request.render('my_sample.epayco', {'tramite': tramites[0]})
        else:
            return http.request.redirect('/cliente/tramite/matricula')
    
    # Ruta que renderiza página de respuesta de pasarela de pagos
    @http.route('/pagos/respuesta', auth='public', website=True)
    def respuesta_epayco(self):
        return http.request.render('my_sample.respuesta_pago', {})
    
    # Ruta que renderiza página de confirmación de pasarela de pagos
    @http.route('/pagos/confirmacion', auth='public', website=True)
    def epayco_confirmacion(self, **kw):
        ref_payco = kw.get('ref_payco')
        if not ref_payco:
            return http.request.redirect('/cliente/tramite/matricula')
        resultado_pago = None
        _logger.info(ref_payco)
        data = self.validar_ref_epayco(ref_payco)
        _logger.info(data.get('data', False))
        success = data.get('success', False)
        if success:
            if data['data']['x_response'] == 'Aceptada':
                data_tramite = {
                    'numero_pago': data['data']['x_transaction_id'],
                    'fecha_pago': data['data']['x_transaction_date'],
                    'banco': data['data']['x_bank_name'],
                    'monto_pago': data['data']['x_amount'],
                    'tipo_pago': data['data']['x_type_payment'],
                    'id_tramite': data['data']['x_extra1']
                }
                resultado_pago = self.tramite_fase_verificacion(data_tramite)
                _logger.info(resultado_pago)
        return http.request.render('my_sample.epayco_confirmacion', {'ok': success, 'data': data, 'resultado_pago': resultado_pago})
    
    def validar_ref_epayco(self, ref_payco):
        base_url = 'https://secure.epayco.co/validation/v1/reference/';
        response = requests.get(base_url + ref_payco)
        return response.json()
    
    # Ruta que renderiza página de formulario de pqrd
    @http.route('/pqrd/formulario', auth='public', website=True)
    def formulario_pqrd(self):
        return http.request.render('my_sample.formulario_pqrd', {})
    
    # Ruta que renderiza página de formulario de denuncias
    @http.route('/denuncias/formulario', auth='public', website=True)
    def formulario_denuncia(self):
        return http.request.render('my_sample.formulario_denuncia', {})
    
    # Activa la automatización para la creación y seguimiento del trámite
    @http.route('/registrar_denuncia', methods=["POST"], auth='public', website=True)
    def registrar_denuncia(self, **kw):
        resp, borrar, evidence_files = {}, [], []
        _logger.info(kw)
        for key, value in kw.items():
            if type(value) != str:
                borrar.append(key)
                evidence_files.append(value)
        for key in borrar:
            del kw[key]
        kw['x_complaint_issues_ID'] = kw['x_complaint_issues_ID'].split(',')
        try:
            consecutivo = http.request.env['x_cpnaa_consecutive'].sudo().search([('x_name','=','DENUNCIAS')])
            kw['x_name'] = 'DENUNCIA-'+str(consecutivo.x_value + 1)
            denuncia = http.request.env['x_cpnaa_complaint'].sudo().create(kw)
            if denuncia:
                count = 0
                for ev in evidence_files:
                    count += 1
                    file = base64.b64encode(ev.read())
                    evidence = {'x_complaint_ID': denuncia.id, 'x_file': file, 'x_name': 'PRUEBA-'+str(count)+'-'+denuncia.x_name}
                    ext = str(ev.filename.split('.')[-1]).lower()
                    if ext == 'pdf':
                        http.request.env['x_evidence_files_pdf'].sudo().create(evidence)
                    else:
                        http.request.env['x_evidence_files_img'].sudo().create(evidence)
                http.request.env['x_cpnaa_consecutive'].browse(consecutivo.id).sudo().write({'x_value':consecutivo.x_value + 1})
            resp = { 'ok': True, 'message': 'Su queja ha sido registrada con el consecutivo '+ denuncia.x_name +' exitosamente.' }
        except:
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    # Ruta que renderiza página de consulta de registro por documento
    @http.route('/consulta_online/por_documento', auth='public', website=True)
    def consulta_por_documento(self):
        return http.request.render('my_sample.consulta_registro', {'form': 'por_documento'})
        
    # Ruta que renderiza página de consulta de registro por numero de tarjeta
    @http.route('/consulta_online/por_numero', auth='public', website=True)
    def consulta_por_numero(self):
        return http.request.render('my_sample.consulta_registro', {'form': 'por_numero'})
        
    # Realiza la consulta del registro online por documento o numero de tarjeta
    @http.route('/realizar_consulta', methods=["POST"], type="json", auth='public', website=True)
    def realizar_consulta(self, **kw):
        data = kw.get('data')
        _logger.info(data)
        tramites = []
        if self.validar_captcha(kw.get('token')):
            ahora = datetime.now() - timedelta(hours=5)
            hora_consulta = ahora.strftime('%Y-%m-%d %H:%M:%S')
            campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_origin_type',
                      'x_studio_pas_de_expedicin_1','x_studio_ciudad_de_expedicin','x_resolution_ID',
                      'x_studio_ciudad_de_expedicin','x_studio_carrera_1','x_studio_gnero','x_studio_fecha_de_resolucin',
                      'x_studio_nombres','x_studio_apellidos','x_enrollment_number','x_fecha_resolucion_corte']
            if data['numero_tarjeta'] != '':
                tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_enrollment_number','=',data['numero_tarjeta']),
                                                                              ('x_cycle_ID.x_order','=',5)],campos)
            else:
                tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',data['doc_type']),
                                                                              ('x_studio_documento_1','=',data['doc']),
                                                                              ('x_cycle_ID.x_order','=',5)],campos)
            _logger.info(tramites)
            if tramites:
                for tramite in tramites:
                    tramite['x_female_career'] = http.request.env['x_cpnaa_career'].sudo().search([('id','=',tramite['x_studio_carrera_1'][0])]).x_female_name
                    tramite['x_resolution_number'] = http.request.env['x_cpnaa_resolution'].sudo().search([
                        ('id','=',tramite['x_resolution_ID'][0])]).x_consecutive
                    if tramite['x_origin_type'] and tramite['x_origin_type'][1] == 'CONVENIO':
                        tramite['x_resolution_date'] = tramite['x_studio_fecha_de_resolucin']
                    else:
                        tramite['x_resolution_date'] = tramite['x_fecha_resolucion_corte']
                return {'ok': True, 'mensaje': 'Usuario registrado', 'tramites': tramites, 'hora_consulta': hora_consulta }
            else:
                return {'ok': False, 'mensaje': 'El usuario no esta registrado', 'hora_consulta': hora_consulta }
        else:
            return { 'ok': True, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True }                    
    
    """
    Valida si el trámite tiene recibo de pago, si es necesario actualiza el consecutivo de los recibos
    Si es convenios o si aún esta vigente el corte le devuelve el mismo número de recibo
    Si paso la fecha limite de pago del corte le asigna un nuevo número de recibo y lo actualiza en el trámite
    """
    @http.route('/recibo_pago', methods=["POST"], type="json", auth='public', website=True)
    def recibo_pago(self, **kw):
        data = kw.get('data')
        _logger.info(data)
        ahora = datetime.now() - timedelta(hours=5)
        tramite = http.request.env['x_cpnaa_procedure'].search([('id','=',int(data['id_tramite']))])
        numero_recibo = tramite.x_voucher_number
        numero_radicado = tramite.x_rad_number
        if (not data['corte'] and numero_recibo) and (data['corte'] == tramite.x_origin_name and numero_recibo):
            pass
        elif not numero_recibo or (data['corte'] and data['corte'] != tramite.x_origin_name):
            consecutivo = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Consecutivo Recibo de Pago')])
            numero_recibo = int(consecutivo.x_value) + 1
            numero_radicado = Sevenet.sevenet_consulta(tramite.id)
            update = {'x_voucher_number': numero_recibo, 'x_radicacion_date': ahora, 'x_rad_number': numero_radicado }
            if data['corte']:
                update = {'x_voucher_number': numero_recibo,'x_origin_name': data['corte'],
                          'x_radicacion_date': ahora, 'x_rad_number': numero_radicado}
            http.request.env['x_cpnaa_parameter'].browse(consecutivo.id).sudo().write({'x_value':str(numero_recibo)})
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).sudo().write(update)
        return {'ok': True, 'numero_recibo': str(numero_recibo), 'numero_radicado': str(numero_radicado)+'-'+str(ahora.year)}
    
    # Envia la información necesaria para el recibo de pago o para el pago desde la pasarela
    @http.route('/tramite_fase_inicial', methods=["POST"], type="json", auth='public', website=True)
    def tramite_fase_inicial(self, **kw):
        data = kw.get('data')
        campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_correo_electrnico',
                  'x_user_celular','x_studio_pas_de_expedicin_1','x_studio_ciudad_de_expedicin','x_studio_direccin','x_studio_telfono',
                  'x_req_date','x_rate','x_studio_universidad_5','x_studio_carrera_1','x_studio_departamento_estado','x_origin_type',
                  'x_studio_fecha_de_grado_2','x_studio_ciudad_1','x_origin_name','x_studio_nombres','x_studio_apellidos','x_grade_ID']
        tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',data['doc_type']),
                                                                      ('x_studio_documento_1','=',data['doc']),
                                                                      ('x_cycle_ID.x_order','=',0)],campos)
        if tramites:
            # Código del servicio para generar el código de barras del recibo
            codigo = http.request.env['x_cpnaa_service'].search([('id','=',tramites[0]['x_service_ID'][0])]).x_code
            if (tramites[0]['x_origin_type'][1] == 'CORTE'):
                corte_vigente = self.buscar_corte(tramites[0]['x_origin_name'])
                _logger.info(corte_vigente)
                tramites[0]['x_origin_name'] = corte_vigente['x_name']
                return {'ok': True, 'tramite': tramites[0], 'codigo': codigo, 'corte': corte_vigente}
            elif tramites[0]['x_grade_ID']:
                grado = http.request.env['x_cpnaa_grade'].sudo().browse(tramites[0]['x_grade_ID'][0])
                fecha_lim = grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)
                ok = True
                if not self.validar_fecha_limite(fecha_lim):
                    ok = False
                return {'ok': ok, 'tramite': tramites[0], 'codigo': codigo, 'grado': { 'id': grado.id, 'x_fecha_limite': fecha_lim }}
            else:
                return {'ok': False, 'error': 'Ha ocurrido un error con el origen del trámite'}
        else:
            return {'ok': False , 'error': 'Tramite no existe'}

    # Si el pago es aprobado pasa el trámite a fase de verificación, registra los cambios en el mailthread
    def tramite_fase_verificacion(self, data):
        datetime_str = datetime.strptime(data['fecha_pago'], '%Y-%m-%d %H:%M:%S')
        datetime_str = datetime_str + timedelta(hours=5)
        _logger.info('Hora del pago UTC: '+str(datetime_str))
        numero_radicado = False
        id_user, error, tramite, pago_registrado, mailthread_registrado, origin_name, grado = False, False, False, False, False, False, False
        try:
            tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('id','=',data["id_tramite"])])
            user = tramite.x_user_ID
            if len(tramite) > 0:
                if tramite.x_cycle_ID.x_order > 0:
                    raise Exception('Este pago ya fue registrado')
                if tramite.x_cycle_ID.x_order == 0:
                    numero_radicado = Sevenet.sevenet_consulta(tramite.id)
                    if (tramite.x_origin_type.x_name == 'CORTE'):
                        corte_vigente = self.buscar_corte(tramite.x_origin_name)
                        origin_name = corte_vigente['x_name']
                    else:
                        origin_name = tramite.x_origin_name
                        grado = http.request.env['x_cpnaa_grade'].sudo().browse(tramite.x_grade_ID.id)
                    ciclo_ID = http.request.env["x_cpnaa_cycle"].sudo().search(["&",("x_service_ID.id","=",tramite["x_service_ID"].id),("x_order","=",1)])
                    update = {'x_cycle_ID': ciclo_ID.id,'x_radicacion_date': datetime_str, 'x_pay_datetime': datetime_str,
                              'x_pay_type': data['tipo_pago'],'x_consignment_number': data['numero_pago'], 'x_bank': data['banco'],
                              'x_consignment_price': data['monto_pago'],'x_origin_name': origin_name, 'x_rad_number': numero_radicado}
                    pago_registrado = http.request.env['x_cpnaa_procedure'].browse(tramite['id']).sudo().write(update)
                    numero_radicado = str(numero_radicado) +'-'+ str(datetime_str.year)
                    if not pago_registrado:
                        raise Exception('Su pago ha sido exitoso pero no se pudo completar el trámite, por favor envie esta información al correo info@cpnaa.gov.co')
            else:
                raise Exception('No se encontro trámite, no se completado la solicitud')                 
        except:        
            error = str(sys.exc_info()[1])
        try:
            if pago_registrado:
                subject = 'Trámite recibido en fase de verificación'
                body = 'Trámite de cliente '+tramite.x_full_name+' realizo el pago y ha sido recibido en fase de verificación'
                mailthread_registrado = self.mailthread_tramite(tramite.id, tramite.x_studio_nombres, tramite.x_studio_apellidos,
                                                                subject, body, tramite.x_user_ID.x_partner_ID.id)
            self.grado_check_pagos(grado)
        except:
            if pago_registrado:
                error = 'Se registro el pago pero no se escribio el mailthread'+'\nTrámite ID: '+str(tramite.id)+'\n'+str(sys.exc_info())
        if not error and mailthread_registrado:
            return { 'ok': True, 'message': 'Trámite actualizado con exito y registrado en el mailthread', 
                    'mailthread': mailthread_registrado.id, 'error': False, 'id_user': user.id } #'numero_radicado': numero_radicado, 
        if pago_registrado and error:
            _logger.info(error)
            return { 'ok': True, 'message': 'Trámite actualizado con exito', 'error': error, 
                     'numero_radicado': numero_radicado, 'id_user': user.id }
        if not pago_registrado:        
            return { 'ok': False, 'error': error, 'id_user': user.id, 'numero_radicado': numero_radicado }
        
    def grado_check_pagos(self, grado):
        _logger.info(grado)
        if len(grado.x_childs_ID) == len(grado.x_childs_procedure):
          grado.x_phase_2 = True
        else:
          grado.x_phase_2 = False

    # Valida si la fecha limite de pago del corte caducó, de ser asi retorna el corte vigente
    def buscar_corte(self, origin_name):
        campos_corte = ['id','x_name','x_lim_pay_date']
        corte_tramite = http.request.env['x_cpnaa_cut'].search_read([('x_name','=',origin_name)],campos_corte)[0]
        fecha_limite_pago = corte_tramite['x_lim_pay_date']
        if not self.validar_fecha_limite(fecha_limite_pago):
            cortes = http.request.env['x_cpnaa_cut'].search_read([],campos_corte)
            primer = True
            nuevo_corte = False
            for corte in cortes:
                if self.validar_fecha_limite(corte['x_lim_pay_date']):
                    # Obtener una fecha limite de pago posterior a hoy y comparar con las fechas limites para validar que sea la mas cercana
                    if primer:
                        fecha_limite_pago = corte['x_lim_pay_date']
                        primer = False
                        nuevo_corte = corte
                    if fecha_limite_pago >= corte['x_lim_pay_date']:
                        fecha_limite_pago = corte['x_lim_pay_date']
                        nuevo_corte = corte
            return nuevo_corte
        else:
            return corte_tramite
        
    # Ruta que renderiza el inicio del trámite (usuarios ya graduados)
    @http.route('/cliente/tramite/<string:form>', auth='public', website=True)
    def inicio_tramite(self, form):
        validos = ['matricula','inscripciontt','licencia']
        if form in validos:
            return http.request.render('my_sample.inicio_tramite', {'form': form, 'inicio_tramite': True})
        else:
            return http.request.redirect('/cliente/tramite/matricula')
    
    # Ruta que renderiza el inicio del trámite (usuarios de convenios)
    @http.route('/convenios/tramite', auth='public', website=True)
    def inicio_convenio(self):
        return http.request.render('my_sample.inicio_tramite', {'form': 'convenio', 'inicio_tramite': True, 'por_nombre': False })
    
    # Ruta que renderiza el inicio del trámite (usuarios de convenios)
    @http.route('/convenios/tramite/por_nombre', auth='public', website=True)
    def inicio_convenio_nombre(self):
        return http.request.render('my_sample.inicio_tramite', {'form': 'convenio', 'inicio_tramite': True, 'por_nombre': True })
    
    # Ruta que renderiza el inicio del trámite certificado de vigencia virtual
    @http.route('/tramites/certificado_de_vigencia', auth='public', website=True)
    def inicio_cert_vigencia(self):
        return http.request.render('my_sample.inicio_cert_vigencia', {})
        
    # Ruta que renderiza el validacion de autenticiadad del certificado de vigencia virtual
    @http.route('/tramites/validacion_cert_de_vigencia', auth='public', website=True)
    def validacion_cert_de_vigencia(self):
        return http.request.render('my_sample.validacion_cert_de_vigencia', {})
    
    # Valida si existe un certificado con el codigo de seguridad recibido
    @http.route('/verificar_autenticidad', methods=["POST"], type="json", auth='public', website=True)
    def verificar_autenticidad(self, **kw):
        data = kw.get('data')
        _logger.info(data)
        if self.validar_captcha(kw.get('token')):
            campos = ['id','x_procedure_ID','create_date', 'x_consecutivo']
            certificado = http.request.env['x_procedure_service'].sudo().search_read([('x_procedure_ID.x_studio_tipo_de_documento_1','=',int(data['tipo_doc'])),
                                                                               ('x_procedure_ID.x_studio_documento_1','=',data['documento']),
                                                                               ('x_validity_code','=',data['x_code'])],campos)
            if certificado:
                campos = ['id','x_studio_nombres','x_studio_apellidos', 'x_studio_tipo_de_documento_1', 'x_studio_documento_1']
                profesional = http.request.env['x_cpnaa_procedure'].sudo().search_read([('id','=',certificado[0]['x_procedure_ID'][0])], campos)
    #             tiempo_expiracion = http.request.env['x_cpnaa_service'].sudo().search([('id','=',certificado[0]['x_service_ID'][0])]).x_validity
                certificado[0]['expiration_date'] = certificado[0]['create_date'] + dateutil.relativedelta.relativedelta(months=6)
                return {'ok': True, 'mensaje': 'El Certificado se encuentra registrado en nuestra Base de Datos.', 
                        'certificado': certificado[0], 'profesional': profesional}
            else:
                return {'ok': False, 'mensaje': 'El Certificado no se encuentra registrado en nuestra Base de Datos.' }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True }
    
    # Ruta que renderiza el resultado del trámite certificado de vigencia virtual
    @http.route('/tramites/certificado_de_vigencia/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def certificado_vigencia(self, tramite):
        _logger.info(tramite.x_legal_status)
        if tramite and tramite.x_legal_status != 'SANCIONADO':
            return http.request.render('my_sample.certificado_vigencia', {'tramite': tramite})
        else:
            return http.request.redirect('/tramites/certificado_de_vigencia')
    
    # Valida si existe un trámite completo
    @http.route('/verificar_certificado', methods=["POST"], type="json", auth='public', website=True)
    def verificar_certificado(self, **kw):
        data = kw.get('data')
        sancionado = False
        if self.validar_captcha(kw.get('token')):
            tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',data['tipo_doc']),
                                                                          ('x_studio_documento_1','=',data['documento']),
                                                                          ('x_cycle_ID.x_order','=',5)],
                                                                          ['id','x_studio_carrera_1','x_legal_status'])
            if tramites:
                mensaje = 'Si existen registros para este tipo y número de documento'
                for tramite in tramites:
                    _logger.info(tramite)
                    if tramite['x_legal_status'] == 'SANCIONADO':
                        mensaje = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','MENSAJE PROFESIONAL SANCIONADO')]).x_value
                        tramite['mensaje'] = mensaje
                return {'ok': True, 'mensaje': 'Si existen registros', 'tramites': tramites }
            else:
                return {'ok': False, 'mensaje': 'No existen registros para este tipo y número de documento', 'tramites': tramites }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True  }
    
    # Enviar el certificado de vigencia al email y lo retorna al navegador para su descarga
    @http.route('/enviar_certificado_vigencia', methods=["POST"], type="json", auth='public', website=True)
    def enviar_certificado_vigencia(self, **kw):
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('id','=',kw.get('id_tramite'))])
        template_obj = http.request.env['mail.template'].sudo().search_read([('name','=','cpnaa_template_validity_certificate')])[0]
        certTemplate = http.request.env['x_cpnaa_template'].sudo().search([('x_name','=','CERTIFICADO DE VIGENCIA')])
        consecutivo = int(http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Consecutivo Certificado de Vigencia')]).x_value) + 1
        certificado = http.request.env['x_procedure_service'].sudo().create({
            'x_doc_gen': certTemplate.x_html_content,
            'x_procedure_ID': tramite.id,
            'x_service_ID': tramite.x_service_ID.id,
            'x_consecutivo': consecutivo,
            'x_validity_code': self.generar_aleatorio(7),
            'x_name': 'CERTIFICADO-'+tramite.x_studio_nombres+'-'+tramite.x_studio_apellidos,
            'x_email': kw.get('email')
        })
        if certificado:
            http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Consecutivo Certificado de Vigencia')]).write({'x_value': str(consecutivo)})
        pdf, _ = http.request.env.ref('my_sample.cert_vigencia').sudo().render_qweb_pdf([certificado.id])
        pdf64 = base64.b64encode(pdf)
        pdfStr = pdf64.decode('ascii')
        cert = http.request.env['ir.attachment'].sudo().create({
            'name': 'Certificado',
            'type': 'binary',
            'datas': pdf64,
            'mimetype': 'application/x-pdf'
        })
        body = template_obj['body_html']
        if template_obj:
            mail_values = {
                'subject': template_obj['subject'],
                'attachment_ids': [cert.id],
                'body_html': body,
                'email_to': kw.get('email'),
                'email_from': template_obj['email_from'],
           }
        try:
            http.request.env['mail.mail'].sudo().create(mail_values).send()
            return {'ok': True, 'mensaje': 'Se ha completado su solicitud exitosamente', 
                    'cert': {'pdf':pdfStr, 'headers': {'Content-Type', 'application/pdf'}}}
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'mensaje': 'No se podido completar su solicitud', 'cert': False}
    
    # Valida tipo y número de documento, valida si es un usuario nuevo, si tiene trámite o si es un graduando
    @http.route('/validar_tramites', methods=["POST"], type="json", auth='public', website=True)
    def validar_tramites(self, **kw):
        data = kw.get('data')
        user = False
        if self.validar_captcha(kw.get('token')):
            result, por_nombre, matricula, certificado, tramite_en_curso = {}, False, False, False, False
            graduando = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select','=',int(data['doc_type'])),
                                                                            ('x_documento','=',data['doc']),('x_origin_type','=','CONVENIO')])
            grado = http.request.env['x_cpnaa_grade'].sudo().browse(graduando.x_grado_ID.id)
            if grado:
                if self.validar_fecha_limite(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)):
                    _logger.info('Graduando reportado por IES con plazo vencido => ['+data['doc_type']+':'+data['doc']+']')
                else:
                    grado = False
            tramites = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1','=',int(data['doc_type'])),
                                                                     ('x_studio_documento_1','=',data['doc'])])
            for tramite in tramites:
                _logger.info(tramite)
                if tramite.x_cycle_ID.x_order < 5:
                    tramite_en_curso = True
                    user = tramite.x_user_ID
                    break
                if tramite.x_service_ID.x_name.find('MATR') != -1 and tramite.x_cycle_ID.x_order == 5:
                    matricula = True
                    user = tramite.x_user_ID
                if tramite.x_service_ID.x_name.find('CERT') != -1 and tramite.x_cycle_ID.x_order == 5:
                    certificado = True
                    user = tramite.x_user_ID
                    result = {'carrera': tramite.x_studio_carrera_1.x_name, 'tipo_documento': tramite.x_studio_tipo_de_documento_1.x_name, 
                              'documento': tramite.x_studio_documento_1 }
            _logger.info(user)
            if len(graduando) > 1:
                graduando = graduando[-1]
            if (tramite_en_curso):
                return { 'ok': True, 'id': user.id, 'tramite_en_curso': tramite_en_curso }
            if (matricula or certificado):
                return { 'ok': True, 'id': user.id, 'matricula': matricula, 'certificado': certificado, 'result': result }
            elif (grado):
                return { 'ok': True, 'id': graduando.id, 'convenio': True }
            elif (user):
                return { 'ok': True, 'id': user.id, 'convenio': False }
            else:
                return { 'ok': False, 'id': False, 'convenio': False }
        else:
            return { 'ok': False, 'id': False, 'convenio': False, 'error_captcha': True,
                    'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página' }
        
    # Busca al graduando de convenios en la tabla de egresados, puede ser por documento o por nombres y apellidos 
    @http.route('/validar_estudiante', methods=["POST"], type="json", auth='public', website=True)
    def validar_estudiante(self, **kw):
        _logger.info(kw)
        if self.validar_captcha(kw.get('token')):
            data = kw.get('data')
            hoy = date.today()
            fecha_maxima, graduandos, definitivos = '', [], []
            if data['doc_type'] == '':
                graduandos = http.request.env['x_procedure_temp'].sudo().search_read([('x_nombres','=',data['nombres']),
                                                                                      ('x_apellidos','=',data['apellidos']),
                                                                                      ('x_grado_ID','!=',False),
                                                                                      ('x_fecha_de_grado','>=',hoy),
                                                                                      ('x_origin_type','=','CONVENIO')])
            else:
                graduandos = http.request.env['x_procedure_temp'].sudo().search_read([('x_tipo_documento_select','=',int(data['doc_type'])),
                                                                                      ('x_grado_ID','!=',False),
                                                                                      ('x_fecha_de_grado','>=',hoy),
                                                                                      ('x_documento','=',data['doc']),
                                                                                      ('x_origin_type','=','CONVENIO')])
            if (len(graduandos) > 0):
                for graduando in graduandos:
                    grado = http.request.env['x_cpnaa_grade'].sudo().browse(graduando['x_grado_ID'][0])
                    id_grado = grado.id
                    if grado:
                        fecha_maxima = grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)
                        if self.validar_fecha_limite(fecha_maxima):
                            _logger.info('Grado vigente hasta: '+str(fecha_maxima))
                        else:
                            id_grado = False
                        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',graduando['x_tipo_documento_select'][0]),
                                                                                   ('x_studio_documento_1','=',graduando['x_documento']),
                                                                                   ('x_cycle_ID.x_order','<','5')])
                        definitivo = {
                            'graduando': graduando,
                            'id_user_tramite': tramite.x_user_ID.id,
                            'id_grado': id_grado,
                            'fecha_maxima': fecha_maxima
                        }
                        definitivos.append(definitivo)
            if (graduandos):
                return { 'ok': True, 'graduandos': definitivos }
            else:
                return { 'ok': False, 'graduandos': False }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True }
        
    # Renderiza el formulario para trámites, valida si ya ha realizado este trámite y lo redirige al inicio del tramite
    @http.route('/tramite/<string:origen>/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def formulario_tramites(self, origen, tipo_doc, documento):
        validos = ['matricula','inscripciontt','licencia']
        doc_validos = ['1','2','5']
        matricula, tramite_en_curso = None, None
        servicio = 'MATRÍCULA PROFESIONAL'
        if tipo_doc == '1' and not self.validar_solo_numeros(documento):
            return http.request.redirect('/cliente/tramite/'+origen)
        if origen == validos[1]:
            servicio = 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL'
        if origen == validos[2]:
            servicio = 'LICENCIA TEMPORAL ESPECIAL'
        tramites = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                 ('x_studio_documento_1','=',documento)])
        if tramites:
            for tramite in tramites:
                matricula = True if tramite.x_service_ID.x_name == 'MATRÍCULA PROFESIONAL' else False
                tramite_en_curso = True if tramite.x_cycle_ID.x_order < 5 else False
        if tramite_en_curso:
            return http.request.redirect('/cliente/'+str(tramite.x_user_ID.id)+'/tramites/')                
        elif matricula and origen == 'matricula':
            return http.request.redirect('/cliente/tramite/'+origen)
        elif origen in validos and tipo_doc in doc_validos:
            return http.request.render('my_sample.formulario_tramites', {'tipo_doc': tipo_doc, 'documento':documento, 'form': origen, 'origen': 1})
        
    # Renderiza el formulario para trámites por convenios, valida si ya hay trámite en curso y lo redirige al estado del tramite
    @http.route('/tramite/convenios/<model("x_procedure_temp"):cliente>', auth='public', website=True)
    def formulario_convenio(self, cliente):
        form = 'inscripciontt'
        if (cliente.x_carrera_select.x_level_ID.x_name == 'PROFESIONAL'):
            form = 'matricula'
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',cliente.x_tipo_documento_select.id),
                                                                           ('x_studio_documento_1','=',cliente.x_documento),
                                                                           ('x_cycle_ID.x_order','<','5')])
        grado = http.request.env['x_cpnaa_grade'].sudo().browse(cliente.x_grado_ID.id)
        if not self.validar_fecha_limite(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)):
            return http.request.redirect('/cliente/tramite/'+form)
        if tramite:
            return http.request.redirect('/cliente/'+str(tramite.x_user_ID.id)+'/tramites')
        else:
            return http.request.render('my_sample.formulario_tramites', {'cliente': cliente, 'form': form, 'origen': 2})
    
    # Renderiza formulario para corregir rechazos, si el trámite no tiene rechazo o ya fue corregido lo redirige al inicio
    @http.route('/tramite/<string:form>/edicion/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def editar_tramite(self, form, tipo_doc, documento):
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                    ('x_studio_documento_1','=',documento),
                                                                    ('x_cycle_ID.x_order','<','5')])
        rechazos = http.request.env['x_cpnaa_refuse_procedure'].sudo().search_read([('x_procedure_ID','=',tramite.id)])
        user = http.request.env['x_cpnaa_user'].sudo().browse(tramite.x_user_ID.id)
        if user and len(rechazos)>0:
            if not rechazos[-1]['x_corrected']:
                return http.request.render('my_sample.formulario_tramites', {'form': form, 'user': user, 'origen': tramite.x_origin_type.id})
            else:
                return http.request.redirect('/cliente/tramite/'+form)
        elif user and tramite.x_cycle_ID.x_order == 0:
            return http.request.render('my_sample.formulario_tramites', {'form': form, 'user': user, 'origen': tramite.x_origin_type.id})
        else:
            return http.request.redirect('/cliente/tramite/'+form)

    # Renderiza el estado del trámite, valida las diferentes opciones a realizar (Pagar, Cargar Diploma, Corregir rechazos, Ver calendario)
    @http.route('/cliente/<model("x_cpnaa_user"):persona>/tramites', auth='public', website=True)
    def list_tramites(self, persona):
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_user_ID','=',persona[0].id),('x_cycle_ID.x_order','<','5')])
        form = 'inscripciontt'
        solicitud_diploma, rechazo, rechazos, pago_vencido = False, False, [], False
        if len(tramites)>0:
            if tramites[0].x_origin_type.x_name == 'CONVENIO' and tramites[0].x_cycle_ID.x_order == 0:
                grado = http.request.env['x_cpnaa_grade'].sudo().browse(tramites.x_grade_ID.id)
                ahora = datetime.now() - timedelta(hours=5)
                _logger.info(ahora)
                if grado:
                    fecha_maxima = grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)
                    fecha_maxima = datetime.combine(fecha_maxima+timedelta(days=1), datetime.min.time())
                    if fecha_maxima < ahora:
                        pago_vencido = True
            if (tramites[0].x_service_ID.x_name.find('MATR') != -1):
                form = 'matricula'
            if (tramites[0].x_service_ID.x_name.find('LICENCIA') != -1):
                form = 'licencia'
            rechazos = http.request.env['x_cpnaa_refuse_procedure'].sudo().search_read([('x_procedure_ID','=',tramites[0].id)],
                                                                                       ['x_observation','x_refuse_ID','x_corrected'])
            if tramites[0].x_cycle_ID.x_order == 4 and tramites[0].x_origin_type.x_name == 'CONVENIO' and not tramites[0].x_CD:
                result = http.request.env['mail.message'].sudo().search_read([('res_id','=',tramites[0].id),('subject','=','Solicitud de cargue de Diploma')])
                if len(result) > 0:
                    solicitud_diploma = True
            if tramites[0].x_origin_type.x_name == 'CONVENIO' and not tramites[0].x_CD:
                result = http.request.env['mail.message'].sudo().search_read([('res_id','=',tramites[0].id),('subject','=','Solicitud de cargue de Diploma')])
                if len(result) > 0:
                    solicitud_diploma = True
        if len(rechazos)>0:
            if not rechazos[-1]['x_corrected']:
                rechazo = rechazos[-1]
        _logger.info(tramites.x_user_ID.x_partner_ID.id)
        return http.request.render('my_sample.lista_tramites', {
            'tramites': tramites,
            'rechazo': rechazo,
            'persona': persona,
            'form': form,
            'diploma': solicitud_diploma,
            'pago_vencido': pago_vencido
        })
    
    # Retorna los datos del trámite para el formulario de edición
    @http.route('/get_data_edicion', methods=["POST"], type="json", auth='public', website=True)
    def get_data_edicion(self, **kw):
        data = kw.get('data')
        campos = ['x_expedition_city','x_expedition_country','x_expedition_state','x_country_ID','x_state_ID','x_city_ID','x_foreign_country']
        data_edicion = http.request.env['x_cpnaa_user'].sudo().search_read([('x_document_type_ID.id','=',data['tipo_doc']),
                                                                            ('x_document','=',data['documento'])],campos)[0]
        return { 'ok': True, 'data': data_edicion }
    
    # Guarda el diploma del graduando, actualiza el trámite, escribe en el mailthread y envia un mail al usuario interno encargado
    @http.route('/save_diploma', methods=["POST"], type="json", auth='public', website=True) 
    def save_diploma(self, **kw):
        archivo = kw.get('diploma')
        id_tramite = kw.get('id_tramite')
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf = archivo_temp.lstrip('data:application/pdf;base64,')
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('id','=',id_tramite)])
        actualizado = False
        try:
            update = {'x_studio_imagen_diploma': archivo_pdf, 'x_CD': True}
            actualizado = http.request.env['x_cpnaa_procedure'].browse(id_tramite).sudo().write(update)
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'error': str(sys.exc_info()[1])}
        if actualizado:
            subject = tramite.x_studio_nombres+' '+tramite.x_studio_apellidos+' ha cargado el PDF del diploma'
            body = tramite.x_studio_nombres+' '+tramite.x_studio_apellidos + ' ha cargado el PDF del diploma'
            self.mailthread_tramite(tramite.id, tramite.x_studio_nombres, tramite.x_studio_apellidos,
                                    subject, body, tramite.x_user_ID.x_partner_ID.id)
            http.request.env['mail.template'].sudo().search([('name','=','cpnaa_template_load_CD')])[0].sudo().send_mail(id_tramite,force_send=True)
            return {'ok': True, 'message': 'Trámite Actualizado, se guardo el diploma en PDF.'}
        else:
            return {'ok': False, 'error': 'Trámite no pudo ser actualizado, intente nuevamente.'}
               
    # Verifica si ya existe un usuario creado con el correo electrónico recibido
    @http.route('/get_email', methods=["POST"], type="json", auth='public', website=True)
    def get_email(self, **kw):
        cadena = kw.get('cadena')
        result = http.request.env['x_cpnaa_user'].sudo().search([('x_email'.lower(),'=',cadena.lower())])
        if (len(result) < 1):
            return { 'ok': True, 'email_exists': False }
        else:
            return { 'ok': False, 'email_exists': True }
    
    # Retorna las universidades que coinciden con la cadena recibida
    @http.route('/get_universidades', methods=["POST"], type="json", auth='public', website=True)
    def get_universidades(self, **kw):
        cadena = kw.get('cadena')
        tipo_universidad = kw.get('tipo_universidad')
        return {'universidades': http.request.env['x_cpnaa_user'].sudo().search_read([('x_user_type_ID.id','=',3),('x_institution_type_ID.id', '=', tipo_universidad),
                                                                               ('x_name', 'ilike', cadena)],['id','x_name'], limit=6)}
    
    # Retorna las carreas que coinciden con la cadena y nivel profesional recibidos
    @http.route('/get_carreras', methods=["POST"], type="json", auth='public', website=True)
    def get_carreras(self, **kw):
        cadena = kw.get('cadena')
        nivel_profesional = kw.get('nivel_profesional')
        id_genero = kw.get('id_genero')
        nombre_carrera = 'x_name'
        _logger.info(id_genero)
        if id_genero == '2':
            nombre_carrera = 'x_female_name'
        return {'carreras': http.request.env['x_cpnaa_career'].sudo().search_read([('x_level_ID.id','=',nivel_profesional),
                                                                                       (nombre_carrera, 'ilike', cadena)],
                                                                                       ['id',nombre_carrera], limit=6)}
    
    # Retorna el nombre de la carrera según el genero 
    @http.route('/get_carrera_genero', methods=["POST"], type="json", auth='public', website=True)
    def get_carrera_genero(self, **kw):
        campo = kw.get('campo')
        id_carrera = kw.get('id_carrera')
        return {'carrera': http.request.env['x_cpnaa_career'].sudo().search_read([('id','=',id_carrera)],[campo])}
    
    # Escribe en el mailthread del trámite
    def mailthread_tramite(self, id_tramite, nombres, apellidos, asunto, mensaje, id_contacto):
        mailthread = {
            'subject': asunto,
            'model': 'x_cpnaa_procedure',
            'email_from': nombres+' '+apellidos,
            'subtype_id': 2,
            'body': mensaje,
            'author_id': id_contacto,
            'message_type': 'notification',
            'res_id': id_tramite
        }
        return http.request.env['mail.message'].sudo().create(mailthread)
        
        
    """   RUTAS DE CONVENIOS  """

    # Menu principal de convenios
    # Valida que el usuario logueado sea un IES y a cual pertenece
    @http.route('/convenios', auth='user', website=True)
    def inicio_convenios(self):
        universidad = http.request.env['x_cpnaa_user'].search([('x_email','=',http.request.session.login)])
        if universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios', {'universidad': universidad, 'convenios': convenios})
    
    # Ruta donde carga por primera vez estudiantes y crea el grado
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/<model("x_cpnaa_agreement"):convenio>', auth='user', website=True) 
    def form_archivo_csv(self, universidad, convenio):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'convenio':convenio})
    
    # Ruta donde agrega mas estudiantes cuando el grado ya esta creado
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoCsv/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_csv_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    # Ruta donde carga el archivo definitivo de graduandos, la fecha actual es para el archivo guia
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoPdf/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_definitivo_pdf(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        fechaActual = datetime.now()
        mes = meses[fechaActual.month]
        fechaActualFormat = mes + fechaActual.strftime(" %d de %Y")
        return http.request.render('my_sample.convenios_definitivo_pdf', {'universidad': universidad, 'grado': grado, 'convenio': convenio,
                                                                          'convenios': convenios, 'fechaActual': fechaActualFormat})
    
    # Ruta donde carga el archivo de actas de diploma
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoActas/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_actas_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_grado_actas', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    # Ruta donde carga el cuadro de mando del grado
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/detalle_grado/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def detalles_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.detalles_grado', {'profesiones': profesiones, 'convenios': convenios,
                                                                'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    # Recibe el archivo definitivo de graduandos, lo guarda y marca fase como realizada
    @http.route('/guardar_pdf_definitivo', methods=['POST'], type="json", auth='user', website=True) 
    def guardar_pdf_definitivo(self, **kw):
        data = kw.get('data')
        archivo = data['archivo_pdf']
        id_universidad = data['universidad']
        id_convenio = data['convenio']
        id_grado = data['grado_id']
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf = archivo_temp.lstrip('data:application/pdf;base64,')
        try:
            update = {'x_phase_3': True, 'x_archivo_pdf_definitivo': archivo_pdf}
            http.request.env['x_cpnaa_grade'].browse(id_grado).write(update)
        except:
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar el archivo, vuelve a intentarlo más tarde'}
        return {'ok': True, 'message': 'Listado guardado con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    # Recibe el archivo de diplomas, lo guarda y marca fase como realizada
    @http.route('/guardar_pdf_actas', methods=['POST'], type="json", auth='user', website=True) 
    def guardar_pdf_actas(self, **kw):
        data = kw.get('data')
        archivo = data['archivo_pdf']
        id_universidad = data['universidad']
        id_convenio = data['convenio']
        id_grado = data['grado_id']
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf = archivo_temp.lstrip('data:application/pdf;base64,')
        try:
            update = {'x_phase_4': True, 'x_archivo_pdf_actas': archivo_pdf}
            http.request.env['x_cpnaa_grade'].browse(id_grado).write(update)
        except:
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar el archivo, vuelve a intentarlo más tarde'}
        return {'ok': True, 'message': 'Listado guardado con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    # Recibe los graduandos verificados y los agrega al grado, si no existe el grado lo crea
    @http.route('/guardar_registros', methods=['POST'], type="json", auth='user', website=True) 
    def guardar_registros_csv(self, **kw):
        registros = kw.get('registros')
        data = kw.get('data')
        hoy = date.today()
        _logger.info('TODAY')
        _logger.info(kw)
        id_carrera = data['profesion']
        id_universidad = data['universidad']
        id_convenio = data['convenio']
        id_grado = data['grado']
        fecha = data['fecha']
        guardados = 0
        grado = False
        try:
            if not id_grado:
                grado = http.request.env['x_cpnaa_grade'].sudo().create({'x_phase_1': True, 'x_carrera_ID': id_carrera, 
                                         'x_date': fecha, 'x_agreement_ID': id_convenio, 'x_studio_universidad': id_universidad})
                id_grado = grado['id']
            else:
                grado = http.request.env['x_cpnaa_grade'].sudo().browse(id_grado)
            for reg in registros:
                carrera_registro = id_carrera
                genero = self.validar_genero(reg['f_gender'])
                id_arquitecto = http.request.env['x_cpnaa_career'].search([('x_name','=','ARQUITECTO')]).id
                id_arquitecta = http.request.env['x_cpnaa_career'].search([('x_name','=','ARQUITECTA')]).id
                id_femenino   = http.request.env['x_cpnaa_gender'].search([('x_name','=','FEMENINO')]).id
                if genero == id_femenino and id_carrera == id_arquitecto:
                    carrera_registro = id_arquitecta
                tipo_doc = self.validar_tipo_doc(reg['a_document_type'])
                name = reg['c_name'].split(' ')[0]
                id_guardado = http.request.env['x_procedure_temp'].sudo().create({
                    'x_tipo_documento_select': tipo_doc, 'x_documento': reg['b_document'], 'x_nombres': reg['c_name'], 'x_genero_ID': genero,
                    'x_apellidos': reg['d_lastname'],  'x_fecha_de_grado': fecha, 'x_email': reg['g_email'], 'x_agreement_ID': id_convenio, 
                    'x_grado_ID': id_grado, 'x_carrera_select': carrera_registro, 'x_universidad_select': id_universidad, 
                    'x_origin_type': 'CONVENIO', 'x_fecha_radicacion_universidad': hoy})
                guardados = guardados + 1
            self.grado_check_pagos(grado)
        except IOError:
            _logger.info(IOError)
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar los registros, vuelve a intentarlo'}
        return {'ok': True, 'message': str(guardados)+' Registros guardados con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    # Recibe el archivo csv de graduandos, verifica los datos y le devuelve el resumen y marca fase como realizada
    @http.route('/procesar_archivo', methods=['POST'], type="json", auth='user', website=True) 
    def procesar_csv(self, **kw):
        data = kw.get('data')
        f = data['fecha_grado'].split('-')
        fecha_grado = f[2]+'/'+f[1]+'/'+f[0]
        
        try:
            cadena = data['archivo'].split(',')
            cadena[0] = 'data:application/vnd.ms-excel;base64'
            str_file = ','.join(cadena)
            data_csv = base64.b64decode(str_file)
            data_str = data_csv.decode('cp1252')
        except:
            return {'ok': False, 'message': 'Ha ocurrido un error al leer el archivo, verifique su contenido'}
        _logger.info(data_str)
        rows = data_str.split('\n')
        results = []
        for i in range(0,len(rows)):
            if rows[i] is not rows[0]:
                result = self.validar_datos(rows[i], fecha_grado)
                if result:
                    results.append(result)
        if len(results)<1:
            return {'ok': False, 'message': 'Ningún registro válido en el archivo'}
        else:
            return {'ok': True, 'results': results, 'fecha_grado': data['fecha_grado'], }
                                             
    # Valida la fecha limite con la fecha tmz -5
    def validar_fecha_limite(self, fecha_maxima):
        ahora = datetime.now() - timedelta(hours=5)
        hora_maxima = datetime.combine(fecha_maxima + timedelta(days=1), datetime.min.time())
        _logger.info(ahora)
        _logger.info(hora_maxima)
        if hora_maxima > ahora:
            return True
        else:
            return False
        
    """ FUNCIONES DE VALIDACIÓN DE DATOS CARGA CSV CONVENIOS """
    
    def validar_datos(self, row, fecha_grado):
        datos = row.split(';')
        ok = True
        vals = {'a_document_type':'','b_document':'','c_name':'','d_lastname':'',
                'e_fecha_grado':{'valor': fecha_grado, 'clase':'valido'},'f_gender':'','g_email':''}
        if len(datos) < 5:
            return False
        for x in range(0,len(datos)):
            if self.validar_tipo_doc(datos[0]) != 0:
                vals['a_document_type'] = {'valor':datos[0], 'clase':'valido'}
            else:
                vals['a_document_type'] = {'valor':datos[0], 'clase':'invalido'}
            if self.validar_tipo_doc(datos[0]) != 5:
                if self.validar_solo_numeros(datos[1]) != 0:
                    vals['b_document'] = {'valor':datos[1], 'clase':'valido'}
                else:
                    vals['b_document'] = {'valor':datos[1], 'clase':'invalido'}
            else:
                vals['b_document'] = {'valor':datos[1], 'clase':'warning'}
            if self.validar_solo_letras(datos[2]):
                vals['c_name'] = {'valor':datos[2].upper(), 'clase':'valido'}
            else:
                vals['c_name'] = {'valor':datos[2], 'clase':'invalido'}
            if self.validar_solo_letras(datos[3]):
                vals['d_lastname'] = {'valor':datos[3].upper(), 'clase':'valido'}
            else:
                vals['d_lastname'] = {'valor':datos[3], 'clase':'invalido'}
            if self.validar_genero(datos[4]) != 0:
                vals['f_gender'] = {'valor':datos[4].upper(), 'clase':'valido'}
            else:
                vals['f_gender'] = {'valor':datos[4], 'clase':'invalido'}
            if len(datos) == 6:
                if self.validar_email(datos[5].lstrip().rstrip()):
                    vals['g_email'] = {'valor':datos[5].lower(), 'clase':'valido'}
                else:
                    vals['g_email'] = {'valor':datos[5], 'clase':'invalido'}
            else:
                vals['g_email'] = {'valor':'N/A', 'clase':'valido'}
            return vals
                
    def validar_solo_letras(self, cadena):
        regex = '^[a-zA-ZÑñ ]*$'
        if(re.search(regex, cadena)):  
            return True
        else:  
            return False
    
    def validar_solo_numeros(self, documento):
        regex = '^[0-9]*$'
        if(re.search(regex, documento)):  
            return True
        else:
            return False
        
    def validar_genero(self, genero):
        if (genero == 'M' or genero == 'm'):  
            return 1
        if (genero == 'F' or genero == 'f'):
            return 2
        else:  
            return 0
            
    def validar_email(self, email):
        regex = '^[a-zA-ZÑñ0-9.&_-]+@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if(re.search(regex, email)):
            return True
        else:  
            return False
    
    def validar_tipo_doc(self, tipo):
        if tipo == 'CC' or tipo == 'C.C.':
            return 1
        elif tipo == 'CE' or tipo == 'C.E.':
            return 2
        elif tipo == 'PA' or tipo == 'PA.':
            return 5
        else:
            return 0
    
    @http.route('/validar_documento_bd', methods=["POST"], type="json", auth='user', website=True) 
    def validar_documento_bd(self, **kw):
        data = kw.get('data')
        error = ''
        results = True
        _logger.info(data)
        if data['profesion_id'] == '110' or data['profesion_id'] == '109':
            data['profesion_id'] = ['110','109']
        else:
            data['profesion_id'] = [data['profesion_id']]
        tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',self.validar_tipo_doc(data['tipo_doc'])),
                                                                ('x_studio_documento_1','=',data['numero_doc']),
                                                                ('x_studio_carrera_1.id','in',data['profesion_id'])])
        egresado = http.request.env['x_procedure_temp'].search([('x_tipo_documento_select.id','=',self.validar_tipo_doc(data['tipo_doc'])),
                                                                ('x_documento','=',data['numero_doc']),
                                                                ('x_carrera_select.id','in',data['profesion_id']),
                                                                ('x_origin_type','=','CONVENIO')])
        if egresado:
            results = False
            error = 'Ya existe en egresados un registro para esta profesión con '+data['tipo_doc']+': ' +data['numero_doc']
        if tramite:
            results = False
            error = 'Ya existe este trámite con '+data['tipo_doc']+': ' +data['numero_doc']
        if results:
            return {'ok': True, 'message': 'Todo OK' }
        else:
            return {'ok': False, 'error': error}
        
    def validar_captcha(self, token):
        base_url = 'https://www.google.com/recaptcha/api/siteverify?response=';
        secret = '&secret=6Lf2UcMZAAAAAPUtz3_vPL7H-z8j8cQ1if9fT1Cn';
        response = requests.post(base_url + token + secret)
        _logger.info(response.json()['success'])
        return response.json()['success']
    
    def generar_aleatorio(self, longitud):
        valores = '0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        p = ''
        return p.join([choice(valores) for i in range(longitud)])