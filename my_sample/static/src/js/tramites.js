odoo.define('website.tramites', function(require) {
'use strict';
    
    console.log('TRAMITES')
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    const Validaciones = require('website.validations');
    const validaciones = new Validaciones();
    
    let tramite = $('#tramite').attr('data-tramite');
    let data = {
        doc: '',
        doc_type: '',
        nombres: '',
        apellidos: '',
        origen: tramite
    }
        
    const Tramites = Class.extend({
        validar_tramites: function() {
            let origen = data.origen;
            (!origen) ? origen = '' : origen = `/${data.origen}`;
            return rpc.query({
                route: '/validar_tramites',
                params: {'data': data}
            }).then(function(response){
                if(response.convenio){
                    $(location).attr('href','/tramite/convenios/'+ response.id);
                } else if(response.id){
                    if (response.matricula){
                        $('#msj_matricula').removeClass('invisible').attr('aria-hidden',false);
                    } else {
                        $(location).attr('href','/cliente/'+ response.id +'/tramites');
                    }
                }
                else {
                    $(location).attr('href','/tramite' + origen+'/['+data.doc_type+':'+data.doc+']');
                }
            })
        },
        validar_convenios: function() {
            let div_msj = $('#msj_nombre');
            if($('#x_names').val() == ''){
                div_msj = $('#msj_documento');
            }
            div_msj.find('div').text('');
            div_msj.addClass('invisible').attr('aria-hidden',true);
            return rpc.query({
                route: '/validar_estudiante',
                params: {'data': data}
            }).then(function(response){
                if (!response.graduandos){
                    div_msj.removeClass('invisible').attr('aria-hidden',false);
                    div_msj.find('div').text(
                        `Usted no se encuentra registrado por Convenio, si ya intentó la búsqueda por documento 
                         y nombre por favor comuníquese con la universidad ó con el CPNAA al siguiente correo 
                         electrónico: convenios@cpnaa.gov.co o al número telefónico (1)3502700 ext 111-115 en Bogotá`);
                } else if (response.graduandos.length == 1){
                    if (response.graduandos[0].id_user_tramite){
                        $(location).attr('href','/cliente/'+ response.graduandos[0].id_user_tramite +'/tramites');
                    } else if(!response.graduandos[0].id_grado){
                        let fecha = response.graduandos[0].fecha_maxima.split('-').reverse().join('-');
                        div_msj.removeClass('invisible').attr('aria-hidden',false);
                        div_msj.find('div').text(
                            `Usted ya no puede ingresar por esta opción, la fecha maxima para pagar el trámite por convenio era hasta el ${fecha}`);
                    } else if (response.graduandos[0].id_grado){
                        $(location).attr('href','/tramite/convenios/'+ response.graduandos[0].graduando.id);
                    }
                } else if (response.graduandos.length > 1){
                    div_msj.removeClass('invisible').attr('aria-hidden',false);
                    let texto = '';
                    response.graduandos.forEach((grad)=>{
                        texto += `GRADUANDO: </br>
                                  ${grad.graduando.x_tipo_documento_select[1]}: ${grad.graduando.x_documento} </br> 
                                  ${grad.graduando.x_nombres} ${grad.graduando.x_apellidos} </br> 
                                  ${grad.graduando.x_service_ID[1]} </br>
                                  ${grad.graduando.x_universidad} </br></br>`;
                    })
                    div_msj.find('div').html(texto);
                }
            })
        },
        mostrar_helper: function(campo, msg){
            $('#'+campo).addClass('invalido');
            $('#help_text').removeClass('invisible').text(msg);
            setTimeout(()=>{ 
                $('#'+campo).removeClass('invalido');
                $('#help_text').addClass('invisible');
            },1500);
        },
        data_autocomplete_univ: function(cadena, tipoUniv){
            return rpc.query({
                route: '/get_universidades',
                params: {'cadena': cadena, 'tipo_universidad': tipoUniv}
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
        cambiar_genero_carrera: function(id, genero){
            let campo = genero == '1' ? 'x_name' : 'x_female_name';
            return rpc.query({
                route: '/get_carrera_genero',
                params: {'id_carrera': id, 'campo': campo, }
            }).then(function(response){
                return response.carrera[0][campo];
            }).catch(function(err){
                console.log(err);
            });
        },
        mostrar_helper_inicio: function(campo, msg) {
            $('#' + campo).addClass('invalido');
            $('#help_text').removeClass('invisible').text(msg);
        },
        ocultar_helper: function(campo) {
            $('#' + campo).removeClass('invalido');
            $('#help_text').addClass('invisible');
        },
        validar_campos: function() {
            let valido = true;
            if (data.doc.length < 1) {
                tramites.mostrar_helper_inicio('doc', 'El documento es requerido');
                valido = false;
            } else if (data.doc.length < 4) {
                tramites.mostrar_helper_inicio('doc', 'Ingrese por lo menos 4 caracteres');
                valido = false;
            } else if (data.doc_type == 1) {
                // Solo numeros
                let regex = /^[0-9]*$/;
                $('#doc').attr('maxlength', '11');
                if (!regex.test(data.doc)) {
                    tramites.mostrar_helper_inicio('doc', 'Ingrese solo números, no incluya espacios, letras, puntos ó caracteres especiales');
                    valido = false;
                } else {
                    tramites.ocultar_helper('doc');
                    valido = true;
                }
                
                if (data.doc.length > 11) {
                    tramites.mostrar_helper_inicio('doc', 'Verifica tu número de documento');
                    valido = false;
                }
            } else if (data.doc_type != 1) {
                // Solo numeros y letras
                let regex = /^[0-9a-zA-Z]*$/;
                $('#doc').attr('maxlength', '45');
                if (!regex.test(data.doc)) {
                    tramites.mostrar_helper_inicio('doc', 'Ingrese solo números ó letras, no incluya espacios, puntos ó caracteres especiales');
                    valido = false;
                } else {
                    tramites.ocultar_helper('doc');
                    valido = true;
                }
            }

            if (valido) {
                $('#btn_verificar').removeAttr('disabled');
                $('#btn_verificar_convenios').removeAttr('disabled');
            } else {
                $('#btn_verificar').attr('disabled', 'disabled');
                $('#btn_verificar_convenios').attr('disabled', 'disabled');
            }
            return valido;
        },
        validar_campos_nombres: function(e, _this){
            data.nombres = $('#x_names').val().length < 1 ? '' 
                : validaciones.quitarAcentos($('#x_names').val().toUpperCase().replace(/\s\s+/g, ' '));
            data.apellidos = $('#x_lastnames').val().length < 1 ? ''
                : validaciones.quitarAcentos($('#x_lastnames').val().toUpperCase().replace(/\s\s+/g, ' '));
            $('#x_names').val(data.nombres);
            $('#x_lastnames').val(data.apellidos);
            if(data.nombres.length > 1 && data.apellidos.length > 1){
                $('#btn_verificar_nombres').removeAttr('disabled');
                if(e.key == "Enter" || e.type == "click"){
                    console.log(e.target.name);
                    $('#btn_verificar_nombres').attr('disabled', 'disabled');
                    data.nombres = data.nombres.trim();
                    data.apellidos = data.apellidos.trim();
                    data.doc = '';
                    data.doc_type = '';
                    $('#doc').val('');
                    $('#doc_type').val('');
                    $('#x_names').val(data.nombres);
                    $('#x_lastnames').val(data.apellidos);
                    _this.validar_convenios();
                }
            }else{
                $('#btn_verificar_nombres').attr('disabled', 'disabled');
            }
        },
        label_input_file: function(elem) {
            $("#preview-"+elem.id).hide();
            let idname = $(elem).attr('id');
            if ($(elem).hasClass('btn-file')) {
                if($(elem)[0].files[0]){

                  let filename = $(elem).val().split('\\').pop();
                  let ext = $(elem).val().split('.').pop();
                  let fileSize = $(elem)[0].files[0].size;

                  if(ext == "pdf" & fileSize <= 819200){

                    $('[for="' + idname + '"]').find('i').removeClass('fa-search').addClass('fa-file-pdf-o');
                    setTimeout(function(){
                        $('[for="' + idname + '"]').find('i').removeClass('fa-file-pdf-o').addClass('fa-check');
                        $('[for="' + idname + '"]').removeClass('texto-gris invalido-form').addClass('texto-verde');
                    }, 1200);
                    $("#preview-"+elem.id).show();
                    // Mostrar modal Preview del PDF
                    $("#preview-"+elem.id).click(function(){ 
                        let inputElm = $("#"+elem.id);
                        let objElm = $("#pdfViewer");
                        $('#viewerModal').on('show.bs.modal', function (e) {
                            let reader = new FileReader();
                            reader.onload = function(e) {
                                console.log(e);
                                objElm.attr('src', e.target.result);
                            }
                            reader.readAsDataURL(inputElm[0].files[0]);
                        });
                        $("#viewerModal").modal('show');
                    });

                  }else{

                    $(elem).val('');
                    filename = ' Selecciona tu Archivo';
                    $('[for="' + idname + '"]').find('i').removeClass('fa-check').addClass('fa-search');
                    $('[for="' + idname + '"]').removeClass('texto-verde').addClass('texto-gris invalido-form');
                    if(ext != "pdf"){
                      validaciones.alert_error_toast( "Extensión ." +ext +" no permitida." );
                    }else if (fileSize > 819200){
                      validaciones.alert_error_toast( "El documento excede el tamaño máximo de 800Kb." );
                    }

                  }

                  $('[for="' + idname + '"]').find('span').html('  ' + filename);

                } else {
                    $(elem).val('');
                    let filename = ' Selecciona tu Archivo';
                    $('[for="' + idname + '"]').find('i').removeClass('fa-check').addClass('fa-search');
                    $('[for="' + idname + '"]').removeClass('texto-verde').addClass('texto-gris invalido-form');
                    $('[for="' + idname + '"]').find('span').html('  ' + filename);
                }
            }
        },
        combinar_select: function (_this, prefijo_clase){
            let elementClass = _this.className.split(" ");
            let childClass = elementClass[0];
            let childName = childClass.split(prefijo_clase)[1];
            let $select = $("select[name='"+childName+"']");
            $select.find("option:not(:first)").hide();
            if (childName.split("_").includes("state")){
              let nb = $select.find("option[data-country_id="+($(_this).val() || 0)+"]").show();
            } else if (childName.split("_").includes("city")){
              let nb = $select.find("option[data-state_id="+($(_this).val() || 0)+"]").show();
            }
            $select.val("");
        },
        get_data_edicion: function(){
            let data = {
                'tipo_doc': $('[name=x_document_type_ID]').val(),
                'documento': $('[name=x_document]').val()
            }
            return rpc.query({
                route: '/get_data_edicion',
                params: {'data': data}
            }).then(function(response){
//                 console.log(response);
                $('#x_expedition_country').val(response.data.x_expedition_country[0]);
                $('#x_expedition_state').val(response.data.x_expedition_state[0]);
                $('#x_expedition_city').val(response.data.x_expedition_city[0]);
                $('#x_country_ID').val(response.data.x_country_ID[0]);
                $('#x_state_ID').val(response.data.x_state_ID[0]);
                $('#x_city_ID').val(response.data.x_city_ID[0]);
                $('#x_foreign_country').val(response.data.x_foreign_country[0]);
            }).catch(function(err){
                console.log(err);
            });
        },
        enviar_data: function(){
            let formSample = document.forms[0];
            let formData = new FormData();
            let elems = formSample.elements;
            for (let i = 0; i < elems.length; i++) {
                if(elems[i].name === 'x_grade_date'){
                    elems[i].value = elems[i].value.split('-').reverse().join('-');
                }
                if(elems[i].name != ''){
                    if(elems[i].type === 'file'){
                        formData.append(elems[i].name, elems[i].files[0]);
                    } else {
                        formData.append(elems[i].name, elems[i].value);
                        if(elems[i].name === 'x_grade_date'){
                            elems[i].value = elems[i].value.split('-').reverse().join('-');
                        }
                    } 
                }

            }
            try {
                const request = new XMLHttpRequest();
                if(location.href.indexOf('/edicion/') == -1){
                    request.open("POST", "/create_user");
                }else{
                    request.open("POST", "/update_tramite");            
                }
                request.send(formData);
                request.onreadystatechange = function (aEvt) {
                    if (request.readyState == 4) {
                        if(request.status == 200){
                            let resp = JSON.parse(request.responseText);
                            if(resp.data_user){
                                location.replace(`/pagos/[${resp.data_user.tipo_doc}:${resp.data_user.documento}]`);
                            }else if(resp.id_user){
                                ocultarSpinner();
                                $('#div_results').removeClass('offset-md-2 col-md-8').addClass('offset-md-4 col-md-6');
                                $('#mssg_result').addClass('alert alert-warning').text('Trámite actualizado con exito');
                                setTimeout(()=>{ 
                                    location.replace(`http://34.70.101.32/`);
                                },800);
                            }else{
                                ocultarSpinner();
                                $('#mssg_result').addClass('alert alert-danger').text('Error: '+resp.message.slice(0,80));
                                $('#btn-registrar').removeAttr('disabled');
                            }
                         } else {
                                ocultarSpinner();
                                console.log('ERROR: '+request.status + request.statusText);
                                $('#mssg_result').addClass('alert alert-danger').text('No hemos podido completar la solicitud en este momento, inténtelo nuevamente');
                         }
                    }
                }
            } catch (err){
                ocultarSpinner();
                $('#mssg_result').addClass('alert alert-danger').text('Error: No se pudo guardar el registro, intente de nuevo al recargar la página');
                $('#btn-registrar').removeAttr('disabled');
                console.warn(err);
            }
        },
    });
    
    const tramites = new Tramites();
    
    // Inicio del trámite boton de enviar
    $('#btn_verificar').click(function(e) {
        if (tramites.validar_campos()) {
            tramites.validar_tramites();
            $('#btn_verificar').attr('disabled', 'disabled');
        }
    });
    
    // Inicio del trámite boton de cancelar
    $('#btn-cancelar').click(function(e){
        $('#doc').val('').focus();
        $('#msj_matricula').addClass('invisible').attr('aria-hidden',true);
    });

    // Inicio del trámite input número de documento
    $('#doc').on('keyup', function(e) {
        e.preventDefault();
        data.doc = $('#doc').val().toUpperCase();
        data.doc_type = $('#doc_type').val();
        $('#doc').val(data.doc);
        tramites.validar_campos();
        if(e.key == "Enter" && tramites.validar_campos()){
            if(location.href.indexOf('/convenios/tramite') == -1){
                tramites.validar_tramites();
                $('#btn_verificar').attr('disabled', 'disabled');
            } else {
                $('#x_names').val('');
                $('#x_lastnames').val('');
                data.nombres = '';
                data.apellidos = '';
                tramites.validar_convenios();
            }
        }
    });
    
    // Inicio del trámite input tipo de documento
    $('#doc_type').change(function(e) {
        data.doc = $('#doc').val();
        data.doc_type = $('#doc_type').val();
        tramites.validar_campos();
    });
        
    // Inicio de trámite convenios input nombres
    $('#x_names').on('keyup', function(e) {
        e.preventDefault();
        tramites.validar_campos_nombres(e, tramites);
    });
            
    // Inicio de trámite convenios input apellidos
    $('#x_lastnames').on('keyup', function(e) {
        e.preventDefault();
        tramites.validar_campos_nombres(e, tramites);
    });
    
    // Inicio del trámite por convenio boton de enviar por nombres
    $('#btn_verificar_nombres').click(function(e) {
        $('#doc').val('');
        $('#doc_type').val('');
        data.doc = '';
        data.doc_type = '';
        tramites.validar_campos_nombres(e, tramites);
    });
        
    // Inicio del trámite por convenios boton de enviar por documento
    $('#btn_verificar_convenios').click(function(e) {
        if (tramites.validar_campos()) {
            $('#x_names').val('');
            $('#x_lastnames').val('');
            data.nombres = '';
            data.apellidos = '';
            tramites.validar_convenios();
            $('#btn_verificar_convenios').attr('disabled', 'disabled');
        }
    });
    
    // Evento de los input files
    $('input[type=file]').change(function(){
        tramites.label_input_file(this);
    });
    
    //Cargar el documento en el input file
    if(location.href.indexOf('/edicion/') != -1){
        tramites.get_data_edicion();
    }
    
    // Validaciones de tipo de datos en los input del formulario
    $('#tramiteForm').on('change', async function(e){
        let valido = await validaciones.validar_formatos(e);
        if (valido){
            if($(e.target).is('select')){
                $(e.target).removeClass('is-invalid');
            };
            if(e.target.id == 'universidades'){
                $('#universidades').removeClass('is-invalid');
            }
            if(e.target.id == 'carreras'){
                $('#carreras').removeClass('is-invalid');
            }
            if(e.target.name == 'x_grade_date'){
                $(e.target).removeClass('is-invalid');
            }
        }else{
            console.log('HAY DATOS NO VALIDOS');
        }
    });
    
    // Validación del formulario antes de enviar
    $('#tramiteForm').submit(async function(e){
        e.preventDefault();
        $('#btn-registrar').attr('disabled', true);
        $('#btn-actualizar').attr('disabled', true);
        let valido = await validaciones.validar_formulario();
        if (valido){
            mostrarSpinner();
            tramites.enviar_data();
        }else{
            $('#mssg_result').text('').removeClass('alert alert-danger');
            setTimeout(()=>{
                ocultarSpinner();
                $('#mssg_result').addClass('alert alert-danger').text('Por favor, verifica el formulario los campos marcados en rojo son requeridos');
                $('#btn-registrar').removeAttr('disabled');
                $('#btn-actualizar').removeAttr('disabled');
            },400);
        }
    });
    
    function mostrarSpinner(){
        $('#div_spinner').attr('aria-hidden', false).removeClass('invisible');
        $('#div_results').attr('aria-hidden', true).addClass('invisible');
    }
    
        
    function ocultarSpinner(){
        $('#div_results').attr('aria-hidden', false).removeClass('invisible');
        $('#div_spinner').attr('aria-hidden', true).addClass('invisible');
    }

    // Mostrar ocultar los campos de ciudad y departamento
    $('#x_expedition_country').change(function(e){
        let pais_seleccionado = $('#x_expedition_country option:selected').text().trim();
        if(pais_seleccionado != 'COLOMBIA'){
            $('#x_expedition_state').addClass('invisible').attr('aria-hidden',true)
                .removeAttr('name').removeClass('i_required');
            $('#x_expedition_city').addClass('invisible').attr('aria-hidden',true)
                .removeAttr('name').removeClass('i_required');
            $('#dpto_otro_pais').removeClass('invisible').attr('aria-hidden',false)
                .attr('name','x_expedition_state').addClass('i_required');
            $('#ciudad_otro_pais').removeClass('invisible').attr('aria-hidden',false)
                .attr('name','x_expedition_city').addClass('i_required');
        }else{
            $('#x_expedition_state').removeClass('invisible').attr('aria-hidden',false)
                .attr('name','x_expedition_state').addClass('i_required');
            $('#x_expedition_city').removeClass('invisible').attr('aria-hidden',false)
                .attr('name','x_expedition_city').addClass('i_required');
            $('#dpto_otro_pais').addClass('invisible').attr('aria-hidden',true)
                .removeClass('i_required').removeAttr('name');
            $('#ciudad_otro_pais').addClass('invisible').attr('aria-hidden',true)
                .removeClass('i_required').removeAttr('name');
        }
    });
    
    // Borra el value de la universidad si cambia el tipo de universidad
    let tipo_univ = $('#x_institution_type_ID').val();
    $('#x_institution_type_ID').change(function(e){
        if($('#universidades') != undefined && $('#seleccion_univ') != undefined ){
            if(tipo_univ != $('#x_institution_type_ID').val() ){
                $('#universidades').val('');
                $('#seleccion_univ').val('');
            }
        }
        if($('#x_institution_type_ID').val() == 1){
            $('#doc_min_pdf').addClass('invisible').attr('aria-hidden',true)
                .find('input').removeAttr('name');
            $('#doc_min_na').removeClass('invisible').attr('aria-hidden',false);
        } else {
            $('#doc_min_na').addClass('invisible').attr('aria-hidden',true);
            $('#doc_min_pdf').removeClass('invisible').attr('aria-hidden',false)
                .find('input').attr('name','x_min_convalidation');
        }
    }).change();

    // Borra el value de la carrera si cambia de nivel profesional
    $('#x_level_ID').change(function(e){
        if($('#carreras') != undefined && $('#seleccion_carreras') != undefined ){
            $('#carreras').val('');
            $('#seleccion_carreras').val('');
        }
    });
    
    // Carga las opciones para el autocomplete de las universidades
    $('#universidades').on('keyup paste', async function(e){
        let tipoUniversidad = $('#x_institution_type_ID').val();
        if(e.target.value.length > 1){
           let consulta = await tramites.data_autocomplete_univ(e.target.value, tipoUniversidad);
           $('#result_univ').html('');
           $.each(consulta.universidades, function(key, value) { 
               $('#result_univ').append('<li class="list-group-item link-univ"><span id="'+ value.id +'" class="text-gray univ">' + value.x_name + '</span></li>');
           });
        }
    })
    
    // Borra la lista de opciones del autocomplete de universidades
    $('#universidades').blur(function(e){
        setTimeout(function(){
            $('#result_univ').html('');
        }, 400);
    })
    
    // Borra la lista de opciones del autocomplete de carreras
    $('#carreras').blur(function(e){
        setTimeout(function(){
            $('#result_carreras').html('');
        }, 400);
    })
    
    // Verifica que ya haya seleccionado un nivel profesional
    $('#carreras').focus(function(e){
        let inputNivelProf = $('#x_level_ID');
        if(inputNivelProf.val() == ''){
            inputNivelProf.addClass('is-invalid');
            $('#carreras').blur();
            setTimeout(function(){
                inputNivelProf.removeClass('is-invalid');
                inputNivelProf.focus();
            }, 1000);
        }
    });
    
    // Verifica que ya haya seleccionado un tipo de universidad
    $('#universidades').focus(function(e){
        let inputTipoU = $('#x_institution_type_ID');
        if(inputTipoU.val() == ''){
            inputTipoU.addClass('is-invalid');
            $('#universidades').blur();
            setTimeout(function(){
                inputTipoU.removeClass('is-invalid');
                inputTipoU.focus();
            }, 1000);
        }
    });
    
    // Carga las opciones para el autocomplete de las carreras
    $('#carreras').on('keyup paste', async function(e){
        let nivelProf = $('#x_level_ID').val();
        let genero = $('#x_gender_ID').val() != '' ? $('#x_gender_ID').val() : '1';
        if(e.target.value.length > 1){
           let consulta = await tramites.data_autocomplete_carreras(e.target.value, nivelProf, genero);
           $('#result_carreras').html('');
           $.each(consulta.carreras, function(key, value) { 
               let carrera = genero == '1' ? value.x_name : value.x_female_name;
               $('#result_carreras').append('<li class="list-group-item link-carreras"><span id="'+ value.id +'" class="text-gray carreras">' + carrera + '</span></li>');
           });
        }
    })
    
    // Asigna la selección de la lista del autocomplete al value del formulario
    $('#academica').click(function(e){
        if(e.target.classList.contains('link-univ')){
            $('#universidades').val(e.target.firstElementChild.textContent);
            $('#seleccion_univ').val(e.target.firstElementChild.id);
            $('#result_univ').html('');
        }else if(e.target.classList.contains('univ')){
            $('#universidades').val(e.target.textContent);
            $('#seleccion_univ').val(e.target.id);
            $('#result_univ').html('');
        }
        if(e.target.classList.contains('link-carreras')){
            $('#carreras').val(e.target.firstElementChild.textContent);
            $('#seleccion_carreras').val(e.target.firstElementChild.id);
            $('#result_carreras').html('');
        }else if(e.target.classList.contains('carreras')){
            $('#carreras').val(e.target.textContent);
            $('#seleccion_carreras').val(e.target.id);
            $('#result_carreras').html('');
        }
    })
    console.log('seleccion_carreras');
    // Cambia arquitecto/arquitecta según selección de género
    $('#x_gender_ID').change(async function(e){
        // Cambiamos el genero de la carrera
        if($('#x_level_ID').val() == '1'){
            if($('#x_gender_ID').val() == '1'){
                $('#x_institute_career').val('109');
            }else if ($('#x_gender_ID').val() == '2'){
                $('#x_institute_career').val('110');
            }
        } else if (($('#x_level_ID').val() != '1') && $('#x_gender_ID').val() != '' && $('#x_institute_career').val() != ''){
            let carrera = await tramites.cambiar_genero_carrera($('#x_institute_career').val(), $('#x_gender_ID').val());
            console.log(carrera);
            if(carrera){
                $('#carreras').val(carrera);
                $('select[name="x_institute_career"] option:selected').text(carrera);
            }
        } else if($('#x_gender_ID').val() == ''){
            $('#carreras').val('');
            $('#seleccion_carreras').val('');
            $('#x_institute_career').val('');
        }
    }).change();
    
    // Inicializa el popup que muestra la imágen de la ciudad de expedición de la cédula
    $('a[rel=popover]').popover({
        html: true,
        trigger: 'hover',
        placement: 'bottom',
        content: function() {
            return '<img src="' + $(this).data('img') + ' width="100%" />';
        }
    });
    
    //Controlador de paises/ciudades (Expedición)
    $("select[class*=child_place]").change(function(){
        let pais_seleccionado = $('select[name="x_expedition_country"] option:selected').text().trim();
        if(pais_seleccionado == 'COLOMBIA'){
          tramites.combinar_select(this, 'child_place-');
        }
    }).change();
    
    //Controlador de paises/ciudades (Residencia)
    $("select[class*=child-place]").change(function(){
          tramites.combinar_select(this, 'child-place-');
    }).change();
  
    // Opciones para idioma e inicializar el datepicker
	$.datepicker.regional['es'] = {
		closeText: 'Cerrar',
		prevText: 'Anterior',
		nextText: 'Siguiente',
		currentText: 'Hoy',
		monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
		monthNamesShort: ['Ene','Feb','Mar','Abr', 'May','Jun','Jul','Ago','Sep', 'Oct','Nov','Dic'],
		dayNames: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
		dayNamesShort: ['Dom','Lun','Mar','Mié','Juv','Vie','Sáb'],
		dayNamesMin: ['Do','Lu','Ma','Mi','Ju','Vi','Sá'],
		weekHeader: 'Sm',
		dateFormat: 'dd/mm/yy',
		firstDay: 1,
		isRTL: false,
		showMonthAfterYear: false,
		yearSuffix: ''
	};
	$.datepicker.setDefaults($.datepicker.regional['es']);
    $("[name=x_grade_date]").datepicker({
      maxDate: '0',
      dateFormat: "dd-mm-yy",
      changeMonth: true,
      changeYear: true,
      yearRange: '-80:+0'
    });
            
})