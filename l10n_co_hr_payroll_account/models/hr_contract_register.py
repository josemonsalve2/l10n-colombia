# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#).

from odoo import fields, models, _


class HrContractRegister(models.Model):
    _name = 'hr.contract.register'
    _description = 'Contribution Register'

    register_id = fields.Many2one(string='Contribution Register',
                                  comodel_name='hr.contribution.register',
                                  required=True)

    partner_id = fields.Many2one(string='Partner',
                                 comodel_name='res.partner',
                                 required=True)

    account_debit_id = fields.Many2one(string='Debit Account',
                                       comodel_name='account.account')

    account_credit_id = fields.Many2one(string='Credit Account',
                                        comodel_name='account.account')

    analytic_account_id = fields.Many2one(
        string='Analytic Account', comodel_name='account.analytic.account')

    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='hr.contract',
                                  required=True,
                                  ondelete='cascade',
                                  index=True)