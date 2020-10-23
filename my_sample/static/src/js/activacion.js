odoo.define('website.activacion', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
        
        const data = {
            'x_doc_type_ID': '',
            'x_document': '',
            'x_studio_universidad_5': '',
            'x_studio_carrera_1': '',
            'x_studio_fecha_de_grado_2': '',
            'x_enrollment_number': '',
            'x_studio_ciudad_de_expedicin': ''
        }
            
        const Activacion = Class.extend({ //data, _this
            habilitarBtn: function(campos_validos, id_btn){
                if (campos_validos) {
                    $('#'+id_btn).removeAttr('disabled');
                } else {
                    $('#'+id_btn).attr('disabled', 'disabled');
                }
            },
            validarCaptcha: function(elem, _this){
                grecaptcha.ready(async function() {
                    let result = await grecaptcha.getResponse();
                    if(result != ''){
                        _this.buscar_tramite(result, elem, _this);
                        elem.attr('disabled', 'disabled');
                    }else{
                        elem.removeAttr('disabled');
                        validaciones.mostrar_helper(false,'Por favor, realiza la validación');
                    }
                });
            },
            buscar_tramite: function(token, elem, _this){
                console.log(data);
                rpc.query({
                    route: '/get_profesional',
                    params: {'tipo_doc': data.tipo_doc, 'documento': data.documento, 'token': token}
                }).then(function(response){
                    _this.mostrar_resultado(response, elem, _this);
                }).catch(function(err){
                    console.log(err);
                    console.log('No se ha podido completar su solicitud');
                });
            },
            mostrar_resultado: function(response, elem, _this){
                let div_results = $('#msj_result');
                if (response.error_captcha){
                    grecaptcha.reset();
                    return;
                } else if (!response.ok){
                    div_results.removeClass('invisible').attr('aria-hidden',false);
                    let texto = `<h5><i class="fa fa-exclamation-triangle"></i> ${response.result}</h5>
                                 <h5>Por favor envie su solicitud al correo electrónico info@cpnaa.gov.co</h5>`;
                    div_results.find('#data_result').html(texto);
                } else if (response.result && response.result.length > 0){
                    $(location).attr('href','/tramites/solicitud_virtual/'+ response.result[0].id);
                }
            },
            validar_formatos: function(_this){
                data.documento = $('#doc_activacion').val().toUpperCase();
                data.tipo_doc = $('#doc_type_activacion').val();
                $('#doc_activacion').val(data.documento);
                let valido = validaciones.validar_campos_inicial(validaciones, 'doc_activacion', 'doc_type_activacion');
                _this.habilitarBtn(valido, 'btn_sol_virtual');
            },
            data_autocomplete_univ: function(cadena, tipo_universidad){
                return rpc.query({
                    route: '/get_universidades',
                    params: {'cadena': cadena, 'tipo_universidad': tipo_universidad}
                }).then(function(response){
                    console.log(response);
                    return response;
                }).catch(function(err){
                    console.log(err);
                });
            },
            data_autocomplete_carreras: function(cadena, nivel_prof, genero){
                return rpc.query({
                    route: '/get_carreras',
                    params: {'cadena': cadena, 'nivel_profesional':nivel_prof, 'id_genero':genero}
                }).then(function(response){
                    return response;
                }).catch(function(err){
                    console.log(err);
                });
            },
            validar_requeridos: function(){
                let valido = true;
                data.x_doc_type_ID = $('#x_doc_type_ID').val();
                data.x_document = $('#x_document').val();
                data.x_studio_universidad_5 = $('#x_institution_ID').val();
                data.x_studio_carrera_1 = $('#x_career_ID').val();
                data.x_studio_fecha_de_grado_2 = $('#x_grade_date').val().split('-').reverse().join('-');
                data.x_enrollment_number = $('#x_enrollment_number').val();
                data.x_studio_ciudad_de_expedicin = $('#x_expedition_city').val();
                console.log(data);
                for (const d in data) {
                    if (data[d] === ''){
                        validaciones.alert_error_toast( "Por favor responde todas las preguntas.", 'top');
                        valido = false;
                    }
                }
                
                return valido;
            },
            enviar_respuestas: function(){
                return rpc.query({
                    route: '/validar_respuestas',
                    params: { 'data': data }
                }).then(function(response){
                    console.log(response);
                    $('#enviar_respuestas').removeAttr('disabled');
                    $("#modal_questions").modal('show'); 
                    if (response.ok){
                        $('#titulo').text('SU SOLICITUD FUE EXITOSA');
                        $("#result").html(`<p>Trámite completado con exito, hemos enviado un email a 
                                ${response.data.email.toLowerCase()} con los datos de acceso a tu 
                                ${validaciones.capitalizeFromUpper(response.data.servicio)} Virtual</p>`)
                        $('#modal_footer').html(`<a class="btn btn-primary btn-lg btn-stadium" href="https://cpnaa.gov.co" target="_top">
                                                 Ir al inicio</a>`)
                    }else{
                        $('#titulo').text('SU SOLICITUD NO FUE EXITOSA');
                        $("#result").html(`<p>Por favor revisa tus respuestas</p>`)
                        $('#modal_footer').html(`<button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                data-dismiss="modal">Cerrar</button>`)                        
                    }
                }).catch(function(err){
                    $('#enviar_respuestas').removeAttr('disabled');
                    console.log(err);
                });
            },
        })
        
        const activacion = new Activacion();
        
        // Inicio del input tipo de documento
        $('#doc_type_activacion').change(function(e) {
            e.preventDefault();
            activacion.validar_formatos(activacion);
        });
        
        // Inicio del input número de documento
        $('#doc_activacion').on('input', function(e) {
            e.preventDefault();
            activacion.validar_formatos(activacion);
        });
    
        $('#btn_sol_virtual').click(function(e) {
            e.preventDefault();
            activacion.validarCaptcha($('#btn_sol_virtual'), activacion);
        });
    
        // Convertir a mayusculas y quitar espacios en blanco del campo numero de matricula
        $('#x_enrollment_number').on('change', function(e){
            let valor = $('#x_enrollment_number').val().trim().toUpperCase();
            $('#x_enrollment_number').val(valor);
        });
        
    
        // Carga las opciones para el autocomplete de las universidades
        $('#universidades_preguntas').on('keyup change input', async function(e){
            if(e.target.value.length > 1){
               let consulta = await activacion.data_autocomplete_univ(e.target.value, false);
               $('#result_univ').html('');
               $.each(consulta.universidades, function(key, value) { 
                   $('#result_univ').append('<li class="list-group-item link-univ"><span id="'+ value.id +'" class="text-gray univ">' + value.x_name + '</span></li>');
               });
            }
        })
    
        // Carga las opciones para el autocomplete de las carreras
        $('#carreras_preguntas').on('keyup change input', async function(e){
            const genero = $('#genero').val();
            if(e.target.value.length > 1){
               let consulta = await activacion.data_autocomplete_carreras(e.target.value, false, genero);
               $('#result_carreras').html('');
               $.each(consulta.carreras, function(key, value) { 
                   let carrera = genero == '1' ? value.x_name : value.x_female_name;
                   $('#result_carreras').append('<li class="list-group-item link-carreras"><span id="'+ value.id +'" class="text-gray carreras">' + carrera + '</span></li>');
               });
            }
        })
     
        // Borra el value de la carrera si cambia de nivel profesional
        $('#universidades_preguntas').on('focus', function(e){
            $('#universidades_preguntas').val('');
            $('#seleccion_univ').val('');
        });
     
        // Borra el value de la carrera si cambia de nivel profesional
        $('#carreras_preguntas').on('focus', function(e){
            $('#carreras_preguntas').val('');
            $('#seleccion_carreras').val('');
        });
    
        // Borra la lista de opciones del autocomplete de universidades
        $('#universidades_preguntas').blur(function(e){
            setTimeout(function(){
                $('#result_univ').html('');
            }, 400);
        })

        // Borra la lista de opciones del autocomplete de carreras
        $('#carreras_preguntas').blur(function(e){
            setTimeout(function(){
                $('#result_carreras').html('');
            }, 400);
        })
    
        // Asigna la selección de la lista del autocomplete al value del formulario
        $('#form_respuestas').click(function(e){
            if(e.target.classList.contains('link-univ')){
                $('#universidades_preguntas').val(e.target.firstElementChild.textContent);
                $('#seleccion_univ').val(e.target.firstElementChild.id);
                $('#result_univ').html('');
            }else if(e.target.classList.contains('univ')){
                $('#universidades_preguntas').val(e.target.textContent);
                $('#seleccion_univ').val(e.target.id);
                $('#result_univ').html('');
            }
            if(e.target.classList.contains('link-carreras')){
                $('#carreras_preguntas').val(e.target.firstElementChild.textContent);
                $('#seleccion_carreras').val(e.target.firstElementChild.id);
                $('#result_carreras').html('');
            }else if(e.target.classList.contains('carreras')){
                $('#carreras_preguntas').val(e.target.textContent);
                $('#seleccion_carreras').val(e.target.id);
                $('#result_carreras').html('');
            }
        })
    
        $('#enviar_respuestas').click(function(e){
            
            if (!activacion.validar_requeridos()){
                return;
            }else{
                $('#enviar_respuestas').attr('disabled','disabled')
                activacion.enviar_respuestas();            
            }
            
        })
    
    })