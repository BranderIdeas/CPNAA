from odoo import http
from odoo.exceptions import ValidationError
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
from . import certicamara as Certicamara
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

    @http.route(['/my','/my/home'], website=True)
    def redirect_home(self):
        user = http.request.env['res.users'].search([('login','=',http.request.session.login)])
        try:
            # if len(user.groups_id) == 2 and  user.groups_id[0].id == 45 and user.groups_id[1].id == 8:
            if len(user.groups_id) == 2 and all(group.id in (45, 8) for group in user.groups_id):
                _logger.info('Client person => %s' % user.login)
                return http.request.redirect('/profile')
            else:
                return http.request.render('portal.portal_my_home', {})
        except:
            return http.request.render('portal.portal_my_home', {})

    # Crea un usuario tipo persona desde el formulario del website
    # Activa la automatización para la creación y seguimiento del trámite
    @http.route('/create_user', methods=["POST"], auth='public', website=True)
    def create_user(self, **kw):
        resp = {}
        _logger.info(kw)
        ahora               = datetime.now() - timedelta(hours=5)
        hoy                 = ahora.date()
        no_beneficio        = ['licencia','renovacion']
        nombre_tramite      = kw.get('x_tramite')
        fecha_fin           = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value
        fecha_fin_beneficio = datetime.strptime(fecha_fin, '%Y-%m-%d')
        univ_extranjera     = kw.get('x_institution_type_ID')
        from_form_beneficio = kw.get('campo_beneficio')
        beneficio_activo    = ahora < fecha_fin_beneficio and nombre_tramite not in no_beneficio
        beneficio_activo    = beneficio_activo and univ_extranjera == '1' or univ_extranjera == 1
        
        # Validar si viene por el formulario de beneficio
        if from_form_beneficio:
#             error_egresado = self.validar_campos_egresado_acuerdo(kw)
#             if error_egresado != '':
#                 _logger.info(error_egresado)
#                 resp = { 'ok': False, 'message': error_egresado }
#                 return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
            kw.pop('campo_beneficio')
            nombre_campo = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Nombre campo beneficio')]).x_value
            kw[nombre_campo] = '1'
        
        # Validar fecha de grado si hay beneficio activo y entró por formulario normal
        if beneficio_activo and not from_form_beneficio:
            
            fecha_de_grado = kw.get('x_grade_date')
            fecha_maxima   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha maxima grado')]).x_value
            mensaje_info   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje profesional beneficiario no encontrado')]).x_value

            fecha_maxima_grado   = datetime.strptime(fecha_maxima, '%Y-%m-%d').date()
            fecha_grado_tramite  = datetime.strptime(fecha_de_grado, '%Y-%m-%d').date()
            
            if fecha_grado_tramite < fecha_maxima_grado:
                resp = { 'ok': False, 'message': mensaje_info }
                return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
            
        if nombre_tramite in self.nombre_tramite:
            _logger.info('validando 1')
            try:
                campos = ['x_studio_carrera_1', 'x_service_ID']
                validation = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_documento_1','=',kw['x_document']),
                                                                                       ('x_studio_tipo_de_documento_1.id', "=", kw['x_document_type_ID']), 
                                                                                       ('x_cycle_ID.x_order','=',5)], campos)
                for i in validation:
                    if (i['x_studio_carrera_1'][0] == int(kw['x_institute_career'])) and (i['x_service_ID'][1] == self.nombre_tramite[kw['x_tramite']]):
                        _logger.info('validando 1')
                        resp = { 'ok': False, 'message': 'Ya cuenta con éste trámite para la carrera seleccionada, no es posible continuar'}
                        return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
            except:
                pass
        kw.pop('x_tramite')
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
            if (key in self.campos_ID_form_tramites):
                kw[key] = int(kw.get(key))
        try:
            user = http.request.env['x_cpnaa_user'].sudo().create(kw)
            resp = { 'ok': True, 'message': 'Usuario creado con exito',
                     'data_user': {'tipo_doc': kw['x_document_type_ID'], 'documento': kw['x_document']} }
        except:
            # tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        
    
    def validar_campos_egresado_acuerdo(self, record):
        error, campos, previo = '', '', False
        egresado = http.request.env['x_procedure_temp'].search([('x_documento','=',record['x_document'])])
        nombres = record['x_name'] == egresado.x_nombres
        apellidos = record['x_last_name'] == egresado.x_apellidos
        fecha_de_grado = record['x_grade_date'] == egresado.x_fecha_de_grado.strftime('%Y-%m-%d')
        carrera = record['x_institute_career'] == str(egresado.x_carrera_select.id)
        universidad = record['x_institution_ID'] == str(egresado.x_universidad_select.id)
        if not nombres or not apellidos or not fecha_de_grado or not carrera or not universidad:
            error = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje error formulario registro')]).x_value
        if not nombres:
            campos += " 'Nombres'"
            previo = True
        if not apellidos:
            campos += ", 'Apellidos'" if previo else " 'Apellidos'"
            previo = True
        if not universidad:
            campos += ", 'Universidad'" if previo else " 'Universidad'"
            previo = True
        if not fecha_de_grado:
            campos += ", 'Fecha de grado'" if previo else " 'Fecha de grado'"
            previo = True
        if not carrera:
            campos += ", 'Carrera'" if previo else " 'Carrera'"
            previo = True
        error = error.replace('<campos>', campos)
        if error != '':
            self.create_attemp(record, campos)
        return error
    
    def create_attemp(self, rec, error_fields):
        http.request.env['x_cpnaa_attempts'].sudo().create({
            'x_cellphone': rec["x_celphone"],
            'x_document': rec["x_document"],
            'x_document_type_ID': int(rec["x_document_type_ID"]),
            'x_email': rec["x_email"],
            'x_error_fields': error_fields,
            'x_phone': rec["x_local_phone"],
            'x_name': rec["x_name"],
            'x_last_name': rec["x_last_name"],
            'x_grade_date': rec["x_grade_date"],
            'x_institution_ID': rec['x_institution_ID'],
            'x_career_ID': rec['x_institute_career']
        })

    
    # Actualiza el registro desde el formulario del website cuando el el trámite tiene un rechazo
    @http.route('/update_tramite', methods=["POST"], auth='public', website=True)
    def update_tramite(self, **kw):
        resp = {}
        data_user = False
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
            if (key in self.campos_ID_form_tramites):
                kw[key] = int(kw.get(key))
        try:
            tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',kw['x_document_type_ID']),
                                                                    ('x_studio_documento_1','=',kw['x_document']),
                                                                    ('x_cycle_ID.x_order','<',5)])
            user = tramite.x_user_ID
            update = {'x_validation_refuse': False,
                      'x_studio_carrera_1': int(kw.get('x_institute_career')),
                      'x_studio_universidad_5': int(kw.get('x_institution_ID')),
                      'x_full_name': kw.get('x_name')+' '+kw.get('x_last_name'),
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

    # Actualiza la contraseña usuarios tipo portal
    @http.route('/update_password', methods=["POST"], type="json", auth='user', website=True)
    def update_password(self, **kw):
        _logger.info(http.request.session)
        try:
            user = http.request.env['res.users'].sudo().search([('login','=',kw["email"])])
            if len(user.groups_id) == 2:
                if user.groups_id[0].id == 45 or user.groups_id[0].id == 8 and user.groups_id[1].id == 45 or user.groups_id[1].id == 8:
                    user.write(kw["data"])
                else:
                    raise Exception('Is not a CPNAAPP user')
            return { 'ok': True, 'message': 'Password actualizado con exito' }
        except:
            tb = sys.exc_info()[2]
            _logger.info(sys.exc_info())
            return { 'ok': False, 'message': str(sys.exc_info()[1]) }
    
    # Envia email de reestablecimiento de contraseña
    @http.route('/email_forget_password', methods=["POST"], type="json", auth='user', website=True)
    def email_forget_password(self, **kw):
        user = http.request.env['res.users'].sudo().search([('login','=',kw["email"])])
        _logger.info(http.request.session)
        try:
            if not user:
                return { 'ok': False, 'message': 'No se encontro profesional registrado con el email ' + kw["email"] }
            if len(user.groups_id) == 2:
                user.sudo().reset_password_cpnapp()
                return { 'ok': True, 'message': 'Correo electrónico enviado con exito a ' + kw["email"] }
            else:
                raise Exception('Is not a CPNAAPP user')
        except:
            tb = sys.exc_info()[2]
            _logger.info(sys.exc_info())
            return { 'ok': False, 'message': str(sys.exc_info()[1]) }

    # Ruta que renderiza pagina de pagos, si no existe un trámite por pagar lo redirige al inicio del trámite
    @http.route('/pagos/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def epayco(self, tipo_doc, documento):
        url_base   = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        modo_test  = '.dev.odoo.com' in url_base
        response   = '%s/pagos/confirmacion' % url_base
        key_epayco = '9e73b510f7dfd7568b5e876a970962cb' if modo_test else '57d20fccb29db60eb4e1be5ff866548f'
        campos = ['id','x_studio_tipo_de_documento_1','x_studio_documento_1', 'x_origin_type',
                  'x_service_ID','x_rate','x_studio_nombres','x_studio_apellidos', 'x_user_celular',
                  'x_studio_direccin','create_date', 'x_studio_fecha_de_grado_2', 'x_acuerdo_4_2022' ]
        tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                      ('x_studio_documento_1','=',documento),
                                                                      ('x_cycle_ID.x_order','=',0)],campos)
        for tram in tramites:
            servicio       = http.request.env['x_cpnaa_service'].browse(tram['x_service_ID'][0])
            tarifa = self.calcular_tarifa(servicio, tram)
            tram['x_rate'] = tarifa
            http.request.env['x_cpnaa_procedure'].browse(tram['id']).sudo().write({'x_rate': tarifa})
        if (tramites):
            tipo_documento = 'CC'
            if tramites[0]['x_studio_tipo_de_documento_1'][0] == 2:
                tipo_documento = 'CE'
            elif tramites[0]['x_studio_tipo_de_documento_1'][0] == 5:
                tipo_documento = 'PPN'
            return http.request.render('my_sample.epayco', {'tramite': tramites[0], 'modo_test': modo_test, 
                                                            'response': response, 'key_epayco': key_epayco,
                                                            'tipo_documento': tipo_documento })
        else:
            return http.request.redirect('/cliente/tramite/matricula')
        
    
    def calcular_tarifa(self, servicio, tramite):
        origen      = tramite['x_origin_type']
        es_acuerdo  = tramite['x_acuerdo_4_2022']
        fecha_grado = tramite['x_studio_fecha_de_grado_2']
        
        if origen[1] == 'CONVENIO':
            return servicio.x_rate - servicio.x_discount
        elif origen[1] == 'CORTE' and es_acuerdo:
        
            hoy = date.today()
            fecha_creacion = tramite['create_date'].date()
            fecha_maxima   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha maxima grado')]).x_value
            fecha_inicio   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha inicio descuento')]).x_value
            fecha_fin      = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value

            fecha_maxima_grado     = datetime.strptime(fecha_maxima, '%Y-%m-%d').date()
            fecha_inicio_descuento = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_descuento    = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

            aplica_descuento = fecha_creacion >= fecha_inicio_descuento and fecha_creacion <= fecha_fin_descuento
            aplica_descuento = aplica_descuento and fecha_grado <= fecha_maxima_grado
            aplica_descuento = aplica_descuento and hoy <= fecha_fin_descuento
        
            if aplica_descuento:
                return servicio.x_rate - servicio.x_discount
            else:
                return servicio.x_rate
        else:
            return servicio.x_rate
    
    
    # Ruta que renderiza página de respuesta de pasarela de pagos
    @http.route('/pagos/respuesta', auth='public', website=True)
    def respuesta_epayco(self):
        return http.request.redirect('/pagos/confirmacion')
    
    # Ruta que renderiza página de confirmación de pasarela de pagos
    @http.route('/pagos/confirmacion', auth='public', website=True, csrf=False)
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
                    'numero_pago' : data['data']['x_transaction_id'],
                    'fecha_pago'  : data['data']['x_transaction_date'],
                    'banco'       : data['data']['x_bank_name'],
                    'monto_pago'  : data['data']['x_amount'],
                    'tipo_pago'   : (data['data']['x_type_payment']).upper(),
                    'id_tramite'  : data['data']['x_extra1']
                }
                resultado_pago = self.tramite_fase_verificacion(data_tramite)
            elif data['data']['x_response'] == 'Pendiente':
                registrado = http.request.env['x_cpnaa_temp_payments_pending'].sudo().search([('x_epayco_ref','=',ref_payco)])
                if not registrado:
                    http.request.env['x_cpnaa_temp_payments_pending'].sudo().create({
                        'x_epayco_ref'   : ref_payco,
                        'x_procedure_ID' : data['data']['x_extra1'],
                        'x_motive'       : data['data']['x_response_reason_text'],
                        'x_type_payment' : (data['data']['x_type_payment']).upper(),
                        'x_name'         : 'PAGO-PENDIENTE-%s' % data['data']['x_ref_payco']
                    })
                resultado_pago = { 'ok': False, 'message': 'La transacción esta pendiente','error': False, 'numero_radicado': False }
            else:
                resultado_pago = { 'ok': False, 'message': 'La transacción no fue aprobada','error': False, 'numero_radicado': False }
            _logger.info(resultado_pago)
        return http.request.render('my_sample.epayco_confirmacion', {'ok': success, 'data': data, 'resultado_pago': resultado_pago})
    
    def validar_ref_epayco(self, ref_payco):
        base_url = 'https://secure.epayco.co/validation/v1/reference/'
        response = requests.get(base_url + ref_payco)
        return response.json()
    
    # Ruta que renderiza página de formulario de pqrd
    @http.route('/pqrs/formulario', auth='public', website=True)
    def formulario_pqrs(self):
        return http.request.render('my_sample.formulario_pqrs', {})
    
    # Registra la pqrs
    @http.route('/registrar_pqrs', methods=["POST"], auth='public', website=True)
    def registrar_pqrs(self, **kw):
        resp, borrar, attachments_files = {}, [], []
        _logger.info(kw)
        for key, value in kw.items():
            if type(value) != str:
                borrar.append(key)
                attachments_files.append(value)
        for key in borrar:
            del kw[key]
        try:
            consecutivo    = http.request.env['x_cpnaa_consecutive'].sudo().search([('x_name','=','PQRS')])
            kw['x_name']   = 'PQRS-'+str(consecutivo.x_value + 1)
            kw['x_states'] = 'open'
            pqrs           = http.request.env['x_cpnaa_pqrs'].sudo().create(kw)
            if pqrs:
                count = 0
                for at in attachments_files:
                    count += 1
                    file       = base64.b64encode(at.read())
                    ext        = str(at.filename.split('.')[-1]).lower()
                    attachment = {'x_request_ID': pqrs.id, 'x_file': file, 'x_name': 'ADJUNTO-'+str(count)+'-'+pqrs.x_name}
                    if ext == 'pdf':
                        http.request.env['x_pqrs_attachments_pdf'].sudo().create(attachment)
                    else:
                        http.request.env['x_pqrs_attachments_img'].sudo().create(attachment)
                http.request.env['x_cpnaa_consecutive'].browse(consecutivo.id).sudo().write({'x_value':consecutivo.x_value + 1})
            resp = { 'ok': True, 'message': 'Su solicitud ha sido registrada con el consecutivo '+ pqrs.x_name +' exitosamente.' }
        except:
            tb   = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    # Ruta que renderiza página de formulario de denuncias
    @http.route('/denuncias/formulario', auth='public', website=True)
    def formulario_denuncia(self):
        return http.request.render('my_sample.formulario_denuncia', {})
    
    # Ruta que renderiza página de seguimiento de denuncias
    @http.route('/denuncias/seguimiento/<model("x_cpnaa_complaint"):denuncia>', auth='public', website=True)
    def seguimiento_denuncia(self, denuncia):
