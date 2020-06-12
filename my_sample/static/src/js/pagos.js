odoo.define('website.pagos', function(require) {
'use strict';
    
    var Class = require('web.Class');
    var rpc = require('web.rpc');
    var dataPDF = {};
        
    var Pagos = Class.extend({
        traer_data: function(_this) {
            if (localStorage.getItem('dataTramite')){
                let dataTramite = JSON.parse(localStorage.getItem('dataTramite'));
                rpc.query({
                    route: '/tramite_fase_inicial',
                        params: {'data': dataTramite}
                    }).then(function(response){
                        if(response.ok){
                            dataPDF = response.tramite[0];
                            _this.data_tabla(response.tramite[0]);
                        }else{
                            location.replace('/cliente/tramite/matricula')
                        }
                    })
            }else{
                location.replace('/cliente/tramite/matricula')
            }
        },
        data_tabla: function(data) {
            $('#titulo').text(`SOLICITUD DE ${data.x_service_ID[1]} - PÁGINA DE PAGOS`);
            $('#tipo_doc').text(`${data.x_studio_tipo_de_documento_1[1]}`);
            $('#nro_doc').text(`${data.x_studio_documento_1}`);
            $('#servicio').text(`${data.x_service_ID[1]}`);
            $('#valor').text(`${data.x_rate}`);
            $('#direccion').text(`${data.x_studio_direccin}`);
            $('#telefono').text(`${data.x_user_celular}`);
            $('#nombres').text(`${data.x_studio_nombres} ${data.x_studio_apellidos}`);
        },
        iniciar_pago: function(){
            
            let tipo_documento = 'CC';
            if(dataPDF.x_studio_tipo_de_documento_1[0] == 2){ tipo_documento = 'CE' };
            if(dataPDF.x_studio_tipo_de_documento_1[0] == 5){ tipo_documento = 'PPN' };
            
            var handler = ePayco.checkout.configure({
                key: '9e73b510f7dfd7568b5e876a970962cb',
                test: true
            })

            var dataTran = {
                //Parametros compra (obligatorio)
                name: 'PAGO CPNAA',
                description: $('#servicio').text(),
                invoice: $('#invoice').val(),
                currency: "cop",
                amount: $('#valor').text(),
                tax_base: "0",
                tax: "0",
                country: "co",
                lang: "es",
                external: false,
                response: "https://branderideas-cpnaa-developing-984497.dev.odoo.com/pagos/confirmacion",

                //Atributos cliente
                name_billing: $('#nombres').text(),
                address_billing: $('#telefono').text(),
                type_doc_billing: tipo_documento,
                mobilephone_billing: $('#telefono').text(),
                number_doc_billing: $('#nro_doc').text(),

                //atributo deshabilitación metodo de pago
                methodsDisable: ["SP","CASH","DP"]

            }

            handler.open(dataTran)
        },
    })
        
    $('#recibo').click(()=>{
        
        $('#modal-recibo-pdf').modal({ keyboard: false, backdrop: 'static' });
        $('#modal-recibo-pdf').modal('show');
        
        let mes = '';
        let dia = '';
        let fecha_exp = dataPDF.x_req_date.split('-');
        parseInt(fecha_exp[2])+ 1 < 10 ? dia = `0${parseInt(fecha_exp[2])+ 1}` : dia = `${parseInt(fecha_exp[2])+ 1}`;
        let fecha_fin = [fecha_exp[0], fecha_exp[1], dia];
        let fecha = new Date();
        fecha.getMonth()+1 < 10 ? mes = `0${fecha.getMonth()+1}` : mes = `${fecha.getMonth()+1}`;
        fecha.getDate() < 10 ? dia = `0${fecha.getDate()}` : dia = `${fecha.getDate()}`;
        let fecha_imp = [`${fecha.getFullYear()}`, mes, dia];
        
        let invoiceData = {
            invoice: "000000016"+dataPDF.id,
            firstname: dataPDF.x_studio_nombres,
            lastname: dataPDF.x_studio_apellidos,
            type_doc: dataPDF.x_studio_tipo_de_documento_1[0],
            num_doc: dataPDF.x_studio_documento_1,
            exp_doc: dataPDF.x_studio_ciudad_de_expedicin[1],
            address: dataPDF.x_studio_direccin,
            city: dataPDF.x_studio_ciudad_1[1],
            department: dataPDF.x_studio_departamento_estado[1],
            email: dataPDF.x_studio_correo_electrnico_1,
            phone: `${dataPDF.x_studio_telfono}`,
            cell_phone: dataPDF.x_user_celular,
            entity: dataPDF.x_studio_universidad_5[1],
            degree: dataPDF.x_studio_carrera_1[1],
            date_grade: dataPDF.x_studio_fecha_de_grado_2.split('-'),
            date_exp: fecha_exp,
            date_end: fecha_fin,
            date_print: fecha_imp,
            amount: dataPDF.x_rate * 10,
            local_code: "7709998454712"
        };

        generatePDF(invoiceData);
        
    })
    
    $('#btn-pagar').click(()=>{
        location.replace('/pagos');
    })
    
    $('#btn-atras').click(()=>{
        let tramite = JSON.parse(localStorage.getItem('dataTramite'));
        location.replace('/cliente/tramite/'+tramite.origen);
    })
        
    $('#btn-contacto').click(()=>{
        location.replace('https://cpnaa.gov.co/');
    })
    
    if(location.href == 'https://branderideas-cpnaa-developing-984497.dev.odoo.com/pagos'){
        console.log('PAGOS')
        var pagos = new Pagos();
        pagos.traer_data(pagos);
        $('#epayco').click(pagos.iniciar_pago);
    }
    
    let pathURLConfirmation = location.href.indexOf('pagos/confirmacion?ref_payco=');
    if(pathURLConfirmation != -1){
        
        $('#imprimir').click(()=>{
            window.print();
        })

        $('#volver').click(()=>{
            location.replace('http://35.222.118.62/');
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
                    document.getElementById("referencia").innerHTML = transaction.data.x_id_invoice;
                    document.getElementById("motivo").innerHTML = transaction.data.x_response_reason_text;
                    document.getElementById("recibo").innerHTML = transaction.data.x_transaction_id;
                    document.getElementById("banco").innerHTML = transaction.data.x_bank_name;
                    document.getElementById("ip_publica").innerHTML = transaction.data.x_customer_ip;
                    document.getElementById("total").innerHTML = transaction.data.x_amount + ' ' + transaction.data.x_currency_code;
                    
                    let dataTramite = JSON.parse(localStorage.getItem('dataTramite'));
                    datosTramite['numero_pago'] = transaction.data.x_transaction_id;
                    datosTramite['fecha_pago'] = transaction.data.x_transaction_date;
                    datosTramite['banco'] = transaction.data.x_bank_name;
                    datosTramite['monto_pago'] = transaction.data.x_amount;
                    datosTramite['tipo_pago'] = transaction.data.x_type_payment;
                    datosTramite['doc'] = dataTramite.doc;
                    datosTramite['doc_type'] = dataTramite.doc_type;
                        rpc.query({
                        route: '/tramite_fase1',
                            params: {'data': datosTramite}
                        }).then(function(response){
                            if(response){
                            console.log(response)
                        }
                    })
                } else {
                    alert("Error consultando la información");
                }
                
            } catch (error) {
                alert('Error en la transaccion ', error);
                console.log('Error en la transaccion ', error)
            }


        }

        gethataTransaction(urlHead);
    
    }
})