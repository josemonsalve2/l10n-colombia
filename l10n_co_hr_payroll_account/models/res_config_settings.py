# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalyear(models.Model):
    _inherit = "account.fiscal.year"

    minimum_wage = fields.Float(
        string='Minimum wage',
        help="Minimum legal salary in force for the current period")
    sub_transport = fields.Float(
        string='Transport allowance',
        help="Legal transport subsidy in force for the current period")
    pension_rate = fields.Float(string="Pension rate",
                                help="Pension rate for the current period")
    health_rate = fields.Float(
        string='Health rate',
        help="Health contribution rate for the current period")
    health_rate_integral = fields.Float(
        string='Tarifa salud salario integral',
        help="Comprehensive salary health rate")
    rate_ccf = fields.Float(
        string='Compensation box rate',
        help="Contribution rate to compensation fund for the current period")
    rate_sena = fields.Float(
        string='SENA rate',
        help="Contribution rate to SENA for the current period")
    rate_icbf = fields.Float(
        string='Rate ICBF',
        help="Contribution rate to the ICBF for the current period")
