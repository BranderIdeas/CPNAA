odoo.define('website.vigencia', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
            
        const Vigencia = Class.extend({
            validar_email: function(input, _this){
                const entrada = validaciones.quitarAcentos(input.val().trim().toLowerCase().replace(/\s+/g, ' '));
                input.val(entrada);
                return validaciones.validar_email(input.val());
            },
            validar_cel_number: function(input, _this){
                const entrada = input.val().trim().replace(/\s+/g, '');
                input.val(entrada);
                return validaciones.validar_celular(input.val());
            },
            class_invalido: function(input){
                input.addClass('is-invalid');
                setTimeout(()=>{
                    input.removeClass('is-invalid');
                },1500);
            },
            verificar_certificado: function(token, data, _this){
                rpc.query({
                    route: '/verificar_certificado',
                    params: {'data': data, 'token': token}
                }).then(function(response){
                    if (response.error_captcha){
                        grecaptcha.reset();
                        return;
                    } 
                    _this.mostrar_resultado(response);
                }).catch(function(e){
                    console.log('No se ha podido completar su solicitud');
                });
            },
            verificar_autenticidad: function(token, data, _this){
                rpc.query({
                    route: '/verificar_autenticidad',
                    params: {'data': data, 'token': token}
                }).then(function(response){
                    if (response.error_captcha){
                        grecaptcha.reset();
                        return;
                    }
                    if(response.ok){
                        $('#msj_result').removeClass('invisible').attr('aria-hidden',false);
                        $('#msj_result').find('div').removeClass('alert-danger').addClass('alert alert-info')
                            .html('<i class="fa fa-check""></i>'+' '+response.mensaje);
                        $('#results_table').removeClass('invisible').attr('aria-hidden', false);
                        _this.insertarDatos(response);
                    }else{
                        let msj = '<i class="fa fa-exclamation-triangle""></i> '+response.mensaje+'<br/>Por favor comuníquese con el CPNAA';
                        if(response.error_catpcha) {  msj = response.mensaje }
                        $('#msj_result').removeClass('invisible').attr('aria-hidden',false);
                        $('#msj_result').find('div').removeClass('alert-info').addClass('alert alert-danger')
                            .html(msj);
                        $('#results_table').addClass('invisible').attr('aria-hidden', true);
                    }
                }).catch(function(e){
                    console.log('No se ha podido completar su solicitud', e);
                    $('#msj_result').removeClass('invisible').attr('aria-hidden',false);
                    $('#msj_result').find('div').addClass('alert alert-danger').html('No se ha podido completar su solicitud');
                    $('#results_table').addClass('invisible').attr('aria-hidden', true);
                });
            },
            insertarDatos: function(data){
                $('#numero_cert').text(data.certificado.x_consecutivo);
                $('#fecha_expedicion').text(validaciones.dateTimeToString(data.certificado.create_date));
                $('#tipo_documento_prof').text(data.profesional[0].x_studio_tipo_de_documento_1[1]);
                $('#documento_prof').text(data.profesional[0].x_studio_documento_1);
                $('#nombres_prof').text(data.profesional[0].x_studio_nombres+' '+data.profesional[0].x_studio_apellidos);
                $('#fecha_vencimiento').text(validaciones.dateTimeToString(data.certificado.expiration_date));
                $("html, body").animate({
                    scrollTop: $('#btn_vigencia_auth').offset().top
                }, 800);
            },
            generar_certificado: function(email, _this){
                rpc.query({
                    route: '/enviar_certificado_vigencia',
                    params: {'email': email, 'id_tramite': $('#id_tramite').val()}
                }).then(function(response){
                    ocultarSpinner();
                    if(response.ok){
                        $('#pdfFrameVigencia').attr('src', `data:application/pdf;base64,${response.cert.pdf}`);
                        _this.downloadPDF();
                        $('#mssg_result').addClass('alert alert-info').text(response.mensaje);
                        setTimeout(()=>{
                            window.top.location.href = 'https://cpnaa.gov.co/';
                        },5000)
                    }else{
                        $('#mssg_result').addClass('alert alert-danger').text(response.mensaje);
                        $('#btn_generar_certificado').removeAttr('disabled');
                    }
                }).catch(function(e){
                    console.log('No se ha podido completar su solicitud', e);
                    ocultarSpinner();
                    $('#mssg_result').addClass('alert alert-danger').text('No se ha podido completar su solicitud');
                });
            },
            generar_certificado_exterior: function(data, _this){
                rpc.query({
                    route: '/generar_certificado_exterior',
                    params: {'email': data.email, 'celular': data.celular, 'id_tramite': $('#id_tramite').val()}
                }).then(function(response){
                    ocultarSpinner();
                    if(response.ok){
                        $('#mssg_result').addClass('alert alert-info').text(response.mensaje);
                        setTimeout(()=>{
                            window.top.location.href = 'https://cpnaa.gov.co/';
                        },10000)
                    }else{
                        $('#mssg_result').addClass('alert alert-danger').text(response.mensaje);
                        $('#btn_generar_certificado').removeAttr('disabled');
                    }
                }).catch(function(e){
                    console.log('No se ha podido completar su solicitud', e);
                    ocultarSpinner();
                    $('#mssg_result').addClass('alert alert-danger').text('No se ha podido completar su solicitud');
                });
            },
            habilitarBtn: function(campos_validos, id_button){
                if (campos_validos) {
                    $('#'+id_button).removeAttr('disabled');
                } else {
                    $('#'+id_button).attr('disabled', 'disabled');
                }
            },
            mostrar_resultado: function(response){
                const route_tramite = location.pathname === '/tramites/certificado_de_vigencia' 
                                    ? 'certificado_de_vigencia'
                                    : 'certificado_vigencia_exterior';
                let div_msj = $('#msj_result');
                    if (!response.ok){
                        div_msj.removeClass('invisible').attr('aria-hidden',false);
                        div_msj.find('div').text(response.mensaje);
                    } else if (response.tramites.length == 1){
                        $(location).attr('href',`/tramites/${route_tramite}/${response.tramites[0].id}`);
                    } else if (response.tramites.length > 1){
                        div_msj.removeClass('invisible').attr('aria-hidden',false);
                        div_msj.find('div').removeClass('alert-primary').addClass('alert-info');
                        let texto = '<h5 class="text-center">Se han encontrado varias coincidencias, por favor selecciona</h5>';
                        response.tramites.forEach((tram)=>{
                            let mensaje = 'Seleccione para generar certificado';
                            let enlace = `href="/tramites/${route_tramite}/${tram.id}"`;
                            texto += `<a class="card card-link fw700" ${enlace}>
                                        <div class="card-header results-vigencia">
                                            PROFESIÓN: ${tram.x_studio_carrera_1[1]}
                                            <h5>${mensaje}</h5>
                                        </div>
                                        </a></br>`;
                        })
                        div_msj.find('div').html(texto);
                    }
            },
            downloadPDF: function() {
                const linkSource = $('#pdfFrameVigencia').attr('src');
                const downloadLink = document.createElement("a");
                const fileName = "certificado_de_vigencia.pdf";
                downloadLink.href = linkSource;
                downloadLink.download = fileName;
                downloadLink.click();
            },
            validar_input_codigo: function(valido){
                if($('#x_code_vigencia').val().length > 0){
                    vigencia.habilitarBtn(valido, 'btn_vigencia_auth');
                    validaciones.ocultar_helper('x_code_vigencia');
                } else {
                    vigencia.habilitarBtn(false, 'btn_vigencia_auth');
                    validaciones.mostrar_helper_inicio('x_code_vigencia','El código único de seguridad es requerido');
                }
            },
            enviar_form_inicio: function(){
                let data = {
                    tipo_doc: $('#x_document_type').val(),
                    documento: $('#x_document').val()
                }
                grecaptcha.ready(async function() {
                    let result = await grecaptcha.getResponse();
                    if(result != ''){
                        vigencia.verificar_certificado(result, data, vigencia);
                        $(this).attr('disabled', 'disabled');
                        validaciones.ocultar_helper(false);
                    }else{
                        $(this).removeAttr('disabled');
                        validaciones.mostrar_helper_inicio(false,'Por favor, realiza la validación');
                    }
                });
            }
        })
        
        const vigencia = new Vigencia();
        
        // Muestra los resultados para el cert de vigencia si no hay coincidencias o si existen varias
        // Si solo hay una coincidencia lo dirige al formulario de generar certificado
        $('#inicio_vigencia').submit(function(e){
            e.preventDefault();
            vigencia.enviar_form_inicio();
        });
        
        // Validar formatos de datos
        $('#x_document').on('keyup change input', function(){
            let valido = validaciones.validar_campos_inicial(validaciones, 'x_document', 'x_document_type');
            vigencia.habilitarBtn(valido, 'btn_enviar_exterior');
            vigencia.habilitarBtn(valido, 'btn_enviar_vigencia');
            if($('#btn_vigencia_auth').length > 0){
                vigencia.validar_input_codigo(valido);
            }
        });
        
        // Validar formatos de datos
        $('#x_document_type').change(function(){
            let valido = validaciones.validar_campos_inicial(validaciones, 'x_document', 'x_document_type');
            vigencia.habilitarBtn(valido, 'btn_enviar_exterior');
            vigencia.habilitarBtn(valido, 'btn_enviar_vigencia');
            if($('#btn_vigencia_auth').length > 0){
                vigencia.validar_input_codigo(valido);
            }
        });
        
        // Valida si la dirección de email tiene el formato correcto
        $('#email_vigencia').change(() => vigencia.validar_email($('#email_vigencia'), vigencia));
        
        // Valida si la dirección de email tiene el formato correcto
        $('#celular_vigencia').change(() => vigencia.validar_cel_number($('#celular_vigencia'), vigencia));
        
        // Realiza la petición del certificado de vigencia al email y genera la descarga del pdf en el navegador
        $('#btn_generar_certificado').click(()=>{
            const input_email   = $('#email_vigencia');
            const input_celular = $('#celular_vigencia');
            if(input_celular.val().trim().length < 1){
                vigencia.class_invalido(input_celular);
                validaciones.mostrar_alerta_vacio('celular de contacto');
                return; 
            }else if(input_email.val().trim().length < 1){
                vigencia.class_invalido(input_email);
                validaciones.mostrar_alerta_vacio('correo electrónico');
                return;
            } 
            const valido = vigencia.validar_cel_number(input_celular, vigencia) && vigencia.validar_email(input_email, vigencia);
            if(valido){
                location.pathname.indexOf('/tramites/certificado_de_vigencia') !== -1
                        ? vigencia.generar_certificado(input_email.val(), vigencia)
                        : vigencia.generar_certificado_exterior({email: input_email.val(), celular: input_celular.val()}, vigencia);
                mostrarSpinner();
            }
        })
        
        // Validar formatos de datos validacion de autenticidad
        $('#x_code_vigencia').on('keyup change input', function(){
            let valido = validaciones.validar_campos_inicial(validaciones, 'x_document', 'x_document_type');
            if(valido){
                vigencia.validar_input_codigo(valido);
            }
        });
        
        
        
        // Realiza la petición para validar el certificado por medio del codigo de seguridad
        $('#autenticidad_vigencia').submit((e)=>{
            e.preventDefault();
            let data = {
                tipo_doc: $('#x_document_type').val(),
                documento: $('#x_document').val(),
                x_code: $('#x_code_vigencia').val()
            }
            grecaptcha.ready(async function() {
                let result = await grecaptcha.getResponse();
                if(result != ''){
                    vigencia.verificar_autenticidad(result, data, vigencia);
                    $(this).attr('disabled', 'disabled');
                    validaciones.ocultar_helper(false);
                }else{
                    $(this).removeAttr('disabled');
                    validaciones.mostrar_helper_inicio(false,'Por favor, realiza la validación');
                }
            });
        })
        
        // Realiza la petición del certificado de vigencia al email y genera la descarga del pdf en el navegador
        $('#btn_validar_vigencia').click(()=>{
            let el = $('#email_vigencia');
            if(el.val().length < 1){
                vigencia.class_invalido(el);
                validaciones.mostrar_alerta_vacio('correo electrónico');
            }
            let valido = vigencia.validar_email(el, vigencia);
            if(!el.hasClass('invalido')){
                vigencia.generar_certificado(el.val(), vigencia);
                mostrarSpinner();
            }else{
                vigencia.class_invalido(el);
            }
        })
        
        function mostrarSpinner(){
            $('#div_spinner_vig').attr('aria-hidden', false).removeClass('invisible');
            $('#div_results_vig').attr('aria-hidden', true).addClass('invisible');
            $('#btn_generar_certificado').attr('disabled','disabled');
        }
        
        function ocultarSpinner(){
            $('#div_results_vig').attr('aria-hidden', false).removeClass('invisible');
            $('#div_spinner_vig').attr('aria-hidden', true).addClass('invisible');
        }
        
    })