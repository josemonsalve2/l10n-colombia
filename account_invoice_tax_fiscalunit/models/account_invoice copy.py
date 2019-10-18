# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanmarin> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    rate_invoice = fields.Float(
        string='Rate',
        compute='get_rate_invoice',
        digits=(12, 4))
    
    @api.multi
    def get_rate_invoice(self):
        for invoice in self:
            company_currency = invoice.company_id.currency_id
            rate = 1

            if invoice.currency_id != company_currency:
                currency = invoice.currency_id.with_context(
                    date=invoice._get_currency_rate_date()
                        or fields.Date.context_today(invoice))
                rate = currency.compute(rate, company_currency)
            
            invoice.rate_invoice = rate

    @api.multi
    def get_taxes_values(self):
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        msg = _('There is no date range corresponding to the date of your invoice')

        if self.date_invoice:
            param = [
                ('date_start','<=',self.date_invoice),
                ('date_end','>=',self.date_invoice)]
        else:
            param = [
                ('date_start','<=',fields.Date.today()),
                ('date_end','>=',fields.Date.today())]

        daterange = self.env['date.range'].search(param)

        if not daterange:
            raise UserError(msg)
        else:
            fiscalunit = daterange.fiscalunit

        base_group = {}

        for key in tax_grouped.keys():
            tax = self.env['account.tax'].search(
                [('id','=', tax_grouped[key]['tax_id'])])

            if not base_group:
                data = {
                    'tax_group_id': tax.tax_group_id.id,
                    'base': tax_grouped[key]['base']}
                base_group[tax.tax_group_id.name] = data
            else:
                exits = False

                for group_key in base_group.keys():
                    if base_group[group_key]['tax_group_id'] == tax.tax_group_id.id:
                        base_group[group_key]['base'] += tax_grouped[key]['base']
                        exits = True

                if not exits:
                    data = {
                        'tax_group_id': tax.tax_group_id.id,
                        'base': tax_grouped[key]['base']}
                    base_group[tax.tax_group_id.name] = data

        if base_group:
            for group_key in base_group.keys():
                group_obj = self.env['account.tax.group'].search(
                    [('id','=',base_group[group_key]['tax_group_id'])])
                base_to_overcome = group_obj.fiscalunit_factor * fiscalunit
                base = base_group[group_key]['base'] * self.rate_invoice
                
                if base_to_overcome > base:
                    for key in tax_grouped.keys():
                        if tax_grouped[key]:
                            tax = self.env['account.tax'].search(
                                [('id','=', tax_grouped[key]['tax_id'])])
                            tax_group_id = base_group[group_key]['tax_group_id']

                            if tax.tax_group_id.id == tax_group_id:
                                tax_grouped.pop(key)

        return tax_grouped
