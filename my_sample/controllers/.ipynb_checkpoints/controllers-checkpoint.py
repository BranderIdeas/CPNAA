 # -*- coding: utf-8 -*-
from odoo import http
import logging
import base64
import tempfile
import csv
import re


# Intancia de logging para imprimir por pantalla
_logger = logging.getLogger(__name__)

class MySample(http.Controller):
    @http.route('/cliente/<model("x_cpnaa_user"):persona>', auth='public', website=True)
    def fun_persona(self, persona):
        return  http.request.render('my_sample.user', {
            'persona': persona
        })
    
    @http.route('/convenios/cliente/<model("x_transient_convenios"):cliente>', auth='public', website=True)
    def form_convenio(self, cliente):
        return http.request.render('my_sample.form_convenios', {'cliente': cliente})

    @http.route('/cliente/<model("x_cpnaa_user"):persona>/tramites', auth='public', website=True)
    def list_tramites(self, persona):
        return http.request.render('my_sample.lista_tramites', {
            'tramites': http.request.env['x_cpnaa_procedure'].search([('x_user_ID','=',persona[0].id)]),
            'persona': persona
        })
    
    @http.route('/cliente/tramite', auth='public', website=True)
    def inicio_tramite(self):
        return http.request.render('my_sample.inicio_tramite', {})

    @http.route('/website_form/validar_tramites', type="json", auth='public', website=True)
    def validar_tramites(self, **kw):
        _logger.info(kw)
        doc = int(kw.get('x_document'))
        doc_type = int(kw.get('x_document_type_ID'))
        user = http.request.env['x_cpnaa_user'].search([('x_document_type_ID','=',doc_type),('x_document','=',doc)])
        convenio = http.request.env['x_transient_convenios'].search([('x_document_type_ID','=',doc_type),('x_document','=',doc)])
        _logger.info(user)
        _logger.info(convenio)
        if (user):
            if len(user) > 1:
                user = user[0]
            return { 'ok': True, 'id': user.id, 'convenio': False }
        elif (convenio):
            return { 'ok': True, 'id': convenio.id, 'convenio': True }
        else:
            return { 'ok': False, 'id': False, 'convenio': False }

    
    @http.route('/convenios', auth='public', website=True) 
    def inicio_convenios(self):
        return http.request.render('my_sample.ies_inicio')
    
    @http.route('/website_form/buscar_convenios', type="json", auth='public', website=True)
    def buscar_convenios(self, **kw):
        univ_id = int(kw.get('univ_id'))
        conv = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',univ_id)])
        if len(conv) > 0:
            return {
                "id": univ_id,
            }
        else:
            return {
                "id": False,
                "message": "No hay convenios vigentes",
            }
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>', auth='public', website=True)
    def listar_convenios(self, universidad):
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        if len(convenios) > 0:
            return http.request.render('my_sample.convenios', {'convenios': convenios, 'universidad':universidad})
        else:
            return http.request.redirect('/convenios')
        
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/<model("x_cpnaa_agreement"):convenio>', auth='public', website=True) 
    def form_archivo_csv(self, universidad, convenio):
        profesiones = http.request.env['x_cpnaa_institute_carreer'].search([('x_institute_ID','=',universidad.id)])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'convenio':convenio})
    
    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/grado/<model("x_cpnaa_grade"):grado>', auth='public', website=True) 
    def form_archivo_csv_grado(self, universidad, grado):
        profesiones = http.request.env['x_cpnaa_institute_carreer'].search([('x_institute_ID','=',universidad.id)])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.convenios_archivo_csv', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})

    @http.route('/convenios/<model("x_cpnaa_user"):universidad>/detalle_grado/<model("x_cpnaa_grade"):grado>', auth='public', website=True) 
    def detalles_grado(self, universidad, grado):
        profesiones = http.request.env['x_cpnaa_institute_carreer'].search([('x_institute_ID','=',universidad.id)])
        convenios = http.request.env['x_cpnaa_agreement'].search([('x_user_ID','=',universidad.id)])
        convenio = http.request.env['x_cpnaa_agreement'].search([('id','=',grado.x_agreement_ID.id)])
        return http.request.render('my_sample.detalles_grado', {'profesiones': profesiones, 'convenios': convenios,
                                                                       'universidad':universidad, 'grado': grado, 'convenio': convenio})
    
    @http.route('/guardar_registros', type="json", auth='public', website=True) 
    def guardar_registros_csv(self, **kw):
        registros = kw.get('registros')
        data = kw.get('data')
        id_carrera = data['profesion']
        id_universidad = data['universidad']
        id_convenio = data['convenio']
        id_grado = data['grado']
        fecha = data['fecha']
        guardados = 0
        _logger.info(id_grado)
        try:
            if (id_grado == ''):
                grado = http.request.env['x_cpnaa_grade'].create({'x_phase_1': True, 'x_institute_carreer_ID': id_carrera, 
                                         'x_date': fecha, 'x_agreement_ID': id_convenio, 'x_studio_universidad': id_universidad})
                id_grado = grado['id']
                _logger.info(grado)
            for reg in registros:
                _logger.info(reg)
                genero = self.validar_genero(reg['f_gender'])
                tipo_doc = self.validar_tipo_doc(reg['a_document_type'])
                name = reg['c_name'].split(' ')[0]
                _logger.info(genero, tipo_doc)
                id_guardado = http.request.env['x_transient_convenios'].create({
                    'x_name': name,'x_document_type_ID': tipo_doc, 'x_document': reg['b_document'], 'x_names': reg['c_name'],
                    'x_last_names': reg['d_lastname'], 'x_gender_ID': genero, 'x_email': reg['g_email'], 'x_agreement_ID': id_convenio, 
                    'x_grade_ID': id_grado, 'x_career_ID': id_carrera, 'x_institution_ID': id_universidad})
                guardados = guardados + 1
        except IOError:
            _logger.info(IOError)
            return {'ok': False, 'error': 'Ha ocurrido un error al intentar guardar los registros, vuelve a intentarlo'}
        return {'ok': True, 'message': str(guardados)+' Registros guardados con exito', 'grado': id_grado, 'convenio': id_convenio, 'universidad': id_universidad}
    
    @http.route('/procesar_archivo', type="json", auth='public', website=True) 
    def procesar_csv(self, **kw):
        data = kw.get('data')
        fecha = data['fecha_grado']
        _logger.info(kw)
        _logger.info(data)
        f = fecha.split('-')
        fecha_grado = f[2]+'/'+f[1]+'/'+f[0]
        try:
            data_csv = base64.b64decode(data['archivo'])
        except:
            return {'ok': False, 'message': 'Ha ocurrido un error al leer el archivo, verifique su contenido'}
        data_str = str(data_csv)
        data_str = data_str[(data_str.find(';') - 7) : (len(data_str) - 5)]
        rows = data_str.split('\\r\\n')
        results = []
        for x in range(0,len(rows)):
            if rows[x] is not rows[0]:
                result = self.validar_datos(rows[x], fecha_grado)
                results.append(result)
        if len(results)<1:
            return {'ok': False, 'message': 'Ningún registro en el archivo'}
        else:
            return {'ok': True, 'results': results, 'fecha_grado': fecha, }
    
    def validar_datos(self, row, fecha_grado):
        datos = row.split(';')
        
        ok = True
        vals = {'a_document_type':'','b_document':'','c_name':'','d_lastname':'',
                'e_fecha_grado':{'valor': fecha_grado, 'clase':'valido'},'f_gender':'','g_email':''}
        for x in range(0,len(datos)):
            if len(datos) < 5:
                return {'vals': {'Registro no cumplen con el formato requerido': datos}}
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
            if datos[5]:
                if self.validar_email(datos[5]):
                    vals['g_email'] = {'valor':datos[5].upper(), 'clase':'valido'}
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
        
#         tipos_validos = http.request.env['x_cpnaa_document_type'].search([])
#             if tipo in tipos_validos:
#                 return True
#             else:
#                 return False
            