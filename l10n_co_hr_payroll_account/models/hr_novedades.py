# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp


class HrNovedades(models.Model):
    _name = 'hr.novedades'
    _description = 'Novedades de nómina'

    input_id = fields.Many2one('hr.rule.input',
                               'Novedad',
                               required=True,
                               help="Código o nombre de la novedad")
    employee_id = fields.Many2one('hr.employee',
                                  'Empleado',
                                  required=True,
                                  domain=[('active', '=', 'true')],
                                  help="Cédula o nombre completo del empleado")
    date_from = fields.Date('Fecha desde', required=True)
    date_to = fields.Date('Fecha hasta', required=True)
    value = fields.Float('Valor', required=True, default=0.0)
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Cuenta analítica')

    #_sql_constraints = [('novedad_uniq', 'unique(code, date_from, date_to, identification_id, account_analytic_id)', 'La novedad debe ser unica para el período y cedula'),
    _sql_constraints = [
        ('novedad_uniq',
         'unique(input_id, date_from, date_to, employee_id, account_analytic_id)',
         'La novedad debe ser unica para el periodo y cedula'),
    ]
