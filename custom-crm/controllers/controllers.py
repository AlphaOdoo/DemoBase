# -*- coding: utf-8 -*-
# from odoo import http


# class CustomCrm(http.Controller):
#     @http.route('/custom-crm/custom-crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom-crm/custom-crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom-crm.listing', {
#             'root': '/custom-crm/custom-crm',
#             'objects': http.request.env['custom-crm.custom-crm'].search([]),
#         })

#     @http.route('/custom-crm/custom-crm/objects/<model("custom-crm.custom-crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom-crm.object', {
#             'object': obj
#         })
