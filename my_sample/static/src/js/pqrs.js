odoo.define('website.pqrs', function(require) {
'use strict';
    
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
        
        let files = [];

        const Pqrs = Class.extend({ //data, _this
          registrar_pqrs: function(){
              let formPqrs = document.forms[0];
              let formData = new FormData();
              let elems = formPqrs.elements;
              for (let i = 0; i < elems.length; i++) {
                  if(elems[i].name != ''){
                    formData.append(elems[i].name, elems[i].value);
                  }
              }
              for (let file of files) {
                  formData.append(file.name, file);
              }
              try {
                  const request = new XMLHttpRequest();
                  request.open("POST", "/registrar_pqrs");
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
                                  $('#registrar_pqrs').removeAttr('disabled');
                              }
                            } else {
                                  ocultarSpinner();
                                  console.log('ERROR: '+request.status +' '+ request.statusText);
                                  $('#registrar_pqrs').removeAttr('disabled');
                                  $('#mssg_result').text('').removeClass('alert alert-info');
                                  $('#mssg_result').addClass('alert alert-danger').text('No hemos podido completar la solicitud en este momento');
                            }
                      }
                  }
              } catch (err){
                  ocultarSpinner();
                  $('#mssg_result').addClass('alert alert-danger').text('Error: No se pudo guardar el registro, intente de nuevo al recargar la página');
                  $('#registrar_pqrs').removeAttr('disabled');
                  console.warn(err);
              }
          },
          esExtensionValida: function(ext) {
              let validos = ["pdf", "jpg", "jpeg", "png"];
              return validos.indexOf(ext) === -1 ? false : true;
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
                          <i id="preview-${files.indexOf(file)}" class="fa fa-eye previewAttachment"></i>
                      </td>
                      <td class="text-center hand" id="delete">
                          <i id="delete-${files.indexOf(file)}" class="fa fa-trash deleteAttachment"></i>
                      </td>
                  </tr>`
              );
          },
        })
    
        const pqrs = new Pqrs();

        // Mostrar u ocultar textfield de otro asunto 
        $("select[name='x_issues_ID']").change((e) => {
            const otro = $("select[name='x_issues_ID'] option:selected").text().includes('Otro') ? true : false;
            if(otro){
                $('#otro_asunto').removeClass('invisible').attr('aria-hidden',false);
                $('select[name="x_pqrs_issue_other"]').addClass('i_required');
            }else{
                $('#otro_asunto').addClass('invisible').attr('aria-hidden',true);
                $('select[name="x_pqrs_issue_other"]').removeClass('i_required is-invalid').val('');
            }
        });

        // Mostrar u ocultar asuntos si se selecciona queja 
        $("select[name='x_request_type_ID']").change((e) => {
            const queja = $("select[name='x_request_type_ID'] option:selected").text().includes('Queja') ? true : false;
            if(!queja){
                $('#asunto_pqrs').removeClass('invisible').attr('aria-hidden',false);
                $('select[name="x_issues_ID"]').addClass('i_required');
            }else{
                $('#asunto_pqrs').addClass('invisible').attr('aria-hidden',true);
                $('select[name="x_issues_ID"]').removeClass('i_required is-invalid').val('');
            }
        });

        // Validación del formulario de los input campos
        $('#pqrsForm').change(async function(e){
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
        $('#pqrsForm').submit(async function(e){
            e.preventDefault();
            $('#registrar_pqrs').attr('disabled', true);
            let valido = await validaciones.validar_formulario(validaciones);
//             if (valido) { valido = validaciones.validarCheckboxsRequired('x_complaint_issues_ID', 'asunto', validaciones); }
            if (valido){
                mostrarSpinner();
                pqrs.registrar_pqrs();
            } else {
                $('#mssg_result').text('').removeClass('alert alert-danger');
                setTimeout(()=>{
                    ocultarSpinner();
                    $('#mssg_result').addClass('alert alert-danger').text('Por favor, verifica en el formulario los campos no válidos y/o requeridos *');
                    $('#registrar_pqrs').removeAttr('disabled');
                },400);
            }
        });
    
        $("#x_pqdr_attachments").change((e) => {
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
                if (!pqrs.esExtensionValida(ext)) {
                    validaciones.alert_error_toast( `${file.name}, No es un formato valido (Permitidos: pdf, png, jpg, jpeg)`, 'top');
                    files = files.filter((el) => el.name != file.name);
                } else if (size > 3) {
                    validaciones.alert_error_toast( `${file.name}, Excede el tamaño permitido de 3mb`, 'top');
                    files = files.filter((el) => el.size != file.size);
                } else {
                    pqrs.insertarFila(file);
                }
            }
        });
    
        $("#tableFiles").click((e) => {
            if (e.target.classList.contains("previewAttachment")) {
                const idx = e.target.id.split("-").pop();
                $("#pdfPreview").attr("src", "");
                $("#viewerModalAttachment").on("show.bs.modal", function (e) {
                    let reader = new FileReader();
                    reader.onload = function (e) {
                        $("#pdfPreview").attr("src", e.target.result);
                    };
                    if(files[idx]) {
                        reader.readAsDataURL(files[idx]);
                    }
                });
                $("#viewerModalAttachment").modal("show");
            }
            if (e.target.classList.contains("deleteAttachment")) {
                const idx = e.target.id.split("-").pop();
                files.splice(idx, 1);
                console.log(idx);
                $("#tableFiles").html("");
                if (files.length < 1) {
                    $("#tableHead").addClass("invisible").attr("aria-hidden",true);
                }
                for (const file of files) {
                    pqrs.insertarFila(file);
                }
            }
        });
        
        function mostrarSpinner(){
            $('#div_spinner_pqrs').attr('aria-hidden', false).removeClass('invisible');
            $('#div_results_pqrs').attr('aria-hidden', true).addClass('invisible');
        }
        
        function ocultarSpinner(){
            $('#div_results_pqrs').attr('aria-hidden', false).removeClass('invisible');
            $('#div_spinner_pqrs').attr('aria-hidden', true).addClass('invisible');
        }
})