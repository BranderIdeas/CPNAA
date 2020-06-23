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
        origen: tramite
    }
        
    const Tramites = Class.extend({
        validar_tramites: function() {
            let origen = data.origen;
            (!origen) ? origen = '' : origen = `/${data.origen}`;
            return rpc.query({
                route: '/validar_tramites',
                params: {'x_document': data.doc.toUpperCase(), 'x_document_type_ID': data.doc_type}
            }).then(function(response){
                localStorage.setItem('dataTramite', JSON.stringify(data));
                if(response.convenio){
                    $(location).attr('href','/tramite/convenios/'+ response.id);
                } else {
                    if(response.id){
                        if (response.matricula){
                            $('#msj_matricula').removeClass('invisible').attr('aria-hidden',false);
                        } else {
                            $(location).attr('href','/cliente/'+ response.id +'/tramites');
                        }
                    }else{
                        $(location).attr('href','/tramite' + origen+'/['+data.doc_type+':'+data.doc+']');
                    }
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
        data_autocomplete_carreras: function(cadena, nivel_prof){
            return rpc.query({
                route: '/get_carreras',
                params: {'cadena': cadena, 'nivel_profesional':nivel_prof}
            }).then(function(response){
                return response;
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
            } else {
                $('#btn_verificar').attr('disabled', 'disabled');
            }
            return valido;
        },
        label_input_file: function(_this) {
            $("#preview-doc").hide();
            let idname = $(_this).attr('id');
            if ($(_this).hasClass('btn-file')) {
                if($(_this)[0].files[0]){

                  let filename = $(_this).val().split('\\').pop();
                  let ext = $(_this).val().split('.').pop();
                  let fileSize = $(_this)[0].files[0].size;

                  if(ext == "pdf" & fileSize <= 500000){

                    $('[for="' + idname + '"]').find('i').removeClass('fa-search').addClass('fa-file-pdf-o');
                    setTimeout(function(){
                        $('[for="' + idname + '"]').find('i').removeClass('fa-file-pdf-o').addClass('fa-check');
                        $('[for="' + idname + '"]').removeClass('texto-gris invalido').addClass('texto-verde');
                    }, 1200);
                    $("#preview-doc").show();

                  }else{

                    $(_this).val('');
                    filename = ' Selecciona tu Archivo';
                    $('[for="' + idname + '"]').find('i').removeClass('fa-check').addClass('fa-search');
                    $('[for="' + idname + '"]').removeClass('texto-verde').addClass('texto-gris invalido');
                    if(ext != "pdf"){
                      validaciones.alert_error_toast( "Extensión ." +ext +" no permitida." );
                    }else if (fileSize > 500000){
                      validaciones.alert_error_toast( "El documento excede el tamaño máximo de 500Kb." );
                    }

                  }

                  $('[for="' + idname + '"]').find('span').html('  ' + filename);

                } else {
                    $(_this).val('');
                    let filename = ' Selecciona tu Archivo';
                    $('[for="' + idname + '"]').find('i').removeClass('fa-check').addClass('fa-search');
                    $('[for="' + idname + '"]').removeClass('texto-verde').addClass('texto-gris invalido');
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
        enviar_data: function(){
            $('#btn-registrar').attr('disabled', true);
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
            var request = new XMLHttpRequest();
            request.open("POST", "/create_user");
            request.send(formData);
            request.onreadystatechange = function (aEvt) {
                if (request.readyState == 4) {
                    if(request.status == 200){
                        let resp = JSON.parse(request.responseText);
                        if(resp.data_user){
                            location.replace(`/pagos/[${resp.data_user.tipo_doc}:${resp.data_user.documento}]`);
                        }else{
                            console.log(resp.message);
                            $('#mssg_result').text(resp.message.substr(40));
                        }
                     } else {
                        console.log(request.message);
                     }
                }
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
        data.doc = $('#doc').val().toUpperCase();
        data.doc_type = $('#doc_type').val();
        $('#doc').val(data.doc);
        tramites.validar_campos();
        if(e.key == "Enter"){
            tramites.tramites(tramites);
            $('#btn_verificar').attr('disabled', 'disabled');
        }
    });
    
    // Inicio del trámite input tipo de documento
    $('#doc_type').change('keyup', function() {
        data.doc = $('#doc').val();
        data.doc_type = $('#doc_type').val();
        tramites.validar_campos();
    });
          
    // Mostrar modal Preview del PDF
    $("#preview-doc").click(function(){ 
        let inputElm = $("#x_document_image");
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
    
    // Evento de los input files
    $('input[type=file]').change(function(){
        tramites.label_input_file(this);
    });
    
    // Validaciones de tipo de datos en los input del formulario
    $('#tramiteForm').on('change', async function(e){
        let valido = await validaciones.validar_formatos(e);
        if (valido){
            console.log('DATOS OK');
        }else{
            console.log('HAY DATOS NO VALIDOS');
        }
    });
    
    // Validación del formulario antes de enviar
    $('#tramiteForm').submit(async function(e){
        e.preventDefault();
        let valido = await validaciones.validar_formulario();
        if (valido){
            tramites.enviar_data();
        }else{
            console.log('FORMULARIO INVALIDO');
        }
    });
    
    // Mostrar ocultar los campos de ciudad y departamento
    $('#x_expedition_country').change(function(e){
        let pais_seleccionado = $('select[name="x_expedition_country"] option:selected').text().trim();
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
    $('#x_institution_type_ID').change(function(e){
        if($('#universidades') != undefined && $('#seleccion_univ') != undefined ){
            $('#universidades').val('');
            $('#seleccion_univ').val('');
        }
    });
    
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
        if(e.target.value.length > 1){
           let consulta = await tramites.data_autocomplete_carreras(e.target.value, nivelProf);
           console.log(consulta.carreras);
           $('#result_carreras').html('');
           $.each(consulta.carreras, function(key, value) { 
               $('#result_carreras').append('<li class="list-group-item link-carreras"><span id="'+ value.id +'" class="text-gray carreras">' + value.x_name + '</span></li>');
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
    
    // Cambia arquitecto/arquitecta según selección de género
    $('#x_gender_ID').change(function(e){
        // Validamos si es profesional para controlar con el genero
        if($('#x_level_ID').val() == '1'){
            if($('#x_gender_ID').val() == '1'){
                $('#x_institute_career').val('109');
            }else{
                $('#x_institute_career').val('110');
            }
        }
    });
    
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
      changeYear: true
    });
            
})