# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
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
    def write(self, vals):
        rec = super(AccountInvoice, self).write(vals)

        if vals.get('invoice_line_ids'):
            for invoice in self:
                invoice.invoice_line_ids._recompute_tax_id()
            '''
            for line in vals.get('invoice_line_ids'):
                if line[0] == 2:
                    for invoice in self:
                        invoice.invoice_line_ids._recompute_tax_id()

                    continue

                if not type(line[2]) is dict:
                    continue

                if ('price_unit' in line[2].keys()
                        or 'quantity' in line[2].keys()
                        or 'discount' in line[2].keys()):
                    for invoice in self:
                        invoice.invoice_line_ids._recompute_tax_id()

                    break
            '''
        return rec

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)

        for invoice in res:
            invoice.invoice_line_ids._recompute_tax_id()

        return res

    @api.multi
    def _get_tax_groups(self):
        tax_groups = {}

        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(
                price_unit,
                line.currency_id,
                line.quantity,
                product=line.product_id,
                partner=self.partner_id)['taxes']
            
            for tax in taxes:
                tax_id = self.env['account.tax'].browse(tax['id'])
                key = str(tax_id.tax_group_id.id)

                if key not in tax_groups:
                    values = {
                        'tax_group_id': tax_id.tax_group_id.id,
                        'base': tax['base'],
                        'amount': tax['amount']}
                    tax_groups[key] = values
                else:
                    tax_groups[key]['base'] += tax['base']
                    tax_groups[key]['amount'] += tax['amount']

        return tax_groups
    
    @api.multi
    def check_base_to_overcome(self):
        msg = _('There is no date range corresponding to the date of your order')

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

        tax_groups = self._get_tax_groups()
        remove_tax_groups_ids = []
                
        if tax_groups:
            for group_key in tax_groups.keys():
                tax_group_id = self.env['account.tax.group'].search(
                    [('id', '=', tax_groups[group_key]['tax_group_id'])])
                base_to_overcome = tax_group_id.fiscalunit_factor * fiscalunit
                base = tax_groups[group_key]['base'] * self.rate_invoice
                    
                if base_to_overcome > base:
                    remove_tax_groups_ids.append(tax_group_id)

        return remove_tax_groups_ids
