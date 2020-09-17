odoo.define('website.convenios', function(require) {

    const Class = require('web.Class');
    const rpc = require('web.rpc');
    const Validaciones = require('website.validations');
    const validaciones = new Validaciones();
    const Toast = Swal.mixin({
                toast: true,
                showConfirmButton: true,
                timer: 3000,
                timerProgressBar: true,
                showLoaderOnConfirm: true,
                confirmButtonColor: '#c8112d',
                preConfirm: () => {},
                onOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer)
                    toast.addEventListener('mouseleave', Swal.resumeTimer)
                }
            });
    
    const Convenios = Class.extend({
        get_pdf: function(){
            let preHtml = `<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word'
                           xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export HTML To Doc</title></head><body>`;
            let postHtml = "</body></html>";
            let html = preHtml + document.getElementById('exportContent').innerHTML + postHtml;
            let blob = new Blob(['\ufeff', html], {
                type: 'application/msword'
            });
            // Specify link url
            let url = 'data:application/vnd.ms-word;charset=utf-8,' + encodeURIComponent(html);
            // Specify file name
            let filename = 'archivoGuiaDefinitivoGraduandos.doc';
            // Create download link element
            let downloadLink = document.createElement("a");
            document.body.appendChild(downloadLink);
            if (navigator.msSaveOrOpenBlob) {
                navigator.msSaveOrOpenBlob(blob, filename);
            } else {
                // Create a link to the file
                downloadLink.href = url;
                // Setting the file name
                downloadLink.download = filename;
                //triggering the function
                downloadLink.click();
            }
            document.body.removeChild(downloadLink);
        },
        archivo_src: function(data, _this) {
            return rpc.query({
                route: '/procesar_archivo',
                params: {'data': data}
            }).then(function(response){
                if(!response.ok){
                    const ToastCerrar = Swal.mixin({
                        toast: true,
                        showConfirmButton: true,
                        showLoaderOnConfirm: true,
                        preConfirm: () => {
                            $('#procesar_archivo').removeAttr('disabled');
                        },
                    })
                    ToastCerrar.fire({
                        title: `<br/>${response.message}<br/><br/> `,
                        icon: 'error',
                        confirmButtonText: 'Cerrar',
                    });
                } else {
                    $('#modal-resultado-csv').modal({ keyboard: false, backdrop: 'static' });
                    $('#modal-resultado-csv').modal('show');
                    $('#resultados').html('');
                    response.results.forEach((r, i)=>{
                        if(r){
                            _this.agregar_fila(i, r);
                        }
                    })
                }

            })
        },
        agregar_fila: function (i, data) {
            let cant = parseInt(i) + 1;
            let htmlTags = '<tr id="row-'+ cant +'"><th scope="row">' + cant + '</th>';
            
            for (let d in data){
                let disabled = '';
                if(d == 'e_fecha_grado'){
                    disabled = 'disabled="true"';
                }
                htmlTags += '<td><input id="'+d+'-'+cant+'" '+ disabled +' value="'+ data[d].valor.trim() +
                            '" type="text" class="form-control '+ data[d].clase +'" /></td>';
            }
            htmlTags += '</tr>';
            $('#resultados').append(htmlTags);
            let row = $('#resultados').find(`#row-${cant}`).find('input')[1];
            validaciones.validar_en_BD(row.id, validaciones);
        },
        hay_duplicados: function(cantidad){
            let campos = [];
            let repetidos = [];
            for (let i = 0; i < cantidad; i++) {
                let tip_doc = $('#a_document_type-'+(i+1)).val();
                let num_doc = $('#b_document-'+(i+1)).val();
                let row = {
                    tip_doc,
                    num_doc,
                    posicion: i+1
                }
                campos.push(row);
            }
            for (let i = 0; i < campos.length; i++) {
                for (let j = 0; j < campos.length; j++) {
                    if(i != j){
                        if (campos[i].tip_doc === campos[j].tip_doc && campos[i].num_doc === campos[j].num_doc){
                            repetidos.push(campos[i]);
                        }
                    }
                }
            }
            if(repetidos.length > 0){
                let rows = [];
                repetidos.forEach(row => {
                    $('#a_document_type-'+(row.posicion)).removeClass('valido').addClass('invalido');
                    $('#b_document-'+(row.posicion)).removeClass('valido').addClass('invalido');
                    rows.push(row.posicion);
                })
                validaciones.alert_error_toast('Existen documentos repetidos en la lista, filas: '+rows, 'top')
                return true;
            }else{
                return false;
            }
        },
        guardar_registros: function(registros, data, _this) {
            Swal.fire({
                toast: true,
                title: `¿Enviar ${registros.length} registros?`,
                showCancelButton: true,
                showLoaderOnConfirm: true,
                confirmButtonText: 'Confirmar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#c8112d',
                preConfirm: (response) => {
                    return rpc.query({
                        route: '/guardar_registros',
                        params: {'registros': registros, 'data': data}
                    }).then(function(response){
                        if (!response.ok) {
                          throw new Error(response.error)
                        }
                        return response
                    }).catch(error => {
                        Swal.showValidationMessage(
                          `Error: ${error.message.data.message}`
                        )
                    })
                },
            }).then((result) => {
                if (result.value) {
                    Toast.fire({
                       title: `${result.value.message}`,
                    })
                    if(result.value.ok){
                        $(location).attr('href','/convenios/'+result.value.universidad+'/detalle_grado/'+result.value.grado);
                    }
                }
            })
        },
        toBase64: async function(file){
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
            });
        },
        mostrar_helper: function(campo){
            let elem = $('#'+campo);
            if(campo == 'fecha_grado'){
                elem = $('[name=fecha_grado]');
            }
            elem.addClass('invalido');
            $('#help_text').removeClass('invisible');
            setTimeout(()=>{ 
                elem.removeClass('invalido');
                $('#help_text').addClass('invisible');
            },1500);
        },
        validar_extension: function(id_elem, ext_valid){
            let archivo_seleccionado = $('#'+id_elem)[0].files[0]
            if(archivo_seleccionado != undefined){
                let extension = archivo_seleccionado.name.split('.');
                extension = extension[extension.length-1];
                if(extension != ext_valid){
                    $('#'+id_elem)[0].files[0] = undefined;
                    $('#'+id_elem).val("");
                    Toast.fire({
                        icon: 'error',
                        title: `<br/>Solo archivos con extensión .${ext_valid}, Los archivos .${extension} no son permitidos.<br/><br/> `,
                        confirmButtonText: 'Ocultar',
                    })
                }
            }
        },
        subir_definitivo_pdf: function(data){
            Swal.fire({
                toast: true,
                title: `¿Confirmar envio de listado definivo de graduandos?`,
                showConfirmButton: true,
                showCancelButton: true,
                confirmButtonText: 'Confirmar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#c8112d',
                showLoaderOnConfirm: true,
                  preConfirm: (response) => {
                    $('#btn_pdf_graduandos').attr('disabled','');
                    return rpc.query({
                        route: '/guardar_pdf_definitivo',
                        params: {'data': data}
                    }).then(function(response){
                        if (!response.ok) {
                          throw new Error(response.error)
                        }
                        return response
                        }).catch(error => {
                            Swal.showValidationMessage(
                              `Error: ${error}`
                            )
                        })
                  },
            }).then((result) => {
                if (result.value) {
                    Toast.fire({
                       title: `${result.value.message}`,
                    })
                    if(result.value.ok){
                        $(location).attr('href','/convenios/'+result.value.universidad+'/detalle_grado/'+result.value.grado);
                    }
                }
            })
        },
        subir_actas_pdf: function(data){
            Swal.fire({
                toast: true,
                title: `¿Confirmar envio de Archivo pdf de Actas de Grado?`,
                showConfirmButton: true,
                showCancelButton: true,
                confirmButtonText: 'Confirmar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#c8112d',
                showLoaderOnConfirm: true,
                  preConfirm: (response) => {
                    $('#btn_pdf_graduandos').attr('disabled','');
                    return rpc.query({
                        route: '/guardar_pdf_actas',
                        params: {'data': data}
                    }).then(function(response){
                        if (!response.ok) {
//                           console.log(response);
                          throw new Error(response.error.message)
                        }
                        return response
                        }).catch(error => {
                            Swal.showValidationMessage(
                              `Error: ${error.message}`
                            )
                        })
                  },
            }).then((result) => {
                if (result.value) {
                    Toast.fire({
                       title: `${result.value.message}`,
                    })
                    if(result.value.ok){
                        $(location).attr('href','/convenios/'+result.value.universidad+'/detalle_grado/'+result.value.grado);
                    }
                }
            })
        },
        exportar_csv: function () {
            let filename = 'usuariosConPago.csv';
            let csv = [];
            let rows = document.querySelectorAll('#pagaron tr');
            for (let i = 0; i < rows.length; i++) {
                let row = [],
                    cols = rows[i].querySelectorAll('td, th');
                for (let j = 0; j < cols.length; j++)
                    row.push(cols[j].innerText);
                csv.push(row.join(','));
            }
            csv = csv.join('\n');
            // CSV file
            let csvFile = new Blob(['\ufeff', csv], { type: "text/csv" });
            // Specify link url
            let url = 'data:text/csv;charset=utf-8,%EF%BB%BF' + encodeURIComponent(csv);
            // Create download link element
            let downloadLink = document.createElement('a');
            document.body.appendChild(downloadLink);
            if (navigator.msSaveOrOpenBlob) {
                navigator.msSaveOrOpenBlob(blob, filename);
            } else {
                // Create a link to the file
                downloadLink.href = url;
                // Setting the file name
                downloadLink.download = filename;
                //triggering the function
                downloadLink.click();
            }
            document.body.removeChild(downloadLink);
        }
    });
    
    var convenios = new Convenios();
   
    $('#getPdf').click(function(e){
        e.preventDefault();
        convenios.get_pdf();
    })
    
    // Datos para el datepicker
    let minDate= $("[name=fecha_grado]").data('min');
    let maxDate= $("[name=fecha_grado]").data('max');
    $("[name=fecha_grado]").datepicker({
        minDate: minDate,
        maxDate: maxDate,
        dateFormat: "dd-mm-yy",
        changeMonth: true,
        changeYear: true,
    });

    $('#procesar_archivo').click(async function(e){
        e.preventDefault();
        let esValido = true;
        let archivo_csv = $('#archivo_csv')[0].files[0];
        let profesion = $('#profesion').val();
        let fecha_grado = $('[name=fecha_grado]').val();
        if(fecha_grado == ''){
            convenios.mostrar_helper('fecha_grado');
            esValido = false;
        }
        if(profesion == ''){
            convenios.mostrar_helper('profesion');
            esValido = false;
        }
        if(archivo_csv == undefined){
            convenios.mostrar_helper('archivo_csv');
            esValido = false;
        }
        if(esValido){
            $('#procesar_archivo').attr('disabled','');
            const archivo = await convenios.toBase64(archivo_csv).catch(e => Error(e));
               if(archivo instanceof Error) {
                  console.log('Error: ', archivo.message);              
                return;
            }
            let data = {
                fecha_grado,
                archivo
            }
            convenios.archivo_src(data, convenios);
        }   
    })
    
    $('#guardar_resultados').click(async function(e){
        e.preventDefault();
        let registros = [];
        let grado = '';
        let convenio = parseInt($('#convenio').attr('name'));
        let profesion = parseInt($('#profesion').val());
        let universidad = parseInt($('#universidad').attr('name'));
        let fecha = $('[name=fecha_grado]').val().split('-').reverse().join('-');
        if(location.href.indexOf('grado')!=-1){
            grado = parseInt($('#grado').attr('name'));
        }
        let rows = $('#resultados').find('tr');
        if(convenios.hay_duplicados(rows.length)){
            return;
        }
        for(let i = 0; i < rows.length; i++){
            let datos = {};
            let row = $('#'+rows[i].id).children('td');
            for (let j = 0; j < row.length; j++){
                let input = row[j].children[0];
                if(input.classList.contains('valido') || input.classList.contains('warning')){
                    let key = input.id.split('-')[0];
                    datos[key] = input.value;
                }
            }
            if(Object.values(datos).length == row.length){
                registros.push(datos);
            }
        }
        let data = { convenio, profesion, universidad, grado, fecha };
        if(registros.length > 0){
            convenios.guardar_registros(registros, data, convenios);
        }else{
            Toast.fire({
                icon: 'error',
                title: `Ningún registro válido para guardar.`,
                confirmButtonText: 'Ocultar',
            })
        }
    })
       
    $('#cerrar_resultados').click((e) => {
        const ToastCerrar = Swal.mixin({
            toast: true,
            showConfirmButton: true,
            showCancelButton: true,
            showLoaderOnConfirm: true,
              preConfirm: () => {
                location.reload();
              },
        })
        ToastCerrar.fire({
            title: `<br/>¿Cerrar sin guardar los registros?<br/><br/> `,
            icon: 'question',
            confirmButtonText: 'Confirmar',
            confirmButtonColor: '#c8112d',
            cancelButtonText: `&nbsp;Cancelar&nbsp;`
        });
    });
    
    $('#archivo_csv').on('change', (e) => {
        convenios.validar_extension('archivo_csv', 'csv');        
    });
    
    $('#pdf_graduandos').on('change', (e) => {
        convenios.validar_extension('pdf_graduandos', 'pdf');        
    });
    
    $('#btn_csv_pagaron').on('click', (e) => {
        convenios.exportar_csv();        
    });
    
    $('#btn_pdf_graduandos').on('click', async (e) => {   
        e.preventDefault();
        let archivo_graduandos = $('#pdf_graduandos')[0].files[0];
        let convenio = parseInt($('#convenio').attr('name'));
        let universidad = parseInt($('#universidad').attr('name'));
        if(archivo_graduandos == undefined){
            convenios.mostrar_helper('pdf_graduandos');
        } else {
            const archivo_pdf = await convenios.toBase64(archivo_graduandos).catch(e => Error(e));
               if(archivo_pdf instanceof Error) {
                  console.log('Error: ', archivo_pdf.message);              
                return;
            }
            let grado_id = $('#grado').data('grado-id');
            let data = {
                grado_id,
                archivo_pdf,
                universidad,
                convenio
            }
            convenios.subir_definitivo_pdf(data);
        }  
    });
    
    $('#archivo_pdf_actas').change((ev) => {
        const input = $('#archivo_pdf_actas');
        const file = input[0].files[0];
        const ext = input.val().split('.').pop();
        if(file){
            if (file.size/1024/1024 > 5 || ext != 'pdf'){
                validaciones.alert_error_toast( "El documento debe ser formato PDF y no exceder los 5mb.", 'top');
                input.val('');
                return;
            }         
        }
    })
    
    $('#btn_archivo_actas').on('click', async (e) => {   
        e.preventDefault();
        let archivo_pdf_actas = $('#archivo_pdf_actas')[0].files[0];
        let convenio = parseInt($('#convenio').attr('name'));
        let universidad = parseInt($('#universidad').attr('name'));
        if(archivo_pdf_actas == undefined){
            convenios.mostrar_helper('archivo_pdf_actas');
        } else {
            const archivo_pdf = await convenios.toBase64(archivo_pdf_actas).catch(e => Error(e));
               if(archivo_pdf instanceof Error) {
                  console.log('Error: ', archivo_pdf.message);              
                return;
            }
            let grado_id = $('#grado').data('grado-id');
            let data = {
                grado_id,
                archivo_pdf,
                universidad,
                convenio
            }
            convenios.subir_actas_pdf(data);
        }  
    });

    
})