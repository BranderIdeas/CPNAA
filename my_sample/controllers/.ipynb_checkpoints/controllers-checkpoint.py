 # -*- coding: utf-8 -*-
from odoo import http
from datetime import date, datetime, timedelta
import logging
import base64
import unicodedata
import re
import io
import base64

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
    
    @http.route('/pagos', auth='public', website=True)
    def epayco(self):
        return  http.request.render('my_sample.epayco')
    
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
        doc = data['doc']
        tipo_doc = data['doc_type']
        _logger.info(data['fecha_pago'])
        try:
            tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),('x_studio_documento_1','=',doc),
                                                                    ('x_cycle_ID.x_order','=',0)])
            ciclo_ID = http.request.env["x_cpnaa_cycle"].search(["&",("x_service_ID.id","=",tramite["x_service_ID"].id),("x_order","=",1)])
            update = {'x_cycle_ID': ciclo_ID.id,'x_radicacion_date': data['fecha_pago'], 'x_pay_datetime': data['fecha_pago'], 'x_pay_type': data['tipo_pago'], 
                      'x_consignment_number': data['numero_pago'], 'x_bank': data['banco'], 'x_consignment_price': data['monto_pago']}
            http.request.env['x_cpnaa_procedure'].browse(tramite.id).write(update)
        except IOError:
            _logger.info(IOError)
            return {'ok': False, 'error': 'Ha ocurrido un error'}
        return {'ok': True, 'message': 'Trámite actualizado con exito'}
        
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
        doc = kw.get('x_document')
        doc_type = int(kw.get('x_document_type_ID'))
        user = http.request.env['x_cpnaa_user'].search([('x_document_type_ID','=',doc_type),('x_document','=',doc)])
        convenio = http.request.env['x_transient_convenios'].search([('x_document_type_ID','=',doc_type),('x_document','=',doc)])
        matricula = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1','=',doc_type),('x_studio_documento_1','=',doc),
                                                                         ('x_cycle_ID.x_order','=',5), ('x_service_ID.x_name','like','MATRÍCULA')])
        if len(user) > 1:
            user = user[0]
        if (matricula):
            return { 'ok': True, 'id': user.id, 'matricula': True }
        elif (user):
            return { 'ok': True, 'id': user.id, 'convenio': False }
        elif (convenio):
            return { 'ok': True, 'id': convenio.id, 'convenio': True }
        else:
            return { 'ok': False, 'id': False, 'convenio': False }
    
    @http.route('/tramite/<string:origen>/[<string:tipo_doc>:<string:documento>]', auth='public', website=True)
    def formulario_tramites(self, origen, tipo_doc, documento):
        validos = ['matricula','inscripciontt','licencia']
        doc_validos = ['1','2','5']
        servicio = 'MATRÍCULA PROFESIONAL'
        if origen == validos[1]:
            servicio = 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL'
        if origen == validos[2]:
            servicio = 'LICENCIA TEMPORAL ESPECIAL'
        mismo_tramite = http.request.env['x_cpnaa_procedure'].search([('x_studio_tipo_de_documento_1.id','=',tipo_doc),
                                                                      ('x_studio_documento_1','=',documento),('x_service_ID.x_name','=',servicio)])
        if origen in validos and tipo_doc in doc_validos and not mismo_tramite:
            _logger.info(origen, tipo_doc, documento);
            return http.request.render('my_sample.formulario_tramites', {'tipo_doc': tipo_doc, 'documento':documento, 'form': origen, 'origen': 1})
        else:
            return http.request.redirect('/')
    
    @http.route('/tramite/convenios/<model("x_transient_convenios"):cliente>', auth='public', website=True)
    def formulario_convenio(self, cliente):
        form = 'inscripciontt'
        if (cliente.x_career_ID.x_studio_level == 'PROFESIONAL'):
            form = 'matricula'
        return http.request.render('my_sample.formulario_tramites', {'cliente': cliente, 'form': form, 'origen': 2})

    @http.route('/cliente/<model("x_cpnaa_user"):persona>/tramites', auth='public', website=True)
    def list_tramites(self, persona):
        return http.request.render('my_sample.lista_tramites', {
            'tramites': http.request.env['x_cpnaa_procedure'].search([('x_user_ID','=',persona[0].id),('x_cycle_ID.x_order','<','5')]),
            'persona': persona
        })
        
    @http.route('/get_email', type="json", auth='public', website=True)
    def get_email(self, **kw):
        cadena = kw.get('cadena')
        result = http.request.env['x_cpnaa_user'].search([('x_email'.lower(),'=',cadena.lower())])
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
        return {'universidades': http.request.env['x_cpnaa_user'].search_read([('x_user_type_ID.id','=',3),('x_institution_type_ID.id', '=', tipo_universidad),
                                                                               ('x_name', 'ilike', cadena)],['id','x_name'], limit=6)}
        
    @http.route('/get_carreras', type="json", auth='public', website=True)
    def get_carreras(self, **kw):
        _logger.info(kw)
        cadena = kw.get('cadena')
        nivel_profesional = kw.get('nivel_profesional')
        return {'carreras': http.request.env['x_cpnaa_career'].search_read([('x_level_ID.id','=',nivel_profesional),
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
        except IOError:
            _logger.info(IOError)
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
        except IOError:
            _logger.info(IOError)
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
                id_guardado = http.request.env['x_transient_convenios'].create({
                    'x_name': name,'x_document_type_ID': tipo_doc, 'x_document': reg['b_document'], 'x_names': reg['c_name'],
                    'x_last_names': reg['d_lastname'], 'x_gender_ID': genero, 'x_email': reg['g_email'], 'x_agreement_ID': id_convenio, 
                    'x_grade_ID': id_grado, 'x_profesion_ID': id_carrera, 'x_institution_ID': id_universidad})
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
        return True
        
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
        _logger.info(kw)
        results = True
        if (results):
            return {'ok': False, 'error': 'Error'}
        else:
            return {'ok': True, 'message': 'Todo OK',  }