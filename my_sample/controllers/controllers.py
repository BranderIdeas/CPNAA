 # -*- coding: utf-8 -*-
from odoo import http
from datetime import date, datetime, timedelta
import logging
import base64
import unicodedata
import re
import io
import base64
import json
import sys

# Intancia de logging para imprimir por consola
_logger = logging.getLogger(__name__)

fechaActual = datetime.now()
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
            return  http.request.redirect('/web/login')
        else:
            return  http.request.redirect('my/home')
        
    @http.route('/create_user', methods=["POST"], auth='public', website=True)
    def form_data(self, **kw):
        resp = {}
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
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
        else:
            return http.request.make_response(json.dumps(resp), headers={'Content-Type': 'application/json'})
    
    @http.route('/pagos/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def epayco(self, tipo_doc, documento):
        tramites = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                ('x_studio_documento_1','=',documento),
                                                                ('x_cycle_ID.x_order','=',0)], 
                                                               ['x_studio_tipo_de_documento_1', 'x_studio_documento_1',
                                                                'x_studio_nombres', 'x_studio_apellidos', 'x_service_ID',
                                                                'x_studio_correo_electrnico_1', 'x_user_celular',
                                                                'x_studio_ciudad_de_expedicin', 'x_studio_direccin',
                                                                'x_studio_telfono', 'x_req_date', 'x_rate',
                                                                'x_studio_universidad_5', 'x_studio_carrera_1',
                                                                'x_studio_departamento_estado','x_studio_fecha_de_grado_2',
                                                                'x_studio_ciudad_1','x_origin_type','x_origin_name'])
        _logger.info(tramites[0]['x_origin_type'][1]) #CORTE
        _logger.info(tramites[0]['x_origin_name'])
#         corte = http.request.env['x_cpnaa_cut'].search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),[])
        if len(tramites) > 0:
            return http.request.render('my_sample.epayco', {'tramite': tramites[0]})
        else:
            return http.request.redirect('/cliente/tramite/matricula')
    
    @http.route('/pagos/respuesta', auth='public', website=True)
    def respuesta_epayco(self):
        return  http.request.render('my_sample.respuesta_pago', {})
        
    @http.route('/pagos/confirmacion', auth='public', website=True)
    def epayco_confirmacion(self):
        return  http.request.render('my_sample.epayco_confirmacion', {})
    
    @http.route('/tramite_fase_inicial', type="json", auth='public', website=True)
    def tramite_fase_inicial(self, **kw):
        data = kw.get('data')
        doc = data['doc']
        tipo_doc = data['doc_type']
        tramite = http.request.env['x_cpnaa_procedure'].search_read([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                ('x_studio_documento_1','=',doc),
                                                                ('x_cycle_ID.x_order','=',0)], 
                                                               ['x_studio_tipo_de_documento_1', 'x_studio_documento_1',
                                                                'x_studio_nombres', 'x_studio_apellidos', 'x_service_ID',
                                                                'x_studio_correo_electrnico_1', 'x_user_celular',
                                                                'x_studio_ciudad_de_expedicin', 'x_studio_direccin',
                                                                'x_studio_telfono', 'x_req_date', 'x_rate',
                                                                'x_studio_universidad_5', 'x_studio_carrera_1',
                                                                'x_studio_departamento_estado','x_studio_fecha_de_grado_2',
                                                                'x_studio_ciudad_1'])
        _logger.info(tramite)
        if tramite:
            return {'ok': True, 'tramite': tramite}
        else:
            return {'ok': False }

            
    @http.route('/tramite_fase1', type="json", auth='public', website=True)
    def pasar_fase1(self, **kw):
        data = kw.get('data')
        format = '%Y-%m-%d %H:%M:%S' # The format 
        datetime_str = datetime.strptime(data['fecha_pago'], format)
        datetime_str = datetime_str + timedelta(hours=5)
        try:
            tramite = http.request.env['x_cpnaa_procedure'].search([('id','=',data['id_tramite']),('x_cycle_ID.x_order','=',0)])
            ciclo_ID = http.request.env["x_cpnaa_cycle"].search(["&",("x_service_ID.id","=",tramite["x_service_ID"].id),("x_order","=",1)])
            update = {'x_cycle_ID': ciclo_ID.id,'x_radicacion_date': datetime_str, 'x_pay_datetime': datetime_str, 'x_pay_type': data['tipo_pago'], 
                      'x_consignment_number': data['numero_pago'], 'x_bank': data['banco'], 'x_consignment_price': data['monto_pago']}
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).write(update)
            if tramite:
                return {'ok': True, 'message': 'Trámite actualizado con exito'}
            else:
                return {'ok': True, 'message': 'No se encontro ningún trámite para actualizar'}
        except:
            return {'ok': False, 'error': 'Ha ocurrido un error'}
        
    @http.route('/cliente/<model("x_cpnaa_user"):persona>', auth='public', website=True)
    def buscar_persona(self, persona):
        return  http.request.render('my_sample.user', {
            'persona': persona
        })
    
    @http.route('/cliente/tramite/<string:form>', auth='public', website=True)
    def inicio_tramite(self, form):
        inicio_tramite = True
        return http.request.render('my_sample.inicio_tramite', {'form': form, 'inicio_tramite': inicio_tramite})

    @http.route('/validar_tramites', type="json", methods=["POST"], auth='public', website=True)
    def validar_tramites(self, **kw):
        hoy = date.today()
