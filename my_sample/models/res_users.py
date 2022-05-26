# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_partner import now
from odoo import http

import logging
    
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    def reset_password_cpnapp(self):
        """ create signup token for user, and send their signup url by email to reset password from CPNAAP """
        expiration = now(days=+1)
        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)
        template = http.request.env['mail.template'].sudo().search([('name','=','Password reset CPNAAPP')])[0]

        if not self.email:
            raise UserError(_("Cannot send email: user %s has no email address.") % self.name)
        template.send_mail(self.id, force_send=True, raise_exception=True)
        _logger.info("Password reset email sent for CPNAAPP user <%s> to <%s>", self.login, self.email)