#         fases = []
#         for x in range(denuncia.x_cycle_ID.x_order + 1):
#             fases.append(http.request.env['x_juridical_service_cycles'].search_read([('x_order','=',x)])[0])
#         for fase in fases:
#             if fase['x_annotation']:
#                 fase['x_annotation'] = fase['x_annotation'].replace('#RADICADO', str(denuncia.x_radicate_number))
#                 fase['x_annotation'] = fase['x_annotation'].replace('#PROCESO', str(denuncia.x_number_process))
#         _logger.info(fases)
        return http.request.render('my_sample.detalle_denuncia', { 'denuncia': denuncia }) #, 'fases': fases
    
    # Servicio para descargar autos de denuncias
    @http.route('/get_attachment', methods=["POST"], type="json", auth='public', website=True)
    def get_attachment(self, **kw):
        _logger.info(kw)
        try:
            denuncia = http.request.env['x_cpnaa_complaint'].sudo().browse(kw['id_denuncia'])
            nom_auto = '%s-%s' % (kw['nombre_archivo'], denuncia.x_name)
            auto     = http.request.env['x_cpnaa_complaints_autos'].sudo().search([('x_name','=',nom_auto),('x_complaint_ID.id','=',denuncia.id)])
            pdf, _   = http.request.env.ref('my_sample.autos_denuncias').sudo().render_qweb_pdf([auto.id])
            pdf64    = base64.b64encode(pdf)
            pdfStr   = pdf64.decode('ascii')
            return {'ok': True, 'mensaje': 'Se ha completado su solicitud exitosamente', 
                    'file_name': 'AUTO-DE-%s' % auto.x_name,
                    'file': {'pdf': pdfStr, 'headers': {'Content-Type', 'application/pdf'}}}
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'error': 'No se podido completar su solicitud', 'file': False}
    
    # Controller para consulta de profesional por tipo y número de documento
    @http.route('/get_profesional', methods=["POST"], type="json", auth='public', website=True)
    def get_profesional(self, **kw):
        _logger.info(kw)
        if kw.get('token'):
            if not self.validar_captcha(kw.get('token')):
                return { 'ok': False, 'error_captcha': True }
        campos = ['x_studio_nombres','x_studio_apellidos','x_studio_carrera_1','x_studio_documento_1','x_enrollment_number',
                  'x_fallecido','x_user_ID'] 
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',kw['tipo_doc']),
                                                                      ('x_studio_documento_1','=',kw['documento']),
                                                                      ('x_cycle_ID.x_order','=',5)],campos)
        if tramites:
            fallecido, user = False, False
            if tramites[0]['x_fallecido']:
                fallecido = True
                user = http.request.env['x_cpnaa_user'].sudo().browse(tramites[0]['x_user_ID'][0])
            if fallecido:
                matricula = user.x_institute_career.x_level_ID.x_name == 'PROFESIONAL'
                return {'ok': True, 'result': tramites, 'data_user': { 'matricula': matricula, 'fallecido': True, 
                        'fecha_resolucion_fallecido': user.x_fecha_resolucion_fallecido, 'documento': user.x_document,
                        'resolucion_fallecido': user.x_resolucion_fallecido, 'tipo_documento': user.x_document_type_ID.x_name,
                        'carrera': user.x_institute_career.x_name}}
            else:
                return {'ok': True, 'result': tramites, 'data_user': {'fallecido': False}}
        else:
            return {'ok': False, 'result': 'No hay registros con la información suministrada'}
        
        # Controller para consulta de profesional por tipo y número de documento
    @http.route('/get_profesional_activacion', methods=["POST"], type="json", auth='public', website=True)
    def get_profesional_activacion(self, **kw):
        _logger.info(kw)
        if kw.get('token'):
            if not self.validar_captcha(kw.get('token')):
                return { 'ok': False, 'error_captcha': True }
        campos = ['x_studio_nombres','x_studio_apellidos','x_studio_carrera_1','x_studio_documento_1','x_enrollment_number',
                  'x_fallecido','x_user_ID','x_expedition_date','x_service_ID','x_studio_tipo_de_documento_1'] 
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.x_name','=',kw['tipo_doc'].upper()),
                                                                      ('x_studio_documento_1','=',kw['documento']),
                                                                      ('x_cycle_ID.x_order','=',5)],campos)
        
        activaciones = http.request.env['x_virtual_activacion_procedure'].sudo().search_read([('x_document_type_ID.x_name','=',kw['tipo_doc'].upper()),
                                                                      ('x_document','=',kw['documento'])],['id'])
        if activaciones:
            return { 'ok': False, 'message': 'Ya ha realizado anteriormente la activación virtual' }
        if tramites:
            fallecido, user, tramite_virtual = False, False, False
            for tram in tramites:
                _logger.info(tram["x_expedition_date"])
                _logger.info(datetime.strptime('2020-09-01' , '%Y-%m-%d'))
                if tram["x_expedition_date"] > datetime.strptime('2020-09-01' , '%Y-%m-%d').date():
                    _logger.info('Ingresando... ')
                    return { 'ok': False, 'message': 'Su Matrícula/Certificado ya es virtual, puede acceder con su documento y contraseña que se envió a su correo. En caso de que no la tenga, acceda por "Olvide mi contraseña"' }
            if tramites[0]['x_fallecido']:
                fallecido = True
                user = http.request.env['x_cpnaa_user'].sudo().browse(tramites[0]['x_user_ID'][0])
            if fallecido:
                matricula = user.x_institute_career.x_level_ID.x_name == 'PROFESIONAL'
                return {'ok': True, 'result': tramites, 'data_user': { 'matricula': matricula, 'fallecido': True, 
                        'fecha_resolucion_fallecido': user.x_fecha_resolucion_fallecido, 'documento': user.x_document,
                        'resolucion_fallecido': user.x_resolucion_fallecido, 'tipo_documento': user.x_document_type_ID.x_name,
                        'carrera': user.x_institute_career.x_name}}
            else:
                return {'ok': True, 'result': tramites, 'data_user': {'fallecido': False}}
        else:
            return {'ok': False, 'result': 'No hay registros con la información suministrada'}
    
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
        kw['x_origin'] = http.request.env["x_cpnaa_origin_complaint"].sudo().search([("x_name","=",'QUEJA EXTERNA')]).id
        try:
            hoy = date.today()
            denuncia = http.request.env['x_cpnaa_complaint'].sudo().create(kw)
            if denuncia:
                count = 0
#                 numero_radicado = Sevenet.sevenet_denuncia(denuncia.id)
                consecutivo = http.request.env['x_cpnaa_consecutive'].sudo().search([('x_name','=','Consecutivo Radicado Temporal Denuncias')])
                numero_radicado = consecutivo.x_value + 1
                consecutivo.sudo().write({'x_value': numero_radicado})
                denuncia.write({ 'x_radicate_number': numero_radicado, 'x_radicate_date': hoy })
                for ev in evidence_files:
                    count += 1
                    file = base64.b64encode(ev.read())
                    evidence = {'x_complaint_ID': denuncia.id, 'x_file': file, 'x_name': 'PRUEBA-'+str(count)+'-'+denuncia.x_name}
                    ext = str(ev.filename.split('.')[-1]).lower()
                    if ext == 'pdf':
                        http.request.env['x_evidence_files_pdf'].sudo().create(evidence)
                    else:
                        evidence['x_extention'] = ext
                        http.request.env['x_evidence_files_img'].sudo().create(evidence)
            message = 'Su queja ha sido registrada con el radicado %s-%s exitosamente.' % (denuncia.x_radicate_number, hoy.year)
            resp = { 'ok': True, 'message': message }
        except:
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    # Ruta que renderiza página de formulario de denuncias
    @http.route('/validar_preguntas', methods=["POST"], type="json", auth='public', website=True)
    def validar_preguntas(self, **kw):
        _logger.info(kw)
        campos = ['x_studio_nombres','x_studio_apellidos','x_studio_carrera_1','x_studio_documento_1','x_enrollment_number'] 
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',kw['tipo_doc']),
                                                                      ('x_studio_documento_1','=',kw['documento']),
                                                                      ('x_cycle_ID.x_order','=',5)],campos)
        if tramites:
            return {'ok': True, 'result': tramites}
        else:
            return {'ok': False, 'result': 'No hay registros con la información suministrada'}
        
    # Guarda el recurso de apelacion, actualiza el trámite, escribe en el mailthread y envia un mail al usuario interno encargado
    @http.route('/save_apelacion', methods=["POST"], type="json", auth='public', website=True) 
    def save_apelacion(self, **kw):
        archivo      = kw.get('archivo_pdf')
        id_denuncia  = kw.get('id_denuncia')
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf  = archivo_temp.lstrip('data:application/pdf;base64,')
        denuncia     = http.request.env['x_cpnaa_complaint'].sudo().search([('id','=',id_denuncia)])
        actualizado  = False
        try:
            update = {'x_appeal_resource_file': archivo_pdf, 'x_state_for_buttons': 'x_appeal_file_received',
                      'x_state': 'x_archive_appeal', 'x_phase_5': True}
            actualizado = http.request.env['x_cpnaa_complaint'].browse(id_denuncia).sudo().write(update)
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'error': str(sys.exc_info()[1])}
        if actualizado:
            subject = '%s %s ha cargado el archivo de Recurso de Apelación' % (denuncia.x_complainant_names, denuncia.x_complainant_lastnames)
            mailthread = {
                'subject': subject,
                'model': 'x_cpnaa_complaint',
                'email_from': denuncia.x_complainant_names+' '+denuncia.x_complainant_lastnames,
                'subtype_id': 2,
                'body': subject,
                'author_id': 4,
                'message_type': 'notification',
                'res_id': denuncia.id
            }
            http.request.env['mail.message'].sudo().create(mailthread)
