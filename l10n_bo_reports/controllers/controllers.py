# -*- coding: utf-8 -*-
# from odoo import http


# class L10nBoReports(http.Controller):
#     @http.route('/l10n_bo_reports/l10n_bo_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_bo_reports/l10n_bo_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_bo_reports.listing', {
#             'root': '/l10n_bo_reports/l10n_bo_reports',
#             'objects': http.request.env['l10n_bo_reports.l10n_bo_reports'].search([]),
#         })

#     @http.route('/l10n_bo_reports/l10n_bo_reports/objects/<model("l10n_bo_reports.l10n_bo_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_bo_reports.object', {
#             'object': obj
#         })
