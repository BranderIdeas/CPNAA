from odoo import http
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta, timezone
import logging
from . import lists

_logger = logging.getLogger(__name__)

class Profile(http.Controller):
    @http.route('/profile', auth='user', website=True)
    def profile(self):
        _logger.info(http.request.session)
        if http.request.session.uid == None:
            return http.request.redirect('/web/login')
        else:
            return http.request.render('my_sample.profile')
        
        
    @http.route('/profile/<path:dummy>', auth='user', website=True)
    def profile_redirect(self):
        _logger.info(http.request.session)
        if http.request.session.uid == None:
            return http.request.redirect('/web/login')
        else:
            return http.request.render('my_sample.profile')

        
    @http.route('/profile_api/data_profesional', methods=['POST'], type="json", auth='user', website=True)
    def data_profesional(self, **kw):
        _logger.info(http.request.session.login)
        email = http.request.session.login
        result = http.request.env['x_cpnaa_user'].sudo().search_read([('x_email','=',email)],lists.person_fields)
        person = result[-1] if result else None
        if not person:
            return { 'ok': False, 'message': 'User not found' }
        person = self.get_related_data(person)
        return { 'ok': True, 'person': person }

        
    @http.route('/profile_api/data_profesional/delete/<string:modelo>', methods=['POST'], type="json", auth='user', website=True)
    def delete_data_profesional(self, modelo, **kw):
        data   = kw.get('data')
        rec_id = data.get('id')
        reg_id = data.get('x_professional_registration_ID')
        failed_response = { 'ok': False, 'message': 'Update Failed: The provided data is not valid' }
        _logger.info(kw)
        if modelo not in lists.can_delete:
            return failed_response
        record = http.request.env[modelo].sudo().browse(rec_id)
        if record:
            record.sudo().unlink()
        else:
            return failed_response
        result = self.data_return(modelo, reg_id)
        return { 'ok': True, 'message': 'Data updated successfully', 'data': result } 
    
        
    @http.route('/profile_api/data_profesional/update/<string:modelo>', methods=['POST'], type="json", auth='user', website=True)
    def update_data_profesional(self, modelo, **kw):
        data   = kw.get('data')
        rec_id = data.get('id')
        update = data.get('update')
        _logger.info(kw)
        reg_id = data.get('x_professional_registration_ID') if modelo != 'x_professional_registration' else rec_id
        if modelo not in lists.can_update:
            return { 'ok': False, 'message': 'Update Failed: The provided data is not valid' }
        record = http.request.env[modelo].sudo().browse(rec_id)
        if record:
            record.write(update)
        else:
            new_rec = http.request.env[modelo].sudo().create(update)
            if modelo in lists.models_data_o2o:
                register = http.request.env['x_professional_registration'].sudo().browse(reg_id)
                field_rel = '%s_ID' % modelo
                register.write({ field_rel: new_rec.id })
        result = self.data_return(modelo, reg_id)
        return { 'ok': True, 'message': 'Data updated successfully', 'data': result } 
    
    
    def data_return(self, modelo, reg_id):
        if modelo in lists.models_data_o2m:
            result = self.get_o2m_data(modelo, reg_id)
            return result
        if modelo in lists.models_data_o2o:
            result = self.get_o2o_data(modelo, reg_id)
            return result
        if modelo == 'x_professional_registration':
            result = self.get_professional_registration(reg_id)
            return result
        
    
    @http.route('/profile_api/data_select/<string:modelo>', methods=['POST'], type="json", auth='user', website=True)
    def data_select(self, modelo):
        _logger.info(http.request.session.login)
        if modelo not in lists.data_select_models:
            return { 'ok': False, 'message': 'Error getting data for model: %s' % modelo }
        domain = ['|',('x_country_ID.x_name','=','COLOMBIA'),('x_name','=','NO APLICA')] if modelo == 'x_cpnaa_state' else []
        fields = self.get_fields_for_select(modelo)
        data = http.request.env[modelo].sudo().search_read(domain, fields)
        return { 'ok': True, 'message': 'Results for model: %s' % modelo, 'data': data }
        
    
    @http.route('/profile_api/cities_by_dptos/<int:state_id>', methods=['POST'], type="json", auth='user', website=True)
    def cities_by_dptos(self, state_id):
        _logger.info(http.request.session.login)
        data = http.request.env['x_cpnaa_city'].sudo().search_read([('x_state_ID','=',state_id)], ['id', 'x_name'])
        return { 'ok': True, 'message': 'Results for state_id: %s' % state_id, 'data': data }
    
    
    @http.route('/get_instituciones', methods=["POST"], type="json", auth='public', website=True)
    def get_instituciones(self, **kw):
        cadena = kw.get('cadena')
        univ = http.request.env['x_cpnaa_user'].sudo().search_read([('x_name', 'ilike', cadena)],['id','x_name'], limit=10)
        return { 'ok': True, data: univ }
    
    
    @http.route('/profile_api/save_image', methods=['POST'], type="json", auth='user', website=True)
    def save_image(self, **kw):
        _logger.info(http.request.session.login)
        email  = http.request.session.login
        image  = kw.get('user_image')
        result = http.request.env['x_cpnaa_user'].sudo().search([('x_email','=',email)])
        person = result[0] if result else None
        if not image:
            return { 'ok': False, 'message': 'User image is required' }
        if not person:
            return { 'ok': False, 'message': 'User not found' }
        update = { 'x_user_image': image }
        person.sudo().write(update)
        return { 'ok': True, 'message': 'User image saved successfully' }
    
    
    def get_related_data(self, person):
        document = person['x_document']
        register_id = person['x_professional_registration_ID'][0] if person['x_professional_registration_ID'] else []
        domain_procedure = [('x_studio_tipo_de_documento_1.id', "=", person['x_document_type_ID'][0]),
                            ('x_studio_documento_1','=',person['x_document']), ('x_cycle_ID.x_order','=',5)]
        person['x_procedures'] = http.request.env['x_cpnaa_procedure'].sudo().search_read(domain_procedure, lists.procedure_fields)
        person['x_procedures'] = self.set_academic_levels_in_procedures(person['x_procedures'])
        for t in person['x_procedures']:
            t = self.get_institution_data(t)
            t = lists.normalize_fields(t)
        if person['x_professional_registration_ID']:
            person['x_professional_registration'] = self.get_professional_registration(register_id)
        else:
            person = self.create_professional_registration(person)
        return person
    
    
    def get_institution_data(self, t):
        univ = http.request.env['x_cpnaa_user'].sudo().browse(t['x_studio_universidad_5'][0])
        t['x_institution'] = univ.read(lists.institution_fields)[0] if univ else {}
        return t
    
    
    def get_professional_registration(self, register_id):
        professional_registration = http.request.env['x_professional_registration'].sudo().search_read([('id','=',register_id)],[])
        professional_registration = professional_registration[0] if professional_registration else {}
        professional_registration = self.delete_base_fields(professional_registration) if professional_registration else {}
        professional_registration = self.delete_related_fields(professional_registration) if professional_registration else {}
        for m in lists.models_data_o2m:
            professional_registration[m] = self.get_o2m_data(m, register_id)
        for m in lists.models_data_o2o:
            professional_registration[m] = self.get_o2o_data(m, register_id)
        return professional_registration
    
    
    def create_professional_registration(self, person):
        register_name = 'REGISTRO PROFESIONAL - %s %s - %s' % (person['x_name'], person['x_last_name'], person['x_document'])
        # levels = self.get_academic_levels(person['x_procedures'])
        data_create = { 'x_name': register_name, 'x_cpnaa_user_ID': person['id']} #, 'x_academic_education_level_IDs': levels }
        new_register = http.request.env['x_professional_registration'].sudo().create(data_create)
        update = { 'x_professional_registration_ID': new_register.id }
        http.request.env['x_cpnaa_user'].sudo().browse(person['id']).write(update)
        person['x_professional_registration'] = self.get_professional_registration(new_register.id)
        person['x_professional_registration_ID'] = [person['x_professional_registration']['id'], person['x_professional_registration']['x_name']]
        return person
    
    
    def get_academic_levels(self, procedures):
        levels = []
        for p in procedures:
            level = http.request.env['x_academic_education_level'].sudo().search([('x_level_procedure_cpnaa.id','=',p['x_professional_level_ID'][0])])
            if level:
                levels.append(level.id)
        return levels
    
    
    def set_academic_levels_in_procedures(self, procedures):
        for p in procedures:
            level = http.request.env['x_academic_education_level'].sudo().search([('x_level_procedure_cpnaa.id','=',p['x_studio_nivel_profesional'][0])])
            if level:
                p['x_studio_nivel_profesional'] = [ level.id, level.x_name ]
        return procedures
    
    
    def get_fields_for_select(self, modelo):
        switch_opts = {
            'x_license_subcategories': ['id', 'x_name', 'x_license_type_ID', 'x_area', 'x_stratum'],
            'x_license_modalities': ['id', 'x_name', 'x_license_subcategory_ID', 'x_stratum'],
        }
        return switch_opts.get(modelo, ['id', 'x_name'])
    
    
    def delete_base_fields(self, data):
        for bf in lists.base_fields:
            del data[bf]
        return data
        
    
    def delete_related_fields(self, data):
        for rf in lists.related_fields:
            del data[rf]
        return data
    
    
    def get_o2m_data(self, modelo, register_id):
        name_field = 'x_professional_registration_id' if modelo in ['x_elected_positions_registered'] else 'x_professional_registration_ID'
        result = http.request.env[modelo].sudo().search_read([(name_field,'=',register_id)])
        for r in result:
            self.delete_base_fields(r)
        return result

        
    def get_o2o_data(self, modelo, register_id):
        result = http.request.env[modelo].sudo().search_read([('x_professional_registration_ID','=',register_id)])
        for r in result:
            self.delete_base_fields(r)
        return result[0] if result else {}    