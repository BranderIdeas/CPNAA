odoo.define('website.validations', function(require) {
    
    console.log('VALIDACIONES')
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    
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
    
    const Validaciones = Class.extend({
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
                        _this.colocar_borde(elem_id, _this.validar_alfanum(entrada, 'pasaporte'));
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
            const tipos_validos = ['CC', 'CE', 'PA', 'C.C.', 'C.E.', 'PA.', 'cc', 'ce', 'pa'];
            const doc_elem = $('#'+elem_id).parent().next().children().attr('id');
            const num_doc = $('#'+elem_id).parent().next().children().val();
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
                    _this.colocar_borde(doc_elem, _this.validar_solo_numeros(num_doc));
                }
                if (entrada == 'CE' || entrada == 'C.E.') {
                    _this.colocar_borde(doc_elem, _this.validar_solo_numeros(num_doc));
                }
                if (entrada == 'PA' || entrada == 'PA.') {
                    _this.colocar_borde(doc_elem, _this.validar_alfanum(num_doc, 'pasaporte'));
                }
                return true;
            }
        },
        validar_celular: function (entrada) {
            const regex = /^[0-9]*$/;
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
        validar_solo_numeros: function (entrada) {
            const regex = /^[0-9]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten números.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return true;
            }
        },
        validar_solo_letras: function (entrada) {
            const regex = /^[a-zA-ZÑñ ]*$/;
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
            const regex = /^[^\/&<>"';%]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, evite los siguientes caracteres ;'\&<>"% <br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return true;
            }
        },
        validar_alfanum: function (entrada, text) {
            const regex = /^[0-9a-zA-Z]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>No es válido, solo se permiten números y letras para ${text}, no ingreses caracteres especiales.<br/><br/> `,
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
            if(location.href.indexOf('/edicion/') != -1){
                return true;
            }
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
                    return response.ok;
                }else{
                    return response.ok;
                }
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
        validar_en_BD: function(elem_id){

            let nro_reg = elem_id.charAt(elem_id.length - 1);
            let input_tipo = $('#a_document_type-'+nro_reg);
            let input_nro_doc = $('#b_document-'+nro_reg);
            let profesion_id = $('#profesion').val();
            
            let tipo_doc = input_tipo.val();
            let numero_doc = input_nro_doc.val();
            let data = { tipo_doc, numero_doc, profesion_id };
            
            return rpc.query({
                route: '/validar_documento_bd',
                params: {'data': data}
            }).then(function(response){
//                 console.log(response);
                if(!response.ok){
                    Toast.fire({
                        title: `<br/>${response.error}<br/><br/>`,
                            icon: 'error',
                            confirmButtonText: 'Ocultar',
                    });
                    input_tipo.removeClass('valido').addClass('invalido');
                    input_nro_doc.removeClass('valido').addClass('invalido');
                }else{
                    input_tipo.removeClass('invalido').addClass('valido');
                    input_nro_doc.removeClass('invalido').addClass('valido');
                }
            })
        },
        validar_duplicados: function validar_duplicados(){
            console.log('ok');
        },
        validar_formatos: async function validar_formatos(e){
            let elem = e.target;
            if(elem.classList.contains('o-letters')){
                let valid = validaciones.validar_solo_letras(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = elem.value.trim().toUpperCase().replace(/\s\s+/g, ' ');
                }            
            } 
            if (elem.classList.contains('v-celular')){
                let valor = elem.value.trim().replace(/\s+/g, '');
                let valid = validaciones.validar_celular(valor);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = valor;
                }
            } 
            if (elem.classList.contains('v-email')){
                let valor = elem.value.trim().toLowerCase().replace(/\s+/g, '');
                let valid = validaciones.validar_email(valor);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    valid = await validaciones.validar_email_unico(valor)
                    if(!valid){
                        elem.classList.add('is-invalid');
                        elem.focus();
                    }else{
                        elem.classList.remove('is-invalid');
                        elem.value = valor;
                    }
                }
                return valid;
            } 
            if (elem.classList.contains('v-address')){
                let valid = validaciones.validar_direccion(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = elem.value.trim().toUpperCase().replace(/\s\s+/g, ' ');
                }
            } 
            if (elem.classList.contains('v-alfanum')){
                let valor = elem.value.trim().toUpperCase().replace(/\s+/g, '');
                let valid = validaciones.validar_alfanum(valor, 'el documento Ministerio de Educación');
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = valor;
                }
            } 
            if (elem.classList.contains('v-telefono')){
                if(elem.value.length > 0){
                    let valid = validaciones.validar_telefono(elem.value);
                    if(!valid){
                        elem.classList.add('is-invalid');
                        return valid;
                    }else{
                        elem.classList.remove('is-invalid');
                        elem.value = elem.value.trim().toUpperCase();
                    }
                }
            }

            return true;

        },
        validar_formulario: async function validar_formulario(){
            let formSample = document.forms[0];
            let elems = formSample.elements;
            let formValido = true;
            let errores = [];
            for (let i = 0; i < elems.length; i++) {
    //             if(elems[i].name === 'x_grade_date'){
    //                 elems[i].value = elems[i].value.split('-').reverse().join('-');
    //             }
                if(elems[i].name != ''){
                    if(elems[i].classList.contains('i_required') && elems[i].type != 'file'){
                        if(elems[i].value == ''){
                            elems[i].classList.add('is-invalid');
//                             elems[i].focus();
                            errores.push(elems[i].name);
                            if(elems[i].name == 'x_institution_ID'){
                                $('#universidades').addClass('is-invalid');
//                                 $('#universidades').focus();
                                errores.push(elems[i].name);
                                formValido= false;
                            }
                            if(elems[i].name == 'x_institute_career'){
                                $('#carreras').addClass('is-invalid');
//                                 $('#carreras').focus();
                                errores.push(elems[i].name);
                                formValido= false;
                            }
                            formValido= false;
                        }else{
                            elems[i].classList.remove('is-invalid');
                            if(elems[i].name == 'x_institution_ID'){
                                $('#universidades').removeClass('is-invalid');
                            }
                            if(elems[i].name == 'x_institute_career'){
                                $('#carreras').removeClass('is-invalid');
                            }
                        }

                    }else if(elems[i].classList.contains('i_required') && elems[i].type == 'file') {
                        if(elems[i].files[0] == undefined){
                            $('[for="' + elems[i].name + '"]').addClass('invalido-form');
//                             $('[for="' + elems[i].name + '"]').focus();
                            errores.push(elems[i].name);
                            formValido= false;
                        }else{
                            $('[for="' + elems[i].name + '"]').removeClass('invalido-form'); 
                        }
                    }
                }

            }
            let inputEmail = $('[name="x_email"]');
            if(inputEmail.val().length > 0 && formValido){
                let valido = await validaciones.validar_email_unico(inputEmail.val());
                if(!valido){
                    inputEmail.focus();
                    errores.push(inputEmail.attr('name'));
                    inputEmail.addClass('is-invalid');
                }
                formValido= valido;
            }
            console.log(errores);
            return formValido;
        },
    });

    const validaciones = new Validaciones();
    
    $('#resultados').change((e) => {
        let entrada = e.target.value.trim().toUpperCase().replace(/\s\s+/g, ' ');
        let elem_id = e.target.id;
        let tipo = elem_id.split('-')[0];
        tipo = tipo.substring(2);
        validaciones.validar_input_resultados(entrada, tipo, elem_id, validaciones);
        if(elem_id.indexOf('email') != -1 && entrada.length < 1){ $('#'+elem_id).val('N/A') };
        if(elem_id.indexOf('document') != -1){
            validaciones.validar_en_BD(elem_id);
        };
        $('#'+elem_id).val($('#'+elem_id).val().trim().toUpperCase().replace(/\s\s+/g, ' '));
    });
    
    return Validaciones; // ~ Exports class

})