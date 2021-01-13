# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    vacaciones = fields.Boolean('Vacaciones parcial', default=False, help="Indica si el valor se acumula para liquidación de vacaciones parciales")
    prima = fields.Boolean('Inlcuir en prima', default=False, help="Indica si el valor se acumula para liquidación de primas")
    cesantias = fields.Boolean('Inlcuir en cesantias', default=False, help="Indica si el valor se acumula para liquidación de cesantias")       
    vacaciones_final = fields.Boolean('Vacaciones final', default=False, help="Indica si el valor se utiliza para calcular las vacciones en la liquidacion del contrato")
    promedio = fields.Boolean('Promedio salarial', default=False, help="Indica si el valor se utiliza para calcular el promedio salarial")
    type_distri = fields.Selection([('na','No aplica'), ('hora','Horas reportadas'),('dpto','Por contrato'),('novedad','Por novedades')],'Tipo distribución', required=True, default='na')
    register_credit_id = fields.Many2one('hr.contribution.register', 'Registro contribución crédito', help="Identificación del movimiento cédito de la regla salarial")   
    #account_bank_type = fields.Many2one('res.partner.bank.type', 'Tipo de cuenta bancaria', help="Se utiliza para relacionar la cuenta bancaria relacionada a aportes voluntarios")  
    salario = fields.Boolean('Salario', default=False, help="Indicador para calcular salario promedio")


class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input' 
    
    _sql_constraints = [('code_uniq', 'unique(code)', 'El codigo debe ser unico. El codigo ingresado ya existe'),
                       ]