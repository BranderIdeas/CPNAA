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
                    route: '/get_profesional',
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
                if (response.error_captcha){
                    grecaptcha.reset();
                    return;
                } else if (!response.ok){
                    div_results.removeClass('invisible').attr('aria-hidden',false);
                    let texto = `<h5><i class="fa fa-exclamation-triangle"></i> ${response.result}</h5>
                                 <h5>Por favor envie su solicitud al correo electrónico info@cpnaa.gov.co</h5>`;
                    div_results.find('#data_result').html(texto);
                } else if (response.result && response.result.length > 0){
                    $(location).attr('href','/tramites/solicitud_correccion/'+ response.result[0].id);
                }
            },
            validar_form: function(){
                let valido = true;
                let formSample = document.forms[0];
                let elems = formSample.elements;
                for (let i = 0; i < elems.length; i++) {
                    if(elems[i].name != ''){
                        if(elems[i].type === 'file'){
                            if(elems[i].classList.contains('i_required') && !elems[i].files[0]){
                                valido = false;
                                $('[for="' + elems[i].id + '"]').addClass('is-invalid');
                            }else{
                                formData.append(elems[i].name, elems[i].files[0]);
                                $('[for="' + elems[i].id + '"]').removeClass('is-invalid');
                            }
                        } else {
                            if(elems[i].classList.contains('i_required') && elems[i].value == ''){
                                valido = false;
                                elems[i].classList.add('is-invalid');
                            }else{
                                formData.append(elems[i].name, elems[i].value);
                                elems[i].classList.remove('is-invalid');
                            }
                        } 
                    }

                }
                if (!valido){
                    $('#mssg_result_correccion').addClass('alert alert-danger')
                        .text(`Por favor, verifica los campos requeridos *.`);
                } else {
                    $('#mssg_result_correccion').removeClass('alert alert-danger').text('');
                }
                return valido;
            },
            enviar_form: function(){
                try {
                    const request = new XMLHttpRequest();
                    request.open("POST", "/registrar_solicitud_correccion");
                    request.send(formData);
                    request.onreadystatechange = function (aEvt) {
                        if (request.readyState == 4) {
                            if(request.status == 200){
                                let resp = JSON.parse(request.responseText);
                                console.log(resp);
                                if(resp.ok){
                                    ocultarSpinner();
                                    $('#mssg_result_correccion').addClass('alert alert-info').text(resp.message);
//                                     setTimeout(()=>{ 
//                                         window.top.location.href = 'https://www.cpnaa.gov.co/';
//                                     },1200);
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
            if ($("select[name='x_issue'] option:selected").val() === '8') {
                $('#row_observaciones').addClass('o_website_form_required');
                $('input[name="x_observation"]').addClass('i_required');
            }else{
                $('#row_observaciones').removeClass('o_website_form_required');
                $('input[name="x_observation"]').removeClass('i_required');
            }
            switch ($("select[name='x_issue'] option:selected").data('classification')) {
              case 'PERSONAL':
                $('#label_soporte').text('Escritura Pública');
                $('#x_support_document').attr('name','x_public_write');
                break;
              case 'ACADEMICO':
                $('#label_soporte').text('Diploma');
                $('#x_support_document').attr('name','x_diploma');
                break;
              default:
                $('#label_soporte').text('Documento Soporte');
                $('#x_support_document').attr('name','x_support_document');
            }
        });
    
        $('#form_correccion').submit(function(e) {
            e.preventDefault();
            if (!correccion.validar_form()){
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