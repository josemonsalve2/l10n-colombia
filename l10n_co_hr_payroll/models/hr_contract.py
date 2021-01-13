# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class HrContractSetting(models.Model):
    _name= 'hr.contract.setting'
    _description = 'Configuracion nomina'

    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True, ondelete='cascade', select=True)                        
    contrib_id = fields.Many2one ('hr.contribution.register','Concepto', help="Concepto de aporte")
    partner_id = fields.Many2one ('res.partner','Entidad', help="Entidad relacionada")
    account_debit_id = fields.Many2one('account.account', 'Cuenta deudora')
    account_credit_id = fields.Many2one('account.account', 'Cuenta acreedora')
    

class HrContractChangeWage(models.Model):
    _name= 'hr.contract.change.wage'
    _description = 'Cambios salario basico'
    _order = 'date_start desc'

    date_start = fields.Date ('Fecha inicio', required=True)
    wage = fields.Float('Salario basico', help="Seguimento de los cambios en el salario ´basico", required=True)
    contract_id = fields.Many2one('hr.contract', 'Riesgos', required=True, ondelete='cascade', select=True)                       
    
    _sql_constraints = [('change_wage_uniq', 'unique(contract_id, date_start)', 'La fecha ingresada ya existe'),
                       ]
    
class HrContractDeduction(models.Model):
    _name= 'hr.contract.deduction'
    _description = 'Deducciones o pagos periodicas'
     
    input_id = fields.Many2one ('hr.rule.input','Regla salarial', required=True, help="Parámetro asociada a la regla salarial")
    period = fields.Selection([('limited','Limitado'),('indefinite','Indefinido')], default='indefinite',string='Tipo', required=True)
    amount = fields.Float('Valor cuota', default=0, help="Valor de la cuota o porcentaje segun formula de la regla salarial", required=True)
    total_deduction = fields.Float('Total obligación', default=0, help="Total a descontar")
    total_accumulated = fields.Float('Acumulado anterior', default=0, help="Total pagado o acumulado del concepto")
    total_acumulados = fields.Float('Acumulado Odoo', compute='_compute_saldo', default=0.0, readonly=True)
    saldo_actual = fields.Float('Saldo actual', compute='_compute_saldo', default=0.0, readonly=True)
    date = fields.Date('Fecha inicio', select=True, help="Fecha del prestamo u obligacion")
    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True, ondelete='cascade', select=True)

    @api.one
    @api.depends('amount','period','total_deduction','total_accumulated')
    def _compute_saldo(self):

        for line in self:
            result = 0.0
            if line.period == 'limited':
#              self.env.cr.execute("""select  sum(l.total) as total 
#                      from hr_payslip_line l
#                      inner join hr_payslip p on (p.id = l.slip_id)
#                      inner join hr_payslip_input i on (i.payslip_id = p.id and i.salary_rule_id = l.salary_rule_id)
#                      where i.deduction_id = %s""" %  (line.id,))

               #Basado solo en entradas
               self.env.cr.execute("""select  coalesce(sum(i.amount),0.0) as total 
                      from hr_payslip_input i
                      inner join hr_payslip p on (p.id = i.payslip_id)
                      where i.deduction_id = %(prestamo_id)s
                      """,  {'prestamo_id': line.id})
                                             
               res = self.env.cr.fetchone() or False
               if res:
                  result = res[0] or 0.0
                  result = result

            line.total_acumulados = result
     
class HrContractRisk(models.Model):
    _name= 'hr.contract.risk'
    _description = 'Riesgos profesionales'
    
    code = fields.Char('Codigo', size=10, required = True)
    name = fields.Char('Nombre', size=100, required = True)
    percent = fields.Float('Porcentaje', default=0, required = True, help="porcentaje del riesgo profesional")
    date = fields.Date ('Fecha vigencia')
    
class HrContractAcumulados(models.Model):
    '''
    Detalle acumulados del contrato
    '''
    _name = 'hr.contract.acumulados'
    _description = 'Acumulados del contrato'
    _order = 'date, contract_id, salary_rule_id'

    date = fields.Date('Fecha')
    salary_rule_id = fields.Many2one('hr.salary.rule', required=True, string='Regla salarial')        
    amount = fields.Float('Valor', required=True, default=0)
    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True, ondelete='cascade', select=True)


class HrContractLiquidacion(models.Model):
    '''
    Detalle liquidacion de contrato
    '''
    _name = 'hr.contract.liquidacion'
    _description = 'Detalle liquidacion de contrato'
    _order = 'contract_id, sequence'

    sequence = fields.Integer('Secuencia', required=True)
    name = fields.Char('Concepto', size=100, required = True)
    base = fields.Float('Base', required=True, default=0)
    desde = fields.Date('Desde', required=False)
    hasta = fields.Date('Hasta', required=False)
    dias = fields.Float('Días', required = True, default=1)
    amount = fields.Float('Valor', required=True, default=0)
    contract_id = fields.Many2one('hr.contract', 'Liquidacion', required=True, ondelete='cascade', select=True)


class HrContractAnalytic(models.Model):
    _name= 'hr.contract.analytic'
    _description = 'Distribucion por cuenta analitica'

    percent = fields.Float('Porcentaje', required=True, default=0)
    account_analytic_id = fields.Many2one('account.analytic.account','Cuenta analítica',required=True) 
    contract_id = fields.Many2one('hr.contract', 'Cuenta analitica', required=True, ondelete='cascade', select=True)    
    

class HrContract(models.Model):
    _inherit = 'hr.contract'

    analytic_ids = fields.One2many('hr.contract.analytic', 'contract_id', 'Cuentas analíticas')
    setting_ids = fields.One2many('hr.contract.setting', 'contract_id', 'Configuración')
    deduction_ids = fields.One2many('hr.contract.deduction', 'contract_id', 'Deducciones')
    liquidacion_ids = fields.One2many('hr.contract.liquidacion', 'contract_id', 'Liquidación')
    acumulado_ids = fields.One2many('hr.contract.acumulados', 'contract_id', 'Acumulados')
    change_wage_ids = fields.One2many('hr.contract.change.wage', 'contract_id', 'Cambios salario')
    risk_id = fields.Many2one('hr.contract.risk', required=True, string='Riesgo profesional')
    date_prima = fields.Date('Fecha de liquidación de prima')
    date_cesantias = fields.Date('Fecha de liquidación de cesantías')
    date_vacaciones = fields.Date('Fecha de liquidación de vacaciones')
    date_liquidacion = fields.Date('Fecha de liquidación contrato')        
    distribuir = fields.Boolean('Distribuir por cuenta analítica', default=False, help="Indica si al calcula la nómina del contrato se distribuye por centro de costo")
    factor = fields.Float('Factor salarial', required=True, default=0.0)
    parcial = fields.Boolean('Tiempo parcial', default=False)
    pensionado = fields.Boolean('Pensionado', default=False)
    integral = fields.Boolean('Salario integral', default=False)
    condicion = fields.Float('Condición anterior', default=0.0, digits_compute=dp.get_precision('Payroll'))
    compensacion = fields.Float('Compensación', default=0.0, digits_compute=dp.get_precision('Payroll'))
    date_to = fields.Date('Finalización contrato fijo')       
    

