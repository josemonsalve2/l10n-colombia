# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import global_functions
from datetime import datetime, date, timedelta
from pytz import timezone
from base64 import b64encode
from odoo import models, fields


class AccountInvoiceDianDocument(models.Model):
    _name = "account.invoice.dian.document"

    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('cancel', 'Cancel'),],
        string='State',
        readonly=True,
        default='draft')
    cufe_cude_uncoded = fields.Char(string='CUFE/CUDE Uncoded')
    cufe_cude = fields.Char(string='CUFE/CUDE')
    software_security_code_uncoded = fields.Char(
        string='SoftwareSecurityCode Uncoded')
    software_security_code = fields.Char(
        string='SoftwareSecurityCode')
    xml_filename = fields.Char(string='XML Filename')
    xml_file = fields.Binary(string='XML File')

    def _prepare_xml_values(self):
        invoice = self.invoice_id
        active_dian_resolution = invoice._get_active_dian_resolution()
        einvoicing_taxes = invoice._get_einvoicing_taxes()
        create_date = datetime.strptime(invoice.create_date, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        ID = invoice.number
        IssueDate = invoice.date_invoice
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        NitOFE = invoice.company_id.partner_id.identification_document
        NitAdq = invoice.partner_id.identification_document
        ClTec = False
        SoftwarePIN = False
        IdSoftware = invoice.company_id.software_id
        
        if invoice.type == 'out_invoice':
            ClTec = active_dian_resolution['technical_key']
        else:
            SoftwarePIN = invoice.company_id.software_pin

        CUFE_CUDE = global_functions.generate_cufe_cude(
            ID,
            IssueDate,
            IssueTime,
            str('{:.2f}'.format(invoice.amount_untaxed)),
            '01',
            str('{:.2f}'.format(
                einvoicing_taxes['01']['total'] if '01' in einvoicing_taxes else 0)),
            '04',
            str('{:.2f}'.format(
                einvoicing_taxes['04']['total'] if '04' in einvoicing_taxes else 0)),
            '03',
            str('{:.2f}'.format(
                einvoicing_taxes['03']['total'] if '03' in einvoicing_taxes else 0)),
            str('{:.2f}'.format(invoice.amount_total)),
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            invoice.company_id.profile_execution_id)
        
        split_date = IssueDate.split('-')
        year = int(split_date[0])
        current_month = int(split_date[1])

        if current_month == 12:
            year += 1
            month = 1
        else:
            month = current_month + 1

        return {
            'InvoiceAuthorization': active_dian_resolution['resolution_number'],
            'StartDate': active_dian_resolution['date_from'],
            'EndDate': active_dian_resolution['date_to'],
            'Prefix': active_dian_resolution['prefix'],
            'From': active_dian_resolution['number_from'],
            'To': active_dian_resolution['number_to'],
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': global_functions.generate_software_security_code(
                IdSoftware,
                invoice.company_id.software_pin,
                ID),
            'ProfileExecutionID': invoice.company_id.profile_execution_id,
            'ID': ID,
            'UUID': CUFE_CUDE,
            'partitionKey': 'co|' + IssueDate.split('-')[2] + '|' + CUFE_CUDE[:2],
            'emissionDate': IssueDate.replace('-', ''),
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'InvoiceTypeCode': '1',
            'LineCountNumeric': len(invoice.invoice_line_ids),
            'DocumentCurrencyCode': invoice.currency_id.name,
            'InvoicePeriodStartDate': date(year, current_month, 1).strftime("%Y-%m-%d"),
            'InvoicePeriodEndDate': (date(year, month, 1) - timedelta(days=1)).strftime("%Y-%m-%d"),
            'AccountingSupplierParty': invoice._get_accounting_supplier_party_values(),
            'AccountingCustomerParty': invoice._get_accounting_customer_party_values(),
            'TaxRepresentativeParty': invoice._get_tax_representative_party_values(),
            'PaymentMeansID': invoice.payment_mean_id.code,
            'PaymentMeansCode': '10',
            'PaymentDueDate': invoice.date_due,
            'PaymentID': 'Efectivo',
            'LineExtensionAmount': '{:.2f}'.format(invoice.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(invoice.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(invoice.amount_total),
            'PrepaidAmount': '{:.2f}'.format(0),
            'PayableAmount': '{:.2f}'.format(invoice.amount_total)}

    def _get_xml_without_signature(self):
        values = self._prepare_xml_values()

        return global_functions.get_template_xml(values, 'generic_invoice')
    
    def _create_xml(self):
        xml_without_signature = self._get_xml_without_signature()
        #signature = self._get_signature(xml_without_signature)
        #xml_with_signature = signature + xml_without_signature
        #print(xml_without_signature)

        return xml_without_signature
    
    def generate_xml_file(self):
        if not self.xml_file:
            xml_file = self._create_xml() or ''
            self.write({
                'xml_filename': 'generic_invoice.xml',
                'xml_file': b64encode(xml_file.encode('utf-8'))})
