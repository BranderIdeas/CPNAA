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
                                    window.top.location.href = 'https://www.cpnaa.gov.co/';
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
        }
    })
    
    const denuncia = new Denuncia();
    
	$("#x_evidence_files").change((e) => {
		files = [...files, ...e.target.files];
		$("#tableFiles").html("");
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
		console.log(files);
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
    
    function mostrarSpinner(){
        $('#div_spinner_denuncia').attr('aria-hidden', false).removeClass('invisible');
        $('#div_results_denuncia').attr('aria-hidden', true).addClass('invisible');
    }
    
    function ocultarSpinner(){
        $('#div_results_denuncia').attr('aria-hidden', false).removeClass('invisible');
        $('#div_spinner_denuncia').attr('aria-hidden', true).addClass('invisible');
    }
    
})