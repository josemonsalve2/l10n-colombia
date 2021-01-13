# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp


class AccountFiscalyear(models.Model):
    _inherit = "account.fiscal.year"

    salario_minimo = fields.Float(
        'Salario minimo',
        help="Salario minimo legal vigente para el periodo vigente")
    sub_transporte = fields.Float(
        'Subsidio de transporte',
        help="Subsidio de transporte legal vigente para el periodo vigente")
    tarifa_pension = fields.Float(
        'Tarifa pension', help="Tarifa pension para el periodo vigente")
    tarifa_salud = fields.Float(
        'Tarifa salud',
        help="Tarifa de aporte pension para el periodo vigente")
    tarifa_salud_integral = fields.Float(
        'Tarifa salud salario integral',
        help="Tarifa de aporte salud salario integral")
    tarifa_ccf = fields.Float(
        'Tarifa caja compensacion',
        help="Tarifa de aporte a caja de compensacion para el periodo vigente")
    tarifa_sena = fields.Float(
        'Tarifa SENA', help="Tarifa de aporte al SENA para el periodo vigente")
    tarifa_icbf = fields.Float(
        'Tarifa ICBF', help="Tarifa de aporte al ICBF para el periodo vigente")


class HrDepartmentSalaryRule(models.Model):
    _name = 'hr.department.salary.rule'
    _description = 'Cuentas contables por departamento'

    department_id = fields.Many2one('hr.department',
                                    'Departamento',
                                    required=True,
                                    ondelete='cascade',
                                    select=True)
    salary_rule_id = fields.Many2one('hr.salary.rule',
                                     'Regla salarial',
                                     required=True)
    account_debit_id = fields.Many2one('account.account', 'Cuenta deudora')
    account_credit_id = fields.Many2one('account.account', 'Cuenta acreedora')

    _sql_constraints = [
        ('department_rule_uniq', 'unique(department_id, salary_rule_id)',
         'La regla debe ser unica por departamento. La regla ingresada ya existe'
         ),
    ]


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Cuenta analítica',
                                          required=False)
    salary_rule_ids = fields.One2many('hr.department.salary.rule',
                                      'department_id', 'Reglas salariales')
