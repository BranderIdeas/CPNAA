odoo.define('website.validations', function(require) {
    
    console.log('VALIDATIONS')
    var Class = require('web.Class');
    var rpc = require('web.rpc');
    
    // Configuración de las alertas
    const Toast = Swal.mixin({
        toast: true,
        position: 'top',
        showConfirmButton: true,
        timer: 3000,
        timerProgressBar: true,
        onOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    })
    
    var Validaciones = Class.extend({
        validar_input_resultados: function (entrada, tipo, elem_id, _this) {
            let esPA = false;
            if (entrada.length < 1) {
                if (tipo != 'email') {
                    let tipo_mostrar = _this.tipoMostrar(tipo);
                    _this.mostrar_alerta_vacio(tipo_mostrar);
                    _this.colocar_borde(elem_id, false);
                    return;
                }
            }
            switch (tipo) {
                case 'document_type':
                    _this.colocar_borde(elem_id, _this.validar_tipo_doc(entrada, elem_id, _this));
                    break;
                case 'document':
                    let tipo_doc = $('#'+elem_id).parent().prev().children().val();
                    if(tipo_doc == 'PA' || tipo_doc == 'PA.'){
                        _this.colocar_borde(elem_id, _this.validar_alfanum(entrada, pasaporte));
                    }else{
                        _this.colocar_borde(elem_id, _this.validar_solo_numeros(entrada));
                    }
                    break;
                case 'name':
                case 'lastname':
                    _this.colocar_borde(elem_id, _this.validar_solo_letras(entrada));
                    break;
                case 'gender':
                    _this.colocar_borde(elem_id, _this.validar_genero(entrada));
                    break;
                case 'email':
                    _this.colocar_borde(elem_id, _this.validar_email(entrada));
                    break;
                default:
                    break;
            }
        },
        colocar_borde: function (elem_id, correcto){
            if(correcto === -1){
                $('#'+elem_id).addClass('warning')
                    .removeClass('invalido')
                    .removeClass('valido');
            }else if(correcto){
                $('#'+elem_id).addClass('valido')
                    .removeClass('invalido')
                    .removeClass('warning');
            } else {
                $('#'+elem_id).addClass('invalido')
                    .removeClass('valido')
                    .removeClass('warning')
                    .focus();
            }
        },
        mostrar_alerta_vacio: function (campo) {
            Toast.fire({
                icon: 'error',
                title: `<br/>El ${campo} no puede estar vacio.<br/><br/> `,
                confirmButtonText: 'Ocultar',
            })
            return false;
        },
        validar_tipo_doc: function (entrada, elem_id, _this) {
            let tipos_validos = ['CC', 'CE', 'PA', 'C.C.', 'C.E.', 'PA.', 'cc', 'ce', 'pa'];
            let doc_elem = $('#'+elem_id).parent().next().children().attr('id');
            let num_doc = $('#'+elem_id).parent().next().children().val();
            console.log(doc_elem, num_doc)
            if (!tipos_validos.some(t => t == entrada)) {
                Toast.fire({
                    icon: 'error',
                    title: `<br/>No es válido, por favor ingrese: "CC" para Cédula de Ciudadanía,
                           "CE" para Cédula de Extranjería o "PA" para Pasaporte.<br/><br/> `,
                    confirmButtonText: 'Ocultar',
                })
                return false;
            } else {
                if (entrada == 'CC' || entrada == 'C.C.') {
                    console.log('CÉDULA DE CIUDADANÍA');
                    _this.colocar_borde(doc_elem, _this.validar_solo_numeros(num_doc));
                }
                if (entrada == 'CE' || entrada == 'C.E.') {
                    console.log('CÉDULA DE EXTRANJERÍA');
                    _this.colocar_borde(doc_elem, _this.validar_solo_numeros(num_doc));
                }
                if (entrada == 'PA' || entrada == 'PA.') {
                    console.log('PASAPORTE');
                    _this.colocar_borde(doc_elem, _this.validar_alfanum(num_doc, 'pasaporte'));
                }
                return true;
            }
        },
        validar_celular: function (entrada) {
            let regex = /^[0-9]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten números.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else if(entrada.length < 10){
                Toast.fire({
                    title: `<br/>No es válido, mínimo 10 caracteres para el télefono célular.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
            }else{
                return true;
            }
        },
        validar_solo_letras: function (entrada) {
            let regex = /^[a-zA-ZÑñ ]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten letras.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return true;
            }
        },
        validar_direccion: function (entrada) {
            let regex = /^[a-zA-Z0-9\-#Ññ ]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten letras, números y los caracteres # - <br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return true;
            }
        },
        validar_alfanum: function (entrada, text) {
            let regex = /^[0-9a-zA-Z]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten números y letras para ${text}.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return -1;
            }
        },
        validar_telefono: function (entrada) {
            let regex = /^[0-9a-zA-Z ]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten números y letras para el télefono fijo.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else if(entrada.length < 7){
                Toast.fire({
                    title: `<br/>No es válido, mínimo 7 caracteres para el télefono fijo.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
            }else{
                return -1;
            }
        },
        validar_genero: function (entrada) {
            let generos_validos = ['M', 'F', 'm', 'f'];
            if (!generos_validos.some(t => t == entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, por favor ingrese "M" para Masculino o "F" para Femenino.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            } else {
                if (entrada == 'M' || entrada == 'm') {
                    console.log('MASCULINO');
                }
                if (entrada == 'F' || entrada == 'f') {
                    console.log('FEMENINO');
                }
                return true;
            }
        },
        validar_email: function (entrada) {
            let regex = /^[a-zA-ZÑñ0-9.&_-]+@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
            if (entrada.length == 0) {
                entrada = 'N/A';
                return true;
            } else {
                if (!regex.test(entrada)) {
                    Toast.fire({
                    title: `<br/>No es válido, por favor ingrese una dirección de correo electrónico válida.<br/><br/> `,
                        icon: 'error',
                        confirmButtonText: 'Ocultar',
                    })
                    return false;
                }else{
                    return true;
                }
            }
        },
        validar_email_unico: function(cadena){
            return rpc.query({
                route: '/get_email',
                params: {'cadena': cadena}
            }).then(function(response){
                if (response.email_exists) {
                    Toast.fire({
                    title: `<br/>El correo electrónico ingresado ya existe.<br/><br/> `,
                        icon: 'error',
                        confirmButtonText: 'Ocultar',
                    })
                }
                return !response.email_exists;
            }).catch(function(err){
                console.log(err);
            });
        },
        tipoMostrar: function (tipo) {
            switch (tipo) {
                case 'tipo_doc':
                    return 'tipo de documento';
                case 'numeros':
                    return 'documento';
                case 'letras':
                    return 'nombre y apellido';
                case 'genero':
                    return 'genero';
                case 'email':
                    return 'correo electronico';
                default:
                    return 'campo';
            }
        },
        alert_error_toast: function (text) {
            Toast.fire({
                title: `<br/>${text}<br/><br/> `,
                icon: 'error',
                confirmButtonText: 'Ocultar',
            })
        },
        validar_en_BD: function(entrada, elem_id){

            let nro_reg = elem_id.charAt(elem_id.length - 1);
            let input_tipo = $('#a_document_type-'+nro_reg);
            let input_nro_doc = $('#b_document-'+nro_reg);
            let profesion_id = $('#profesion').val();
            
            let tipo_doc = input_tipo.val();
            let numero_doc = input_nro_doc.val();
            let data = { tipo_doc, numero_doc, profesion_id };
            
            if(input_tipo.hasClass('invalido') && input_nro_doc.hasClass('invalido')){
                return;
            } else {
                console.log(data);
                return rpc.query({
                    route: '/validar_documento_bd',
                    params: {'data': data}
                }).then(function(response){
                    if(!response.ok){
                        Toast.fire({
                        title: `<br/>${response.error}<br/>`,
                            icon: 'error',
                            confirmButtonText: 'Ocultar',
                        })
                    }
                })
            }
            
        }
    });

    var validaciones = new Validaciones();
    $('#resultados').change((e) => {
        let entrada = e.target.value;
        let elem_id = e.target.id;
        let tipo = elem_id.split('-')[0];
        tipo = tipo.substring(2);
        validaciones.validar_input_resultados(entrada, tipo, elem_id, validaciones);
        if(elem_id.indexOf('email') != -1 && entrada.length < 1){ $('#'+elem_id).val('N/A') };
//         if(elem_id.indexOf('document') != -1){
//             validaciones.validar_en_BD(entrada, elem_id);
//         };
        $('#'+elem_id).val($('#'+elem_id).val().toUpperCase());
    });
    
    return Validaciones; // ~ Exports class

})