# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"

    is_einvoicing = fields.Boolean(string="Does it Apply for E-Invoicing?")

    def name_get(self):
        res = []
        for record in self:
            if record.is_einvoicing:
                name = u'[DIAN][%s] %s' % (record.code or '', record.name
                                           or '')
            else:
                name = u'[%s] %s' % (record.code or '', record.name or '')
            res.append((record.id, name))

        return res
