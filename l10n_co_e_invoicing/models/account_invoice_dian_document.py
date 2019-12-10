# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
from StringIO import StringIO
from datetime import datetime
from base64 import b64encode, b64decode
from zipfile import ZipFile
import global_functions
from pytz import timezone
from requests import post
from lxml import etree
from odoo import models, fields
from odoo.exceptions import ValidationError


DIAN = {'wsdl': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl'}


class AccountInvoiceDianDocument(models.Model):
    ''''''
    _name = "account.invoice.dian.document"

    state = fields.Selection(
        [('draft', 'Draft'),
         ('sent', 'Sent'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        string='State',
        readonly=True,
        default='draft')
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice')
    company_id = fields.Many2one(
        'res.company',
        string='Company')
    cufe_cude_uncoded = fields.Char(string='CUFE/CUDE Uncoded')
    cufe_cude = fields.Char(string='CUFE/CUDE')
    software_security_code_uncoded = fields.Char(
        string='SoftwareSecurityCode Uncoded')
    software_security_code = fields.Char(
        string='SoftwareSecurityCode')
    xml_filename = fields.Char(string='XML Filename')
    xml_file = fields.Binary(string='XML File')
    zipped_filename = fields.Char(string='Zipped Filename')
    zipped_file = fields.Binary(string='Zipped File')
    zip_key = fields.Char(string='ZipKey')
    get_status_zip_status_code = fields.Selection(
        [('00', 'Procesado Correctamente'),
         ('66', 'NSU no encontrado'),
         ('90', 'TrackId no encontrado'),
         ('99', 'Validaciones contienen errores en campos mandatorios'),
         ('other', 'Other')],
        string='StatusCode',
        default=False)
    get_status_zip_response = fields.Text(string='GetStatusZip Response')

    def _set_filenames(self):
        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        if self.company_id.partner_id.identification_document:
            nnnnnnnnnn = self.company_id.partner_id.identification_document.zfill(10)
        else:
            raise ValidationError("The company identification document is not "
                                  "established in the partner.\n\nGo to Contacts>"
                                  "[Your company name] to configure it.")
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
        out_invoice_sent = self.company_id.out_invoice_sent
        out_refund_sent = self.company_id.out_refund_sent
        in_refund_sent = self.company_id.in_refund_sent
        zip_sent = out_invoice_sent + out_refund_sent + in_refund_sent

        if self.invoice_id.type == 'out_invoice':
            xml_filename_prefix = 'fv'
            dddddddd = str(out_invoice_sent + 1).zfill(8)
        elif self.invoice_id.type == 'out_refund':
            xml_filename_prefix = 'nc'
            dddddddd = str(out_refund_sent + 1).zfill(8)
        elif self.invoice_id.type == 'in_refund':
            xml_filename_prefix = 'nd'
            dddddddd = str(in_refund_sent + 1).zfill(8)
        #pendiente
        #arnnnnnnnnnnpppaadddddddd.xml
        #adnnnnnnnnnnpppaadddddddd.xml
        else:
            raise ValidationError("ERROR: TODO")

        zdddddddd = str(zip_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + znnnnnnnnnnpppaadddddddd + '.zip'})

    def _get_xml_values(self):
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        create_date = datetime.strptime(self.invoice_id.create_date, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        ID = self.invoice_id.number
        IssueDate = self.invoice_id.date_invoice
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        NitOFE = self.company_id.partner_id.identification_document
        NitAdq = self.invoice_id.partner_id.identification_document
        ClTec = False
        SoftwarePIN = False
        IdSoftware = self.company_id.software_id

        if self.invoice_id.type == 'out_invoice':
            ClTec = active_dian_resolution['technical_key']
        else:
            SoftwarePIN = self.company_id.software_pin

        ValFac = self.invoice_id.amount_untaxed
        ValImp1 = einvoicing_taxes['01']['total']
        ValImp2 = einvoicing_taxes['04']['total']
        ValImp3 = einvoicing_taxes['03']['total']
        ValTot = ValFac + ValImp1 + ValImp2 + ValImp3
        cufe_cude = global_functions.get_cufe_cude(
            ID,
            IssueDate,
            IssueTime,
            str('{:.2f}'.format(ValFac)),
            '01',
            str('{:.2f}'.format(ValImp1)),
            '04',
            str('{:.2f}'.format(ValImp2)),
            '03',
            str('{:.2f}'.format(ValImp3)),
            str('{:.2f}'.format(ValTot)),#invoice.amount_total
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            self.company_id.profile_execution_id)
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            self.company_id.software_pin,
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
            'ProviderIDschemeID': self.company_id.partner_id.check_digit,
            'ProviderIDschemeName': self.company_id.partner_id.document_type_id.code,
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'ProfileExecutionID': self.company_id.profile_execution_id,
            'ID': ID,
            'UUID': cufe_cude['CUFE/CUDE'],
            'partitionKey': 'co|' + IssueDate.split('-')[2] + '|' + cufe_cude['CUFE/CUDE'][:2],
            'emissionDate': IssueDate.replace('-', ''),
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'InvoiceTypeCode': '01',
            'LineCountNumeric': len(self.invoice_id.invoice_line_ids),
            'DocumentCurrencyCode': self.invoice_id.currency_id.name,
            'InvoicePeriodStartDate': period_dates['PeriodStartDate'],
            'InvoicePeriodEndDate': period_dates['PeriodEndDate'],
            'AccountingSupplierParty': self.invoice_id._get_accounting_supplier_party_values(),
            'AccountingCustomerParty': self.invoice_id._get_accounting_customer_party_values(),
            'TaxRepresentativeParty': self.invoice_id._get_tax_representative_party_values(),
            'PaymentMeansID': self.invoice_id.payment_mean_id.code,
            'PaymentMeansCode': '10',
            'PaymentDueDate': self.invoice_id.date_due,
            'PaymentID': 'Efectivo',
            'TaxTotalIVA': einvoicing_taxes['01']['total'],
            'TaxSubtotalIVA': einvoicing_taxes['01']['taxes'],
            'TaxTotalICA': einvoicing_taxes['04']['total'],
            'TaxSubtotalICA': einvoicing_taxes['04']['taxes'],
            'TaxTotalINC': einvoicing_taxes['03']['total'],
            'TaxSubtotalINC': einvoicing_taxes['03']['taxes'],
            'LineExtensionAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(ValTot),#self.invoice_id.amount_total
            'PrepaidAmount': '{:.2f}'.format(0),
            'PayableAmount': '{:.2f}'.format(ValTot),#self.invoice_id.amount_total
            'InvoiceLines': self.invoice_id._get_invoice_lines()}

    def _get_xml_file(self):
        xml_without_signature = global_functions.get_template_xml(
            self._get_xml_values(),
            'Invoice')
        xml_with_signature = global_functions.get_xml_with_signature(
            xml_without_signature,
            self.company_id.signature_policy_url,
            self.company_id.signature_policy_description,
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        return xml_with_signature

    def _get_zipped_file(self):
        output = StringIO()
        zipfile = ZipFile(output, mode='w')
        zipfile_content = StringIO()
        zipfile_content.write(b64decode(self.xml_file))
        zipfile.writestr(self.xml_filename, zipfile_content.getvalue())
        zipfile.close()

        return output.getvalue()

    def set_files(self):
        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()

        if not self.xml_file:
            self.write({'xml_file': b64encode(self._get_xml_file())})

        if not self.zipped_file:
            self.write({'zipped_file': b64encode(self._get_zipped_file())})

    def _get_SendTestSetAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = self.zipped_file
        xml_soap_values['testSetId'] = self.company_id.test_set_id

        return xml_soap_values

    def _get_SendBillAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = self.zipped_file

        return xml_soap_values

    def sent_zipped_file(self):
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"

        if self.company_id.profile_execution_id == '1':
            SendBillAsync_values = self._get_SendBillAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendBillAsync_values,
                    'SendBillAsync'),
                SendBillAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)
        elif self.company_id.profile_execution_id == '2':
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendTestSetAsync_values,
                    'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)

        response = post(
            DIAN['wsdl'],
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature))

        if response.status_code == 200:
            root = etree.fromstring(response.text)

            for element in root.iter("{%s}ZipKey" % b):
                self.write({'zip_key': element.text, 'state': 'sent'})
        else:
            raise ValidationError(response.status_code)

    def _get_GetStatusZip_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.zip_key

        return xml_soap_values

    def GetStatusZip(self):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        c = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
        s = "http://www.w3.org/2003/05/soap-envelope"
        strings = ''
        status_code = 'other'
        GetStatusZip_values = self._get_GetStatusZip_values()
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(
                GetStatusZip_values,
                'GetStatusZip'),
            GetStatusZip_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            DIAN['wsdl'],
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature))

        if response.status_code == 200:
            #root = etree.fromstring(response.content)
            #root = etree.tostring(root, encoding='utf-8')
            root = etree.fromstring(response.content)

            for element in root.iter("{%s}StatusCode" % b):
                if element.text in ('00', '66', '90', '99'):
                    if element.text == '00':
                        self.write({'state': 'done'})

                        if self.invoice_id.type == 'out_invoice':
                            self.company_id.out_invoice_sent += 1
                        elif self.invoice_id.type == 'out_refund':
                            self.company_id.out_refund_sent += 1
                        elif self.invoice_id.type == 'in_refund':
                            self.company_id.in_refund_sent += 1

                    status_code = element.text
            if status_code == '00':
                for element in root.iter("{%s}StatusMessage" % b):
                    strings = element.text

            for element in root.iter("{%s}string" % c):
                if strings == '':
                    strings = '- ' + element.text
                else:
                    strings += '\n\n- ' + element.text

            if strings == '':
                for element in root.iter("{%s}Body" % s):
                    strings = etree.tostring(element, pretty_print=True)

                if strings == '':
                    strings = etree.tostring(root, pretty_print=True)

            self.write({
                'get_status_zip_status_code': status_code,
                'get_status_zip_response': strings})
        else:
            raise ValidationError(response.status_code)

    def action_reprocess(self):
        self.write({'xml_file': b64encode(self._get_xml_file())})
        self.write({'zipped_file': b64encode(self._get_zipped_file())})
        self.sent_zipped_file()
        self.GetStatusZip()
