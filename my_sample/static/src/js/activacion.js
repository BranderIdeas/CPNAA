odoo.define('website.activacion', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
        
        const MAX_YEAR = new Date().getFullYear();
        const MIN_YEAR = 1929;
        const data = {
            'x_doc_type_ID': '',
            'x_document': '',
            'x_studio_universidad_5': '',
            'x_studio_carrera_1': '',
            'x_studio_fecha_de_grado_2': '',
            'x_enrollment_number': '',
            'x_studio_ciudad_de_expedicin': ''
        }
        const data_confirmacion = {
            'id_tramite': 0,
            'id_usuario': 0,
            'x_request_email': '',
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
                }  else if (!response.ok){
                    div_results.removeClass('invisible').attr('aria-hidden',false);
                    let texto = `<h5><i class="fa fa-exclamation-triangle"></i> ${response.result}</h5>
                                 <h5>Por favor envie su solicitud al correo electrónico info@cpnaa.gov.co</h5>`;
                    div_results.find('#data_result').html(texto);
                    $('#msj_result').find('#data_result').removeClass('alert-info').addClass('alert-primary');
                } else if (response.result && response.data_user.fallecido){
                    const nombre_tramite = response.data_user.matricula ? 'Matrícula Profesional' : 'Certificado de Incripción Profesional';
                    const cancel = response.data_user.matricula ? 'Cancelada' : 'Cancelado';
                        const html_msj =
                            response.result.resolucion_fallecido &&
                            response.result.fecha_resolucion_fallecido
                                ? `<i class="fa fa-info-circle"></i>
                          El documento ${validaciones.capitalizeFromUpper(
                              response.data_user.tipo_documento
                          )}: 
                          ${response.data_user.documento} se encuentra registrado como: 
                          ${validaciones.capitalizeFromUpper(
                              response.data_user.carrera
                          )} y su ${nombre_tramite} 
                          tiene el Estado: ${cancel} por muerte, de acuerdo con la información de la Registraduría Nacional del Estado Civil,
                          Resolución: ${response.result.resolucion_fallecido}. Fecha Resolución: ${
                                      response.result.fecha_resolucion_fallecido
                                  }.`
                                : `<i class="fa fa-info-circle"></i>
                          El documento ${validaciones.capitalizeFromUpper(
                              response.data_user.tipo_documento
                          )}: 
                          ${response.data_user.documento} se encuentra registrado como: 
                          ${validaciones.capitalizeFromUpper(
                              response.data_user.carrera
                          )} y su ${nombre_tramite} 
                          tiene el Estado: ${cancel} por muerte, de acuerdo con la información de la Registraduría Nacional del Estado Civil.`;
                    $('#data_result').html(html_msj);
                    $('#msj_result').removeClass('invisible').attr('aria-hidden',false);
                    $('#msj_result').find('#data_result').removeClass('alert-primary').addClass('alert-info');
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
                const form = document.forms[0];
                for (const input of form.elements) {
                    const {name, value, type} = input;
                    if(name){
                        const validationValues = validationData[name];
                        if(isInvalid(value, validationValues.type_validator)){
                            $(`#${validationValues.id_input}`).addClass("is-invalid");
                            valido = false;
                        }else{
                            $(`#${validationValues.id_input}`).removeClass("is-invalid");
                        }
                        data[name] = value;
                    }
                }
                if(!valido){
                    validaciones.alert_error_toast(
                        "Por favor, verifica en el formulario los campos no válidos y/o requeridos *",
                        "top"
                    );
                }
                return valido;
            },
            enviar_respuestas: function(){
                return rpc.query({
                    route: '/validar_respuestas',
                    params: { 'data': data }
                }).then(function(response){
                    $('#enviar_respuestas').removeAttr('disabled');
                    $("#modal_questions").modal('show'); 
                    if (response.ok){
                        $('#titulo').text('SU SOLICITUD FUE EXITOSA');
                        $("#result").html(`<p>Trámite completado con exito, hemos enviado un email a 
                                ${response.data.email.toLowerCase()} con los datos de acceso a su 
                                ${validaciones.capitalizeFromUpper(response.data.servicio)} Virtual</p>`)
                        $('#modal_footer').html(`<a class="btn btn-primary btn-lg btn-stadium" href="https://cpnaa.gov.co" target="_top">
                                                 Ir al inicio</a>`)
                    }else{
                        if(response.email_existe && response.id_usuario){
                            $('#titulo').text('NO HEMOS PODIDO COMPLETAR SU SOLICITUD');
                            $("#result").html(`<p>${response.message}</p>`)
                            $('#modal_footer').html(`<button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                        id="confirmar_email">Si</button>
                                                    <button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                        data-dismiss="modal">No</button>`);
                            data_confirmacion.id_tramite = response.id_tramite;
                            data_confirmacion.id_usuario =  response.id_usuario;
                            data_confirmacion.x_request_email = response.email;
                            $('#confirmar_email').click(function(e) {
                                e.preventDefault();
                                activacion.confirmar_email();
                            });
                        }else if(response.email_existe){
                            $('#titulo').text('NO HEMOS PODIDO COMPLETAR SU SOLICITUD');
                            $("#result").html(`<p>${response.message}</p>`)
                            $('#modal_footer').html(`<button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                    data-dismiss="modal">Cerrar</button>`)   
                        }else{
                            $('#titulo').text('NO HEMOS PODIDO VERIFICAR SUS RESPUESTAS');
                            $("#result").html(`<p>Por favor, verifique sus respuestas</p>`)
                            $('#modal_footer').html(`<button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                    data-dismiss="modal">Cerrar</button>`)  
                        }
                    }
                }).catch(function(err){
                    $('#enviar_respuestas').removeAttr('disabled');
                    console.log(err);
                });
            },
            confirmar_email: function(){
                $("#modal_questions").modal('hide');
                return rpc.query({
                    route: '/confirmar_email',
                    params: { 'data': data_confirmacion }
                }).then(function(response){
                    $("#modal_questions").modal('show');
                    if (response.ok){
                        $('#titulo').text('SU SOLICITUD FUE EXITOSA');
                        $("#result").html(`<p>Trámite completado con exito, hemos enviado un email a 
                                ${response.data.email.toLowerCase()} con los datos de acceso a su 
                                ${validaciones.capitalizeFromUpper(response.data.servicio)} Virtual</p>`)
                        $('#modal_footer').html(`<a class="btn btn-primary btn-lg btn-stadium" href="https://cpnaa.gov.co" target="_top">
                                                 Ir al inicio</a>`);
                    } else {
                        $('#titulo').text('NO HEMOS PODIDO COMPLETAR SU SOLICITUD');
                        $("#result").html(`<p>${response.message}</p>`)
                        $('#modal_footer').html(`<button type="button" class="btn btn-primary btn-lg btn-stadium" 
                                                data-dismiss="modal">Cerrar</button>`)
                    }
                })
            }
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
                    $("#result_carreras").append(`
                        <li class="list-group-item link-carreras">
                            <span id="${value.id}"class="text-gray carreras">${value.x_name}</span>
                        </li>`
                    );
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
    
        $(".yearpicker").yearpicker({
          year: MAX_YEAR,
          startYear: MIN_YEAR,
          endYear: MAX_YEAR
        });
    
        $('#x_studio_fecha_de_grado_2').on('keyup change', function (e) {
          const regex = /^[0-9]*$/;
          const elem = e.target;
          if (!regex.test(elem.value)) {
            elem.value = elem.value.trim().replace(/[^\d]/g, '');
          }
          if (elem.value.length == 4){
            if(!isValidYear(elem.value)){
              validaciones.alert_error_toast(`${elem.value} no es un valor válido, ingrese un valor entre ${MIN_YEAR}-${MAX_YEAR}`, 'top');
              elem.classList.add('is-invalid');
            } else {
              elem.classList.remove('is-invalid');
            }
          }
        })
    
        $('#x_request_email').on('change', function (e) {
            const elem = e.target;
            const valor = elem.value.trim().toLowerCase().replace(/\s+/g, '');
            const valid = validaciones.validar_email(valor);
            if(!valid){
                elem.classList.add('is-invalid');
                return valid;
            } else {
                elem.classList.remove('is-invalid');
                elem.value = valor;
            }
        })
    
        const isValidYear =  (value) => (Number(value) > MAX_YEAR || Number(value) < MIN_YEAR) ? false : true;
    
        const validationData = {
            genero: {
                id_input: "genero",
                type_validator: false,
            },
            x_doc_type_ID: {
                id_input: "x_doc_type_ID",
                type_validator: "required",
            },
            x_document: {
                id_input: "x_document",
                type_validator: "required",
            },
            x_studio_universidad_5: {
                id_input: "universidades_preguntas",
                type_validator: "required",
            },
            x_studio_carrera_1: {
                id_input: "carreras_preguntas",
                type_validator: "required",
            },
            x_studio_fecha_de_grado_2: {
                id_input: "x_studio_fecha_de_grado_2",
                type_validator: "required",
            },
            x_enrollment_number: {
                id_input: "x_enrollment_number",
                type_validator: "required",
            },
            x_studio_ciudad_de_expedicin: {
                id_input: "x_studio_ciudad_de_expedicin",
                type_validator: "required",
            },
            x_request_email: {
                id_input: "x_request_email",
                type_validator: "email",
            },
        };

        function isInvalid(value, type){
            switch (type) {
                case false:
                    return false;
                case "email":
                    return !validaciones.validar_email(value) || value === '';
                case "required":
                    return value === '';
                default:
                    console.log({value, type});
                    return true;
            }
        }

    })