#             http.request.env['mail.template'].sudo().search([('name','=','cpnaa_template_load_CD')])[0].sudo().send_mail(id_tramite,force_send=True)
            return {'ok': True, 'message': 'Denuncia Actualizada, se guardo el archivo de apelación en PDF.'}
        else:
            return {'ok': False, 'error': 'Denuncia no pudo ser actualizada, intente nuevamente.'}
        
    # Ruta que renderiza página de consulta de registro por documento
    @http.route('/consulta_online/por_documento', auth='public', website=True)
    def consulta_por_documento(self):
        return http.request.render('my_sample.consulta_registro', {'form': 'por_documento'})
        
    # Ruta que renderiza página de consulta de registro por numero de tarjeta
    @http.route('/consulta_online/por_numero', auth='public', website=True)
    def consulta_por_numero(self):
        return http.request.render('my_sample.consulta_registro', {'form': 'por_numero'})
    
    # Ruta que renderiza página de consulta estado trámite
    @http.route('/cliente/tramite/consulta', auth='public', website=True)
    def estado_tramite(self):
        return http.request.render('my_sample.inicio_tramite', {'form': 'consulta', 'inicio_tramite': False})
    
           
    # Realiza la consulta del registro online por documento o numero de tarjeta
    @http.route('/realizar_consulta', methods=["POST"], type="json", auth='public', website=True)
    def realizar_consulta(self, **kw):
        data = kw.get('data')
        tramites = []
        if self.validar_captcha(kw.get('token')):
            ahora = datetime.now() - timedelta(hours=5)
            hora_consulta = ahora.strftime('%Y-%m-%d %H:%M:%S')
            campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_pas_de_expedicin_1',
                      'x_origin_type', 'x_studio_ciudad_de_expedicin','x_resolution_ID', 'x_legal_status', 'x_sanction', 'x_user_ID',
                      'x_studio_ciudad_de_expedicin','x_studio_carrera_1','x_studio_gnero','x_studio_fecha_de_resolucin',
                      'x_studio_nombres','x_studio_apellidos','x_enrollment_number','x_fecha_resolucion_corte', 'x_fallecido']
            if data['numero_tarjeta'] != '':
                tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_enrollment_number','=',data['numero_tarjeta']),
                                                                              ('x_cycle_ID.x_order','=',5)],campos)
            else:
                tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',data['doc_type']),
                                                                              ('x_studio_documento_1','=',data['doc']),
                                                                              ('x_cycle_ID.x_order','=',5)],campos)
            if tramites:
                for tramite in tramites:
                    tramite['x_female_career'] = http.request.env['x_cpnaa_career'].sudo().search([('id','=',tramite['x_studio_carrera_1'][0])]).x_female_name
                    tramite['x_resolution_number'] = http.request.env['x_cpnaa_resolution'].sudo().search([
                        ('id','=',tramite['x_resolution_ID'][0])]).x_consecutive
                    if tramite['x_fallecido']:
                        user = http.request.env['x_cpnaa_user'].sudo().browse(tramite['x_user_ID'][0])
                        tramite['x_resolucion_fallecido'] = user.x_resolucion_fallecido
                        tramite['x_fecha_resolucion_fallecido'] = user.x_fecha_resolucion_fallecido
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
        url_base  = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        modo_test = '.dev.odoo.com' in url_base
        _logger.info(data)
        ahora = datetime.now() - timedelta(hours=5)
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('id','=',int(data['id_tramite']))])
        numero_recibo = tramite.x_voucher_number
        numero_radicado = tramite.x_orfeo_radicate
        if (not data['corte'] and numero_recibo) and (data['corte'] == tramite.x_origin_name and numero_recibo):
            pass
        elif not numero_recibo or (data['corte'] and data['corte'] != tramite.x_origin_name):
            consecutivo = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Consecutivo Recibo de Pago')])
            numero_recibo = int(consecutivo.x_value) + 1
            numero_radicado = Sevenet.sevenet_consulta(tramite.id, 'Recibo')
            update = {'x_voucher_number': numero_recibo, 'x_orfeo_date': ahora, 'x_orfeo_radicate': numero_radicado }
            if data['corte']:
                update = {'x_voucher_number': numero_recibo,'x_origin_name': data['corte'],
                          'x_orfeo_date': ahora, 'x_orfeo_radicate': numero_radicado}                
            http.request.env['x_cpnaa_parameter'].browse(consecutivo.id).sudo().write({'x_value':str(numero_recibo)})
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).sudo().write(update)
        return {'ok': True, 'numero_recibo': str(numero_recibo), 'numero_radicado': str(numero_radicado)}
    
    # Envia la información necesaria para el recibo de pago o para el pago desde la pasarela
    @http.route('/tramite_fase_inicial', methods=["POST"], type="json", auth='public', website=True)
    def tramite_fase_inicial(self, **kw):
        data = kw.get('data')
        now = datetime.now() - timedelta(hours=5)
        today = now.date()
        campo_beneficio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Nombre campo beneficio')]).x_value
        campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_correo_electrnico',
                  'x_user_celular','x_studio_pas_de_expedicin_1','x_studio_ciudad_de_expedicin','x_studio_direccin',
                  'x_req_date','x_rate','x_studio_universidad_5','x_studio_carrera_1','x_studio_departamento_estado',
                  'x_studio_fecha_de_grado_2','x_studio_ciudad_1','x_origin_name','x_studio_nombres','x_studio_apellidos',
                  'x_studio_telfono','x_origin_type','x_grade_ID',campo_beneficio]
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',data['doc_type']),
                                                                      ('x_studio_documento_1','=',data['doc']),
                                                                      ('x_cycle_ID.x_order','=',0)],campos)
        
        fecha_inicio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha inicio descuento')]).x_value
        fecha_fin = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value
        fecha_inicio_descuento = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_descuento = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        beneficio_activo = today >= fecha_inicio_descuento and today <= fecha_fin_descuento
        
        if tramites:
            # Código del servicio para generar el código de barras del recibo
            codigo = http.request.env['x_cpnaa_service'].search([('id','=',tramites[0]['x_service_ID'][0])]).x_code
            if (tramites[0]['x_origin_type'][1] == 'CORTE'):
                corte_vigente = self.buscar_corte(tramites[0]['x_origin_name'])
                _logger.info(corte_vigente)
                if beneficio_activo:
                    #Si el tramite es por beneficio y esta activo que la fecha limite de pago no sea mayor a la fecha fin del beneficio
                    if tramites[0][campo_beneficio]:
                        fecha_fin = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value
                        fecha_fin_descuento = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                        if fecha_fin_descuento < corte_vigente['x_lim_pay_date']:
                            corte_vigente['x_lim_pay_date'] = fecha_fin_descuento
                    tramites[0]['x_origin_name'] = corte_vigente['x_name']
                # else:
                #     http.request.env['x_cpnaa_procedure'].sudo().browse(tramites[0]['id']).write({ campo_beneficio: False })
                return {'ok': True, 'tramite': tramites[0], 'codigo': codigo, 'corte': corte_vigente}
            elif tramites[0]['x_grade_ID']:
                grado = http.request.env['x_cpnaa_grade'].sudo().browse(tramites[0]['x_grade_ID'][0])
                fecha_lim = None
                if grado:
                    if grado.x_agreement_ID.x_before_after_agreement:
                        fecha_lim = grado.x_date + timedelta(days=grado.x_agreement_ID.x_days_to_pay_after)
                    else:
                        fecha_lim = grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)
                ok = True if self.validar_fecha_limite(fecha_lim) else False
                return {'ok': ok, 'tramite': tramites[0], 'codigo': codigo, 'grado': { 'id': grado.id, 'x_fecha_limite': fecha_lim }}
            else:
                return {'ok': False, 'error': 'Ha ocurrido un error con el origen del trámite'}
        else:
            return {'ok': False , 'error': 'Tramite no existe'}

    # Si el pago es aprobado pasa el trámite a fase de verificación, registra los cambios en el mailthread
    def tramite_fase_verificacion(self, data):
        url_base  = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        modo_test = '.dev.odoo.com' in url_base
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
                    numero_radicado = Sevenet.sevenet_consulta(tramite.id, data['tipo_pago'])
                    if (tramite.x_origin_type.x_name == 'CORTE'):
                        corte_vigente = self.buscar_corte(tramite.x_origin_name)
                        origin_name = corte_vigente['x_name']
                    else:
                        origin_name = tramite.x_origin_name
                        grado = http.request.env['x_cpnaa_grade'].sudo().browse(tramite.x_grade_ID.id)
                    ciclo_ID = http.request.env["x_cpnaa_cycle"].sudo().search(["&",("x_service_ID.id","=",tramite["x_service_ID"].id),("x_order","=",1)])
                    update = {'x_cycle_ID': ciclo_ID.id,'x_orfeo_date': datetime_str, 'x_pay_datetime': datetime_str,
                              'x_pay_type': data['tipo_pago'],'x_consignment_number': data['numero_pago'], 'x_bank': data['banco'],
                              'x_consignment_price': int(float(data['monto_pago'])),'x_origin_name': origin_name, 'x_orfeo_radicate': numero_radicado}
                    pago_registrado = http.request.env['x_cpnaa_procedure'].browse(tramite['id']).sudo().write(update)
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
                    'mailthread': mailthread_registrado.id, 'error': False, 'id_user': user.id, 'numero_radicado': numero_radicado }
        if pago_registrado and error:
            _logger.info(error)
            return { 'ok': True, 'message': 'Trámite actualizado con exito', 'error': error, 
                    'id_user': user.id, 'numero_radicado': numero_radicado } 
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
        nombre_tramite = self.nombres_tramites(form)
        if nombre_tramite:
            return http.request.render('my_sample.inicio_tramite', {'form': form, 'inicio_tramite': True, 'nombre_tramite': nombre_tramite})
        else:
            return http.request.redirect('/cliente/tramite/matricula')
        
    # Ruta que renderiza el inicio del trámite (beneficiarios)
    @http.route('/cliente/tramite/beneficio/<string:form>', auth='public', website=True)
    def inicio_beneficio(self, form):
        validos = ['matricula','inscripciontt']
        if form in validos:
            texto_beneficio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Texto beneficio')]).x_value
            return http.request.render('my_sample.inicio_tramite_beneficio', {'form': form, 'inicio_tramite': True, 
                                                                              'texto_beneficio': texto_beneficio })
        else:
            return http.request.redirect('https://cpnaa.gov.co/')
    
    # Ruta que renderiza el inicio del trámite (usuarios de convenios)
    @http.route('/convenios/tramite', auth='public', website=True)
    def inicio_convenio(self):
        return http.request.render('my_sample.inicio_tramite', {'form': 'convenio', 'inicio_tramite': True, 'por_nombre': False })
    
    # Ruta que renderiza el inicio del trámite (usuarios de convenios)
    @http.route('/convenios/tramite/por_nombre', auth='public', website=True)
    def inicio_convenio_nombre(self):
        return http.request.render('my_sample.inicio_tramite', {'form': 'convenio', 'inicio_tramite': True, 'por_nombre': True })
        
    # Ruta que renderiza el inicio de actualización/coreeción de registro
    @http.route('/tramites/correccion_datos', auth='public', website=True)
    def inicio_correccion(self):
        return http.request.render('my_sample.inicio_correccion', {})
    
    # Ruta que renderiza página de formulario de denuncias
    @http.route('/get_correccion', methods=["POST"], type="json", auth='public', website=True)
    def get_correccion(self, **kw):
        if kw.get('token'):
            if not self.validar_captcha(kw.get('token')):
                return { 'ok': False, 'error_captcha': True }

        campos = ['x_studio_nombres','x_studio_apellidos','x_studio_carrera_1','x_studio_documento_1','x_enrollment_number',
                  'x_fallecido', 'x_user_ID', 'x_studio_tipo_de_documento_1'] 
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',kw['tipo_doc']),
                                                                             ('x_studio_documento_1','=',kw['documento']),
                                                                             ('x_cycle_ID.x_order','=',5)], campos)
        
        for tram in tramites:
            campos = ['x_names','x_lastnames','x_document_type_ID','x_document_number','x_issue','x_state', 'x_procedure_ID', 
                      'x_name', 'x_rejected']
            correccion = http.request.env['x_registry_correction_request'].sudo().search_read([('x_procedure_ID','=',tram['id']),
                                                                                               ('x_state','!=','x_completed')], campos)
        
            if len(correccion) > 0:
                for corr in correccion:
                    tram['solicitud_en_curso'] = True
                    tram['nombre_solicitud'] = corr['x_name']
                    tram['tiene_rechazo'] = corr['x_rejected']
            else:
                tram['solicitud_en_curso'] = False
            
            if tram['x_fallecido']:
                user = http.request.env['x_cpnaa_user'].sudo().browse(tram['x_user_ID'][0])
                tram['x_matricula'] = user.x_institute_career.x_level_ID.x_name == 'PROFESIONAL'
                tram['x_resolucion_fallecido'] = user.x_resolucion_fallecido
                tram['x_fecha_resolucion_fallecido'] = user.x_fecha_resolucion_fallecido

        if len(tramites) < 1:
            return {'ok': False, 'result': 'No hay registros con la información suministrada'}
        return {'ok': True, 'result': tramites}

        
    # Ruta que renderiza el inicio del trámite actualización/coreeción de registro
    @http.route('/tramites/solicitud_correccion/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def solicitud_correccion(self, tramite):
        solicitud = http.request.env['x_registry_correction_request'].sudo().search([('x_procedure_ID','=',tramite.id),
                                                                                     ('x_state','!=','x_complete')])
        if tramite.x_cycle_ID.x_order != 5 or solicitud:
            return http.request.redirect('/tramites/correccion_datos')
        return http.request.render('my_sample.solicitud_correccion', {'tramite': tramite})
    
    # Ruta que renderiza el inicio del trámite actualización/coreeción de registro
    @http.route('/tramites/editar/solicitud_correccion/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def edit_solicitud_correccion(self, tramite):
        solicitud = http.request.env['x_registry_correction_request'].sudo().search([('x_procedure_ID','=',tramite.id),
                                                                                     ('x_rejected','=',True)])
        if tramite.x_cycle_ID.x_order != 5 or not solicitud:
            return http.request.redirect('/tramites/correccion_datos')
        return http.request.render('my_sample.solicitud_correccion', {'tramite': tramite, 'solicitud': solicitud})
    
    # Ruta que renderiza el inicio del trámite actualización/coreeción de registro
    @http.route('/registrar_solicitud_correccion', methods=["POST"], auth='public', website=True)
    def registrar_solicitud_correccion(self, **kw):
        resp = {}
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
        try:
            kw['x_issue'] = int(kw['x_issue'])
            kw['x_service_ID'] = self.asignar_servicio(kw['x_service_ID'])
            kw['x_procedure_ID'] = int(kw['x_procedure_ID'])
            kw['x_name'] = http.request.env['ir.sequence'].sudo().next_by_code('x_registry_correction_request.sequence')
            kw['x_state'] = 'x_VD'
            message = 'Su solicitud ha sido recibida correctamente con el radicado No. %s y a vuelta de correo electrónico recibira la respuesta.' % kw['x_name']
            solicitud = http.request.env['x_registry_correction_request'].sudo().create(kw)
            resp = { 'ok': True, 'message': message, 'id': solicitud.id }
        except:
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    def asignar_servicio(self, service_ID):
        nivel_prof = http.request.env['x_cpnaa_service'].sudo().search([('id','=',service_ID)]).x_studio_nivel_profesional
        nivel_prof = nivel_prof if len(nivel_prof) == 1 else nivel_prof[0]
        if nivel_prof.x_name == 'PROFESIONAL':
            return http.request.env['x_cpnaa_service'].sudo().search([('x_name','=','ACTUALIZACION DE DATOS Y CORRECCION DEL REGISTRO DE ARQUITECTO')]).id
        else:
            return http.request.env['x_cpnaa_service'].sudo().search([('x_name','=','ACTUALIZACIÓN DE DATOS Y CORRECIÓN DEL REGISTRO DE AUXILIAR')]).id
    
    # Ruta que actualiza el trámite actualización/correción de registro
    @http.route('/update_solicitud_correccion', methods=["POST"], auth='public', website=True)
    def update_solicitud_correccion(self, **kw):
        resp = {}
        _logger.info(kw)
        id_solicitud = kw.get('id_solicitud')
        del kw['id_solicitud']
        for key, value in kw.items():
            if type(value) != str:
                kw[key] = base64.b64encode(kw[key].read())
        try:
            kw['x_issue'] = int(kw['x_issue'])
            kw['x_rejected'] = False
            solicitud = http.request.env['x_registry_correction_request'].sudo().browse(int(id_solicitud))
            solicitud.write(kw)
            message = 'Su solicitud %s ha sido actualizada correctamente y a vuelta de correo electrónico recibira la respuesta.' % solicitud.x_name
            resp = { 'ok': True, 'message': message, 'id': solicitud.id }
            mailthread = {
                'subject': '%s %s ha sido corregido su solicitud' % (solicitud.x_names, solicitud.x_lastnames),
                'model': 'x_registry_correction_request',
                'email_from': solicitud.x_names+' '+solicitud.x_lastnames,
                'subtype_id': 2,
                'body': '%s %s ha sido corregido su solicitud' % (solicitud.x_names, solicitud.x_lastnames),
                'author_id': 4,
                'message_type': 'notification',
                'res_id': solicitud.id
            }
            http.request.env['mail.message'].sudo().create(mailthread)
            rechazos = http.request.env['x_refuse_correction_request'].sudo().search([('x_request_ID','=',solicitud.id)])
            rechazos[-1].write({'x_corrected': True})
        except:
            tb = sys.exc_info()[2]
            resp = { 'ok': False, 'message': str(sys.exc_info()[1]) }
            _logger.info(sys.exc_info())
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        
    # Ruta que renderiza el inicio del trámite acceso matrícula virtual
    @http.route('/tramites/solicitud_virtual', auth='public', website=True)
    def inicio_mat_virtual(self):
        return http.request.render('my_sample.inicio_mat_virtual', {})
    
    # Ruta que renderiza las preguntas para el trámite acceso matrícula virtual
    @http.route('/tramites/solicitud_virtual/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def preguntas_mat_virtual(self, tramite):
        return http.request.render('my_sample.preguntas_mat_virtual', {'tramite': tramite})
    
    # Retorna los datos del trámite para el formulario de edición
    @http.route('/validar_respuestas', methods=["POST"], type="json", auth='public', website=True)
    def validar_respuestas(self, **kw):
        correctas, tramite_valido, success = None, False, False
        min_validas = 3
        data = kw.get('data')
        _logger.info(data)
        camposString = ['x_enrollment_number']
        camposManyTo = ['x_studio_ciudad_de_expedicin','x_studio_carrera_1','x_studio_universidad_5']
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',data['x_doc_type_ID']),
                                                                        ('x_studio_documento_1','=',data['x_document'])])
        for tram in tramites:
            correctas = 0
            _logger.info(tram['x_studio_fecha_de_grado_2'].year)
            if str(tram['x_studio_fecha_de_grado_2'].year) == data['x_studio_fecha_de_grado_2']:
                correctas += 1
            for val in camposString:
                if str(tram[val]) == str(data[val]):
                    correctas += 1
            for val in camposManyTo:
                if str(tram[val]['id']) == str(data[val]):
                    correctas += 1
            if correctas >= min_validas:
                tramite_valido = tram
                success = True
        _logger.info(tramite_valido)
        if success:
            usuario = http.request.env['res.users'].sudo().search([('login','=',tramite_valido.x_studio_correo_electrnico)])
            if len(usuario) > 1:
                message_dup = 'No es posible activar la matrícula virtual en este momento. Ya existe una matrícula virtual con estos datos. Por favor comuníquese con el CPNAA'
                return { 'ok': False, 'email_existe': True, 'message': message_dup }
            # Valida si ya existe un usuario con esa dirección de email
            search_user = http.request.env["res.users"].sudo().search(['|',("login","=",data.get('x_request_email').lower()),
                                                                           ("login","=",data.get('x_request_email').upper())])
            if data.get('x_request_email') == tramite_valido.x_studio_correo_electrnico.lower():
                pass
            elif search_user and len(search_user) == 1 and search_user.login == usuario.login:
                return { 'ok': False, 'email_existe': True, 'message': 'Ya existe otro usuario registrado con el correo electrónico suministrado' }
            elif not search_user and data.get('x_request_email') != tramite_valido.x_studio_correo_electrnico.lower():
                return { 'ok': False, 'email_existe': True, 'message': 'El correo ingresado no coincide con el que tenemos registrado, ¿Desea actualizarlo?',
                         'id_tramite': tramite_valido.id, 'id_usuario': usuario.id, 'email': data.get('x_request_email')}
            actualizacion = self.actualizar_usuario(tramite_valido, usuario, data.get('x_request_email'))
            if actualizacion:
                return { 'ok': True, 'data': { 'ok': True, 'email': data.get('x_request_email'), 
                                           'servicio': tramite_valido.x_service_ID.x_name } }
        else:
            return { 'ok': False, 'respuestas': False,'message': 'No cumple con el minimo de respuestas validas' }
    
    # Confirmación de cambio de email en activación virtual 
    @http.route('/confirmar_email', methods=["POST"], type="json", auth='public', website=True)
    def confirmacion_email(self, **kw):
        _logger.info(kw)
        data = kw.get('data')
        tramite = http.request.env['x_cpnaa_procedure'].sudo().browse(data.get('id_tramite'))
        usuario = http.request.env['res.users'].sudo().browse(data.get('id_usuario'))
        actualizacion = self.actualizar_usuario(tramite, usuario, data.get('x_request_email'))
        if actualizacion:
            return { 'ok': True, 'data': { 'ok': True, 'email': data.get('x_request_email'), 
                                           'servicio': tramite.x_service_ID.x_name } }
        else:
            return { 'ok': False, 'message': 'No se pudo completar la autorización' }
        
    def actualizar_usuario(self, tramite, usuario, email):
        try:
            # Asigna contraseña
            password = str(tramite.id)+str(tramite.x_resolution_ID.x_consecutive)
            cambio_email = '.' if tramite.x_studio_correo_electrnico == email else ' y ha actualizado su email "%s" por "%s".' % (tramite.x_studio_correo_electrnico, email)
            update_user = {'login': email, 'password': password, 'new_password': password}
            update_tramite = {'x_studio_correo_electrnico': email}
            http.request.env['res.users'].browse(usuario.id).sudo().write(update_user)
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).sudo().write(update_tramite)
            http.request.env['x_virtual_activacion_procedure'].sudo().create({
                'x_name': 'ACTIVACION-VIRTUAL-%s-%s' % (tramite.x_studio_nombres, tramite.x_studio_apellidos),
                'x_procedure_ID': tramite.id,
                'x_request_email': email,
            })
            http.request.env['mail.template'].sudo().browse(29).send_mail(tramite.id,force_send=True)
            subject = '%s %s ha realizado la activación virtual' % (tramite.x_studio_nombres, tramite.x_studio_apellidos)
            body = '%s %s ha realizado la activación virtual%s' % (tramite.x_studio_nombres, tramite.x_studio_apellidos, cambio_email)
            self.mailthread_tramite(tramite.id, tramite.x_studio_nombres, tramite.x_studio_apellidos,
                                    subject, body, tramite.x_user_ID.x_partner_ID.id)
            return True
        except:
            _logger.info(sys.exc_info())
            return False
        
    # Ruta que renderiza el validacion de autenticiadad del certificado de vigencia virtual
    @http.route('/tramites/validacion_cert_de_vigencia', auth='public', website=True)
    def validacion_cert_de_vigencia(self):
        return http.request.render('my_sample.validacion_cert_de_vigencia', {})
            
    # Ruta que renderiza el validacion de autenticiadad del certificado de vigencia con destino al exterior
    @http.route('/tramites/validacion_cert_de_vigencia_exterior', auth='public', website=True)
    def validacion_cert_de_vigencia_exterior(self):
        return http.request.render('my_sample.validacion_cert_de_vigencia_exterior', {})
    
    # Valida si existe un certificado con el codigo de seguridad recibido
    @http.route('/verificar_autenticidad', methods=["POST"], type="json", auth='public', website=True)
    def verificar_autenticidad(self, **kw):
        data = kw.get('data')
        _logger.info(data)
        is_exterior = data.get('is_exterior')
        model = 'x_procedure_service_exterior' if is_exterior else 'x_procedure_service'
        if self.validar_captcha(kw.get('token')):
            campos = ['id','x_procedure_ID','create_date', 'x_consecutive'] if is_exterior else ['id','x_procedure_ID','create_date', 'x_consecutivo', 'x_create_date_migration']
            certificado = http.request.env[model].sudo().search_read([('x_procedure_ID.x_studio_tipo_de_documento_1','=',int(data['tipo_doc'])),
                                                                      ('x_procedure_ID.x_studio_documento_1','=',data['documento']),
                                                                      ('x_validity_code','=',data['x_code'])],campos)
            if certificado:
                campos = ['id','x_studio_nombres','x_studio_apellidos', 'x_studio_tipo_de_documento_1', 'x_studio_documento_1']
                profesional = http.request.env['x_cpnaa_procedure'].sudo().search_read([('id','=',certificado[0]['x_procedure_ID'][0])], campos)
    #             tiempo_expiracion = http.request.env['x_cpnaa_service'].sudo().search([('id','=',certificado[0]['x_service_ID'][0])]).x_validity
                _logger.info(certificado[0])
                if not is_exterior and certificado[0]['x_create_date_migration']:
                    certificado[0]['create_date'] = certificado[0]['x_create_date_migration']
                certificado[0]['expiration_date'] = certificado[0]['create_date'] + dateutil.relativedelta.relativedelta(months=6)
                return {'ok': True, 'mensaje': 'El Certificado se encuentra registrado en nuestra Base de Datos.', 
                        'certificado': certificado[0], 'profesional': profesional}
            else:
                return {'ok': False, 'mensaje': 'El Certificado no se encuentra registrado en nuestra Base de Datos.' }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True }
    
    # Ruta que renderiza el inicio del trámite certificado de vigencia con destino al exterior
    @http.route('/tramites/certificado_vigencia_exterior', auth='public', website=True)
    def inicio_cert_exterior(self):
        return http.request.render('my_sample.inicio_cert_vigencia', {'exterior': True})

    # Ruta que renderiza el resultado del trámite certificado de vigencia con destino al exterior
    @http.route('/tramites/certificado_vigencia_exterior/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def certificado_vigencia_exterior(self, tramite):
        _logger.info(tramite.x_legal_status)
        if tramite:
            return http.request.render('my_sample.certificado_vigencia', {'tramite': tramite, 'exterior': True})
        else:
            return http.request.redirect('/tramites/certificado_vigencia')
        
    # Ruta que renderiza el inicio del trámite certificado de vigencia virtual
    @http.route('/tramites/certificado_de_vigencia', auth='public', website=True)
    def inicio_cert_vigencia(self):
        return http.request.render('my_sample.inicio_cert_vigencia', {'digital': True})
    
    # Ruta que renderiza el resultado del trámite certificado de vigencia virtual
    @http.route('/tramites/certificado_de_vigencia/<model("x_cpnaa_procedure"):tramite>', auth='public', website=True)
    def certificado_vigencia(self, tramite):
        _logger.info(tramite.x_legal_status)
        if tramite:
            return http.request.render('my_sample.certificado_vigencia', {'tramite': tramite, 'digital': True})
        else:
            return http.request.redirect('/tramites/certificado_de_vigencia')

            
    # Ruta que renderiza el inicio del trámite certificado de vigencia virtual fallecidos
    @http.route('/tramites/certificado_vigencia_fallecidos', auth='public', website=True)
    def inicio_cert_fallecidos(self):
        return http.request.render('my_sample.inicio_cert_vigencia', {'fallecidos': True})

    
    # Valida si existe un trámite completo
    @http.route('/verificar_certificado', methods=["POST"], type="json", auth='public', website=True)
    def verificar_certificado(self, **kw):
        data = kw.get('data')
        campos = ['id','x_studio_carrera_1','x_legal_status', 'x_fallecido', 'x_user_ID']
        if self.validar_captcha(kw.get('token')):
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',data['tipo_doc']),
                                                                          ('x_studio_documento_1','=',data['documento']),
                                                                          ('x_cycle_ID.x_order','=',5)], campos)
            if tramites:
                fallecido, user = False, False
                mensaje = 'Si existen registros para este tipo y número de documento'
                if tramites[0]['x_fallecido']:
                    fallecido = True
                    user = http.request.env['x_cpnaa_user'].sudo().browse(tramites[0]['x_user_ID'][0])
                if fallecido:
                    matricula = user.x_institute_career.x_level_ID.x_name == 'PROFESIONAL'
                    return {'ok': True, 'tramites': tramites, 'mensaje': mensaje, 'data_user': { 'matricula': matricula, 'fallecido': True, 
                            'fecha_resolucion_fallecido': user.x_fecha_resolucion_fallecido, 'documento': user.x_document,
                            'resolucion_fallecido': user.x_resolucion_fallecido, 'tipo_documento': user.x_document_type_ID.x_name,
                            'carrera': user.x_institute_career.x_name}}
                else:
                    return {'ok': True, 'mensaje': mensaje, 'tramites': tramites, 'data_user': {'fallecido': False}}
            else:
                return {'ok': False, 'mensaje': 'No existen registros para este tipo y número de documento', 'tramites': tramites }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True  }
    
    
    # Valida si existe un trámite y el profesional esta registrado como fallecido
    @http.route('/verificar_fallecidos', methods=["POST"], type="json", auth='public', website=True)
    def verificar_fallecidos(self, **kw):
        data = kw.get('data')
        if self.validar_captcha(kw.get('token')):
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_tipo_de_documento_1.id','=',data['tipo_doc']),
                                                                          ('x_studio_documento_1','=',data['documento']),
                                                                          ('x_fallecido','=',True),
                                                                          ('x_cycle_ID.x_order','=',5)],
                                                                          ['id','x_studio_carrera_1','x_legal_status'])
            if tramites:
                mensaje = 'Si existe registro de profesional fallecido para este tipo y número de documento'
                return {'ok': True, 'mensaje': mensaje, 'tramites': tramites }
            else:
                return {'ok': False, 'mensaje': 'No existe registro de profesional fallecido para este tipo y número de documento', 'tramites': tramites }
        else:
            return { 'ok': False, 'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página', 'error_captcha': True  }


    # Enviar el certificado de vigencia al email y lo retorna al navegador para su descarga
    @http.route('/enviar_certificado_vigencia', methods=["POST"], type="json", auth='public')
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
        # pdf_firmado = Certicamara.firmar_certificado(pdfStr, certificado.id, 'vigencia')
        cert = http.request.env['ir.attachment'].sudo().create({
            'name': 'certificado-vigencia-profesional-%s.pdf' % tramite.x_studio_documento_1,
            'type': 'binary',
            'datas': pdfStr,
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

    # Enviar el certificado de vigencia al email y lo retorna al navegador para su descarga
    @http.route('/generar_certificado_exterior', methods=["POST"], type="json", auth='public')
    def generar_certificado_exterior(self, **kw):
        now   = datetime.now() - timedelta(hours=5)
        today = now.date()
        nombre_tramite = 'CERTIFICADO DE VIGENCIA CON DESTINO AL EXTERIOR'
        tramite        = http.request.env['x_cpnaa_procedure'].sudo().search([('id','=',kw.get('id_tramite'))])
        cert_template  = http.request.env['x_cpnaa_template'].sudo().search([('x_name','=',nombre_tramite)])
        consecutivo    = http.request.env['x_cpnaa_consecutive'].sudo().search([('x_name','=',nombre_tramite)])
        servicio       = http.request.env['x_cpnaa_service'].sudo().search([('x_name','like',nombre_tramite),
                                                                            ('x_studio_nivel_profesional.x_name','=',tramite.x_service_ID.x_studio_nivel_profesional[0].x_name)])
        certificado = http.request.env['x_procedure_service_exterior'].sudo().create({
            'x_doc_gen': cert_template.x_html_content,
            'x_procedure_ID': tramite.id,
            'x_service_ID': servicio.id,
            'x_consecutive': consecutivo.x_value + 1,
            'x_state': 'x_completed',
            'x_completed': True,
            'x_procedure_finish_date': today,
            'x_validity_code': self.generar_aleatorio(7),
            'x_name': 'CERT-VIG-EXT-%s-%s' % (tramite.x_studio_nombres, tramite.x_studio_apellidos),
            'x_email': kw.get('email'),
            'x_cel_contact': kw.get('celular')
        })
        if certificado:
            consecutivo.sudo().write({'x_value': consecutivo.x_value + 1})
#             numero_radicado = Sevenet.sevenet_certificado_exterior(certificado.id)
#             certificado.sudo().write({'x_radicate_number': numero_radicado })

        pdf, _ = http.request.env.ref('my_sample.cert_vigencia_exterior').sudo().render_qweb_pdf([certificado.id])
        pdf64  = base64.b64encode(pdf)
        pdfStr = pdf64.decode('ascii')
        # pdf_firmado = Certicamara.firmar_certificado(pdfStr, certificado.id, 'exterior')
        cert   = http.request.env['ir.attachment'].sudo().create({
            'name': 'certificado-vigencia-profesional-destino-exterior-%s.pdf' % tramite.x_studio_documento_1,
            'type': 'binary',
            'datas': pdfStr,
            'mimetype': 'application/x-pdf'
        })
        mail_template = http.request.env['mail.template'].sudo().search([('name','=','x_cpnaa_template_cert_dest_ext')])[0]

        if not mail_template:
           return {'ok': False, 'mensaje': 'No se podido completar su solicitud', 'cert': False} 
            
        mail_values = {
            'subject': mail_template['subject'],
            'attachment_ids': [cert.id],
            'body_html': mail_template['body_html'],
            'email_to': kw.get('email'),
            'email_from': mail_template['email_from'],
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
        user, data_user, fallecido = False, False, False
        origen = data.get('origen')
        ano = timedelta(days=365)
        now = datetime.now() - timedelta(hours=5)
        today = now.date()
        if self.validar_captcha(kw.get('token')):
            if origen == 'renovacion':
                campos = ['x_studio_tipo_de_documento_1', 'x_studio_documento_1',  'x_expedition_date', 'x_expiration_date', 'x_renovacion_licencia', 'x_service_ID']    
                vigencia = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_documento_1','=',kw['data']['doc']), 
                                                                                     ('x_studio_tipo_de_documento_1.id', "=", kw['data']['doc_type']), 
                                                                                     ('x_cycle_ID.x_order','=',5)], campos)
                _logger.info('yo soy el vigencia en consulta renovacion: ' + str(vigencia))
                
                try:
                    fecha_expiracion = str(vigencia[0]['x_expiration_date']) + ' 00:00'
                    _logger.info('yo soy la fecha de expiración emitida: ' + str(fecha_expiracion))
                    fecha_expiracion = datetime.strptime(fecha_expiracion, '%Y-%m-%d %H:%M')
                    dias = (fecha_expiracion - now) / timedelta(days=1)
                except:
                    try:
                        fecha_expedicion = str(vigencia[0]['x_expedition_date']) + ' 00:00'
                        fecha_expiracion = datetime.strptime(fecha_expedicion, '%Y-%m-%d %H:%M')
                        dias = (fecha_expiracion + ano - now) / timedelta(days=1)
                        _logger.info('yo soy la fecha de expiración sumando 1 año a la fecha de expedicion: ' + str(fecha_expiracion))  
                    except:
                        return { 'ok': 'False', 'messaje': 'Señor usuario usted no puede realizar solicitud de Renovación de Licencia Temporal Especial, favor solicitar Licencia Temporal Especial por primera vez, dirigirse al link: https://cpnaa.gov.co/tramite-licencia-temporal/'}
                for i in vigencia:
                    if i['x_service_ID'][1] == 'RENOVACIÓN - LICENCIA TEMPORAL ESPECIAL':
                        return { 'ok': 'False', 'messaje': 'Señor usuario usted ya solicitó una renovación de Licencia Temporal Especial, favor solicitar nuevamente Licencia Temporal Especial por primera vez, dirigirse al link: https://cpnaa.gov.co/tramite-licencia-temporal/'}
                _logger.info('dias => '+str(dias))
                if (dias < 0):
                    #return { 'ok': 'True'}
                    return { 'ok': 'False', 'messaje': 'Su solicitud de Renovación de Licencia Temporal Especial no puede ser recibida, tiempo vencido para radicar la solicitud. Favor tramitar Licencia Temporal Especial por primera vez en el link: https://cpnaa.gov.co/tramite-licencia-temporal/' + str(dias)}                
                else:
                    return { 'ok': 'False', 'messaje': 'Su solicitud de Renovación de Licencia Temporal Especial no puede ser recibida, tiempo vencido para radicar la solicitud. Favor tramitar Licencia Temporal Especial por primera vez en el link: https://cpnaa.gov.co/tramite-licencia-temporal/' + str(dias)}                
                
            result, por_nombre, matricula, certificado, tramite_en_curso, grado, beneficiario = {}, False, False, False, False, False, False
            egresado = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select','=',int(data['doc_type'])),('x_documento','=',data['doc'])])
            mensaje_beneficiario = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje beneficiario')]).x_value
            mensaje_no_beneficiario = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje no beneficiario')]).x_value
            fecha_maxima = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha maxima grado')]).x_value
            fecha_inicio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha inicio descuento')]).x_value
            fecha_fin = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value
            fecha_maxima_grado = datetime.strptime(fecha_maxima, '%Y-%m-%d').date()
            fecha_inicio_descuento = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_descuento = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            beneficio_activo = today >= fecha_inicio_descuento and today <= fecha_fin_descuento
            
            if egresado:
                if len(egresado) > 1:
                    egresado = egresado[-1]
                if egresado.x_origin_type == 'CONVENIO':
                    grado = http.request.env['x_cpnaa_grade'].sudo().browse(egresado.x_grado_ID.id)
                    if grado:
                        if self.validar_fecha_limite(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)):
                            _logger.info('Graduando reportado por IES con plazo vencido => ['+data['doc_type']+':'+data['doc']+']')
                        else:
                            grado = False
                            if egresado.x_fecha_de_grado < fecha_maxima_grado and beneficio_activo:
                                beneficiario = True
                else:
                    if (egresado.x_fecha_de_grado < fecha_maxima_grado and origen in ['matricula','inscripciontt']) and beneficio_activo:
                        beneficiario = True
                        
            _logger.info('origen %s' % origen)
            _logger.info('egresado %s' % egresado)
            _logger.info('beneficiario %s' % beneficiario)
            _logger.info('grado %s' % grado)
                        
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1','=',int(data['doc_type'])),
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
                          'documento': tramite.x_studio_documento_1, 'fallecido': tramite.x_fallecido,
                          'resolucion_fallecido': tramite.x_user_ID.x_resolucion_fallecido, 
                          'fecha_resolucion_fallecido': tramite.x_user_ID.x_fecha_resolucion_fallecido }
                if tramite.x_fallecido:
                    fallecido = True
                if user:
                    data_user = { 'tipo_documento': user.x_document_type_ID.x_name, 'documento': user.x_document, 'carrera': user.x_institute_career.x_name }
            _logger.info(user)
            if len(egresado) > 1:
                egresado = egresado[-1]
            if (tramite_en_curso):
                return { 'ok': True, 'id': user.id, 'tramite_en_curso': tramite_en_curso }
            if (matricula or certificado):
                return { 'ok': True, 'id': user.id, 'matricula': matricula, 'certificado': certificado, 'result': result, 
                        'data_user': data_user, 'fallecido': fallecido }
            elif (grado):
                return { 'ok': True, 'id': egresado.id, 'convenio': True }
            elif (beneficiario and not grado):
                return { 'ok': True, 'id': egresado.id, 'aplica_beneficio': True, 'mensaje_beneficiario': mensaje_beneficiario }
            elif (user):
                return { 'ok': True, 'id': user.id, 'convenio': False, 'user': data_user }
            else:
                return { 'ok': False, 'id': False, 'convenio': False }
        else:
            return { 'ok': False, 'id': False, 'convenio': False, 'error_captcha': True,
                    'mensaje': 'Ha ocurrido un error al validar el captcha, por favor recarga la página' }
        
        
    # Valida tipo y número de documento, valida si es un usuario nuevo, si tiene trámite o si es un graduando
    @http.route('/validar_tramites_beneficio', methods=["POST"], type="json", auth='public', website=True)
    def validar_tramites_beneficio(self, **kw):
        data = kw.get('data')
        user, data_user, fallecido = False, False, False
        if self.validar_captcha(kw.get('token')):
            result, por_nombre, matricula, certificado, tramite_en_curso = {}, False, False, False, False
            mensaje_beneficiario = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje beneficiario')]).x_value
            mensaje_no_beneficiario = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Mensaje no beneficiario')]).x_value
            fecha_maxima = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha maxima grado')]).x_value
            fecha_maxima_grado = datetime.strptime(fecha_maxima, '%Y-%m-%d').date()
            
            graduando = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select','=',int(data['doc_type'])),
                                                                            ('x_documento','=',data['doc']),('x_origin_type','=','CONVENIO')])
            
