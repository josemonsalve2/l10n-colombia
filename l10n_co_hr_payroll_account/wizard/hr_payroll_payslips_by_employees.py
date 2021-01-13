# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')

    @api.multi
    def compute_sheet(self):
        print('***  compute_sheet')
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        journal_id = False
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note','struct_id','journal_id','liquida','tipo_liquida','struct_liquida_id','date_liquidacion','date_prima','date_cesantias','date_vacaciones'])
            journal_id = self.env['hr.payslip.run'].browse(self.env.context.get('active_id')).journal_id.id

        print('run_data: ',run_data)
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')

        #++
        if run_data.get('liquida', False) and not run_data.get('struct_id', False):
           raise UserError(_("Debe seleccionar una estrutura salarial para liquidar")) 

        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        tipo_liquida = run_data.get('tipo_liquida', False)    
        if tipo_liquida in ['otro','nomi_otro']:                
           struct = run_data.get('struct_id')[0]
           liquida_struct_id = run_data.get('struct_id')[0] or False
        else:               
           liquida_struct_id = False

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)

            tipo = run_data.get('tipo_liquida', False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                #++
                'liquida': run_data.get('liquida', False),
                'tipo_liquida': run_data.get('tipo_liquida', False),
                'motivo_retiro': run_data.get('motivo_retiro', False),
                'struct_liquida_id' : liquida_struct_id,
                'date_liquidacion': run_data.get('date_liquidacion', False),
                'date_prima': run_data.get('date_prima', False),
                'date_cesantias': run_data.get('date_cesantias', False),
                'date_vacaciones': run_data.get('date_vacaciones', False),
                'journal_id': journal_id,                 
            }
            payslips += self.env['hr.payslip'].create(res)

        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
