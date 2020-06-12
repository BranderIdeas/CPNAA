odoo.define('website.tramites', function(require) {
'use strict';
    
    console.log('TRAMITES')
    let Class = require('web.Class');
    let rpc = require('web.rpc');
    let Validaciones = require('website.validations');
    let validaciones = new Validaciones();
    
    let param = location.href.split('/');
    param = param[param.length - 1];
    let data = {
        doc: '',
        doc_type: '',
        origen: param
    }
        
    let Tramites = Class.extend({
        tramites: function(_this) {
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
//         tramite_mostrar: function(origen){
//             if (origen == 'matricula'){
//                 return 'MATRÍCULA PROFESIONAL DE ARQUITECTO';
//             }else if(origen == 'inscripciontt'){
//                 return 'CERTIFICADO DE INSCRIPCIÓN PROFESIONAL';
//             }else if(origen == 'licencia'){
//                 return 'LICENCIA TEMPORAL ESPECIAL';
//             }
//         },
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
    });
    
    let tramites = new Tramites();
    
    $('#btn_verificar').click(function(e) {
        if (tramites.validar_campos()) {
            tramites.tramites(tramites);
            $('#btn_verificar').attr('disabled', 'disabled');
        }
    });

    $('#doc').on('keyup', function(e) {
        data.doc = $('#doc').val();
        data.doc_type = $('#doc_type').val();
        $('#doc').val(data.doc.toUpperCase());
        tramites.validar_campos();
        if(e.key == "Enter"){
            tramites.tramites(tramites);
            $('#btn_verificar').attr('disabled', 'disabled');
        }
    });
    
    $('#doc_type').change('keyup', function() {
        data.doc = $('#doc').val();
        data.doc_type = $('#doc_type').val();
        tramites.validar_campos();
    });
            
    //console.log("Funcion");
    /*function readURL(input,object) {
      if (input[0].files && input[0].files[0]) {
        let reader = new FileReader();
        reader.onload = function(e) {
          console.log(e);
          object.attr('data',  e.target.result);
        }
        reader.readAsDataURL(input[0].files[0]);
      }
    }*/
    
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
    $('input[type=file]').change(function() {
        $("#preview-doc").hide();
        if ($(this).hasClass('btn-file')) {
            if($(this)[0].files[0]){
            
          let filename = $(this).val().split('\\').pop();
          let ext = $( this ).val().split('.').pop();
          let idname = $(this).attr('id');
          let fileSize = $(this)[0].files[0].size;

          if(ext == "pdf" & fileSize <= 500000){
            $('[for="' + idname + '"]').find('i').removeClass('fa-search').addClass('fa-file-pdf-o');
            setTimeout(function(){
                $('[for="' + idname + '"]').find('i').removeClass('fa-file-pdf-o').addClass('fa-check');
                $('[for="' + idname + '"]').removeClass('texto-gris invalido').addClass('texto-verde');
            }, 1000);
                $("#preview-doc").show();
          }else{
              
            $( this ).val('');
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
            }else{
                $( this ).val('');
                filename = ' Selecciona tu Archivo';
                $('[for="' + idname + '"]').find('i').removeClass('fa-check').addClass('fa-search');
                $('[for="' + idname + '"]').removeClass('texto-verde').addClass('texto-gris invalido');
            }
        }
        
      });

    // Validaciones en formulario de trámites
    async function validar_form(e){
        let elem = e.target;
        console.log(elem);
        if(elem.classList.contains('o-letters')){
            let valid = validaciones.validar_solo_letras(elem.value);
            if(!valid){
                elem.classList.add('is-invalid');
                return valid;
            }else{
                elem.classList.remove('is-invalid');
                elem.value = elem.value.toUpperCase();
            }            
        } else if (elem.classList.contains('v-celular')){
            let valid = validaciones.validar_celular(elem.value);
            if(!valid){
                elem.classList.add('is-invalid');
                return valid;
            }else{
                elem.classList.remove('is-invalid');
            }
        } else if (elem.classList.contains('v-email')){
            let valid = validaciones.validar_email(elem.value);
            if(!valid){
                elem.classList.add('is-invalid');
            }else{
                valid = await validaciones.validar_email_unico(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                }else{
                    elem.classList.remove('is-invalid');
                }
            }
            return valid;
        } else if (elem.classList.contains('v-address')){
            let valid = validaciones.validar_direccion(elem.value);
            if(!valid){
                elem.classList.add('is-invalid');
                return valid;
            }else{
                elem.classList.remove('is-invalid');
                elem.value = elem.value.toUpperCase();
            }
        } else if (elem.classList.contains('v-alfanum')){
            
            let valid = validaciones.validar_alfanum(elem.value, 'el documento Ministerio de Educación')
            if(!valid){
                elem.classList.add('is-invalid');
                return valid;
            }else{
                elem.classList.remove('is-invalid');
                elem.value = elem.value.toUpperCase();
            }
        } else if (elem.classList.contains('v-telefono')){
            if(elem.value.length > 0){
                let valid = validaciones.validar_telefono(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = elem.value.toUpperCase();
                }
            }
        }
        
        if($('#x_document_image')[0].files[0] === undefined){
            $("label[for='x_document_image']").addClass('invalido');
            return false;
        }else{
            $("label[for='x_document_image']").removeClass('invalido');
        }
        if($('#x_institute_career').val() == ''){
            $('#carreras').addClass('is-invalid');
            return false;               
        }else{
            $('#carreras').removeClass('is-invalid');
        } 
        if($('#x_institution_ID').val() == ''){
            $('#universidades').addClass('is-invalid');
            return false;
        }else{
            $('#universidades').removeClass('is-invalid');
        }
        if($('input[name=x_grade_date]').val() == ''){
            $('input[name=x_grade_date]').addClass('is-invalid');
            return false;
        }else{
            $('input[name=x_grade_date]').removeClass('is-invalid');
        }
        if(!$('input[name=x_elec_terminos]').prop('checked')){
            $('input[name=x_elec_terminos]').addClass('is-invalid');
            return false;
        }else{
            $('input[name=x_elec_terminos]').removeClass('is-invalid');
        }
        
        return true;
        
    }
    
    $('#tramiteForm').on('submit change', function(e){
        let form_valido = validar_form(e);
        console.log(form_valido);
        if (form_valido){
            $('#btn-registrar').removeAttr('disabled');
        }else{
            $('#btn-registrar').attr('disabled', true);
        }
    });
        
    $('#btn-cancelar').click(function(e){
        $('#doc').val('').focus();
        $('#msj_matricula').addClass('invisible').attr('aria-hidden',true);
    });
    
    $('#x_expedition_country').change(function(e){
        let pais_seleccionado = $('select[name="x_expedition_country"] option:selected').text().trim();
        if(pais_seleccionado != 'COLOMBIA'){
            $('#x_expedition_state').addClass('invisible').attr('aria-hidden',true).removeAttr('required');
            $('#x_expedition_city').addClass('invisible').attr('aria-hidden',true).removeAttr('required');
            $('#dpto_otro_pais').removeClass('invisible').attr('aria-hidden',false);
            $('#ciudad_otro_pais').removeClass('invisible').attr('aria-hidden',false);
        }else{
            $('#x_expedition_state').removeClass('invisible').attr('aria-hidden',false).attr('required',true);
            $('#x_expedition_city').removeClass('invisible').attr('aria-hidden',false).attr('required',true);
            $('#dpto_otro_pais').addClass('invisible').attr('aria-hidden',true);
            $('#ciudad_otro_pais').addClass('invisible').attr('aria-hidden',true);
        }
    });
    
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
    
    $('#x_institution_type_ID').change(function(e){
        if($('#universidades') != undefined && $('#seleccion_univ') != undefined ){
            $('#universidades').val('');
            $('#seleccion_univ').val('');
        }
    });
        
    $('#x_level_ID').change(function(e){
        if($('#carreras') != undefined && $('#seleccion_carreras') != undefined ){
            $('#carreras').val('');
            $('#seleccion_carreras').val('');
        }
    });
    
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
    
    $('#universidades').blur(function(e){
        setTimeout(function(){
            $('#result_univ').html('');
        }, 400);
    })
        
    $('#carreras').blur(function(e){
        setTimeout(function(){
            $('#result_carreras').html('');
        }, 400);
    })
    
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

    
    // CODIGO QUE ESTABA EN EL WEBSITE ALEX
    //
    // This file is meant to regroup your javascript code. You can either copy/past
    // any code that should be executed on each page loading or write your own
    // taking advantage of the Odoo framework to create new behaviors or modify
    // existing ones. For example, doing this will greet any visitor with a 'Hello,
    // world !' message in a popup:
    //
    /*
    odoo.define('website.user_custom_code', function (require) {
    'use strict';

    let Dialog = require('web.Dialog');
    let publicWidget = require('web.public.widget');

    publicWidget.registry.HelloWorldPopup = publicWidget.Widget.extend({
        selector: '#wrapwrap',

        start: function () {
            Dialog.alert(this, "Bienevenido al modulo de Matricula Profesional!");
            return this._super.apply(this, arguments);
        },
    })
    });

    */
    /*let fieldList = ['x_foreign_country', 
                     'x_foreign_state', 
                     'x_foreign_city', 
                     'x_foreign_address', 
                     'x_certification_image', 
                     'x_certification_studies_completed', 
                     'x_foreign_professional_accreditation', 
                     'x_professional_experience', 
                     'x_company_existence_certificate', 
                     'x_entity_request'
                    ];

    function checkForeign(){
        if ($("input[name='x_foreign_origin']").is(':checked')){
            fieldList.forEach(function(item){
                $("[name='"+item+"']").parent().parent().removeClass("o_website_form_field_hidden");
                $("[name='"+item+"']").attr("required", "required");
            });
        }else{
            fieldList.forEach(function(item){
                $("[name='"+item+"']").parent().parent().addClass("o_website_form_field_hidden");
                $("[name='"+item+"']").removeAttr("required");
            });
        }
    }

    checkForeign();*/


    /*$("input[name='x_foreign_origin']").change(function(){
        checkForeign();
    });*/

    //Controlador de paises/ciudades etc
    $("select[class*=child_place]").change(function(){
      let elementClass = this.className.split(" ");
      let childClass = elementClass[0];
      let childName = childClass.split("child_place-")[1];
      //console.log(childName);
      let $select = $("select[name='"+childName+"']");
      $select.find("option:not(:first)").hide();
      if (childName.split("_").includes("state")){
        let nb = $select.find("option[data-country_id="+($(this).val() || 0)+"]").show();
      } else if (childName.split("_").includes("city")){
        let nb = $select.find("option[data-state_id="+($(this).val() || 0)+"]").show();
      }
      $select.val("");
    }).change();


    //Controlador de IES por tipo
    let elm;
    $("select#x_institution_type_ID").change(function(){
      if($(this).val()==2){
        $("[name=x_doc_min_educa]").removeClass("inputDisabled");
        $("[name=x_doc_min_educa]").attr("required",true);
        $("[name=x_doc_min_educa]").val("");
      }else{
        $("[name=x_doc_min_educa]").addClass("inputDisabled");
        $("[name=x_doc_min_educa]").removeAttr("required");
        $("[name=x_doc_min_educa]").val("NO APLICA");
      }
      let elementClass = this.className.split(" ");
      let $select = $("select#x_institution_ID");
      $select.find("option:not(:first)").hide();
      let nb = $select.find("option[data-x_institution_type_ID="+($(this).val() || 0)+"]").show();
      $select.val("");
    });
//     $("select.career-selector").change(function(){
//       //let elementClass = this.className.split(" ");
//       let $select = $("select#x_studio_carrera");
//       $select.find("option:not(:first)").hide();
//       let nb = $select.find("option[data-x_level_ID="+($("#x_level_ID").val() || 0)+"][data-x_institute_ID="+($("#x_institution_ID").val() || 0)+"]").show();
//       console.log($("#x_level_ID").val(), $("#x_institution_ID").val());
//       $select.val("");
//     });
    
    if (urlParams.get("form")){

      if ($("select[name=x_document_type_ID]").val() == 1){
        $("#x_expedition_country").val(1).trigger("change");
      }else{
        $("#x_expedition_country").removeClass("inputDisabled")
      }

      let origin = urlParams.get("form");
      let contentForm = origin.toLowerCase();
      if (origin == null){
        contentForm = "matricula";
      }
      if(origin == "matricula"){
        $("#x_level_ID").val(1).trigger("change");
      }else{
        $("#x_level_ID").removeClass("inputDisabled");  
      }
      if (origin == "inscripciontt"){
        //$("input[name=x_foreign_origin]").parent().parent().hide();
        $("#x_level_ID option[value=1]").remove();
      }
      if (origin != "licencia"){
        $("#foreignInfo").remove();
        //$("#x_institution_type_ID").val(1).trigger("change");
        $("#x_institution_type_ID").removeClass("inputDisabled"); 
      } else {
        $("#x_institution_type_ID").val(2).trigger("change");
        $("[name=x_foreign_origin]").prop('checked', true);
        $("[name=x_foreign_origin]").addClass("inputDisabled"); 
      }
      elm = $("#"+contentForm);
    }else{
      elm = $("#matricula");
    }
    
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
    

    $("select[name=x_user_type_ID]").find("option:not(:first)").hide();
    elm.show();
        
})