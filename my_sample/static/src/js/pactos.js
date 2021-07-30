odoo.define('website.pactos', function(require) {
    'use strict';
        
        const Class = require('web.Class');
        const rpc = require('web.rpc');
        const Validaciones = require('website.validations');
        const validaciones = new Validaciones();
        
        const data = {
            tipo: '',
            tipo_2:'',
            value: '',
            value_2: ''
        }
        var tabla;
        var id_tabla = 0;
        var id = '';
        
        var nombre_apellido = '';
        
        const Pactos = Class.extend({ //data, _this
            
            realizar_consulta: function(_this){
                 rpc.query({
                     route: '/consulta_pactos',
                     params: {'data': data}
                 }).then(function(response){
                     _this.mostrar_resultado(response.tramites, _this);
                 }).catch(function(e){
                    // console.log(e);
                    console.log('No se ha podido completar su solicitud');
               });
                
             },
            
            mostrar_resultado: function(tramites, _this){
                const bodyResults = $('#bodyResults');
                let htmlBody = '';
                id = $('table.tabla').attr("id");
                $("#" + id).show();
                tramites.forEach((result)=>{
                    const fecha_resolucion = result.x_origin_type[1] == 'CONVENIO' ? result.x_studio_fecha_de_resolucin : result.x_fecha_resolucion_corte;
                    //console.log(result.x_origin_type);
                    htmlBody += `
                        <tr>
                            <th scope="row">${result.x_studio_tipo_de_documento_1[1]}</th>
                            <td>${result.x_studio_documento_1}</td>
                            <td>${result.x_studio_nombres}</td>
                            <td>${result.x_studio_apellidos}</td>
                            <td>${result.x_enrollment_number}</td>
                            <td>${fecha_resolucion}</td>
                            <td>${result.x_resolution_ID[1]}</td>
                            <td>${result.x_expedition_date}</td>
                            <td>${result.x_studio_universidad_5[1]}</td>
                            <td>${result.x_studio_carrera_1[1]}</td>
                        </tr>`;
                });
                bodyResults.html('');
                bodyResults.html(htmlBody);
                _this.initDatatable();
                
                $("html, body").animate({
                    scrollTop: elem.offset().top
                }, 800);
            },
            
            initDatatable: function() {
                console.log('initDatatable');
                id = $('table.tabla').attr("id");
                tabla = $("#" + id).DataTable({
                    
                    language: {
                            "lengthMenu": "Mostrar _MENU_ registros",
                            "zeroRecords": "No se encontraron resultados",
                            "info": "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
                            "infoEmpty": "Mostrando registros del 0 al 0 de un total de 0 registros",
                            "infoFiltered": "(filtrado de un total de _MAX_ registros)",
                            "sSearch": "Filtrar:",
                            "oPaginate": {
                                "sFirst": "Primero",
                                "sLast":"Último",
                                "sNext":"Sig.",
                                "sPrevious": "Prev."
                             },
                             "sProcessing":"Procesando...",
                        },
                    //para usar los botones   
                    responsive: "true",
                    dom: 'Bfrtilp',       
                    buttons:[ 
                        {
                            extend:    'excelHtml5',
                            text:      '<i class="fa fa-file-excel-o"></i> ',
                            titleAttr: 'Exportar a Excel',
                            className: 'waves-effect waves-light btn blue white-text'
                        },
                    ]
                    
                });
            },
        });
        
        const pactos = new Pactos();
       
        // Inicio del input tipo de documento
        $('#btn_buscar_pactos').click(function(e) {
            console.log('sumado');
            id_tabla = id_tabla + 1;
            id = $('table.tabla').attr("id");
            $("#" + id).dataTable().fnDestroy();
            console.log('id anterior: ' + id);
            $('#' + id).attr("id", id_tabla.toString());
            id = $('table.tabla').attr("id");
            console.log('id nuevo: ' + id);
            e.preventDefault();
            data['tipo'] = '';
            data['tipo_2'] = '';
            data['value'] = '';
            data['value_2'] = '';
            
            data['tipo'] = $('select[name="select_search"]').val();
            
            if (data['tipo'] == "x_document"){
                data['value'] = $('input[name="buscar_documento"]').val().trim().toUpperCase();
            }
            else if (data['tipo'] == "x_names"){
                if(($('input[name="buscar_nombre"]').val().trim() != '') && (($('input[name="buscar_apellido"]').val().trim()) != '')){
                    data['tipo_2'] = "x_apellidos";
                    nombre_apellido = $('input[name="buscar_nombre"]').val().trim() + " " + $('input[name="buscar_apellido"]').val().trim();
                    data['value'] = $('input[name="buscar_nombre"]').val().trim().toUpperCase();
                    data['value_2'] = $('input[name="buscar_apellido"]').val().trim().toUpperCase();
                }
                else if (($('input[name="buscar_nombre"]').val().trim() != '') && (($('input[name="buscar_apellido"]').val().trim()) == '')){
                    nombre_apellido = $('input[name="buscar_nombre"]').val().trim();
                    data['value'] = $('input[name="buscar_nombre"]').val().trim().toUpperCase();
                }
                else if (($('input[name="buscar_nombre"]').val().trim() == '') && (($('input[name="buscar_apellido"]').val().trim()) != '')){
                    data['tipo'] = "x_apellidos";
                    nombre_apellido = $('input[name="buscar_apellido"]').val().trim();
                    data['value'] = $('input[name="buscar_apellido"]').val().trim().toUpperCase();
                }
    
            }
            else if (data['tipo'] == "x_enrollment"){
                data['value'] = $('input[name="buscar_matricula"]').val();
            }
            else if (data['tipo'] == "x_fecha_resolucion_corte"){
                data['tipo_2'] = "x_studio_fecha_de_resolucin";
                data['value'] = $('input[name="buscar_fecha_resolucion"]').val();
            }
            else if (data['tipo'] == "x_resolution_ID"){
                data['value'] = "RESOLUCION " + $('input[name="buscar_resolucion"]').val();
                data['value_2'] = "RESOLUCION PROFESIONAL " + $('input[name="buscar_resolucion"]').val();
            }
            
            pactos.realizar_consulta(pactos);
            return id_tabla;
        });
        
        
        $(document).ready(function(){
            //$( "#datepicker" ).datepicker();
            //Establece las condiciones iniciales para los campos de entrada
            $('#buscar_documento').show(); //muestro mediante id
            $('#buscar_nombre').hide(); //oculto mediante id
            $('#buscar_apellido').hide(); //oculto mediante id
            $('#buscar_matricula').hide(); //oculto mediante id
            $('#buscar_fecha_resolucion').hide(); //oculto mediante id
            $('#buscar_resolucion').hide(); //oculto mediante id
            
            $("#select_search").on( "click", function() {
                if ($('select[name="select_search"]').val() == "x_document") {
                    $('#buscar_documento').show(); //muestro mediante id
                    $('#buscar_nombre').hide(); //oculto mediante id
                    $('#buscar_apellido').hide(); //oculto mediante id
                    $('#buscar_matricula').hide(); //oculto mediante id
                    $('#buscar_fecha_resolucion').hide(); //oculto mediante id
                    $('#buscar_resolucion').hide(); //oculto mediante id
                }
                else if($('select[name="select_search"]').val() == "x_names"){
                    //alert("Por favor ingrese los nombres o los apellidos completos");
                    $('#buscar_documento').hide(); //muestro mediante id
                    $('#buscar_nombre').show(); //oculto mediante id
                    $('#buscar_apellido').show(); //oculto mediante id
                    $('#buscar_matricula').hide(); //oculto mediante id
                    $('#buscar_fecha_resolucion').hide(); //oculto mediante id
                    $('#buscar_resolucion').hide(); //oculto mediante id
                }
                else if($('select[name="select_search"]').val() == "x_enrollment"){
                    $('#buscar_documento').hide(); //muestro mediante id
                    $('#buscar_nombre').hide(); //oculto mediante id
                    $('#buscar_apellido').hide(); //oculto mediante id
                    $('#buscar_matricula').show(); //oculto mediante id
                    $('#buscar_fecha_resolucion').hide(); //oculto mediante id
                    $('#buscar_resolucion').hide(); //oculto mediante id      
                }
                else if($('select[name="select_search"]').val() == "x_fecha_resolucion_corte"){
                    $('#buscar_documento').hide(); //muestro mediante id
                    $('#buscar_nombre').hide(); //oculto mediante id
                    $('#buscar_apellido').hide(); //oculto mediante id
                    $('#buscar_matricula').hide(); //oculto mediante id
                    $('#buscar_fecha_resolucion').show(); //oculto mediante id
                    $("#datepicker").datepicker();
                    $('#buscar_resolucion').hide(); //oculto mediante id
                }
                else if($('select[name="select_search"]').val() == "x_resolution_ID"){
                    $('#buscar_documento').hide(); //muestro mediante id
                    $('#buscar_nombre').hide(); //oculto mediante id
                    $('#buscar_apellido').hide(); //oculto mediante id
                    $('#buscar_matricula').hide(); //oculto mediante id
                    $('#buscar_fecha_resolucion').hide(); //oculto mediante id
                    $('#buscar_resolucion').show(); //oculto mediante id
                }
                else{
                    $('#buscar_documento').hide(); //muestro mediante id
                    $('#buscar_nombre').hide(); //oculto mediante id
                    $('#buscar_apellido').hide(); //oculto mediante id
                    $('#buscar_matricula').hide(); //oculto mediante id
                    $('#buscar_fecha_resolucion').hide(); //oculto mediante id
                    $('#buscar_resolucion').hide(); //oculto mediante id
                }
            });
        });
    
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
            dateFormat: 'yy/mm/dd',
            firstDay: 1,
            isRTL: false,
            showMonthAfterYear: false,
            yearSuffix: ''
        };
        $.datepicker.setDefaults($.datepicker.regional['es']);
        $("[name=buscar_fecha_resolucion]").datepicker({
            maxDate: '0',
            dateFormat: "yy-mm-dd",
            changeMonth: true,
            changeYear: true,
            yearRange: '-80:+0'
        });
        
        
    })