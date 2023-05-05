from odoo import http
import logging
import requests
import json

_logger = logging.getLogger(__name__)

def firmar_certificado(cert_b64, cert_id, type):
    
    url       = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','URL ENDPOINT CERTICAMARA')]).x_value
    api_key   = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','API KEY CERTICAMARA')]).x_value
    password  = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','PASSWORD CERTICAMARA')]).x_value
    path_cert = http.request.env['x_cpnaa_parameter'].sudo().search([('x_name','=','PATH CERTIFICATE CERTICAMARA')]).x_value
    
    headers = {
      'Content-Type': 'application/json',
      'x-api-key': api_key,
    }
    
    payload = json.dumps({
        "signType": "PADES",
        "signReason_idXml": "Certicamara S.A",
        "signLocation": "Bogota",
        "visibleSign": "false",
        "stamp": "false",
        "ltv": "false",
        "signByParts": "false",
        "fileToSignBytes": cert_b64,
        "tsaParameters": {
            "userTSA": "USUARIO ESTAMPA",
            "passwordTSA": "CONTRASEÑA ESTAMPA",
            "stampType": "user"
        },
        "certificateParameters": {
            "certitoken": "false",
            "password": password,
            "certificatePath": path_cert
        }
    })
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code == 200:
        _logger.info(response.text)
        try:
            resp = json.loads(response.text)
            if resp["exitoso"]:
                name_model = 'x_procedure_service_exterior' if type == 'exterior' else 'x_procedure_service'
                http.request.env[name_model].sudo().browse(cert_id).write({ 'x_pdf_signed': True })
                return resp["signResponse"]["signedBytes"]
        except json.JSONDecodeError:
            _logger.info("La respuesta no está en formato JSON")
    else:
        _logger.info("Error en la petición: %s" % response.status_code)
    return cert_b64