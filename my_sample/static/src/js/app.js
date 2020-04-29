odoo.define('website.website', function(require) {
    
    console.log('OK')
    var Class = require('web.Class');
    var rpc = require('web.rpc');
    
    var MyClass = Class.extend({
        tramites: function(data) {
            let origen = data.origen;
            (!origen) ? origen = '' : origen = `?form=${data.origen}`; 
            return rpc.query({
                route: '/website_form/validar_tramites',
                params: {'x_document': data.doc, 'x_document_type_ID': data.doc_type}
            }).then(function(response){
                console.log(response);
                if(response.convenio){
                    $(location).attr('href','/convenios/cliente/'+ response.id);
                } else {
                    if(response.id){
                        $(location).attr('href','/cliente/'+ response.id +'/tramites');
                    }else{
                        $(location).attr('href','/cliente' + origen);
                    }
                }
            })
        },
        convenios: function(univ_id) {
            return rpc.query({
                route: '/website_form/buscar_convenios',
                params: {'univ_id': univ_id}
            }).then(function(response){
                if(response.id){
                    $(location).attr('href','/convenios/'+ response.id);
                }else{
                    $('#message').removeClass('invisible');
                    setTimeout(()=>{ 
                        $('#buscar_convenios').val('');
                        $('#message').addClass('invisible');
                    },1500);
                }
            })
        },
        archivo_src: function(data, _this) {
            return rpc.query({
                route: '/procesar_archivo',
                params: {'data': data}
            }).then(function(response){
                console.log(response);
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
                        _this.agregar_fila(i, r);
                    })
                }

            })
        },
        agregar_fila: function (i, data) {
            let cant = parseInt(i) + 1;
            let htmlTags = '<tr id="row-'+ cant +'"><th scope="row">' + cant + '</th>';
            
            for (let d in data){
                let disabled = 'disabled=""';
                if(data[d].clase == 'invalido'){
                    disabled = '';
                }
                htmlTags += '<td><input id="'+d+'-'+cant+'" '+ disabled +' value="'+ data[d].valor +
                            '" type="text" class="form-control '+ data[d].clase +'" /></td>';
            }
            htmlTags += '</tr>';
            $('#resultados').append(htmlTags);
        },
        guardar_registros: function(registros, data, _this) {
            const Toast = Swal.mixin({
                toast: true,
                showConfirmButton: true,
                timer: 3000,
                timerProgressBar: true,
                showLoaderOnConfirm: true,
                preConfirm: () => {
//                     location.replace('/convenios');
                },
                onOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer)
                    toast.addEventListener('mouseleave', Swal.resumeTimer)
                }
            });
            Swal.fire({
                toast: true,
                title: `${registros.length} Registros enviados`,
                showConfirmButton: true,
                showLoaderOnConfirm: true,
                  preConfirm: (response) => {
                    return rpc.query({
                        route: '/guardar_registros',
                        params: {'registros': registros, 'data': data}
                    }).then(function(response){
                        console.log(response);
                        if (!response.ok) {
                          throw new Error(response.error)
                        }
                        return response
                    }).catch(error => {
                        Swal.showValidationMessage(
                          `${error}`
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
    });
    
    var my_object = new MyClass();
    let hoy = new Date();
    let mes = hoy.getMonth() + 2;
    if (mes < 10) { mes = `0${mes}` };
    let fecha_minima_grado = `${hoy.getFullYear()}-${mes}-${hoy.getDate()}`;
    if(location.href.indexOf('grado') == -1){
        $('#fecha_grado').attr('min', fecha_minima_grado);
    }
    
    $('#verificar').click(function(e){
        e.preventDefault();
        let params = new URLSearchParams(location.search);
        let data = { doc:'', doc_type:'', origen:'' }
        data.doc = $('#doc').val();
        data.doc_type = $('#doc_type').val();
        data.origen = params.get('form');
        my_object.tramites(data);
    })
    
    $('#buscar_convenios').change(function(e){
        e.preventDefault();
        let univ = $('#buscar_convenios').val();
        my_object.convenios(univ);
    })
    
    $('#cargar_csv').on("submit", async function(e){
        e.preventDefault();
        let archivo_csv = $('#archivo_csv')[0].files[0];
        let fecha_grado = $('#fecha_grado').val();
        if(fecha_grado == ''){
            mostrar_helper('fecha_grado');
        }
        if(profesion == ''){
            mostrar_helper('profesion');
        }
        if(archivo_csv == undefined){
            mostrar_helper('archivo_csv');
        } else {
            $('#procesar_archivo').attr('disabled','');
            const toBase64 = file => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
            });
            const archivo = await toBase64(archivo_csv).catch(e => Error(e));
               if(archivo instanceof Error) {
                  console.log('Error: ', archivo.message);              
                return;
            }
            let data = {
                fecha_grado,
                archivo
            }
            my_object.archivo_src(data, my_object);
        }   
    })
    
    $('#guardar_resultados').click(async function(e){
        e.preventDefault();
        let registros = [];
        let grado = '';
        let convenio = parseInt($('#convenio').attr('name'));
        let profesion = parseInt($('#profesion').val());
        let universidad = parseInt($('#universidad').attr('name'));
        let fecha = $('#fecha_grado').val();
        if(location.href.indexOf('grado')!=-1){
            grado = parseInt($('#grado').text());
        }
        let rows = $('#resultados tr');
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
        console.log(data,registros);
        my_object.guardar_registros(registros, data, my_object);

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
            icon: 'warning',
            confirmButtonText: 'Confirmar',
            cancelButtonText: `&nbsp;Cancelar&nbsp;`
        });
    });
    
    function mostrar_helper(campo){
        $('#'+campo).addClass('invalido');
        $('#help_text').removeClass('invisible');
        setTimeout(()=>{ 
            $('#'+campo).removeClass('invalido');
            $('#help_text').addClass('invisible');
        },1500);
    }
    
})