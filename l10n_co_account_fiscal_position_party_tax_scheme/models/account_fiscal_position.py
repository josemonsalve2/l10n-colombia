# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, _


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    listname = fields.Selection(selection=[
        ('48', _('Responsible for sales tax - VAT')),
        ('49', _('Not responsible for VAT'))
    ],
                                string='Fiscal Regime',
                                default=False)
    tax_level_code_ids = fields.Many2many(
        comodel_name='account.fiscal.position.tax.level.code',
        relation='account_fiscal_position_tax_level_code_rel',
        column1='account_fiscal_position_id',
        column2='tax_level_code_id',
        string='Fiscal Responsibilities (TaxLevelCode)')
    tax_group_type_id = fields.Many2one(string="Tax Group Type",
                                        comodel_name="account.tax.group.type")
