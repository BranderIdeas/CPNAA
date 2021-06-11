odoo.define('website.correccion', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
    
        const data = {
            'tipo_doc': '',
            'documento': ''
        }
        let formData = new FormData();
        
        const Correccion = Class.extend({ //data, _this
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
                    route: '/get_correccion',
                    params: {'tipo_doc': data.tipo_doc, 'documento': data.documento, 'token': token}
                }).then(function(response){
                    console.log(response);
                    _this.mostrar_resultado(response, elem, _this);
                }).catch(function(err){
                    console.log(err);
                    console.log('No se ha podido completar su solicitud');
                });
            },
            validar_formatos: function(_this){
                data.documento = $('#doc_correccion').val().toUpperCase();
                data.tipo_doc = $('#doc_type_correccion').val();
                $('#doc_correccion').val(data.documento);
                let valido = validaciones.validar_campos_inicial(validaciones, 'doc_correccion', 'doc_type_correccion');
                _this.habilitarBtn(valido, 'btn_correccion');
            },
            mostrar_resultado: function(response, elem, _this){
                let div_results = $('#msj_result');
                let texto = '';
                if (response.error_captcha){
                    grecaptcha.reset();
                    return;
                } else if (!response.ok){
                    div_results.removeClass('invisible').attr('aria-hidden',false);
                    texto = `<h5><i class="fa fa-exclamation-triangle"></i> ${response.result}</h5>
                             <h5>Por favor envie su solicitud al correo electrónico info@cpnaa.gov.co</h5>`;
                    div_results.find('#data_result').html(texto);
                } else if (response.result && response.result.length == 1){
                    if(response.result[0].solicitud_en_curso){
                        div_results.removeClass('invisible').attr('aria-hidden',false);
                        if(response.result[0].tiene_rechazo){
                            texto = `<h5><i class="fa fa-info-circle"></i> 
                                         ${response.result[0].x_studio_nombres} ${response.result[0].x_studio_apellidos} <br/>
                                         Profesión: ${response.result[0].x_studio_carrera_1[1]} <br/>
                                         Su solicitud ${response.result[0].nombre_solicitud} fue devuelta, 
                                         <a href="/tramites/editar/solicitud_correccion/${response.result[0].id}">
                                         click aquí </a> para continuar con su trámite <br/>
                                        * Recuerde cargar nuevamente todos los archivos que le solicita el formulario para completar su trámite
                                    </h5>`;
                        }else{
                            texto = `<h5><i class="fa fa-info-circle"></i> 
                                         ${response.result[0].x_studio_nombres} ${response.result[0].x_studio_apellidos} <br/>
                                         Profesión: ${response.result[0].x_studio_carrera_1[1]} <br/>
                                         Su solicitud ${response.result[0].nombre_solicitud} está en proceso, la respuesta la recibiras por
                                        correo electrónico
                                     </h5>`;
                        }
                        div_results.find('#data_result').html(texto);
                    }else{
                        $(location).attr('href','/tramites/solicitud_correccion/'+ response.result[0].id);
                    }
                } else if (response.result && response.result.length > 1){    
                    response.result.forEach((res) => {
                        if(res.solicitud_en_curso){
                            if(res.tiene_rechazo){
                                texto += `<h5><i class="fa fa-info-circle"></i> 
                                             ${res.x_studio_nombres} ${res.x_studio_apellidos} <br/>
                                             Profesión: ${res.x_studio_carrera_1[1]}
                                             Su solicitud ${res.nombre_solicitud} fue devuelta, 
                                             <a href="/tramites/editar/solicitud_correccion/${res.id}">
                                             click aquí </a> para continuar con su trámite <br/>
                                            * Recuerde cargar nuevamente todos los archivos que le solicita el formulario para completar su trámite
                                        </h5>`;
                            }else{
                                texto += `<h5><i class="fa fa-info-circle"></i> 
                                             ${res.x_studio_nombres} ${res.x_studio_apellidos} <br/>
                                             Profesión: ${res.x_studio_carrera_1[1]} <br/>
                                             Su solicitud ${res.nombre_solicitud} está en proceso, la respuesta la recibiras por
                                             correo electrónico
                                         </h5>`;
                            }
                        }else{
                                texto += `<h5>
                                             ${res.x_studio_nombres} ${response.result[0].x_studio_apellidos} <br/>
                                             Profesión: ${res.x_studio_carrera_1[1]} <br/>
                                                Para iniciar una solicitud, 
                                             <a href="/tramites/solicitud_correccion/${res.id}">
                                             click aquí </a> <br/>
                                        </h5>`;
                        }
                    })
                    div_results.removeClass('invisible').attr('aria-hidden',false);
                    div_results.find('#data_result').html(texto);
                }
            },
            validar_form: async function(){
                let formSample = document.forms[0];
                let elems = formSample.elements;
                let valido = await validaciones.validar_formulario(validaciones);
                if (!valido){
                    $('#mssg_result_correccion').addClass('alert alert-danger')
                        .text(`Por favor, verifica la información ingresada.`);
                } else {
                    $('#mssg_result_correccion').removeClass('alert alert-danger').text('');
                    for(let el of elems){
                        if(el.name != ''){
                            if(el.type === 'file'){
                                formData.append(el.name, el.files[0]);
                            }else{
                                formData.append(el.name, el.value);   
                            }   
                        }
                    }
                }
                return valido;
            },
            enviar_form: function(){
                try {
                    const request = new XMLHttpRequest();
                    if($('[name=id_solicitud]').length > 0){
                        request.open("POST", "/update_solicitud_correccion");     
                    }else{
                        request.open("POST", "/registrar_solicitud_correccion"); 
                    }
                    request.send(formData);
                    request.onreadystatechange = function (aEvt) {
                        if (request.readyState == 4) {
                            if(request.status == 200){
                                let resp = JSON.parse(request.responseText);
                                console.log(resp);
                                if(resp.ok){
                                    ocultarSpinner();
                                    $('#mssg_result_correccion').addClass('alert alert-info').text(resp.message);
                                    setTimeout(()=>{ 
                                        window.top.location.href = 'https://cpnaa.gov.co/';
                                    },1600);
                                }else{
                                    ocultarSpinner();
                                    $('#mssg_result_correccion').addClass('alert alert-danger').text('Error: '+resp.message.slice(0,80));
                                    $('#btn_enviar_correccion').removeAttr('disabled');
                                }
                             } else {
                                ocultarSpinner();
                                console.log('ERROR: '+request.status + request.statusText);
                                $('#mssg_result_correccion').addClass('alert alert-danger')
                                    .text('No hemos podido completar la solicitud en este momento');
                                $('#btn_enviar_correccion').removeAttr('disabled');
                             }
                        }
                    }
                } catch (err){
                    ocultarSpinner();
                    $('#mssg_result_correccion').addClass('alert alert-danger')
                        .text('Error: No se pudo guardar el registro, intente de nuevo al recargar la página');
                    $('#btn_enviar_correccion').removeAttr('disabled');
                    console.warn(err);
                }
            },
        })
        
        const correccion = new Correccion();
        
        // Inicio del input tipo de documento
        $('#doc_type_correccion').change(function(e) {
            e.preventDefault();
            correccion.validar_formatos(correccion);
        });
        
        // Inicio del input número de documento
        $('#doc_correccion').on('input', function(e) {
            e.preventDefault();
            correccion.validar_formatos(correccion);
        });
    
        $('#btn_correccion').click(function(e) {
            e.preventDefault();
            correccion.validarCaptcha($('#btn_correccion'), correccion);
        });
    
        // Colocar obligatorio el campo observaciones si selecciona otro
        $("select[name='x_issue']").change((e) => {
            switch ($("select[name='x_issue'] option:selected").data('classification')) {
              case 'PERSONAL':
                $('#label_soporte').text('Escritura Pública');
                $('#x_support_document').attr('name','x_public_write');
                mostrarDocumentoSoporte('x_public_write');
                break;
              case 'ACADEMICO':
                $('#label_soporte').text('Diploma');
                $('#x_support_document').attr('name','x_diploma');
                mostrarDocumentoSoporte('x_diploma');
                break;
              case 'DATOS PERSONALES':
                ocultarDocumentoSoporte();
                break;
              default:
                $('#label_soporte').text('Documento Soporte');
                $('#x_support_document').attr('name','x_support_document');
                mostrarDocumentoSoporte('x_support_document');
            }
        }).change();
    
        // Muestra/Oculta las ciudades depende del departamento seleccionado
        $("select[name='x_actual_state']").change((e) => {
            let $select = $("select[name='x_actual_city']");
            $select.find("option:not(:first)").hide();
            $select.find("option[data-state_id="+($("select[name='x_actual_state']").val() || 0)+"]").show();
            $select.val("");
        })
    
        function ocultarDocumentoSoporte(){
            $('#label_soporte').hide();
            $('label[for="x_support_document"]').hide();
            $('label[for="x_support_document"]').next().hide();
            $('#x_support_document').removeAttr('name').hide();
        }
    
        function mostrarDocumentoSoporte(name){
            $('#label_soporte').show();
            $('label[for="x_support_document"]').show();
            $('label[for="x_support_document"]').next().show();
            $('#x_support_document').attr('name', name).show();
        }
    
        $('#form_correccion').submit(async function(e) {
            e.preventDefault();
            const formValido = await correccion.validar_form();
            if (!formValido){
                return;
            }else{
                $('#btn_enviar_correccion').attr('disabled','disabled')
                mostrarSpinner();
                correccion.enviar_form();           
            }
        })
    
        function mostrarSpinner(){
            $('#div_spinner_correccion').attr('aria-hidden', false).removeClass('invisible');
            $('#div_results_correccion').attr('aria-hidden', true).addClass('invisible');
        }

        function ocultarSpinner(){
            $('#div_results_correccion').attr('aria-hidden', false).removeClass('invisible');
            $('#div_spinner_correccion').attr('aria-hidden', true).addClass('invisible');
        }

    
    })