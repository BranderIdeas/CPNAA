odoo.define('website.pagos', function(require) {
'use strict';
    
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    const Validaciones = require('website.validations');
    const validaciones = new Validaciones();
    let dataPDF = {};
    let urlBase = "https://branderideas-cpnaa.odoo.com";
    if(location.href.indexOf(urlBase) === -1 ){
        urlBase = "https://branderideas-cpnaa-developing-984497.dev.odoo.com";
    }
    
    const Pagos = Class.extend({
        traer_data: function(_this) {
            let dataTramite = {
                'doc_type': $('#tipo_doc').attr('data-tipo'),
                'doc': $('#nro_doc').text(),
            };
            rpc.query({
                route: '/tramite_fase_inicial',
                params: {'data': dataTramite}
            }).then(function(response){
                if(response.ok){
                    dataPDF.tramite = response.tramite;
                    dataPDF.corte = response.corte;
                    dataPDF.grado = response.grado;
                    dataPDF.tramite.codigo_recibo = response.codigo;
                    $('#recibo').removeAttr('disabled');
                    $('#epayco').removeAttr('disabled');
                }else{
                    location.replace('https://www.cpnaa.gov.co');
                }
            })
        },
        iniciar_pago: function(){
            let tipo_documento = 'CC';
            if(dataPDF.tramite.x_studio_tipo_de_documento_1[0] == 2){ tipo_documento = 'CE' };
            if(dataPDF.tramite.x_studio_tipo_de_documento_1[0] == 5){ tipo_documento = 'PPN' };
            
            var handler = ePayco.checkout.configure({
                key: '57d20fccb29db60eb4e1be5ff866548f',
                test: true
            })
            var dataTran = {
                //Parametros compra (obligatorio)
                name: 'PAGO CPNAA',
                description: dataPDF.tramite.x_service_ID[1],
                extra1: dataPDF.tramite.id,
                currency: "cop",
                amount: dataPDF.tramite.x_rate,
                tax_base: "0",
                tax: "0",
                country: "co",
                lang: "es",
                external: false,
                response: `${urlBase}/pagos/confirmacion`,

                //Atributos cliente
                name_billing: `${dataPDF.tramite.x_studio_nombres} ${dataPDF.tramite.x_studio_apellidos}`,
                address_billing: dataPDF.tramite.x_studio_direccin,
                type_doc_billing: tipo_documento,
                mobilephone_billing: dataPDF.tramite.x_user_celular,
                number_doc_billing: dataPDF.tramite.x_studio_documento_1,

                //atributo deshabilitación metodo de pago
                methodsDisable: ["SP","CASH","DP"]

            }
            handler.open(dataTran)
        },
        buscar_numero_recibo: async function() {
            let corte = dataPDF.corte ? dataPDF.corte.x_name : false;
            let numero_recibo = 0;
            let data = {
                'id_tramite': dataPDF.tramite.id,
                'corte': corte,
            };
            await rpc.query({
                route: '/recibo_pago',
                params: {'data': data}
            }).then(function(response){
                if(response.ok){
                    numero_recibo = response.numero_recibo
                }
            })
            return numero_recibo;
        },
        downloadPDF: function() {
            const linkSource = $('#pdfFrame').attr('src');
            const downloadLink = document.createElement("a");
            const fileName = "recibo_cpnaa.pdf";

            downloadLink.href = linkSource;
            downloadLink.download = fileName;
            downloadLink.click();
        },
    })

    $('#recibo').click(async ()=>{
        
        let num_recibo = await pagos.buscar_numero_recibo();
        let mes = '';
        let dia = '';
        let re = /[a-zA-Z]/g;
        let fecha_exp = dataPDF.tramite.x_req_date.split('-');
        parseInt(fecha_exp[2])+ 1 < 10 ? dia = `0${parseInt(fecha_exp[2])+ 1}` : dia = `${parseInt(fecha_exp[2])+ 1}`;
        let fecha_fin = '';
        if (dataPDF.corte){
            fecha_fin = dataPDF.corte.x_lim_pay_date.split('-');
            parseInt(fecha_fin[2])+ 1 < 10 ? dia = `0${parseInt(fecha_fin[2])+ 1}` : dia = `${parseInt(fecha_fin[2])+ 1}`;
        } else {
            fecha_fin = dataPDF.grado.x_fecha_limite.split('-');
        }
        let fecha = new Date();
        fecha.getMonth()+1 < 10 ? mes = `0${fecha.getMonth()+1}` : mes = `${fecha.getMonth()+1}`;
        fecha.getDate() < 10 ? dia = `0${fecha.getDate()}` : dia = `${fecha.getDate()}`;
        let fecha_imp = [`${fecha.getFullYear()}`, mes, dia];
        let lugar_expedicion = dataPDF.tramite.x_studio_pas_de_expedicin_1[1] == 'COLOMBIA' 
                             ? dataPDF.tramite.x_studio_ciudad_de_expedicin[1]
                             : dataPDF.tramite.x_studio_pas_de_expedicin_1[1];
        while (num_recibo.length < 12) {
            num_recibo = '0' + num_recibo;
        }
        let invoiceData = {
            code: dataPDF.tramite.codigo_recibo,
            invoice: num_recibo,
            firstname: dataPDF.tramite.x_studio_nombres,
            lastname: dataPDF.tramite.x_studio_apellidos,
            type_doc: dataPDF.tramite.x_studio_tipo_de_documento_1[0],
            procedure: dataPDF.tramite.x_service_ID[1],
            num_doc: dataPDF.tramite.x_studio_documento_1,
            exp_doc: validaciones.quitarAcentos(lugar_expedicion),
            address: dataPDF.tramite.x_studio_direccin,
            city: validaciones.quitarAcentos(dataPDF.tramite.x_studio_ciudad_1[1]),
            department: validaciones.quitarAcentos(dataPDF.tramite.x_studio_departamento_estado[1]),
            email: dataPDF.tramite.x_studio_correo_electrnico,
            phone: `${dataPDF.tramite.x_studio_telfono}`,
            cell_phone: dataPDF.tramite.x_user_celular,
            entity: dataPDF.tramite.x_studio_universidad_5[1],
            degree: dataPDF.tramite.x_studio_carrera_1[1],
            date_grade: dataPDF.tramite.x_studio_fecha_de_grado_2.split('-'),
            date_exp: fecha_exp,
            date_end: fecha_fin,
            date_print: fecha_imp,
            amount: dataPDF.tramite.x_rate,
            local_code: "7709998454712"
        };
//         console.log(dataPDF.tramite);
        try {
            generatePDF(invoiceData);
            $('#modal-recibo-pdf').modal({ keyboard: false, backdrop: 'static' });
            $('#modal-recibo-pdf').modal('show');
            pagos.downloadPDF();
        } catch (e) {
            console.error('Error al generar recibo PDF: '+e);
            console.log(invoiceData);
            validaciones.alert_error_toast('No hemos podido generar tu recibo PDF.', 'center');
        }
        
    })
    
    $('#btn-pagar').click(()=>{
        let tipo_doc = $('[name="x_document_type"]').attr('data-tipo');
        let doc = $('[name="x_document"]').val();
        location.replace(`/pagos/[${tipo_doc}:${doc}]`);
    })
    
    $('#btn-atras').click(()=>{
        let tramite = 'matricula';
        if($('[name="x_service_name"]').val().indexOf('LICENCIA') != -1){
            tramite = 'licencia';
        }
        if($('[name="x_service_name"]').val().indexOf('CERTIFICADO') != -1){
            tramite = 'inscripciontt';
        }
        location.replace('/cliente/tramite/'+tramite);
    })

    if(location.href.indexOf(`${urlBase}/pagos/[`) != -1){
        console.log('PAGOS')
        var pagos = new Pagos();
        pagos.traer_data(pagos);
        $('#epayco').click(pagos.iniciar_pago);
        $('#download_recibo').click(()=>{
            pagos.downloadPDF();
        })
    }
    
    let pathURLConfirmation = location.href.indexOf('pagos/confirmacion?ref_payco=');
    if(pathURLConfirmation != -1){
        
        $('#imprimir').click(()=>{
            let img = `<span role="img" aria-label="Logo of CPNAA OFICINA VIRTUAL" title="CPNAA OFICINA VIRTUAL">
                            <img src="/web/image/website/1/logo/CPNAA%20OFICINA%20VIRTUAL?unique=7291d2f"
                                 class="img img-fluid" alt="CPNAA OFICINA VIRTUAL"></span>`;
            $('#logo').attr('aria-hidden',false).html(img);
            let contenido = $('#resumenPago').html();
            $('body').html(contenido);
            setTimeout(()=>{
                window.print();
                location.reload();
            },300);
        })

        $('#volver').click(()=>{
            location.replace('https://www.cpnaa.gov.co/');
        })
    
        const urlHead = "https://secure.epayco.co/validation/v1/reference/";
        let datosTramite = {};

        var gethataTransaction = async(urlHead) => {
            try {
                let urlParams = new URLSearchParams(window.location.search);
                let ref_payco = urlParams.get('ref_payco');
                let urlApp = urlHead + ref_payco;

                let res = await fetch(urlApp);
                let transaction = await res.json();
                if (transaction.success) {
                    document.getElementById("fecha").innerHTML = transaction.data.x_transaction_date;
                    document.getElementById("respuesta").innerHTML = transaction.data.x_response;
                    document.getElementById("motivo").innerHTML = transaction.data.x_response_reason_text;
                    document.getElementById("recibo").innerHTML = transaction.data.x_transaction_id;
                    document.getElementById("banco").innerHTML = transaction.data.x_bank_name;
                    document.getElementById("ip_publica").innerHTML = transaction.data.x_customer_ip;
                    document.getElementById("total").innerHTML = transaction.data.x_amount + ' ' + transaction.data.x_currency_code;
                    
                    datosTramite['numero_pago'] = transaction.data.x_transaction_id;
                    datosTramite['fecha_pago'] = transaction.data.x_transaction_date;
                    datosTramite['banco'] = transaction.data.x_bank_name;
                    datosTramite['monto_pago'] = transaction.data.x_amount;
                    datosTramite['tipo_pago'] = transaction.data.x_type_payment;
                    datosTramite['id_tramite'] = transaction.data.x_extra1;
//                     console.log(datosTramite);    
                    if(transaction.data.x_response === 'Aceptada'){
                        rpc.query({
                            route: '/tramite_fase_verificacion',
                            params: {'data': datosTramite}
                        }).then(function(response){
                            if(response.ok && !response.error){
                                console.log(response.message)
                            }else if(response.ok && response.error){
                                console.warn(response.message+'\n'+response.error)
                            }else if(!response.ok && response.error){
                                console.error(response.error);
                                let enlaceEstado = response.id_user ? `<a href="${urlBase}/cliente/${response.id_user}/tramites">Ver estado del trámite</a><br/>` : '';
                                $('#error_pagos').removeClass('invisible').attr('aria-hidden',false);
                                $('#error_pagos').find('.alert').html(
                                    `${response.error}<br/>${enlaceEstado}
                                     Si tiene alguna duda, por favor comuníquese con el CPNAA al siguiente correo 
                                     electrónico: info@cpnaa.gov.co o al número telefónico (1)3502700 ext 111-115 en Bogotá`);
                            }
                        }).catch(function(e){
                            console.error('Ha ocurrido un error: '+e);
                            $('#error_pagos').removeClass('invisible').attr('aria-hidden',false);
                            $('#error_pagos').find('.alert').html(
                                `Su pago ha sido exitoso pero no se pudo completar el trámite, por favor envie esta información al
                                 correo info@cpnaa.gov.co`);
                        })
                    }
                } else {
                    validaciones.alert_error_toast('Error consultando la información.', 'center');
                }
                
            } catch (error) {
                validaciones.alert_error_toast('Error consultando la información.', 'center');
                console.log('Error en la transaccion ', error);
            }


        }

        gethataTransaction(urlHead);
    
    }
})