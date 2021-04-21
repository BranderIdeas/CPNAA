odoo.define('website.denuncia', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
        
        let files = [];
        
        const Denuncia = Class.extend({ //data, _this
            enviar_denuncia: function(){
                let formDenuncia = document.forms[0];
                let formData = new FormData();
                let elems = formDenuncia.elements;
                for (let i = 0; i < elems.length; i++) {
                    if(elems[i].name != ''){
                        if(elems[i].name === 'x_complaint_issues_ID'){
                            let values = [];
                            $("input[name='x_complaint_issues_ID']:checked").each(function() {
                                values.push($(this).val());
                            });
                            formData.append(elems[i].name, values);
                        } else if(elems[i].name === 'x_facts_rural'){
                            $('#radio_rural').prop('checked') ? formData.append('x_facts_rural', true) : formData.append('x_facts_urban', true);
                        } else {
                            formData.append(elems[i].name, elems[i].value);
                        }
                    }
                }
                for (let file of files) {
                    formData.append(file.name, file);
                }
                for (let value of formData.values()) {
                   console.log(value); 
                }
                try {
                    const request = new XMLHttpRequest();
                    request.open("POST", "/registrar_denuncia");
                    request.send(formData);
                    request.onreadystatechange = function (aEvt) {
                        if (request.readyState == 4) {
                            if(request.status == 200){
                                let resp = JSON.parse(request.responseText);
                                if(resp.ok){
                                    ocultarSpinner();
                                    $('#div_results').removeClass('offset-md-2 col-md-8').addClass('offset-md-4 col-md-6');
                                    $('#mssg_result').text('').removeClass('alert alert-danger');
                                    $('#mssg_result').addClass('alert alert-info').text(resp.message);
                                    setTimeout(()=>{ 
                                        window.top.location.href = 'https://cpnaa.gov.co/';
                                    },1200);
                                }else{
                                    ocultarSpinner();
                                    $('#mssg_result').text('').removeClass('alert alert-info');
                                    $('#mssg_result').addClass('alert alert-danger').text('Error: '+resp.message.slice(0,80));
                                    $('#enviar_denuncia').removeAttr('disabled');
                                }
                             } else {
                                    ocultarSpinner();
                                    console.log('ERROR: '+request.status +' '+ request.statusText);
                                    $('#enviar_denuncia').removeAttr('disabled');
                                    $('#mssg_result').text('').removeClass('alert alert-info');
                                    $('#mssg_result').addClass('alert alert-danger').text('No hemos podido completar la solicitud en este momento');
                             }
                        }
                    }
                } catch (err){
                    ocultarSpinner();
                    $('#mssg_result').addClass('alert alert-danger').text('Error: No se pudo guardar el registro, intente de nuevo al recargar la página');
                    $('#enviar_denuncia').removeAttr('disabled');
                    console.warn(err);
                }
            },
            insertarFila: function(file) {
                const size = (Number(file.size) / 1024 / 1024).toFixed(2);
                const ext = file.name.split(".").pop();
                $("#tableHead").removeClass("invisible").attr("aria-hidden", false);
                $("#tableFiles").html(
                    $("#tableFiles").html() +
                    `<tr id="tr-${files.indexOf(file)}">
                        <th scope="row">${files.indexOf(file) + 1}</th>
                        <td>${file.name}</td>
                        <td class="text-center">.${ext}</td>
                        <td class="text-center">${size}mb</td>
                        <td class="text-center hand" id="preview">
                            <i id="preview-${files.indexOf(file)}" class="fa fa-eye previewEvidence"></i>
                        </td>
                        <td class="text-center hand" id="delete">
                            <i id="delete-${files.indexOf(file)}" class="fa fa-trash deleteEvidence"></i>
                        </td>
                    </tr>`
                );
            },
            esExtensionValida: function(ext) {
                let validos = ["pdf", "jpg", "jpeg", "png"];
                return validos.indexOf(ext) === -1 ? false : true;
            },
            get_profesional: function(_this){
                const documento = $("input[name='x_implicated_document']").val();
                    const tipo_doc = $("select[name='x_implicated_document_type_ID']").val();
                return rpc.query({
                    route: '/get_profesional',
                    params: {'documento': documento, 'tipo_doc': tipo_doc}
                }).then(function(response){
                    console.log(response);
                    if(response.ok){
                        if(response.result.length === 1){
                           _this.insertar_profesional(response.result[0]);
                        }else if (response.result.length > 1){
                            let select = `<label class="col-form-label mb-3" for="selected">
                                            Profesiones registradas de ${validaciones.capitalizeFromUpper(response.result[0].x_studio_nombres)} ${validaciones.capitalizeFromUpper(response.result[0].x_studio_apellidos)}
                                            <select class="form-control o_website_form_input mt-2" id="selected">
                                         `;
                            response.result.forEach( (res,i) => {
                                select += `<option value=${i}>${res.x_studio_carrera_1[1]}</option>`;
                            })
                            select += '</option>';
                            $("#select_profesional").html(select);
                            $("#results_profesional").modal('show');
                            $("#results_profesional").on('hidden.bs.modal', function(){
                                _this.insertar_profesional(response.result[$("#selected").val()]); 
                                $("#results_profesional").modal('hide');
                                $("#open-modal-prof").show();
                                $("#open-modal-prof").click(function(){
                                    $("#results_profesional").modal('show');
                                });
                            });
                        }
                    }else{
                        validaciones.alert_error_toast( response.result, 'top');
                        $("input[name='x_implicated_enrollment_number']").val("")
                        $("input[name='x_implicated_names']").val("")
                        $("input[name='x_implicated_lastnames']").val("")
                        $("#open-modal-prof").hide();
                    }
                }).catch(function(err){
                    console.log(err);
                });  
            },
            insertar_profesional: function(prof){
                $("input[name='x_implicated_enrollment_number']").val(prof.x_enrollment_number)
                $("input[name='x_implicated_names']").val(prof.x_studio_nombres)
                $("input[name='x_implicated_lastnames']").val(prof.x_studio_apellidos)
            },
            descargar_adjunto_fase: function(elem, _this){
                _this.mostrar_loading_btn_icon(elem, _this);
                const nombre_archivo = elem.dataset.id.split('-').slice(0,-1).join('-');
                const id_denuncia    = Number(elem.dataset.id.split('-').pop());
                return rpc.query({
                    route: '/get_attachment',
                    params: { id_denuncia, nombre_archivo }
                }).then(function(response){
                    if(response.ok){
                        $('#pdfFrameVigencia').attr('src', `data:application/pdf;base64,${response.file.pdf}`);
                        const linkSource = $('#pdfFrameVigencia').attr('src');
                        const downloadLink = document.createElement("a");
                        const fileName = response.file_name;
                        downloadLink.href = linkSource;
                        downloadLink.download = fileName;
                        downloadLink.click();
                    }else{
                        validaciones.alert_error_toast( response.error, 'top');
                    }
                    _this.ocultar_loading_btn_icon(elem, _this);
                }).catch(function(err){
                    console.log(err);
                    validaciones.alert_error_toast( "No hemos podido completar su solicitud.", 'top');
                    _this.ocultar_loading_btn_icon(elem, _this);
                })
            },
            mostrar_loading_btn_icon: function(elem, _this){
                if(elem.tagName === 'I'){
                    _this.rotar(elem);
                    elem.parentNode.setAttribute('disabled', true);
                }else if(elem.tagName === 'BUTTON'){
                    _this.rotar(elem.children[0]);
                    elem.setAttribute('disabled', true);
                }
            },
            ocultar_loading_btn_icon: function(elem, _this){
                if(elem.tagName === 'I'){
                    _this.quitar_rotar(elem);
                    elem.parentNode.removeAttribute('disabled');
                }else if(elem.tagName === 'BUTTON'){
                    _this.quitar_rotar(elem.children[0]);
                    elem.removeAttribute('disabled');
                }
            },
            rotar: function(icono){
                icono.classList.remove('fa-download');
                icono.classList.add('fa-spinner');
                icono.classList.add('rotate-spin');
            },
            quitar_rotar: function(icono){
                icono.classList.add('fa-download');
                icono.classList.remove('fa-spinner');
                icono.classList.remove('rotate-spin');
            },
            guardar_apelacion: function(archivo_pdf, id_denuncia){
                Swal.fire({
                    toast: true,
                    title: `¿Confirmar envio del archivo PDF?`,
                    showConfirmButton: true,
                    showCancelButton: true,
                    confirmButtonText: 'Confirmar',
                    cancelButtonText: 'Cancelar',
                    confirmButtonColor: '#c8112d',
                    showLoaderOnConfirm: true,
                      preConfirm: (response) => {
                        return rpc.query({
                                route: '/save_apelacion',
                                params: {'archivo_pdf': archivo_pdf, 'id_denuncia': id_denuncia}
                            }).then(function(response){
                                if (!response.ok) {
                                  throw new Error(response.error.message)
                                }
                                return response;
                            }).catch((error) => {
                                let message = error.message.message == undefined ? error : error.message.message;
                                Swal.showValidationMessage(
                                  `Error: ${message}`
                                )
                            })
                      },
                }).then((result) => {
                    if (result.value) {
                        validaciones.alert_success_toast(`${result.value.message}`,'center')
                        if(result.value.ok){
                            setTimeout(()=>{
                                location.reload();
                            },1000)
                        }
                    }
                })
            },
        })
        
        const denuncia = new Denuncia();
        
        $("#x_evidence_files").change((e) => {
            const MAX_FILES = 10;
            files = [...files, ...e.target.files];
            $("#tableFiles").html("");
            if(files.length > MAX_FILES){
                files = files.slice(0, MAX_FILES);
                validaciones.alert_error_toast( 'Puede adjuntar hasta 10 archivos', 'top');
            }
            for (const file of files) {
                const size = (Number(file.size) / 1024 / 1024).toFixed(2);
                const ext = file.name.split(".").pop();
                if (!denuncia.esExtensionValida(ext)) {
                    validaciones.alert_error_toast( `${file.name}, No es un formato valido (Permitidos: pdf, png, jpg, jpeg)`, 'top');
                    files = files.filter((el) => el.name != file.name);
                } else if (size > 3) {
                    validaciones.alert_error_toast( `${file.name}, Excede el tamaño permitido de 3mb`, 'top');
                    files = files.filter((el) => el.size != file.size);
                } else {
                    denuncia.insertarFila(file);
                }
            }
        });
    
        $(".btn-attachment").click((e) => {
            denuncia.descargar_adjunto_fase(e.target, denuncia);
        });
        
        $("#tableFiles").click((e) => {
            if (e.target.classList.contains("previewEvidence")) {
                const idx = e.target.id.split("-").pop();
                $("#pdfPreview").attr("src", "");
                $("#viewerModalEvidence").on("show.bs.modal", function (e) {
                    let reader = new FileReader();
                    reader.onload = function (e) {
                        $("#pdfPreview").attr("src", e.target.result);
                    };
                    if(files[idx]) {
                        reader.readAsDataURL(files[idx]);
                    }
                });
                $("#viewerModalEvidence").modal("show");
            }
            if (e.target.classList.contains("deleteEvidence")) {
                const idx = e.target.id.split("-").pop();
                files.splice(idx, 1);
                console.log(idx);
                $("#tableFiles").html("");
                if (files.length < 1) {
                    $("#tableHead").addClass("invisible").attr("aria-hidden",true);
                }
                for (const file of files) {
                    denuncia.insertarFila(file);
                }
            }
        });
        
        // Mostrar u ocultar textfield de otro asunto 
        $("input[name='x_complaint_issues_ID']").change((e) => {
            let otro = false;
            $("input[name='x_complaint_issues_ID']:checked").each(function() {
                if ($(this).val() === '8') { otro = true; } 
            });
            if(otro){
                $('#otro_asunto').removeClass('invisible').attr('aria-hidden',false);
                $('input[name="x_complaint_issues_other"]').addClass('i_required');
            }else{
                $('#otro_asunto').addClass('invisible').attr('aria-hidden',true);
                $('input[name="x_complaint_issues_other"]').removeClass('i_required is-invalid').val('');
            }
        });
        
        // Evento del input documento para buscar los dataos
        $("input[name='x_implicated_document']").change(async function(e){
            if(e.target.value.length > 3){
                denuncia.get_profesional(denuncia);
            }
        });
        
        // Validación del formulario de los input campos
        $('#denunciaForm').change(async function(e){
            let valido = await validaciones.validar_formatos(e.target, validaciones);
            if (valido){
                if($(e.target).is('select')){
                    $(e.target).removeClass('is-invalid');
                };
            }else{
                console.warn('Formulario Invalido');
            }
        });
        
        // Validación del formulario antes de enviar
        $('#denunciaForm').submit(async function(e){
            e.preventDefault();
            $('#enviar_denuncia').attr('disabled', true);
            let valido = await validaciones.validar_formulario(validaciones);
            if (valido) { valido = validaciones.validarCheckboxsRequired('x_complaint_issues_ID', 'asunto', validaciones); }
            if (valido){
                mostrarSpinner();
                denuncia.enviar_denuncia();
            } else {
                $('#mssg_result').text('').removeClass('alert alert-danger');
                setTimeout(()=>{
                    ocultarSpinner();
                    $('#mssg_result').addClass('alert alert-danger').text('Por favor, verifica en el formulario los campos no válidos y/o requeridos *');
                    $('#enviar_denuncia').removeAttr('disabled');
                },400);
            }
        });
    
        // Muestra el número de caracteres del textarea de narración de los hechos
        $("[name='x_facts_narration']").on('input propertychange', e => {
            $('#counter_facts_narration').text(`${e.target.value.length}/1000`);
        });
    
        // Mostrar modal preview del cargue de diploma en PDF
        $("#btn_apelacion").change(function(ev){
            let file = ev.target.files[0];
            let ext = $('#btn_apelacion').val().split('.').pop();
            let objElm = $("#pdfViewerApelacion");
            if(file){
                if (file.size > 1024000 || ext != 'pdf'){
                    validaciones.alert_error_toast( "El archivo debe ser formato PDF y no exceder de 1Mb.", 'top');
                    return;
                }
                $('#viewerModalApelacion').on('show.bs.modal', function (e) {
                    let reader = new FileReader();
                    reader.onload = function(e) {
                        objElm.attr('src', e.target.result);
                    }
                    reader.readAsDataURL(file);
                });
                $("#viewerModalApelacion").modal('show');          
            }
        });

        // Guardar el Archivo de Apelación PDF
        $("#guardarApelacion").click(function(e){
            e.preventDefault();
            let id_denuncia = $(this).data('denuncia_id');
            let archivo_b64 = $("#pdfViewerApelacion").attr('src');
            denuncia.guardar_apelacion(archivo_b64, id_denuncia); 
        })
        
        function mostrarSpinner(){
            $('#div_spinner_denuncia').attr('aria-hidden', false).removeClass('invisible');
            $('#div_results_denuncia').attr('aria-hidden', true).addClass('invisible');
        }
        
        function ocultarSpinner(){
            $('#div_results_denuncia').attr('aria-hidden', false).removeClass('invisible');
            $('#div_spinner_denuncia').attr('aria-hidden', true).addClass('invisible');
        }
        
    })