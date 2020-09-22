odoo.define('website.certificadoVigencia', function(require) {
'use strict';
    
    const Class = require('web.Class');
    const rpc = require('web.rpc');
    const Validaciones = require('website.validations');
    const validaciones = new Validaciones();
    
    const Denuncia = Class.extend({ //data, _this
        traer_data: function() {
            console.log('Denuncia......');
        }
    })
    
    const denuncia = new Denuncia();
    denuncia.traer_data();
    
})