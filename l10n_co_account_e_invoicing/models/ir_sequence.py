# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    dian_type = fields.Selection(
        selection=[('e-invoicing', _('E-Invoicing')),
                   ('contingency_checkbook_e-invoicing',
                    _('Contingency Checkbook E-Invoicing'))])
