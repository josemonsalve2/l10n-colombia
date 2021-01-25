# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'

    _sql_constraints = [
        ('code_uniq', 'unique(code)',
         'El codigo debe ser unico. El codigo ingresado ya existe'),
    ]
