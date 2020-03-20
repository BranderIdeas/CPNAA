# -*- coding: utf-8 -*-
from odoo import http


class MySample(http.Controller):
    @http.route('/my_sample/<model("x_example1"):persona>', auth='public', website=True)
    def fun_persona(self, persona):
        return http.request.render('my_sample.index', {
            "persona": persona
        })

#     @http.route('/my_sample/my_sample/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('my_sample.listing', {
#             'root': '/my_sample/my_sample',
#             'objects': http.request.env['my_sample.my_sample'].search([]),
#         })

#     @http.route('/my_sample/my_sample/objects/<model("my_sample.my_sample"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('my_sample.object', {
#             'object': obj
#         })
