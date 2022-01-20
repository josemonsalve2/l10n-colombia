# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class hrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    type = fields.Selection(selection=[('Devengado', 'Devengado'),
                                       ('Deducción', 'Deducción')],
                            string='Type')
