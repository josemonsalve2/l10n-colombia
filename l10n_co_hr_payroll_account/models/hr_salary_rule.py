# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    holidays = fields.Boolean(
        string='Parcial Holidays',
        default=False,
        help=
        "Indicates if the value is accumulated for partial vacation settlement"
    )
    bonus = fields.Boolean(
        string='Include in Bunos',
        default=False,
        help="Indicates if the value is accumulated for premium settlement")
    layoff_fund = fields.Boolean(
        string='Include in severance pay',
        default=False,
        help="Indicates if the value is accumulated for severance pay")
    holidays_final = fields.Boolean(
        string='Holidays final',
        default=False,
        help=
        "Indicates if the value is used to calculate the payments in the settlement of the contract"
    )
    average = fields.Boolean(
        string='Average salary',
        default=False,
        help="Indicates if value is used to calculate average salary")
    type_distri = fields.Selection(selection=[('na', 'No aplica'),
                                              ('hora', 'Horas reportadas'),
                                              ('dpto', 'Por contrato'),
                                              ('novedad', 'Por novedades')],
                                   string='Type Distri',
                                   required=True,
                                   default='na')
    register_credit_id = fields.Many2one(
        comodel_name='hr.contribution.register',
        string='Credit contribution record',
        help="Identification of the credit movement of the wage rule")
    # account_bank_type = fields.Many2one('res.partner.bank.type', 'Tipo de cuenta bancaria', help="Se utiliza para relacionar la cuenta bancaria relacionada a aportes voluntarios")
    salary = fields.Boolean(string='Salary',
                            default=False,
                            help="Indicator to calculate average salary")