#             aplica_beneficio = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select','=',int(data['doc_type'])),
#                                                                                    ('x_fecha_de_grado','<',fecha_maxima_grado),
#                                                                                    ('x_documento','=',data['doc'])]) 
            aplica_beneficio = [1] # Remover validación contra tabla de egresado 16/09/2022
            
            grado = http.request.env['x_cpnaa_grade'].sudo().browse(graduando.x_grado_ID.id)
            
            if grado:
                if self.validar_fecha_limite(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)):
                    _logger.info('Graduando reportado por IES con plazo vencido => ['+data['doc_type']+':'+data['doc']+']')
                else:
                    grado = False
                    
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1','=',int(data['doc_type'])),
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
                          'documento': tramite.x_studio_documento_1, 'fallecido': tramite.x_fallecido,
                          'resolucion_fallecido': tramite.x_user_ID.x_resolucion_fallecido, 
                          'fecha_resolucion_fallecido': tramite.x_user_ID.x_fecha_resolucion_fallecido }
                if tramite.x_fallecido:
                    fallecido = True
                if user:
                    data_user = { 'tipo_documento': user.x_document_type_ID.x_name, 
                                  'documento': user.x_document, 'carrera': user.x_institute_career.x_name }
            
            if len(graduando) > 1:
                graduando = graduando[-1]
            if (tramite_en_curso):
                return { 'ok': True, 'id': user.id, 'tramite_en_curso': tramite_en_curso }
            if (matricula or certificado):
                return { 'ok': True, 'id': user.id, 'matricula': matricula, 'certificado': certificado, 'result': result, 
                         'data_user': data_user, 'fallecido': fallecido }
            elif len(aplica_beneficio) < 1:
                return { 'ok': False, 'id': False, 'consulta_beneficio': True, 
                         'aplica_beneficio': False, 'mensaje_no_beneficiario': mensaje_no_beneficiario }
            elif (grado):
                return { 'ok': True, 'id': graduando.id, 'convenio': True }
            elif (user):
                return { 'ok': True, 'id': user.id, 'convenio': False, 'user': data_user }
            elif len(aplica_beneficio) > 0:
                return { 'ok': True, 'id': False, 'consulta_beneficio': True, 
                         'aplica_beneficio': True, 'mensaje_beneficiari': mensaje_beneficiario }
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
#                                                                                       ('x_fecha_de_grado','>=',hoy),
                                                                                      ('x_origin_type','=','CONVENIO')])
            else:
                graduandos = http.request.env['x_procedure_temp'].sudo().search_read([('x_tipo_documento_select','=',int(data['doc_type'])),
                                                                                      ('x_grado_ID','!=',False),
#                                                                                       ('x_fecha_de_grado','>=',hoy),
                                                                                      ('x_documento','=',data['doc']),
                                                                                      ('x_origin_type','=','CONVENIO')])
            if (len(graduandos) > 0):
                for graduando in graduandos:
                    grado = http.request.env['x_cpnaa_grade'].sudo().browse(graduando['x_grado_ID'][0])
                    id_grado = grado.id
                    if grado:
                        if grado.x_agreement_ID.x_before_after_agreement:
                            fecha_maxima = grado.x_date + timedelta(days=grado.x_agreement_ID.x_days_to_pay_after)
                        else:
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
                            'fecha_maxima': fecha_maxima,
                            'nivel_profesional': grado.x_carrera_ID.x_level_ID.x_name
                        }
                        definitivos.append(definitivo)
            if (graduandos):
                return { 'ok': True, 'graduandos': definitivos }
            else:
                return { 'ok': False, 'graduandos': False }
        else:
            return { 'ok': False, 'mensaje': 'Valida nuevamente el captcha', 'error_captcha': True }
        
    # Renderiza el formulario para trámites, valida si ya ha realizado este trámite y lo redirige al inicio del tramite
    @http.route('/tramite/<string:origen>/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def formulario_tramites(self, origen, tipo_doc, documento):
        doc_validos = http.request.env['x_cpnaa_document_type'].sudo().search([('id','=',tipo_doc),('x_user_type_IDs.x_name','in',['PERSONA NATURAL'])])
        doc_validos = len(doc_validos) > 0
        servicio = self.nombres_tramites(origen)
        service_odoo = http.request.env['x_cpnaa_service'].sudo().search([('x_name','=',servicio)])
        tarifa = service_odoo.x_rate
        matricula, tramite_en_curso = None, None
        if (tipo_doc == '1' and not self.validar_solo_numeros(documento)) or not doc_validos:
            return http.request.redirect('/cliente/tramite/'+origen)
        if not servicio:
            return http.request.redirect('/cliente/tramite/matricula')
        try:
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                     ('x_studio_documento_1','=',documento)])
            user = http.request.env['x_cpnaa_user'].sudo().browse(tramites[0].x_user_ID.id)
        except:
            pass
        if tramites:
            for tramite in tramites:
                matricula = True if tramite.x_service_ID.x_name == 'MATRÍCULA PROFESIONAL' else False
                tramite_en_curso = True if tramite.x_cycle_ID.x_order < 5 else False
        if tramite_en_curso:
            return http.request.redirect('/cliente/'+str(tramite.x_user_ID.id)+'/tramites/')
        elif matricula and origen == 'matricula':
            return http.request.redirect('/cliente/tramite/'+origen)
        elif servicio:
            #si el origen de la consulta viene por renovación, se evaluan los 30 días calendario que se deben tener para poder renovar la licencia
            if origen == 'renovacion':
                campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_universidad_5', 'x_studio_correo_electrnico',
                  'x_origin_type', 'x_studio_ciudad_de_expedicin','x_resolution_ID', 'x_legal_status', 'x_sanction', 'x_studio_ciudad_de_expedicin', 'x_studio_telfono',
                  'x_studio_carrera_1','x_studio_gnero','x_studio_fecha_de_resolucin', 'x_studio_nombres','x_studio_apellidos','x_enrollment_number',
                  'x_fecha_resolucion_corte', 'x_expedition_date', 'x_expiration_date', 'x_studio_pas_de_expedicin_1', 'x_studio_celular', 'x_studio_direccin',
                  'x_studio_ciudad_de_residencia_en_el_extranjero', 'x_renovacion_licencia', 'x_service_ID', 'x_studio_departamento_de_expedicin', 'x_studio_pas_de_residencia_en_el_extranjero_1']
                vigencia = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_documento_1','=',documento)], campos)
                if len(vigencia) > 0:
                    vigencia = vigencia[0]
                else:
                    return http.request.redirect('/cliente/tramite/'+origen)
                
                _logger.info('yo soy el vigencia: ' + str(vigencia))
                
                ano = timedelta(days=365)
                now = datetime.now() - timedelta(hours=5)
                try:
                    fecha_expiracion = str(vigencia['x_expiration_date']) + ' 00:00'
                    _logger.info('yo soy la fecha de expiración emitida: ' + str(fecha_expiracion))
                    fecha_expiracion = datetime.strptime(fecha_expiracion, '%Y-%m-%d %H:%M')
                    dias = (fecha_expiracion - now) / timedelta(days=1)
                except:
                    fecha_expedicion = str(vigencia['x_expedition_date']) + ' 00:00'
                    fecha_expiracion = datetime.strptime(fecha_expedicion, '%Y-%m-%d %H:%M')
                    dias = (fecha_expiracion + ano - now) / timedelta(days=1)
                    _logger.info('yo soy la fecha de expiración sumando 1 año a la fecha de expedicion: ' + str(fecha_expiracion))
                if dias < 3000 and not vigencia['x_renovacion_licencia']:
                    #_logger.info('formulario tramites')
                    #actualizado = http.request.env['x_cpnaa_procedure'].browse('x_renovacion_licencia').sudo().write(1)
                    return http.request.render('my_sample.formulario_tramites', {'user': user, 'tipo_doc': tipo_doc, 'tarifa': tarifa,
                                                                                 'documento':documento, 'form': origen, 'origen': 1, 'renovar': vigencia})
                else:
                    return http.request.render('my_sample.inicio_tramite', {'form': 'renovacion', 'inicio_tramite': False})
            else:
                return http.request.render('my_sample.formulario_tramites', {'tipo_doc': tipo_doc, 'documento':documento, 
                                                                             'form': origen, 'origen': 1, 'tarifa': tarifa})

    
    # Renderiza el formulario para trámites, valida si ya ha realizado este trámite y lo redirige al inicio del tramite
    @http.route('/beneficio/tramite/<string:origen>/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def formulario_tramites_beneficio(self, origen, tipo_doc, documento):
        validos = ['matricula','inscripciontt']
        doc_validos = http.request.env['x_cpnaa_document_type'].sudo().search([('id','=',tipo_doc),('x_user_type_IDs.x_name','in',['PERSONA NATURAL'])])
        doc_validos = len(doc_validos) > 0
        matricula, tramite_en_curso = None, None
        servicio = 'MATRÍCULA PROFESIONAL'
        ahora    = datetime.now() - timedelta(hours=5)
        hoy      = ahora.date()
        
        if tipo_doc == '1' and not self.validar_solo_numeros(documento):
            return http.request.redirect('https://cpnaa.gov.co/')
        
        if origen == validos[1]:
            servicio = 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL'
        
        campo_beneficio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Nombre campo beneficio')]).x_value
        fecha_maxima = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha maxima grado')]).x_value
        fecha_maxima_grado = datetime.strptime(fecha_maxima, '%Y-%m-%d').date()
        tramites = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                        ('x_studio_documento_1','=',documento)])
        service_odoo = http.request.env['x_cpnaa_service'].sudo().search([('x_name','=',servicio)])
        tarifa = service_odoo.x_rate - service_odoo.x_discount
        
        fecha_inicio = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha inicio descuento')]).x_value
        fecha_fin = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','Fecha fin descuento')]).x_value
        fecha_inicio_descuento = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_descuento = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
