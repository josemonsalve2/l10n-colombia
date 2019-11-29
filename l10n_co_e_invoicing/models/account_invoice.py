# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    dian_document_lines = fields.One2many(
        comodel_name='account.invoice.dian.document',
        inverse_name='invoice_id',
        string='Dian Document Lines')

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()

        if self.company_id.einvoicing_enabled:
            dian_document_obj = self.env['account.invoice.dian.document']
            dian_document = dian_document_obj.create({'invoice_id': self.id})
            dian_document.set_files()
            #einv.action_post_validate()

        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()

        for dian_document in self.dian_document_lines:
            if dian_document.state == 'done':
                raise UserError('You cannot cancel a invoice sent to DIAN')

        return res

    def _get_active_dian_resolution(self):
        msg1 = _("Your active dian resolution has no technical key, " +
                 "contact with your administrator.")
        msg2 = _("You do not have an active dian resolution, " +
                 "contact with your administrator.")
        resolution_number = False
        date_from = False
        date_to = False
        number_from = False
        number_to = False
        technical_key = False

        for date_range_id in self.journal_id.sequence_id.date_range_ids:
            if date_range_id.active_resolution:
                resolution_number = date_range_id.resolution_number
                date_from = date_range_id.date_from
                date_to = date_range_id.date_to
                number_from = date_range_id.number_from
                number_to = date_range_id.number_to

                if not date_range_id.technical_key:
                    raise UserError(msg1)

                technical_key = date_range_id.technical_key
                break

        if not resolution_number:
            raise UserError(msg2)

        return {
            'prefix': self.journal_id.sequence_id.prefix or '',
            'resolution_number': resolution_number,
            'date_from': date_from,
            'date_to': date_to,
            'number_from': number_from,
            'number_to': number_to,
            'technical_key': technical_key}

    def _get_einvoicing_taxes(self):
        msg = _("Your tax '%s' has no e-invoicing tax group type, " +
                "contact with your administrator.")
        einvoicing_taxes = {}

        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id.is_einvoicing:
                if not tax.tax_id.tax_group_id.tax_group_type_id:
                    raise UserError(msg % tax.name)

                tax_code = tax.tax_id.tax_group_id.tax_group_type_id.code
                tax_name = tax.tax_id.tax_group_id.tax_group_type_id.name
                tax_percent = '{:.2f}'.format(tax.tax_id.amount or 0)

                if tax_code not in einvoicing_taxes:
                    einvoicing_taxes[tax_code] = {}
                    einvoicing_taxes[tax_code]['total'] = 0
                    einvoicing_taxes[tax_code]['name'] = tax_name
                    einvoicing_taxes[tax_code]['taxes'] = {}

                if tax_percent not in einvoicing_taxes[tax_code]['taxes']:
                    einvoicing_taxes[tax_code]['taxes'][tax_percent] = {}
                    einvoicing_taxes[tax_code]['taxes'][tax_percent]['base'] = 0
                    einvoicing_taxes[tax_code]['taxes'][tax_percent]['amount'] = 0

                einvoicing_taxes[tax_code]['total'] += tax.amount
                einvoicing_taxes[tax_code]['taxes'][tax_percent]['base'] += tax.base
                einvoicing_taxes[tax_code]['taxes'][tax_percent]['amount'] += tax.amount

        if '01' not in einvoicing_taxes:
            einvoicing_taxes['01'] = {}
            einvoicing_taxes['01']['total'] = 0
            einvoicing_taxes['01']['name'] = 'IVA'
            einvoicing_taxes['01']['taxes'] = {}
            einvoicing_taxes['01']['taxes']['0.00'] = {}
            einvoicing_taxes['01']['taxes']['0.00']['base'] = 0
            einvoicing_taxes['01']['taxes']['0.00']['amount'] = 0

        if '04' not in einvoicing_taxes:
            einvoicing_taxes['04'] = {}
            einvoicing_taxes['04']['total'] = 0
            einvoicing_taxes['04']['name'] = 'ICA'
            einvoicing_taxes['04']['taxes'] = {}
            einvoicing_taxes['04']['taxes']['0.00'] = {}
            einvoicing_taxes['04']['taxes']['0.00']['base'] = 0
            einvoicing_taxes['04']['taxes']['0.00']['amount'] = 0

        if '03' not in einvoicing_taxes:
            einvoicing_taxes['03'] = {}
            einvoicing_taxes['03']['total'] = 0
            einvoicing_taxes['03']['name'] = 'INC'
            einvoicing_taxes['03']['taxes'] = {}
            einvoicing_taxes['03']['taxes']['0.00'] = {}
            einvoicing_taxes['03']['taxes']['0.00']['base'] = 0
            einvoicing_taxes['03']['taxes']['0.00']['amount'] = 0

        return einvoicing_taxes

    def _get_accounting_supplier_party_values(self):
        if self.type in ('out_invoice', 'out_refund'):
            supplier = self.company_id.partner_id
        else:
            supplier = self.partner_id

        return {
            'AdditionalAccountID': supplier.person_type,
            'Name': supplier.name,
            'AddressID': supplier.zip_id.code,
            'AddressCityName': supplier.zip_id.city,
            'AddressCountrySubentity': supplier.state_id.name,
            'AddressCountrySubentityCode': supplier.state_id.code,
            'AddressLine': supplier.street,
            'CompanyIDschemeID': supplier.check_digit,
            'CompanyIDschemeName': supplier.document_type_id.code,
            'CompanyID': supplier.identification_document,
            'TaxLevelCode': supplier.property_account_position_id.tax_level_code_id.code,
            'TaxSchemeID': supplier.property_account_position_id.tax_scheme_id.code,
            'TaxSchemeName': supplier.property_account_position_id.tax_scheme_id.name,
            'CorporateRegistrationSchemeName': supplier.ref,
            'CountryIdentificationCode': supplier.country_id.code,
            'CountryName': supplier.country_id.name}

    def _get_accounting_customer_party_values(self):
        if self.type in ('in_invoice', 'in_refund'):
            customer = self.company_id.partner_id
        else:
            customer = self.partner_id

        return {
            'AdditionalAccountID': customer.person_type,
            'Name': customer.name,
            'AddressID': customer.zip_id.code,
            'AddressCityName': customer.zip_id.city,
            'AddressCountrySubentity': customer.state_id.name,
            'AddressCountrySubentityCode': customer.state_id.code,
            'AddressLine': customer.street,
            'CompanyIDschemeID': customer.check_digit,
            'CompanyIDschemeName': customer.document_type_id.code,
            'CompanyID': customer.identification_document,
            'TaxLevelCode': customer.property_account_position_id.tax_level_code_id.code,
            'TaxSchemeID': customer.property_account_position_id.tax_scheme_id.code,
            'TaxSchemeName': customer.property_account_position_id.tax_scheme_id.name,
            'CorporateRegistrationSchemeName': customer.ref,
            'CountryIdentificationCode': customer.country_id.code,
            'CountryName': customer.country_id.name}

    def _get_tax_representative_party_values(self):
        if self.type in ('out_invoice', 'out_refund'):
            supplier = self.company_id.partner_id
        else:
            supplier = self.partner_id

        return {
            'IDschemeID': supplier.check_digit,
            'IDschemeName': supplier.document_type_id.code,
            'ID': supplier.identification_document}

    def _get_invoice_lines(self):
        invoice_lines = {}
        count = 1

        for invoice_line in self.invoice_line_ids:
            invoice_lines[count] = {}
            invoice_lines[count]['InvoicedQuantity'] = '{:.2f}'.format(
                invoice_line.quantity)
            invoice_lines[count]['LineExtensionAmount'] = '{:.2f}'.format(
                invoice_line.price_subtotal)
            invoice_lines[count]['MultiplierFactorNumeric'] = '{:.2f}'.format(
                invoice_line.discount)
            invoice_lines[count]['AllowanceChargeAmount'] = '{:.2f}'.format(
                invoice_line.disc_amount)
            invoice_lines[count]['AllowanceChargeBaseAmount'] = '{:.2f}'.format(
                invoice_line.total_wo_disc)
            invoice_lines[count]['TaxesTotal'] = {}

            for tax in invoice_line.invoice_line_tax_ids:
                if tax.amount_type == 'group':
                    tax_ids = tax.children_tax_ids
                else:
                    tax_ids = tax

                for tax_id in tax_ids:
                    if tax_id.tax_group_id.is_einvoicing and tax_id.amount != 0:
                        invoice_lines[count]['TaxesTotal'] = (
                            invoice_line._get_invoice_lines_taxes(
                                tax_id,
                                invoice_lines[count]['TaxesTotal']))

            invoice_lines[count]['ItemDescription'] = invoice_line.name
            invoice_lines[count]['PriceAmount'] = '{:.2f}'.format(
                invoice_line.price_unit)

            count += 1

        return invoice_lines
