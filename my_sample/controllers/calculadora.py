from odoo import http
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta, timezone
import logging
from . import lists

_logger = logging.getLogger(__name__)

class Calculadora(http.Controller):
    @http.route('/calculadora', auth='user', website=True)
    def calculadora(self):
        _logger.info(http.request.session)
        if http.request.session.uid == None:
            return http.request.redirect('/web/login')
        else:
            return http.request.render('my_sample.calculadora')
        
        
    @http.route('/calculadora/<path:dummy>', auth='user', website=True)
    def calculadora_redirect(self):
        _logger.info(http.request.session)
        if http.request.session.uid == None:
            return http.request.redirect('/web/login')
        else:
            return http.request.render('my_sample.calculadora')
        
    
    @http.route('/calculadora_api/data_profesional', methods=['POST'], type="json", auth='user', website=True, cors='*')
    def data_profesional(self, **kw):
        _logger.info(http.request.session.login)
        email = http.request.session.login
        result = http.request.env['x_cpnaa_user'].sudo().search_read([('x_email','=',email)],self.person_fields)
        person = result[-1] if result else None
        if not person:
            return { 'ok': False, 'message': 'User not found' }
        person = self.get_related_data(person)
        return { 'ok': True, 'person': person }
   
            
    @http.route('/calculadora_api/get', methods=['POST'], type="json", auth='user', website=True)
    def get_simulations(self, **kw):
        _logger.info(http.request.session)
        email = http.request.session.login
        result = http.request.env['x_cpnaa_user'].sudo().search_read([('x_email','=',email)], self.person_fields)
        person = result[-1] if result else None
        if not person:
            return { 'ok': False, 'message': 'User not found' }
        result = self.get_simulations_by_person_id(person["id"])
        return { 'ok': True, 'data': result }
    
    
    def get_simulations_by_id(self, id):
        simulation_rec = http.request.env['x_simulations'].sudo().browse(id)
        if simulation_rec:
            simulation = simulation_rec.sudo().read(self.simulations_fields)[0]
            simulation['x_project_usages'] = self.get_project_usages_by_simulation_id(id)
            return simulation
        else:
            return False
           
    
    def get_simulations_by_person_id(self, person_id):
        modelo = 'x_simulations'
        domain = [('x_cpnaa_user_id','=',person_id)]
        fields = self.simulations_fields
        simulations = http.request.env[modelo].sudo().search_read(domain, fields)
        for s in simulations:
            s['x_project_usages'] = self.get_project_usages_by_simulation_id(s['id'])
        return simulations
    
    
    def get_project_usages_by_simulation_id(self, simulation_id):
        modelo = 'x_project_usages_of_simulations'
        domain = [('x_simulations_id','=',simulation_id)]
        fields = self.usage_simulations_fields
        usages = http.request.env[modelo].sudo().search_read(domain, fields)
        for u in usages:
            u = self.update_usage_factor(u)
        return usages
    
    
    def update_usage_factor(self, usage):
        model_usages_of_simulations = 'x_project_usages_of_simulations'
        model_usage_values = 'x_project_usages'
        fields = self.usage_simulations_fields
        the_usage = http.request.env[model_usages_of_simulations].sudo().browse(usage['id'])
        usage_updated_values = http.request.env[model_usage_values].sudo().browse(the_usage['x_project_usages_id'].id)
        level = self.get_level_name(the_usage.x_level)
        factor = getattr(usage_updated_values, level)
        the_usage.write({ 'x_factor': factor })
        _logger.info(str(the_usage))
        return the_usage
        
    
    def get_related_data(self, person):
        modelo = 'x_cpnaa_procedure'
        fields = lists.procedure_fields
        domain = [('x_studio_tipo_de_documento_1.id', "=", person['x_document_type_ID'][0]),
                  ('x_studio_documento_1','=',person['x_document']), ('x_cycle_ID.x_order','=',5)]
        person['x_procedures'] = http.request.env[modelo].sudo().search_read(domain, fields)
        for t in person['x_procedures']:
            t = lists.normalize_fields(t)
        person["x_simulations"] = self.get_simulations_by_person_id(person["id"])
        return person
    
        
    @http.route('/calculadora_api/create', methods=['POST'], type="json", auth='user', website=True)
    def create_simulation(self, **kw):
        _logger.info(kw)
        simulation = kw.get('simulation')
        modelo = 'x_simulations'
        if simulation:
            new_rec = http.request.env[modelo].sudo().create(simulation)
            result = self.get_simulations_by_id(new_rec.id)
            return { 'ok': True, 'message': 'Simulation created successfully', 'data': result } 
        else:
            return { 'ok': False, 'message': 'Create Failed: The provided data is not valid' }
    
    
    @http.route('/calculadora_api/update', methods=['POST'], type="json", auth='user', website=True)
    def update_simulation(self, **kw):
        _logger.info(kw)
        simulation = kw.get('simulation')
        rec_id = simulation.get('id')
        modelo = 'x_simulations'
        record = http.request.env[modelo].sudo().browse(rec_id)
        if record:
            complementary_fees_empty   = 'x_complementary_fees_ids' in simulation and len(simulation['x_complementary_fees_ids']) == 0
            construction_service_empty = 'x_construction_service_ids' in simulation and len(simulation['x_construction_service_ids']) == 0
            if complementary_fees_empty:
                record.x_complementary_fees_ids = [(5, 0, 0)] # Elimina todos los registros existentes en el campo Many2Many
            if construction_service_empty:
                record.x_construction_service_ids = [(5, 0, 0)] # Elimina todos los registros existentes en el campo Many2Many
            record.write(simulation)
            result = self.get_simulations_by_id(record.id)
            return { 'ok': True, 'message': 'Simulation updated successfully', 'data': result }
        else:
            return { 'ok': False, 'message': 'Update Failed: The provided data is not valid' }
    
    
    @http.route('/calculadora_api/delete', methods=['POST'], type="json", auth='user', website=True)
    def delete_simulation(self, **kw):
        _logger.info(kw)
        rec_id = kw.get('simulation_id')
        modelo = 'x_simulations'
        record = http.request.env[modelo].sudo().browse(rec_id)
        if record:
            record.unlink()
            return { 'ok': True, 'message': 'Simulation deleted successfully', 'data': { 'id': rec_id } }
        else:
            return { 'ok': False, 'message': 'Delete Failed: The provided data is not valid' }
        
        
    @http.route('/calculadora_api/save_uses', methods=['POST'], type="json", auth='user', website=True)
    def save_uses(self, **kw):
        use = kw.get('use')
        modelo = 'x_project_usages_of_simulations'
        _logger.info(kw)
        if use:
            if use.get('id'):
                use_rec = http.request.env[modelo].sudo().browse(use)
                use_rec.write(use)
                result = new_rec.read(self.usage_simulations_fields)[0]
                return { 'ok': True, 'message': 'Use updated successfully', 'data': result }
            else:
                new_rec = http.request.env[modelo].sudo().create(use)
                result = new_rec.read(self.usage_simulations_fields)[0]
                return { 'ok': True, 'message': 'Use created successfully', 'data': result }
        else:
            return { 'ok': False, 'message': 'Save Failed: The provided data is not valid' }
    
        
    @http.route('/calculadora_api/delete_uses', methods=['POST'], type="json", auth='user', website=True)
    def delete_uses(self, **kw):
        use_id = kw.get('use_id')
        modelo = 'x_project_usages_of_simulations'
        _logger.info(kw)
        if use_id:
            use = http.request.env[modelo].sudo().browse(use_id)
            use.sudo().unlink()
            return { 'ok': True, 'message': 'Use deleted successfully', 'data': { 'id': use_id } } 
        else:
            return { 'ok': False, 'message': 'Delete Failed: The provided data is not valid, use_id is required' }


    @http.route('/calculadora_api/data_select/<string:modelo>', methods=['POST'], type="json", auth='user', website=True)
    def data_select(self, modelo):
        _logger.info(http.request.session.login)
        if modelo not in lists.data_select_models:
            return { 'ok': False, 'message': 'Error getting data for model: %s' % modelo }
        domain = [('x_inactive','!=',True)] if modelo == 'x_categories_of_use' or modelo == 'x_project_usages' else []
        fields = self.get_fields_for_forms(modelo)
        data = http.request.env[modelo].sudo().search_read(domain, fields)
        return { 'ok': True, 'message': 'Results for model: %s' % modelo, 'data': data }


    @http.route('/calculadora_api/getSMLV', methods=['POST'], type="json", auth='user', website=True)
    def getSMLV(self):
        _logger.info(http.request.session.login)
        result = http.request.env['x_cpnaa_parameter'].sudo().search_read([('x_name','=','SMLV')], ['x_value'])
        if result:
            data = {}
            data["smlv"] = float(result[0]["x_value"])
            return { 'ok': True, 'message': 'Current value to SMLV', 'data': data }
        else:
            return { 'ok': False, 'message': 'Not found SMLV parameter' }

        
    # Enviar el certificado de vigencia al email y lo retorna al navegador para su descarga
    @http.route('/calculadora_api/send_pdf_mail', methods=["POST"], type="json", auth='public')
    def send_pdf_mail(self, **kw):
        _logger.info(kw.get('subject') + ' ' +kw.get('email'))
        template_obj = http.request.env['mail.template'].sudo().search_read([('name','=','cpnaa_template_calculadoras_pdf')])[0]
        pdf = http.request.env['ir.attachment'].sudo().create({
            'name': kw.get('fileName'),
            'type': 'binary',
            'datas': kw.get('pdfBase64'),
            'mimetype': 'application/x-pdf'
        })
        body = template_obj['body_html']
        body = body.replace('###DESTINATARIO###',kw.get('nameTo'))
        body = body.replace('###REMITENTE###',kw.get('nameFrom'))
        body = body.replace('###PLATAFORMA###',kw.get('calculator'))
        if template_obj:
            mail_values = {
                'subject': kw.get('subject'),
                'attachment_ids': [pdf.id],
                'body_html': body,
                'email_to': kw.get('email'),
                'email_from': template_obj['email_from'],
           }
        try:
            http.request.env['mail.mail'].sudo().create(mail_values).send()
            pdf.unlink()
            return {'ok': True, 'mensaje': 'Se ha completado su solicitud exitosamente' }
        except:
            _logger.info(sys.exc_info())
            return {'ok': False, 'mensaje': 'No se podido completar su solicitud'}
    
    
    def get_fields_for_forms(self, modelo):
        switch_opts = {
            'x_project_usages': [
                'id',
                'x_name',
                'x_categories_of_use_id',
                'x_type',
                'x_one',
                'x_two',
                'x_three',
                'x_four',
                'x_five',
                'x_six',
                'x_high',
                'x_medium',
                'x_low',
            ],
            'x_agglomeration': [
                'id',
                'x_name',
                'x_cost',
            ],
            'x_complexity': [
                'id',
                'x_name',
                'x_factor',
                'x_min',
                'x_max',
            ],
            'x_deliverables': [
                'id',
                'x_name',
                'x_factor',
                'x_field_name',
                'x_multiple',
            ],
            'x_complementary_fees': [
                'id',
                'x_name',
                'x_value',
            ],
            'x_construction_service': [
                'id',
                'x_name',
                'x_factor',
                'x_code',
            ],
            'x_project_management_fee_values': [
                'id',
                'x_name',
                'x_initial_smlv',
                'x_final_smlv',
                'x_management_factor',
                'x_structuring_factor',
            ],
            'x_values_factor_multiplier': [
                'id',
                'x_name',
                'x_category',
                'x_percentage',
            ],
            'x_professional_reference_fees': [
                'id',
                'x_fees',
                'x_general_experience',
                'x_specific_experience',
                'x_reference_fees_categories_id',
                'x_reference_fees_subcategories_id',
            ],
        }
        return switch_opts.get(modelo, ['id', 'x_name'])

    
    def get_level_name(self, level):
        switch_opts = {
            '1': 'x_one',
            '2': 'x_two',
            '3': 'x_three',
            '4': 'x_four',
            '5': 'x_five',
            '6': 'x_six',
            'Alto': 'x_high',
            'Medio': 'x_medium',
            'Bajo': 'x_low',
        }
        return switch_opts.get(level, 'x_one')
    
    
    usage_simulations_fields = [
        'id',
        'x_area',
        'x_factor',
        'x_level',
        'x_name',
        'x_project_usages_id',
        'x_simulations_id'
    ]
    
    
    simulations_fields = [
        'id',
        'x_name',
        'x_client_name',
        'x_client_email',
        'x_client_address',
        'x_client_phone_number',
        'x_project_type',
        'x_city',
        'x_address',
        'x_latitude',
        'x_longitude',
        'create_date',
        'write_date',
        'x_complexity_factor',
        'x_complexity_level',
        'x_observations',
        'x_agglomeration_factor',
        'x_direct_cost_per_m2_construction',
        'x_factor_construction',
        'x_total_cost_construction',
        'x_cpnaa_user_id',
        'x_architectural_requirements_program',
        'x_basic_scheme_conceptual_idea',
        'x_executive_project',
        'x_brand_factor',
        'x_preliminary_project',
        'x_preliminary_studies_DTS',
        'x_project_usages_ids',
        'x_complementary_fees_ids',
        'x_construction_service_ids',
    ]
    
        
    person_fields = [
        'id',
        'x_state_ID',
        'x_user_type_ID',
        'x_cpnaa_enrollment_state',
        'x_name',
        'x_expedition_country',
        'x_expedition_state',
        'x_celphone',
        'x_gender_ID',
        'x_phone',
        'x_email',
        'x_local_phone',
        'x_address',
        'x_document',
        'x_city_ID',
        'x_country_ID',
        'x_document_type_ID',
        'x_expedition_city',
        'x_last_name',
        'x_fecha_resolucion_fallecido',
        'x_resolucion_fallecido',
        'x_fallecido'
    ]