#         aplica_beneficio = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select.id','=',tipo_doc),
#                                                                         ('x_documento','=',documento),
#                                                                         ('x_fecha_de_grado','<',fecha_maxima_grado)])
#         _logger.info(campo_beneficio)
#         if len(aplica_beneficio) < 1:
#             return http.request.redirect('https://cpnaa.gov.co/')

        beneficio_activo = hoy >= fecha_inicio_descuento and hoy <= fecha_fin_descuento
        if not beneficio_activo:
            return http.request.redirect('https://cpnaa.gov.co/')

        if tramites:
            for tramite in tramites:
                matricula = True if tramite.x_service_ID.x_name == 'MATRÍCULA PROFESIONAL' else False
                tramite_en_curso = True if tramite.x_cycle_ID.x_order < 5 else False
        if tramite_en_curso:
            return http.request.redirect('/cliente/'+str(tramite.x_user_ID.id)+'/tramites/')
        elif matricula and origen == 'matricula':
            return http.request.redirect('/cliente/tramite/'+origen)
        elif origen in validos and doc_validos:
            return http.request.render('my_sample.formulario_tramites', {'tipo_doc': tipo_doc, 'documento':documento,
                                                                         'form': origen, 'origen': 1, 'beneficio': True, 'tarifa': tarifa,
                                                                         'fecha_maxima': fecha_maxima, 'campo_beneficio': campo_beneficio })



    # Renderiza el formulario para trámites por convenios, valida si ya hay trámite en curso y lo redirige al estado del tramite
    @http.route('/tramite/convenios/<model("x_procedure_temp"):cliente>', auth='public', website=True)
    def formulario_convenio(self, cliente):
        form = 'matricula' if cliente.x_carrera_select.x_level_ID.x_name == 'PROFESIONAL' else 'inscripciontt'
        servicio = 'MATRÍCULA PROFESIONAL CONVENIO' if form == 'matricula' else 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL CONVENIO'
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',cliente.x_tipo_documento_select.id),
                                                                           ('x_studio_documento_1','=',cliente.x_documento),
                                                                           ('x_cycle_ID.x_order','<','5')])
        grado = http.request.env['x_cpnaa_grade'].sudo().browse(cliente.x_grado_ID.id)
        service_odoo = http.request.env['x_cpnaa_service'].sudo().search([('x_name','=',servicio)])
        tarifa = service_odoo.x_rate - service_odoo.x_discount
        if not grado.x_agreement_ID.x_before_after_agreement:
            if not self.validar_fecha_limite(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay)):
                return http.request.redirect('/cliente/tramite/'+form)
        else:
            if not self.validar_fecha_limite(grado.x_date + timedelta(days=grado.x_agreement_ID.x_days_to_pay_after)):
                return http.request.redirect('/cliente/tramite/'+form)
        if tramite:
            return http.request.redirect('/cliente/'+str(tramite.x_user_ID.id)+'/tramites')
        else:
            return http.request.render('my_sample.formulario_tramites', {'cliente': cliente, 'form': form, 'origen': 2, 'tarifa': tarifa })
    
    # Renderiza formulario para corregir rechazos, si el trámite no tiene rechazo o ya fue corregido lo redirige al inicio
    @http.route('/tramite/<string:form>/edicion/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def editar_tramite(self, form, tipo_doc, documento):
        tramite = http.request.env['x_cpnaa_procedure'].sudo().search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                    ('x_studio_documento_1','=',documento),
                                                                    ('x_cycle_ID.x_order','<','5')])
        rechazos  = http.request.env['x_cpnaa_refuse_procedure'].sudo().search_read([('x_procedure_ID','=',tramite.id)])
        user      = http.request.env['x_cpnaa_user'].sudo().browse(tramite.x_user_ID.id)
        if user and len(rechazos)>0:
            if not rechazos[-1]['x_corrected']:
                return http.request.render('my_sample.formulario_tramites', {'form': form, 'user': user, 'rechazo': True,
                                                                             'origen': tramite.x_origin_type.id})
            else:
                return http.request.redirect('/cliente/tramite/'+form)
        elif user and tramite.x_cycle_ID.x_order == 0:
            return http.request.render('my_sample.formulario_tramites', {'form': form, 'user': user,
                                                                         'origen': tramite.x_origin_type.id})
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
                    fecha_maxima = None
                    if grado.x_agreement_ID.x_before_after_agreement:
                        fecha_maxima = grado.x_date + timedelta(days=grado.x_agreement_ID.x_days_to_pay_after)
                    else:
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
        
            
    # Retorna las ciudades que contienen la cadena recibidas
    @http.route('/get_ciudades', methods=["POST"], type="json", auth='public', website=True)
    def get_ciudades(self, **kw):
        cadena = kw.get('cadena')
        data = http.request.env['x_cpnaa_city'].sudo().search_read([('x_name', 'ilike', cadena)],['id','x_name'], limit=8)
        return { 'ciudades': data }
    
    # Retorna las universidades que coinciden con la cadena recibida
    @http.route('/get_universidades', methods=["POST"], type="json", auth='public', website=True)
    def get_universidades(self, **kw):
        cadena = kw.get('cadena')
        tipo_universidad = [kw.get('tipo_universidad')]
        if not kw.get('tipo_universidad'):
            tipo_universidad = [1,2,3]
        return {'universidades': http.request.env['x_cpnaa_user'].sudo().search_read([('x_user_type_ID.id','=',3),('x_institution_type_ID.id', 'in', tipo_universidad),
                                                                               ('x_name', 'ilike', cadena)],['id','x_name'], limit=6)}
    
    # Retorna las carreas que coinciden con la cadena y nivel profesional recibidos
    # Retorna las carreas que coinciden con la cadena y nivel profesional recibidos
    @http.route('/get_carreras', methods=["POST"], type="json", auth='public', website=True)
    def get_carreras(self, **kw):
        cadena = kw.get('cadena')
        nivel_profesional = [kw.get('nivel_profesional')]
        if not kw.get('nivel_profesional'):
            nivel_profesional = [1,2,3]
        id_genero = int(kw.get('id_genero'))
        genero = http.request.env['x_cpnaa_gender'].sudo().browse(id_genero)
        nombre_carrera = genero.x_field_to_career_name if genero else 'x_name'
        data = http.request.env['x_cpnaa_career'].sudo().search_read([('x_level_ID.id','in',nivel_profesional),
                                                                      ('x_profession_type_ID.x_name','not ilike','NO ACTIVA'),
                                                                      (nombre_carrera, 'ilike', cadena)],
                                                                      ['id',nombre_carrera], limit=8)
        for d in data:
            x_name = d[nombre_carrera]
            del d[nombre_carrera]
            d['x_name'] = x_name
        return { 'carreras': data }
    
    # Retorna el nombre de la carrera según el genero 
    @http.route('/get_carrera_genero', methods=["POST"], type="json", auth='public', website=True)
    def get_carrera_genero(self, **kw):
        id_genero = int(kw.get('genero'))
        id_carrera = int(kw.get('id_carrera'))
        genero = http.request.env['x_cpnaa_gender'].sudo().browse(id_genero)
        campo = genero.x_field_to_career_name
        carrera = http.request.env['x_cpnaa_career'].sudo().search_read([('id','=',id_carrera)], ['x_name', campo])[0]
        level_prof = http.request.env['x_cpnaa_career'].sudo().browse(id_carrera).x_level_ID.x_name
        if carrera and level_prof != 'PROFESIONAL':
            x_name = carrera[campo]
            del carrera[campo]
            carrera['x_name'] = x_name
        return carrera
    
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
    
    """   RUTAS CLIENTE EMPRESA   """
    
    # Ruta que renderiza el inicio del trámite actualización/coreeción de registro
    @http.route('/convenios-inter-administrativos', auth='user', website=True)
    def inicio_pactos(self):
        empresa = http.request.env['x_cpnaa_user'].search([('x_email','=',http.request.session.login)])
        if empresa.x_user_type_ID.x_name != 'EMPRESA':
            return http.request.redirect('/')
        hoy = date.today()
        fecha_consulta = '%s-01-%s' % (hoy.month-2, hoy.year)
        mes_desde = hoy.month-2 if hoy.month > 10 else '0%s' % str(hoy.month-2)
        desde = '01-%s-%s' % (mes_desde, hoy.year)
        tramites = http.request.env['x_cpnaa_procedure'].search([('create_date','>',fecha_consulta)])
        _logger.info(hoy)
        return http.request.render('my_sample.inicio_pactos', { 'tramites': tramites, 'desde': desde, 'hoy': hoy })

    # Ruta que realiza la consulta de convenios inter administrativos
    @http.route('/consulta_pactos', auth='user', methods=['POST'], type="json", website=True)
    def consulta_pactos(self, **kw):
        tramites = []
        _logger.info(kw)
        campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_universidad_5',
                  'x_origin_type', 'x_studio_ciudad_de_expedicin','x_resolution_ID', 'x_legal_status', 'x_sanction',
                  'x_studio_ciudad_de_expedicin','x_studio_carrera_1','x_studio_gnero','x_studio_fecha_de_resolucin',
                  'x_studio_nombres','x_studio_apellidos','x_enrollment_number','x_fecha_resolucion_corte', 'x_expedition_date']
        
        if ((kw['data']['tipo'] == 'x_names') and (kw['data']['tipo_2'] == 'x_apellidos')):
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo']],'ilike',kw['data']['value']), (self.campos_interregulacion[kw['data']['tipo_2']],'ilike',kw['data']['value_2']), ('x_cycle_ID.x_order','=',5)], campos)
        
        elif ((kw['data']['tipo'] == 'x_names') or (kw['data']['tipo'] == 'x_apellidos')):
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo']],'ilike',kw['data']['value']),('x_cycle_ID.x_order','=',5)], campos)
        
        elif (kw['data']['tipo'] == 'x_fecha_resolucion_corte'):
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo']],'=',kw['data']['value']), ('x_cycle_ID.x_order','=',5)], campos)
            tramites_2 = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo_2']],'=',kw['data']['value']), ('x_cycle_ID.x_order','=',5)], campos)
            if tramites:
                pass
            else:
                tramites = tramites_2
                
        elif (kw['data']['tipo'] == 'x_resolution_ID'):
            tramites_1 = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo']],'ilike',kw['data']['value']), ('x_cycle_ID.x_order','=',5)], campos)
            for i in range(len(tramites_1)):
                if (kw['data']['value'] in tramites_1[i]['x_resolution_ID'][1].split()):
                    tramites.append(tramites_1[i])
            
        else:
            tramites = http.request.env['x_cpnaa_procedure'].sudo().search_read([(self.campos_interregulacion[kw['data']['tipo']],'=',kw['data']['value']),('x_cycle_ID.x_order','=',5)], campos)
        
        return { 'tramites': tramites }


                
    
    
