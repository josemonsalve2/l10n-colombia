# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import global_functions
from StringIO import StringIO
from datetime import datetime
from pytz import timezone
from base64 import b64encode, b64decode
from zipfile import ZipFile
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
    xml_filename = fields.Char(string='XML Filename')
    xml_file = fields.Binary(string='XML File')
    zipped_filename = fields.Char(string='Zipped Filename')
    zipped_file = fields.Binary(string='Zipped File')

    def _get_xml_values(self):
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

        cufe_cude = global_functions.get_cufe_cude(
            ID,
            IssueDate,
            IssueTime,
            str('{:.2f}'.format(invoice.amount_untaxed)),
            '01',
            str('{:.2f}'.format(einvoicing_taxes['01']['total'])),
            '04',
            str('{:.2f}'.format(einvoicing_taxes['04']['total'])),
            '03',
            str('{:.2f}'.format(einvoicing_taxes['03']['total'])),
            str('{:.2f}'.format(invoice.amount_total)),
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            invoice.company_id.profile_execution_id)
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            invoice.company_id.software_pin,
            ID)
        period_dates = global_functions.get_period_dates(IssueDate)

        self.write({
            'cufe_cude_uncoded': cufe_cude['CUFE/CUDEUncoded'],
            'cufe_cude': cufe_cude['CUFE/CUDE'],
            'software_security_code_uncoded':
                software_security_code['SoftwareSecurityCodeUncoded'],
            'software_security_code':
                software_security_code['SoftwareSecurityCode']})

        return {
            'InvoiceAuthorization': active_dian_resolution['resolution_number'],
            'StartDate': active_dian_resolution['date_from'],
            'EndDate': active_dian_resolution['date_to'],
            'Prefix': active_dian_resolution['prefix'],
            'From': active_dian_resolution['number_from'],
            'To': active_dian_resolution['number_to'],
            'ProviderIDschemeID': invoice.company_id.partner_id.check_digit,
            'ProviderIDschemeName': invoice.company_id.partner_id.document_type_id.code,
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'ProfileExecutionID': invoice.company_id.profile_execution_id,
            'ID': ID,
            'UUID': cufe_cude['CUFE/CUDE'],
            'partitionKey': 'co|' + IssueDate.split('-')[2] + '|' +
                cufe_cude['CUFE/CUDE'][:2],
            'emissionDate': IssueDate.replace('-', ''),
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'InvoiceTypeCode': '01',
            'LineCountNumeric': len(invoice.invoice_line_ids),
            'DocumentCurrencyCode': invoice.currency_id.name,
            'InvoicePeriodStartDate': period_dates['PeriodStartDate'],
            'InvoicePeriodEndDate': period_dates['PeriodEndDate'],
            'AccountingSupplierParty': invoice._get_accounting_supplier_party_values(),
            'AccountingCustomerParty': invoice._get_accounting_customer_party_values(),
            'TaxRepresentativeParty': invoice._get_tax_representative_party_values(),
            'PaymentMeansID': invoice.payment_mean_id.code,
            'PaymentMeansCode': '10',
            'PaymentDueDate': invoice.date_due,
            'PaymentID': 'Efectivo',
            'TaxTotalIVA': einvoicing_taxes['01']['total'],
            'TaxSubtotalIVA': einvoicing_taxes['01']['taxes'],
            'TaxTotalICA': einvoicing_taxes['04']['total'],
            'TaxSubtotalICA': einvoicing_taxes['04']['taxes'],
            'TaxTotalINC': einvoicing_taxes['03']['total'],
            'TaxSubtotalINC': einvoicing_taxes['03']['taxes'],
            'LineExtensionAmount': '{:.2f}'.format(invoice.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(invoice.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(invoice.amount_total),
            'PrepaidAmount': '{:.2f}'.format(0),
            'PayableAmount': '{:.2f}'.format(invoice.amount_total),
            'InvoiceLines': invoice._get_invoice_lines()}

    def _set_filenames(self):
        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        nnnnnnnnnn = self.invoice_id.company_id.partner_id.identification_document.zfill(10)
        #El Código “ppp” es 000 para Software Propio
        ppp = '000'
        #aa: Dos (2) últimos dígitos año calendario
        aa = datetime.now().replace(
            tzinfo=timezone('America/Bogota')).strftime('%y')
        #dddddddd: consecutivo del paquete de archivos comprimidos enviados;
        # de ocho (8) dígitos decimales alineados a la derecha y ajustado a la
        # izquierda con ceros; en el rango:
        #   00000001 <= 99999999
        # Ejemplo de la décima primera factura del Facturador Electrónico con
        # NIT 800197268 con software propio para el año 2019.
        # Regla: el consecutivo se iniciará en “00000001” cada primero de enero.
        
        if self.invoice_id.type == 'out_invoice':
            xml_filename_prefix = 'fv'
            dddddddd = str(self.invoice_id.company_id.out_invoice_sent + 1).zfill(8)
        elif self.invoice_id.type == 'out_refund':
            xml_filename_prefix = 'nc'
            dddddddd = str(self.invoice_id.company_id.out_refund_sent + 1).zfill(8)
        elif self.invoice_id.type == 'in_refund':
            xml_filename_prefix = 'nd'
            dddddddd = str(self.invoice_id.company_id.in_refund_sent + 1).zfill(8)
        #pendiente
        #arnnnnnnnnnnpppaadddddddd.xml 
        #adnnnnnnnnnnpppaadddddddd.xml
        else:
            return True

        zdddddddd = str(self.invoice_id.company_id.invoices_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + znnnnnnnnnnpppaadddddddd + '.zip'})
    
    def _get_zipped_file(self):
        output = StringIO()
        zipfile = ZipFile(output, mode='w')
        zipfile_content = StringIO()
        zipfile_content.write(b64decode(self.xml_file))
        zipfile.writestr(self.xml_filename, zipfile_content.getvalue())
        zipfile.close()

        return output.getvalue()

    def _get_xml_without_signature(self):
        xml_values = self._get_xml_values()

        return global_functions.get_template_xml(
            xml_values,
            'generic_invoice')

    def _get_xml_file(self):
        xml_without_signature = self._get_xml_without_signature()
        xml_with_signature = global_functions.get_xml_with_signature(
            xml_without_signature.encode('utf-8'),
            self.invoice_id.company_id.signature_policy_url,
            self.invoice_id.company_id.signature_policy_description,
            self.invoice_id.company_id.certificate_file,
            self.invoice_id.company_id.certificate_password)

        return xml_with_signature

    def set_files(self):
        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()
        
        if not self.xml_file:
            self.write({'xml_file': b64encode(self._get_xml_file())})

        if not self.zipped_file:
            self.write({'zipped_file': b64encode(self._get_zipped_file())})
