from odoo import http
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta, timezone
import logging
from . import person_fields

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
        result = http.request.env['x_cpnaa_user'].sudo().search_read([('x_email','=',email)],person_fields.campos_persona)
        person = result[0] if result else None
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
        if modelo not in self.can_delete:
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
        if modelo not in self.can_update:
            return { 'ok': False, 'message': 'Update Failed: The provided data is not valid' }
        record = http.request.env[modelo].sudo().browse(rec_id)
        if record:
            record.write(update)
        else:
            http.request.env[modelo].sudo().create(update)
        result = self.data_return(modelo, reg_id)
        return { 'ok': True, 'message': 'Data updated successfully', 'data': result } 
    
    
    def data_return(self, modelo, reg_id):
        if modelo in self.models_data_o2m:
            result = self.get_o2m_data(modelo, reg_id)
            return result
        if modelo in self.models_data_o2o:
            result = self.get_o2o_data(modelo, reg_id)
            return result
        if modelo == 'x_professional_registration':
            result = self.get_professional_registration(reg_id)
            return result
        
    
    @http.route('/profile_api/data_select/<string:modelo>', methods=['POST'], type="json", auth='user', website=True)
    def data_select(self, modelo):
        _logger.info(http.request.session.login)
        if modelo not in self.data_select_models:
            return { 'ok': False, 'message': 'Error getting data for model: %s' % modelo }
        domain = ['|',('x_country_ID.x_name','=','COLOMBIA'),('x_name','=','NO APLICA')] if modelo == 'x_cpnaa_state' else [] 
        data = http.request.env[modelo].sudo().search_read(domain, ['id', 'x_name'])
        return { 'ok': True, 'message': 'Results for model: %s' % modelo, 'data': data }
        
    
    @http.route('/profile_api/cities_by_dptos/<int:state_id>', methods=['POST'], type="json", auth='user', website=True)
    def cities_by_dptos(self, state_id):
        _logger.info(http.request.session.login)
        data = http.request.env['x_cpnaa_city'].sudo().search_read([('x_state_ID','=',state_id)], ['id', 'x_name'])
        return { 'ok': True, 'message': 'Results for state_id: %s' % state_id, 'data': data }
    
    
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
        register_id = person['x_professional_registration_ID'][0]
        campos_procedure = ['id', 'x_studio_universidad_5', 'x_service_ID', 'x_enrollment_number', 'x_expedition_date']
        person['x_procedures'] = http.request.env['x_cpnaa_procedure'].sudo().search_read([('x_studio_documento_1','=',person['x_document'])], campos_procedure)
        for t in person['x_procedures']:
            t['x_institution_ID'] = t['x_studio_universidad_5']
            del t['x_studio_universidad_5']
        person['x_professional_registration'] = self.get_professional_registration(register_id)
        return person
        
    
    def get_professional_registration(self, register_id):
        professional_registration = http.request.env['x_professional_registration'].sudo().search_read([('id','=',register_id)],[])
        professional_registration = professional_registration[0] if professional_registration else {}
        professional_registration = self.delete_base_fields(professional_registration) if professional_registration else {}
        professional_registration = self.delete_related_fields(professional_registration) if professional_registration else {}
        # for m in self.models_data_o2m:
        #     professional_registration[m] = self.get_o2m_data(m, register_id)
        # for m in self.models_data_o2o:
        #     professional_registration[m] = self.get_o2o_data(m, register_id)
        return professional_registration
    
    
    def delete_base_fields(self, data):
        for bf in self.base_fields:
            del data[bf]
        return data
        
    
    def delete_related_fields(self, data):
        for rf in self.related_fields:
            del data[rf]
        return data
    
    
    def get_o2m_data(self, modelo, register_id):
        result = http.request.env[modelo].sudo().search_read([('x_professional_registration_ID','=',register_id)])
        for r in result:
            self.delete_base_fields(r)
        return result

        
    def get_o2o_data(self, modelo, register_id):
        result = http.request.env[modelo].sudo().search_read([('x_professional_registration_ID','=',register_id)])
        for r in result:
            self.delete_base_fields(r)
        return result[0] if result else {}
    
      
    data_select_models = [
        'x_academic_education_level',
        'x_product_type',
        'x_professional_performance_categories',
        'x_elected_positions',
        'x_cpnaa_country',
        'x_cpnaa_state',
    ]
    
      
    models_data_o2m = [
        'x_academic_education',
        'x_scientific_academic_experience',
        'x_experience',
        'x_languages',
        'x_construction_license_register',
        'x_elected_positions_registered',
    ]    
      
    models_data_o2o = [
        'x_executed_amounts',
        'x_construction_experience_sqm',
    ]
    
      
    base_fields = [
        'display_name',
        'create_uid',
        'create_date',
        'write_uid',
        'write_date',
        '__last_update',
    ]
    
      
    related_fields = [
        'x_user_image_rel',
    ]
    
      
    can_update = [
        'x_professional_registration',
        'x_executed_amounts',
        'x_construction_experience_sqm',
        'x_academic_education',
        'x_scientific_academic_experience',
        'x_experience',
        'x_languages',
        'x_elected_positions_registered',
    ]
        
      
    can_delete = [
        'x_academic_education',
        'x_scientific_academic_experience',
        'x_experience',
        'x_languages',
        'x_x_elected_positions_x_professional_registration_rel',
    ]