# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmInherit(models.Model):
    _inherit = 'crm.lead'

    personalizado = fields.Char(string='Campo Personalizado')
