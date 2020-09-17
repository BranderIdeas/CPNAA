# -*- coding: utf-8 -*-
# from odoo import http


# class Modulo-prueba(http.Controller):
#     @http.route('/modulo-prueba/modulo-prueba/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/modulo-prueba/modulo-prueba/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('modulo-prueba.listing', {
#             'root': '/modulo-prueba/modulo-prueba',
#             'objects': http.request.env['modulo-prueba.modulo-prueba'].search([]),
#         })

#     @http.route('/modulo-prueba/modulo-prueba/objects/<model("modulo-prueba.modulo-prueba"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('modulo-prueba.object', {
#             'object': obj
#         })