#     # Realiza la consulta del registro online 
#    @http.route('/convenios-inter-administrativos/consulta/<model("x_cpnaa_procedure"):tramite>', auth='user', website=True)
#    def realizar_consulta(self, **kw):
#        empresa = http.request.env['x_cpnaa_user'].search([('x_email','=',http.request.session.login)])
#        if empresa.x_user_type_ID.x_name != 'EMPRESA':
#           return http.request.redirect('/')
#       data = kw.get('data')
#        _logger.info(data)
#        tramites = []
#         if ahora = datetime.now() - timedelta(hours=5)
#           hora_consulta = ahora.strftime('%Y-%m-%d %H:%M:%S')
#           campos = ['id','x_studio_tipo_de_documento_1', 'x_studio_documento_1','x_service_ID','x_studio_pas_de_expedicin_1',
#                       'x_origin_type', 'x_studio_ciudad_de_expedicin','x_resolution_ID', 'x_legal_status', 'x_sanction',
#                       'x_studio_ciudad_de_expedicin','x_studio_carrera_1','x_studio_gnero','x_studio_fecha_de_resolucin',
#                       'x_studio_nombres','x_studio_apellidos','x_enrollment_number','x_fecha_resolucion_corte']
            
#             _logger.info(tramites)
    
        
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
        profesiones = http.request.env['x_cpnaa_career'].search([('x_profession_type_ID.x_name','not ilike','NO ACTIVA'),('x_name','!=','ARQUITECTE')], order="x_name")
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'convenio':convenio})
    
    # Ruta donde agrega mas estudiantes cuando el grado ya esta creado
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoCsv/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_csv_grado(self, universidad, grado):
        hoy = date.today()
        redirect = False
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            redirect = True
            
        # Si ya ha caducado la fecha de carga de archivo csv para el grado 
        if grado.x_agreement_ID.x_before_after_agreement:
            if grado.x_date + timedelta(days=grado.x_agreement_ID.x_days_to_load_later) <= hoy:
                redirect = True
        else:
            if grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_before_degree) <= hoy:
                redirect = True
                
        if redirect:
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([('x_profession_type_ID.x_name','not ilike','NO ACTIVA'),('x_name','!=','ARQUITECTE')], order="x_name")
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
        fechaActual = datetime.now() - timedelta(hours=5)
        mes = meses[fechaActual.month]
        fechaActualFormat = mes + fechaActual.strftime(" %d de %Y")
        return http.request.render('my_sample.convenios_definitivo_pdf', {'universidad': universidad, 'grado': grado, 'convenio': convenio,
                                                                          'convenios': convenios, 'fechaActual': fechaActualFormat})
    
    # Ruta donde carga el archivo de actas de diploma
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoActas/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_actas_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([('x_profession_type_ID.x_name','not ilike','NO ACTIVA'),('x_name','!=','ARQUITECTE')], order="x_name")
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_grado_actas', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    # Ruta donde carga el cuadro de mando del grado
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/detalle_grado/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def detalles_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([('x_profession_type_ID.x_name','not ilike','NO ACTIVA'),('x_name','!=','ARQUITECTE')], order="x_name")
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
        grado = http.request.env['x_cpnaa_grade'].browse(id_grado)
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf = archivo_temp.lstrip('data:application/pdf;base64,')
        template_obj = http.request.env['mail.template'].sudo().search_read([('name','=','cpnaa_template_pdf_definitive_load')])[0]
        attachment = http.request.env['ir.attachment'].sudo().create({
            'name': 'listado-definitivo-graduandos-%s.pdf' % grado.x_name,
            'type': 'binary',
            'datas': archivo_pdf,
            'mimetype': 'application/x-pdf'
        })
        try:
            if template_obj:
                body = template_obj['body_html'].replace('${object.x_studio_universidad.x_name}', grado.x_studio_universidad.x_name)
                body = body.replace('${object.x_date}', grado.x_date.strftime("%d-%m-%Y"))
                mail_values = {
                    'subject': template_obj['subject'],
                    'attachment_ids': [attachment.id],
                    'body_html': body,
                    'email_to': template_obj['email_to'],
                    'email_from': template_obj['email_from'],
                }
                http.request.env['mail.mail'].sudo().create(mail_values).send()
            update = {'x_phase_3': True, 'x_archivo_pdf_definitivo': archivo_pdf}
            grado.write(update)
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
        grado = http.request.env['x_cpnaa_grade'].browse(id_grado)
        archivo_temp = unicodedata.normalize('NFKD', archivo)
        archivo_pdf = archivo_temp.lstrip('data:application/pdf;base64,')
        template_obj = http.request.env['mail.template'].sudo().search_read([('name','=','cpnaa_template_pdf_diplomas')])[0]
        attachment = http.request.env['ir.attachment'].sudo().create({
            'name': 'cargue-diplomas-%s.pdf' % grado.x_name,
            'type': 'binary',
            'datas': archivo_pdf,
            'mimetype': 'application/x-pdf'
        })
        try:
            if template_obj:
                body = template_obj['body_html'].replace('${object.x_studio_universidad.x_name}', grado.x_studio_universidad.x_name)
                body = body.replace('${object.x_date}', grado.x_date.strftime("%d-%m-%Y"))
                mail_values = {
                    'subject': template_obj['subject'],
                    'attachment_ids': [attachment.id],
                    'body_html': body,
                    'email_to': template_obj['email_to'],
                    'email_from': template_obj['email_from'],
                }
                http.request.env['mail.mail'].sudo().create(mail_values).send()
            update = {'x_phase_4': True, 'x_archivo_pdf_actas': archivo_pdf}
            grado.write(update)
        except:
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar el archivo, vuelve a intentarlo más tarde'}
        return {'ok': True, 'message': 'Listado guardado con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    # Recibe los graduandos verificados y los agrega al grado, si no existe el grado lo crea
    @http.route('/guardar_registros', methods=['POST'], type="json", auth='user', website=True) 
    def guardar_registros_csv(self, **kw):
        registros = kw.get('registros')
        data = kw.get('data')
        hoy = date.today()
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
            data_str = data_csv.decode('cp1252',errors='ignore')
        except Exception as e:
            _logger.info(e)
            return {'ok': False, 'message': 'Ha ocurrido un error al leer el archivo, verifique su contenido'}
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
        if hora_maxima > ahora:
            return True
        else:
            return False
        
    """ FUNCIONES DE VALIDACIÓN DE DATOS CARGA CSV CONVENIOS """
    
    def validar_datos(self, row, fecha_grado):
        datos = row.split(';')
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
        base_url = 'https://www.google.com/recaptcha/api/siteverify?response='
        secret = '&secret=6Lf2UcMZAAAAAPUtz3_vPL7H-z8j8cQ1if9fT1Cn'
        response = requests.post(base_url + token + secret)
        _logger.info(response.json()['success'])
        return response.json()['success']
    
    def generar_aleatorio(self, longitud):
        valores = '0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        p = ''
        return p.join([choice(valores) for i in range(longitud)])
    
    def radicado_test(self):
        rad = http.request.env['x_cpnaa_consecutive'].sudo().search([('x_name','=','RADICADO TRAMITES')])
        val = rad.x_value + 1
        rad.sudo().write({'x_value': val})
        return val

    def nombres_tramites(self, form_value):
        nombre_tramite = {
            'matricula': 'MATRÍCULA PROFESIONAL',
            'inscripciontt': 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL',
            'licencia': 'LICENCIA TEMPORAL ESPECIAL',
            'renovacion': 'RENOVACIÓN - LICENCIA TEMPORAL ESPECIAL'
        }
        return nombre_tramite.get(form_value, False)
    
    nombre_tramite = {
            #'matricula': 'MATRÍCULA PROFESIONAL',
            'inscripciontt': 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL',
            #'licencia': 'LICENCIA TEMPORAL ESPECIAL',
            #'renovacion': 'RENOVACIÓN - LICENCIA TEMPORAL ESPECIAL'
        }

    campos_interregulacion = {
        "x_document":"x_studio_documento_1",
        "x_names":"x_studio_nombres",
        "x_apellidos":"x_studio_apellidos",
        "x_enrollment":"x_enrollment_number",
        "x_fecha_resolucion_corte":"x_fecha_resolucion_corte", #["x_fecha_resolucion_corte", ], #"x_studio_fecha_de_resolucin",
        'x_studio_fecha_de_resolucin': 'x_studio_fecha_de_resolucin',
        "x_resolution_ID": "x_resolution_ID",
    }

    campos_ID_form_tramites = [
        'x_origin_type',
        'x_user_type_ID',
        'x_document_type_ID',
        'x_expedition_country',
        'x_expedition_state',
        'x_expedition_city',
        'x_gender_ID',
        'x_country_ID',
        'x_state_ID',
        'x_city_ID',
        'x_level_ID',
        'x_institution_type_ID',
        'x_institution_ID',
        'x_institute_career',
        'x_foreign_country',
        'x_foreign_state',
        'x_foreign_city',
        'x_related_service'
    ]