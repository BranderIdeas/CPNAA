odoo.define('website.denuncia', function(require) {
'use strict';
    
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    const Validaciones = require('website.validations');
    const validaciones = new Validaciones();
    
    let files = [];
    const Denuncia = Class.extend({ //data, _this
        insertarFila: function(file) {
            const size = (Number(file.size) / 1024 / 1024).toFixed(2);
            const ext = file.name.split(".").pop();
            $("#tableHead").removeClass("invisible").attr("aria-hidden", "false");
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
				$("#tableHead").addClass("invisible").attr("aria-hidden", "true");
			}
			for (const file of files) {
				denuncia.insertarFila(file);
			}
		}
	});
    
	$("#btn-registrar").click((e) => {
		let formData = new FormData();
		for (const file of files) {
			formData.append(file.name, file);
		}
		for (const val of formData.values()) {
			console.log(val);
		}
	});

    
})