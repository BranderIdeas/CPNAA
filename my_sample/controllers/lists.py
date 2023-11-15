person_fields = [
    'id',
    # 'create_date',
    # 'x_institute_career',
    # 'x_institution_type_ID',
    # 'x_level_ID',
    'x_state_ID',
    'x_user_type_ID',
    # 'x_performances',
    # 'x_registry',
    'x_cpnaa_enrollment_state',
    'x_name',
    'x_partner_ID',
    'x_grade_date',
    'x_expedition_country',
    'x_expedition_state',
    'x_celphone',
    # 'x_linkedin',
    # 'x_foreign_state',
    'x_gender_ID',
    'x_phone',
    'x_email',
    'x_local_phone',
    # 'x_professional_experience',
    'x_address',
    'x_document',
    # 'x_folder',
    'x_city_ID',
    'x_country_ID',
    'x_document_type_ID',
    'x_professional_registration_ID',
    # 'x_certification_studies_completed',
    # 'x_min_convalidation',
    'x_expedition_city',
    'x_institution_ID',
    'x_last_name',
    # 'x_tramite',
    # 'x_certification_vigencia',
    # 'x_address_char',
    # 'x_phone_char',
    # 'x_is_working',
    # 'x_company',
    # 'x_position',
    # 'x_phone_char_2',
    # 'x_birthdate',
    # 'x_characterization',
    # 'x_email_char',
    # 'x_email_char_2',
    'x_user_image',
    # 'x_profession',
    'x_fecha_resolucion_fallecido',
    'x_resolucion_fallecido',
    'x_fallecido'
]

procedure_fields = [
    'id',
    'x_studio_universidad_5',
    'x_service_ID',
    'x_enrollment_number',
    'x_expedition_date',
    'x_studio_nivel_profesional',
    'x_studio_carrera_1'
]

institution_fields = [
    'id',
    'x_name',
    'x_state_ID',
    'x_country_ID',
]

replace_names = {
    'x_studio_universidad_5': 'x_institution_ID',
    'x_studio_nivel_profesional': 'x_professional_level_ID',
    'x_studio_carrera_1': 'x_career_ID'
}

data_select_models = [
    'x_academic_education_level',
    'x_product_type',
    'x_professional_performance_categories',
    'x_elected_positions',
    'x_usage_type',
    'x_cpnaa_country',
    'x_cpnaa_state',
    'x_professional_registry_institutions',
    'x_license_types',
    'x_license_subcategories',
    'x_license_modalities',
    'x_abilities_or_tools',
    'x_categories_of_use',
    'x_project_usages',
    'x_agglomeration',
    'x_complexity',
    'x_deliverables',
    'x_complementary_fees',
    'x_construction_service',
    'x_project_management_fee_values',
    'x_values_factor_multiplier',
    'x_general_expenses',
    'x_professional_reference_fees'
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
    'x_construction_license_register',
    'x_elected_positions_registered',
]


can_delete = [
    'x_academic_education',
    'x_scientific_academic_experience',
    'x_experience',
    'x_languages',
    'x_elected_positions_registered',
    'x_construction_license_register',
]

def normalize_fields(procedure):
    for field in procedure:
        if 'studio' in field:
            new_name = replace_names.get(field, field)
            procedure[new_name] = procedure[field]
            del procedure[field]
    return procedure