#         hoy= datetime.strptime('24062020', '%d%m%Y').date()
        doc = kw.get('x_document')
        doc_type = int(kw.get('x_document_type_ID'))
        user = http.request.env['x_cpnaa_user'].search([('x_document_type_ID','=',doc_type),('x_document','=',doc)])
        graduando = http.request.env['x_procedure_temp'].sudo().search([('x_tipo_documento_select','=',doc_type),('x_documento','=',doc)])
        grado = http.request.env['x_cpnaa_grade'].sudo().browse(graduando.x_grado_ID.id)
        if grado:
            if grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay) >= hoy:
                _logger.info(grado.x_date - timedelta(days=grado.x_agreement_ID.x_days_to_pay))
            else:
                grado = False
        matricula = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1','=',doc_type),('x_studio_documento_1','=',doc),
                                                                         ('x_cycle_ID.x_order','=',5), ('x_service_ID.x_name','like','MATRÍCULA')])
        if len(user) > 1:
            user = user[0]
        if (matricula):
            return { 'ok': True, 'id': user.id, 'matricula': True }
        elif (user):
            return { 'ok': True, 'id': user.id, 'convenio': False }
        elif (grado):
            return { 'ok': True, 'id': graduando.id, 'convenio': True }
        else:
            return { 'ok': False, 'id': False, 'convenio': False }
    
    @http.route('/tramite/<string:origen>/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def formulario_tramites(self, origen, tipo_doc, documento):
        validos = ['matricula','inscripciontt','licencia']
        doc_validos = ['1','2','5']
        servicio = 'MATRICULA PROFESIONAL'
        if tipo_doc == '1' and not self.validar_solo_numeros(documento):
            return http.request.redirect('/')
        if origen == validos[1]:
            servicio = 'CERTIFICADO DE INSCRIPCION PROFESIONAL'
        if origen == validos[2]:
            servicio = 'LICENCIA TEMPORAL ESPECIAL'
        mismo_tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                      ('x_studio_documento_1','=',documento),('x_service_ID.x_name','like',servicio)])
        if origen in validos and tipo_doc in doc_validos and not mismo_tramite:
            _logger.info(origen, tipo_doc, documento);
            return http.request.render('my_sample.formulario_tramites', {'tipo_doc': tipo_doc, 'documento':documento, 'form': origen, 'origen': 1})
        else:
            return http.request.redirect('/')
    
    @http.route('/tramite/convenios/<model("x_procedure_temp"):cliente>', auth='public', website=True)
    def formulario_convenio(self, cliente):
        form = 'inscripciontt'
        if (cliente.x_carrera_select.x_level_ID.x_name == 'PROFESIONAL'):
            form = 'matricula'
        return http.request.render('my_sample.formulario_tramites', {'cliente': cliente, 'form': form, 'origen': 2})

    @http.route('/cliente/<model("x_cpnaa_user"):persona>/tramites', auth='public', website=True)
    def list_tramites(self, persona):
        return http.request.render('my_sample.lista_tramites', {
            'tramites': http.request.env['x_cpnaa_procedure'].sudo().search([('x_user_ID','=',persona[0].id),('x_cycle_ID.x_order','<','5')]),
            'persona': persona
        })
        
    @http.route('/get_email', type="json", auth='public', website=True)
    def get_email(self, **kw):
        cadena = kw.get('cadena')
        result = http.request.env['x_cpnaa_user'].sudo().search([('x_email'.lower(),'=',cadena.lower())])
        _logger.info(len(result))
        _logger.info(result)
        if (len(result) < 1):
            return { 'ok': True, 'email_exists': False }
        else:
            return { 'ok': False, 'email_exists': True }
                                                                               
    @http.route('/get_universidades', type="json", auth='public', website=True)
    def get_universidades(self, **kw):
        _logger.info(kw)
        cadena = kw.get('cadena')
        tipo_universidad = kw.get('tipo_universidad')
        return {'universidades': http.request.env['x_cpnaa_user'].sudo().search_read([('x_user_type_ID.id','=',3),('x_institution_type_ID.id', '=', tipo_universidad),
                                                                               ('x_name', 'ilike', cadena)],['id','x_name'], limit=6)}
        
    @http.route('/get_carreras', type="json", auth='public', website=True)
    def get_carreras(self, **kw):
        _logger.info(kw)
        cadena = kw.get('cadena')
        nivel_profesional = kw.get('nivel_profesional')
        return {'carreras': http.request.env['x_cpnaa_career'].sudo().search_read([('x_level_ID.id','=',nivel_profesional),
                                                                                       ('x_name', 'ilike', cadena)],
                                                                                       ['id','x_name'], limit=6)}
        
    """   RUTAS DE CONVENIOS  """

    @http.route('/convenios', auth='user', website=True)
    def inicio_convenios(self):
        universidad = http.request.env['x_cpnaa_user'].search([('x_email','=',http.request.session.login)])
        if universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios', {'universidad': universidad, 'convenios': convenios})
        
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/<model("x_cpnaa_agreement"):convenio>', auth='user', website=True) 
    def form_archivo_csv(self, universidad, convenio):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'convenio':convenio})
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoCsv/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_csv_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoPdf/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_definitivo_pdf(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        mes = meses[fechaActual.month]
        fechaActualFormat = mes + fechaActual.strftime(" %d de %Y")
        return http.request.render('my_sample.convenios_definitivo_pdf', {'universidad': universidad, 'grado': grado, 'convenio': convenio,
                                                                          'convenios': convenios, 'fechaActual': fechaActualFormat})
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/gradoActas/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def form_archivo_actas_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_grado_actas', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/detalle_grado/<model("x_cpnaa_grade"):grado>', auth='user', website=True) 
    def detalles_grado(self, universidad, grado):
        if universidad.x_email != http.request.session.login or universidad.x_user_type_ID.x_name != 'IES':
            return http.request.redirect('/')
        profesiones = http.request.env['x_cpnaa_career'].search([])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.detalles_grado', {'profesiones': profesiones, 'convenios': convenios,
                                                                'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    @http.route('/guardar_pdf_definitivo', type="json", auth='user', website=True) 
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
        
    @http.route('/guardar_pdf_actas', type="json", auth='user', website=True) 
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
    
    @http.route('/guardar_registros', type="json", auth='user', website=True) 
    def guardar_registros_csv(self, **kw):
        registros = kw.get('registros')
        data = kw.get('data')
        _logger.info(data)
        id_carrera = data['profesion']
        id_universidad = data['universidad']
        id_convenio = data['convenio']
        id_grado = data['grado']
        fecha = data['fecha']
        guardados = 0
        try:
            if (id_grado == ''):
                grado = http.request.env['x_cpnaa_grade'].create({'x_phase_1': True, 'x_carrera_ID': id_carrera, 
                                         'x_date': fecha, 'x_agreement_ID': id_convenio, 'x_studio_universidad': id_universidad})
                id_grado = grado['id']
            for reg in registros:
                genero = self.validar_genero(reg['f_gender'])
                tipo_doc = self.validar_tipo_doc(reg['a_document_type'])
                name = reg['c_name'].split(' ')[0]
                id_guardado = http.request.env['x_procedure_temp'].sudo().create({
                    'x_tipo_documento_select': tipo_doc, 'x_documento': reg['b_document'], 'x_nombres': reg['c_name'], 'x_genero_ID': genero,
                    'x_apellidos': reg['d_lastname'],  'x_fecha_de_grado': fecha, 'x_email': reg['g_email'], 'x_agreement_ID': id_convenio, 
                    'x_grado_ID': id_grado, 'x_carrera_select': id_carrera, 'x_universidad_select': id_universidad})
                guardados = guardados + 1
        except IOError:
            _logger.info(IOError)
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar los registros, vuelve a intentarlo'}
        return {'ok': True, 'message': str(guardados)+' Registros guardados con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    @http.route('/procesar_archivo', type="json", auth='user', website=True) 
    def procesar_csv(self, **kw):
        data = kw.get('data')
        fecha = data['fecha_grado']
        f = fecha.split('-')
        fecha_grado = f[2]+'/'+f[1]+'/'+f[0]
        try:
            data_csv = base64.b64decode(data['archivo'])
        except:
            return {'ok': False, 'message': 'Ha ocurrido un error al leer el archivo, verifique su contenido'}
        data_str = str(data_csv)
        rows = data_str.split('\\r\\n')
        if len(rows) == 1:
            rows = data_str.split('\\n')
        _logger.info(data_str)
        results = []
        for x in range(0,len(rows)):
            if rows[x] is not rows[0]:
                result = self.validar_datos(rows[x], fecha_grado)
                if result:
                    results.append(result)
        if len(results)<1:
            return {'ok': False, 'message': 'Ningún registro válido en el archivo'}
        else:
            return {'ok': True, 'results': results, 'fecha_grado': fecha, }
        
        
    """ FUNCIONES DE VALIDACIÓN DE DATOS CARGA CSV CONVENIOS """
    
    def validar_datos(self, row, fecha_grado):
        datos = row.split(';')
        _logger.info(len(datos))
#         _logger.info(datos)
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
                if datos[5] != '':
                    if self.validar_email(datos[5]):
                        vals['g_email'] = {'valor':datos[5].upper(), 'clase':'valido'}
                    else:
                        vals['g_email'] = {'valor':datos[5], 'clase':'invalido'}
                else:
                    vals['g_email'] = {'valor':'N/A', 'clase':'valido'}
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
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
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
    
    @http.route('/validar_documento_bd', type="json", auth='user', website=True) 
    def validar_documento_bd(self, **kw):
        data = kw.get('data')
        error = ''
        results = True
        if data['profesion_id'] == '110' or data['profesion_id'] == '109':
            data['profesion_id'] = ['110','109']
        else:
            data['profesion_id'] = [data['profesion_id']]
        tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',self.validar_tipo_doc(data['tipo_doc'])),
                                                                ('x_studio_documento_1','=',data['numero_doc']),
                                                                ('x_studio_carrera_1.id','in',data['profesion_id'])])
        egresado = http.request.env['x_procedure_temp'].search([('x_tipo_documento_select.id','=',self.validar_tipo_doc(data['tipo_doc'])),
                                                                ('x_documento','=',data['numero_doc']),
                                                                ('x_carrera_select.id','in',data['profesion_id'])])
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