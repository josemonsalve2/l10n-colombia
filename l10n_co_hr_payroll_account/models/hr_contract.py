# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import fields, models, _

class HrContract(models.Model):
    _inherit = 'hr.contract'

    register_ids = fields.One2many(
        string = 'Contribution Registers',
        comodel_name = 'hr.contract.register',
        inverse_name = 'contract_id'
    )

    deduction_ids = fields.One2many(
        string = 'Deductions or Periodic Payments',
        comodel_name = 'hr.contract.deduction',
        inverse_name = 'contract_id',
    )    

    risk_id = fields.Many2one(
        string = 'Professional Risk',
        comodel_name = 'hr.contract.risk',
    )