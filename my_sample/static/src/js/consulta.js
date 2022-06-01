odoo.define("website.consulta", function (require) {
    "use strict";

    const Class = require("web.Class");
    const rpc = require("web.rpc");
    const Validaciones = require("website.validations");
    const validaciones = new Validaciones();

    const data = {
        doc: "",
        doc_type: "",
        numero_tarjeta: "",
    };

    const Consulta = Class.extend({
        //data, _this
        habilitarBtn: function (campos_validos, id_btn) {
            if (campos_validos) {
                $("#" + id_btn).removeAttr("disabled");
            } else {
                $("#" + id_btn).attr("disabled", "disabled");
            }
        },
        validarCaptcha: function (elem, _this) {
            grecaptcha.ready(async function () {
                let result = await grecaptcha.getResponse();
                if (result != "") {
                    _this.realizar_consulta(result, elem, _this);
                    elem.attr("disabled", "disabled");
                } else {
                    elem.removeAttr("disabled");
                    validaciones.mostrar_helper(
                        false,
                        "Por favor, realiza la validación"
                    );
                }
            });
        },
        realizar_consulta: function (token, elem, _this) {
            rpc.query({
                route: "/realizar_consulta",
                params: { data: data, token: token },
            })
                .then(function (response) {
                    _this.mostrar_resultado(response, elem, _this);
                })
                .catch(function (e) {
                    console.log("No se ha podido completar su solicitud");
                    console.log(e);
                });
        },
        mostrar_resultado: async function (response, elem, _this) {
            let div_results = $("#results");
            if (response.error_captcha) {
                grecaptcha.reset();
                return;
            } else if (!response.ok) {
                div_results.removeClass("invisible").attr("aria-hidden", false);
                let texto = `<h5><i class="fa fa-exclamation-triangle"></i> ${response.mensaje.toUpperCase()}
                                 <h5>Por favor envie su solicitud al correo electrónico info@cpnaa.gov.co</h5>`;
                div_results.find("#data_result").html(texto);
            } else if (response.tramites && response.tramites.length > 0) {
                const first = response.tramites[0];
                const texto = first.x_fallecido
                    ? _this.mensaje_fallecido(response, _this)
                    : _this.mensaje_tramites(response, _this);
                div_results.find("#data_result").html(texto);
                div_results.removeClass("invisible").attr("aria-hidden", false);
            }
            $("#hora_consulta").html(`Fecha y hora de consulta: 
                        ${validaciones.dateTimeToString(
                            response.hora_consulta
                        )} ${response.hora_consulta.slice(11)}`);
            $("html, body").animate(
                {
                    scrollTop: elem.offset().top,
                },
                800
            );
        },
        mensaje_tramites: function (response, _this) {
            const tramite = response.tramites[0];
            let sr = "EL SR";
            let identificado = "Identificado";
            let registrado = "registrado";
            let de = ", de ";
            let expedicion = tramite.x_studio_ciudad_de_expedicin[1];
            if (expedicion == "NO APLICA") {
                expedicion = tramite.x_studio_pas_de_expedicin_1
                    ? tramite.x_studio_pas_de_expedicin_1[1]
                    : " ";
                if ((expedicion = " ")) {
                    de = "";
                }
            }
            if (tramite.x_studio_gnero[1] === "FEMENINO") {
                sr = "LA SRA";
                identificado = "Identificada";
                registrado = "registrada";
            }
            if (tramite.x_studio_gnero[1] === "OTRO") {
                sr = "";
                identificado = "Identificade";
                registrado = "registrade";
            }
            let texto = `<b>${sr} ${tramite.x_studio_nombres} ${
                tramite.x_studio_apellidos
            } </b><br/>
                                ${identificado} con ${_this.capitalize(
                tramite.x_studio_tipo_de_documento_1[1]
            )}: 
                                    ${
                                        tramite.x_studio_documento_1
                                    }${de}${_this.capitalize(expedicion)},  
                                    Se encuentra ${registrado} como `;
            response.tramites.forEach((tram, idx) => {
                const txt_antecedentes = !tram.x_legal_status
                    ? `no registra ANTECEDENTES ni SANCIONES VIGENTES en el ejercicio de su profesión por parte del Consejo 
                                Profesional Nacional de Arquitectura y sus Profesiones Auxiliares.`
                    : tram.x_sanction.slice(15);
                const antecedentes =
                    txt_antecedentes != "" ? `y ${txt_antecedentes}` : "";
                const status = !tram.x_legal_status
                    ? "VIGENTE"
                    : tram.x_legal_status.toUpperCase();
                const text_final =
                    response.tramites.length - 1 === idx
                        ? ""
                        : " y registra como ";
                const carrera =
                    tram.x_studio_gnero[1] === "FEMENINO"
                        ? tram.x_female_career
                        : tram.x_studio_carrera_1[1];

                texto += `${_this.capitalize(
                    carrera
                )} con número de ${_this.capitalize(
                    _this.quitarConvenio(tram.x_service_ID[1])
                )}: 
                                    ${
                                        tram.x_enrollment_number
                                    } de acuerdo a la resolución Nro. ${
                    tram.x_resolution_number
                } de fecha 
                                    ${validaciones.dateTimeToString(
                                        tram.x_resolution_date
                                    )}, se encuentra <b>${status}</b> ${antecedentes}`;
                texto += text_final;
            });
            return texto;
        },
        mensaje_fallecido: function (response, _this) {
            const tramite = response.tramites[0];
            let sr = "EL SR";
            let identificado = "Identificado";
            let registrado = "registrado";
            let de = ", de ";
            let expedicion = tramite.x_studio_ciudad_de_expedicin[1];
            if (expedicion == "NO APLICA") {
                expedicion = tramite.x_studio_pas_de_expedicin_1
                    ? tramite.x_studio_pas_de_expedicin_1[1]
                    : " ";
                if ((expedicion = " ")) {
                    de = "";
                }
            }
            if (tramite.x_studio_gnero[1] === "FEMENINO") {
                sr = "LA SRA";
                identificado = "Identificada";
                registrado = "registrada";
            }
            if (tramite.x_studio_gnero[1] === "OTRO") {
                sr = "";
                identificado = "Identificade";
                registrado = "registrade";
            }
            const carrera =
                tramite.x_studio_gnero[1] === "FEMENINO"
                    ? tramite.x_female_career
                    : tramite.x_studio_carrera_1[1];
            return tramite.x_fecha_resolucion_fallecido && tramite.x_resolucion_fallecido
                ? `<i class="fa fa-info-circle"></i>
            <b>${sr} ${tramite.x_studio_nombres} ${
                      tramite.x_studio_apellidos
                  } </b><br/>
            ${identificado} con ${_this.capitalize(
                      tramite.x_studio_tipo_de_documento_1[1]
                  )}: 
            ${tramite.x_studio_documento_1}${de}${_this.capitalize(
                      expedicion
                  )},  
            Se encuentra ${registrado} como  ${_this.capitalize(
                      carrera
                  )} con número de
            ${_this.capitalize(_this.quitarConvenio(tramite.x_service_ID[1]))}: 
            ${tramite.x_enrollment_number} de acuerdo a la resolución Nro. ${
                      tramite.x_resolution_number
                  } de fecha 
            ${validaciones.dateTimeToString(
                tramite.x_resolution_date
            )}, con el Estado: Cancelada por muerte, 
            de acuerdo con la información de la Registraduría Nacional del Estado Civil, Resolución: 
            ${tramite.x_fecha_resolucion_fallecido}. Fecha Resolución: ${
                      tramite.x_resolucion_fallecido
                  }.`
                : `<i class="fa fa-info-circle"></i>
            <b>${sr} ${tramite.x_studio_nombres} ${
                      tramite.x_studio_apellidos
                  } </b><br/>
            ${identificado} con ${_this.capitalize(
                      tramite.x_studio_tipo_de_documento_1[1]
                  )}: 
            ${tramite.x_studio_documento_1}${de}${_this.capitalize(
                      expedicion
                  )},  
            Se encuentra ${registrado} como  ${_this.capitalize(
                      carrera
                  )} con número de
            ${_this.capitalize(_this.quitarConvenio(tramite.x_service_ID[1]))}: 
            ${tramite.x_enrollment_number} de acuerdo a la resolución Nro. ${
                      tramite.x_resolution_number
                  } de fecha 
            ${validaciones.dateTimeToString(
                tramite.x_resolution_date
            )}, con el Estado: Cancelada por muerte, 
            de acuerdo con la información de la Registraduría Nacional del Estado Civil.`;
        },
        capitalize: function (cadena) {
            if (cadena.indexOf("BOGOTA") === 0) {
                cadena = cadena.split(" ");
                cadena[0] = cadena[0]
                    .toLowerCase()
                    .replace(/^\w/, (c) => c.toUpperCase());
                return cadena.join(" ");
            } else if (cadena) {
                return cadena
                    .trim()
                    .toLowerCase()
                    .replace(/\w\S*/g, (w) =>
                        w.replace(/^\w/, (c) => c.toUpperCase())
                    );
            } else {
                return "";
            }
        },
        quitarConvenio: function (cadena) {
            return cadena
                .toLowerCase()
                .split(" ")
                .filter((x) => x.indexOf("convenio") === -1)
                .join(" ");
        },
        validar_formatos: function (_this) {
            data.doc = $("#doc_consulta").val().toUpperCase();
            data.doc_type = $("#doc_type_consulta").val();
            $("#doc_consulta").val(data.doc);
            let valido = validaciones.validar_campos_inicial(
                validaciones,
                "doc_consulta",
                "doc_type_consulta"
            );
            _this.habilitarBtn(valido, "btn_consulta_documento");
        },
    });

    const consulta = new Consulta();

    // Inicio del input tipo de documento
    $("#doc_type_consulta").change(function (e) {
        e.preventDefault();
        consulta.validar_formatos(consulta);
    });

    // Inicio del input número de documento
    $("#doc_consulta").on("input", function (e) {
        e.preventDefault();
        consulta.validar_formatos(consulta);
    });

    // Inicio del input número de tarjeta profesional
    $("#numero_tarjeta").on("input", function (e) {
        e.preventDefault();
        data.numero_tarjeta = $("#numero_tarjeta").val().toUpperCase();
        $("#numero_tarjeta").val(data.numero_tarjeta);
        let valido = data.numero_tarjeta.length > 4 ? true : false;
        consulta.habilitarBtn(valido, "btn_consulta_numero");
    });

    $("#btn_consulta_documento").click(function (e) {
        e.preventDefault();
        consulta.validarCaptcha($("#btn_consulta_documento"), consulta);
    });

    $("#btn_consulta_numero").click(function (e) {
        e.preventDefault();
        consulta.validarCaptcha($("#btn_consulta_numero"), consulta);
    });
});
