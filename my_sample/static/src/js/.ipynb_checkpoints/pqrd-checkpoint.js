odoo.define('website.pqrd', function(require) {
'use strict';
    
    const Class = require('web.Class');
    const rpc = require('web.rpc');
        
    const Pqrd = Class.extend({ //data, _this
        traer_data: function() {
            console.log('Pqrd......');
        }
    })
    
    const pqrd = new Pqrd();
    pqrd.traer_data();
    
    // Mostrar u ocultar textfield de otro asunto 
	$("input[name='x_issues_ID']").change((e) => {
        let otro = false;
        $("input[name='x_issues_ID']:checked").each(function() {
            if ($(this).val() === '5') { otro = true; }
        });
        if(otro){
            $('#otro_asunto').removeClass('invisible').attr('aria-hidden',false);
            $('input[name="x_pqrd_issue_other"]').addClass('i_required');
        }else{
            $('#otro_asunto').addClass('invisible').attr('aria-hidden',true);
            $('input[name="x_pqrd_issue_other"]').removeClass('i_required is-invalid').val('');
        }
    });
    
})