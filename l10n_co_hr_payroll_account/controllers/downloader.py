# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import base64
from odoo.exceptions import Warning
from datetime import datetime, timedelta, date


class Binary(http.Controller):
    def document(self, filename, filecontent):
        if not filecontent:
            return request.not_found()
        headers = [
            ('Content-Type', 'application/xml'),
            ('Content-Disposition', content_disposition(filename)),
            ('charset', 'utf-8'),
        ]
        return request.make_response(filecontent,
                                     headers=headers,
                                     cookies=None)

    @http.route(["/download/xls/payslip/<model('hr.payslip'):document_id>"],
                type='http',
                auth='user')
    @serialize_exception
    def download_document(self, document_id, **post):
        filename = document_id.number.replace('/', '-') + '.xlsx'
        xls_attachment = request.env['ir.attachment'].sudo().search([
            ('datas_fname', '=', filename), ('res_id', '=', document_id.id)
        ])
        filecontent = base64.decodestring(xls_attachment[0].datas)
        return self.document(filename, filecontent)
