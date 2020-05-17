# -*- coding: utf-8 -*-
from odoo import http

# class Ranchyloans(http.Controller):
#     @http.route('/ranchyloans/ranchyloans/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ranchyloans/ranchyloans/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ranchyloans.listing', {
#             'root': '/ranchyloans/ranchyloans',
#             'objects': http.request.env['ranchyloans.ranchyloans'].search([]),
#         })

#     @http.route('/ranchyloans/ranchyloans/objects/<model("ranchyloans.ranchyloans"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ranchyloans.object', {
#             'object': obj
#         })