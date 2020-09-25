odoo.define('website.validations', function(require) {
    
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    
    // Configuración de las alertas
    const Toast = Swal.mixin({
        toast: true,
        position: 'top',
        showConfirmButton: true,
        confirmButtonColor: '#c8112d',
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
                    let tipo_doc = $('#'+elem_id).parent().prev().children();
                    _this.colocar_borde(tipo_doc.attr("id"), _this.validar_tipo_doc(tipo_doc.val(), tipo_doc.attr("id"), _this));
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
            const tipos_validos = ['CC', 'CE', 'PA', 'C.C.', 'C.E.', 'PA.'];
            const doc_elem = $('#'+elem_id).parent().next().children().attr('id');
            const num_doc = $('#'+elem_id).parent().next().children().val();
            if (!tipos_validos.some(t => t == entrada)) {
                Toast.fire({
                    icon: 'error',
                    title: `<br/>Por favor ingrese: "CC" para Cédula de Ciudadanía,
                           "CE" para Cédula de Extranjería o "PA" para Pasaporte.<br/><br/> `,
                    confirmButtonText: 'Ocultar',
                })
                return false;
            } else {
                let result = false;
                if (entrada == 'CC' || entrada == 'C.C.' || entrada == 'CE' || entrada == 'C.E.') {
                    result = _this.validar_solo_numeros(num_doc);
                    _this.colocar_borde(doc_elem, result);
                }
                if (entrada == 'PA' || entrada == 'PA.') {
                    result = _this.validar_alfanum(num_doc, 'pasaporte');
                    _this.colocar_borde(doc_elem, result);
                }
                return result;
            }
        },
        validar_celular: function (entrada) {
            const regex = /^[0-9]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>Ingrese solo números para el teléfono celular.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else if(entrada.length > 0 && entrada.length < 10){
                Toast.fire({
                    title: `<br/>Ingrese mínimo 10 caracteres para el télefono celular.<br/><br/> `,
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
                    title: `<br/>Ingrese solo números para este campo.<br/><br/> `,
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
                    title: `<br/>Solo se permiten letras, evite números, tildes ó caracteres especiales para nombres y apellidos.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else{
                return true;
            }
        },
        validar_direccion: function (entrada) {
            const regex = /^[0-9a-zA-ZÑñ\-#() ]*$/;
            if (!regex.test(entrada)) {
                Toast.fire({
                    title: `<br/>Evite tildes y caracteres como \;'&<>"% para la dirección<br/><br/> `,
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
                    title: `<br/>Solo se permiten números y letras para ${text}, no ingreses caracteres especiales.<br/><br/> `,
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
                    title: `<br/>Solo se permiten números y letras para el télefono fijo.<br/><br/> `,
                    icon: 'error',
                    confirmButtonText: 'Ocultar',
                })
                return false;
            }else if(entrada.length < 7){
                Toast.fire({
                    title: `<br/>Ingrese mínimo 7 caracteres para el télefono fijo.<br/><br/> `,
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
                    title: `<br/>Por favor ingrese "M" para Masculino o "F" para Femenino.<br/><br/> `,
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
                    title: `<br/>El formato de la dirección de correo electrónico no es válido.<br/><br/> `,
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
        alert_error_toast: function (text, pos) {
            Toast.fire({
                title: `<br/>${text}<br/><br/> `,
                icon: 'error',
                confirmButtonText: 'Ocultar',
                position: pos
            })
        },
        alert_success_toast: function (text) {
            Toast.fire({
                title: `<br/>${text}<br/><br/> `,
                icon: 'success',
                confirmButtonText: 'Aceptar',
                position: 'center'
            })
        },
        quitarAcentos: function(cadena){
            const acentos = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'};
            return cadena.split('').map( letra => acentos[letra] || letra).join('').toString();	
        },
        validar_en_BD: function(elem_id, _this){

            let nro_reg = elem_id.split('-')[1];
            let input_tipo = $('#a_document_type-'+nro_reg);
            let input_nro_doc = $('#b_document-'+nro_reg);
            let profesion_id = $('#profesion').val();
            
            if(_this.es_invalido(input_tipo) || _this.es_invalido(input_nro_doc)) { return }
            
            let tipo_doc = input_tipo.val();
            let numero_doc = input_nro_doc.val();
            let data = { tipo_doc, numero_doc, profesion_id };
            
            return rpc.query({
                route: '/validar_documento_bd',
                params: {'data': data}
            }).then(function(response){
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
        es_invalido: function(elem){
            if(elem.hasClass('invalido')){
                return true;
            }else{
                return false;
            }
        },
        capitalizeFromUpper: function(cadena) {
            if(cadena){
                return cadena.trim().toLowerCase().replace(/\w\S*/g, (w) => (w.replace(/^\w/, (c) => c.toUpperCase())));
            }else{
                return '';
            }
        },
        validar_tipoDoc: function(nameSelect, nameInput, _this){
            let valido = true;
            const selectTipoDoc = $("select[name='"+nameSelect+"']");
            const inputDoc = $("input[name='"+nameInput+"']");
            const tipo_doc = selectTipoDoc.val();
            const documento = inputDoc.val().trim().toUpperCase().replace(/\s+/g, ' ');
            if (documento.length > 0 && documento.length < 4) {
                _this.alert_error_toast('Ingrese por lo menos 4 caracteres', 'top');
                valido = false;
            } else if (tipo_doc == 1) {
                // Solo numeros
                let regex = /^[0-9]*$/;
                inputDoc.attr('maxlength', '11');
                if (!regex.test(documento)) {
                    _this.alert_error_toast('Ingrese solo números, no incluya espacios, letras, puntos ó caracteres especiales', 'top');
                    valido = false;
                } else {
                    valido = true;
                }
                if (documento.length > 11) {
                    _this.alert_error_toast('Verifica tu número de documento', 'top');
                    valido = false;
                }
            } else if (tipo_doc != 1) {
                // Solo numeros y letras
                let regex = /^[0-9a-zA-Z]*$/;
                inputDoc.attr('maxlength', '45');
                if (!regex.test(documento)) {
                    _this.alert_error_toast('Ingrese solo números ó letras, no incluya espacios, puntos ó caracteres especiales', 'top');
                    valido = false;
                } else {
                    valido = true;
                }
            }
            if(!valido){
                inputDoc.addClass('is-invalid');
                selectTipoDoc.addClass('is-invalid');
            }else{
                inputDoc.removeClass('is-invalid');
                selectTipoDoc.removeClass('is-invalid');
                inputDoc.val(documento);
            }     
            return valido;
        },
        validar_formatos: async function validar_formatos(elem, _this){
            if(elem.classList.contains('upper')){
                elem.value = elem.value.trim().toUpperCase().replace(/\s\s+/g, ' ');           
            }
            if(elem.classList.contains('o-letters')){
                let valid = _this.validar_solo_letras(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = elem.value.trim().toUpperCase().replace(/\s\s+/g, ' ');
                }            
            }
            if(elem.classList.contains('v-document')){
                let valid = _this.validar_tipoDoc(elem.dataset.type_doc, elem.name, _this);
            }
            if(elem.classList.contains('v-document_type')){
                let valid = _this.validar_tipoDoc(elem.name, elem.dataset.input_doc, _this);
            }
            if (elem.classList.contains('v-address')){
                let valid = _this.validar_direccion(elem.value);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = elem.value.trim().toUpperCase().replace(/\s+/g, ' ');
                }
            }            
            if (elem.classList.contains('v-email')){
                let valor = elem.value.trim().toLowerCase().replace(/\s+/g, '');
                let valid = _this.validar_email(valor);
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                } else {
                    elem.classList.remove('is-invalid');
                    elem.value = valor;
                }
            } 
            if (elem.classList.contains('v-celular')){
                let valor = elem.value.trim().replace(/\s+/g, '');
                let valid = _this.validar_celular(valor);
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
                    let valid = _this.validar_telefono(elem.value);
                    if(!valid){
                        elem.classList.add('is-invalid');
                        return valid;
                    }else{
                        elem.classList.remove('is-invalid');
                        elem.value = elem.value.trim().toUpperCase();
                    }
                }
            }
            if (elem.classList.contains('v-alfanum')){
                let valor = elem.value.trim().toUpperCase().replace(/\s+/g, '');
                let valid = _this.validar_alfanum(valor, 'el documento Ministerio de Educación');
                if(!valid){
                    elem.classList.add('is-invalid');
                    return valid;
                }else{
                    elem.classList.remove('is-invalid');
                    elem.value = valor;
                }
            }

            return true;

        },
        validar_formulario: async function validar_formulario(_this){
            let formSample = document.forms[0];
            let elems = formSample.elements;
            let formValido = true;
            let errores = [];
            for (let i = 0; i < elems.length; i++) {
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
                            errores.push(elems[i].name);
                            formValido= false;
                        }else{
                            $('[for="' + elems[i].name + '"]').removeClass('invalido-form'); 
                        }
                    }
                }
            }
            if(formValido){
                for (let i = 0; i < elems.length; i++) {
                    let formatosValidos = await _this.validar_formatos(elems[i], _this);
                    if(!formatosValidos){
                        console.log('fromForm', '==>', elems[i].value);
                        formValido= false;
                    }
                }
            }
//             console.log(errores);
            return formValido;
        },
        mostrar_helper_inicio: function(campo, msg) {
            if(campo) {$('#' + campo).addClass('invalido');}
            $('#help_text').removeClass('invisible').text(msg);
        },
        ocultar_helper: function(campo) {
            if(campo) {$('#' + campo).removeClass('invalido');}
            $('#help_text').addClass('invisible');
        },
        validar_campos_inicial: function(_this, id_input_doc, id_input_tipo_doc) {
            let valido = true;
            let tipo_doc = $('#'+id_input_tipo_doc).val();
            let documento = $('#'+id_input_doc).val();
            if (documento.length < 1) {
                _this.mostrar_helper_inicio(id_input_doc, 'El documento es requerido');
                valido = false;
            } else if (documento.length > 0 && documento.length < 4) {
                _this.mostrar_helper_inicio(id_input_doc, 'Ingrese por lo menos 4 caracteres');
                valido = false;
            } else if (tipo_doc == 1) {
                // Solo numeros
                let regex = /^[0-9]*$/;
                $('#'+id_input_doc).attr('maxlength', '11');
                if (!regex.test(documento)) {
                    _this.mostrar_helper_inicio(id_input_doc, 'Ingrese solo números, no incluya espacios, letras, puntos ó caracteres especiales');
                    valido = false;
                } else {
                    _this.ocultar_helper(id_input_doc);
                    valido = true;
                }
                
                if (documento.length > 11) {
                    _this.mostrar_helper_inicio(id_input_doc, 'Verifica tu número de documento');
                    valido = false;
                }
            } else if (tipo_doc != 1) {
                // Solo numeros y letras
                let regex = /^[0-9a-zA-Z]*$/;
                $('#'+id_input_doc).attr('maxlength', '45');
                if (!regex.test(documento)) {
                    _this.mostrar_helper_inicio(id_input_doc, 'Ingrese solo números ó letras, no incluya espacios, puntos ó caracteres especiales');
                    valido = false;
                } else {
                    _this.ocultar_helper(id_input_doc);
                    valido = true;
                }
            }
            return valido;
        },
        validarCheckboxsRequired: function(nameElems, nombreCampo, _this){
            let valido = $('input[name="'+nameElems+'"]:checked').length > 0 ? true : false;
            if(!valido){
               _this.alert_error_toast(`Selecciona por lo menos un ${nombreCampo}`, 'top');
            }
            return valido;
        },
        mostrar_helper: function(campo, msg){
            if(campo) {$('#' + campo).addClass('invalido');}
            $('#help_text').removeClass('invisible').text(msg);
            setTimeout(()=>{
                if(campo) {$('#' + campo).removeClass('invalido');}
                $('#help_text').addClass('invisible');
            },1500);
        },
        dateTimeToString: function(fecha){ // 'YYYY-mm-dd 00:00:00'
            try{
                if (fecha.length == 10) { fecha = fecha + ' 01:00:00'; }
                let fechaHora = new Date(fecha);
                let dia = '';
                meses = [
                    "Enero",
                    "Febrero",
                    "Marzo",
                    "Abril",
                    "Mayo",
                    "Junio",
                    "Julio",
                    "Agosto",
                    "Septiembre",
                    "Octubre",
                    "Noviembre",
                    "Diciembre",
                ]
                fechaHora.getDate() < 10 ? dia = `0${fechaHora.getDate()}` : dia = fechaHora.getDate();
                return `${dia} de ${meses[fechaHora.getMonth()]} de ${fechaHora.getFullYear()}`;
            }catch (e){
                console.log(e)
                return 'Formato de fecha incorrecto';
            }
        }
    });

    const validaciones = new Validaciones();
    
    $('#resultados').change((e) => {
        let entrada = validaciones.quitarAcentos(e.target.value.trim().toUpperCase().replace(/\s\s+/g, ' '));
        let elem_id = e.target.id;
        let tipo = elem_id.split('-')[0];
        tipo = tipo.substring(2);
        validaciones.validar_input_resultados(entrada, tipo, elem_id, validaciones);
        if(elem_id.indexOf('email') != -1 && entrada.length < 1){ $('#'+elem_id).val('N/A') };
        if(elem_id.indexOf('document') != -1){
            validaciones.validar_en_BD(elem_id, validaciones);
        };
        $('#'+elem_id).val(entrada);
    });

    return Validaciones; // ~ Exports class

})