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
from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


DIAN = {
    'wsdl-hab': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
    'wsdl': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
    'catalogo-hab': 'https://catalogo-vpfe-hab.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}',
    'catalogo': 'https://catalogo-vpfe.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}'}

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
    invoice_url = fields.Char(string='Invoice Url')
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
    get_status_zip_response = fields.Text(string='Response')

    def _set_filenames(self):
        msg = _("'%s' does not have a identification document established.")

        if not self.company_id.partner_id.identification_document:
            raise UserError(msg)
        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        nnnnnnnnnn = self.company_id.partner_id.identification_document.zfill(10)
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

    def _get_xml_values(self, ClTec):
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        create_date = datetime.strptime(self.invoice_id.create_date, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        ID = self.invoice_id.number
        IssueDate = self.invoice_id.date_invoice
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        supplier = self.company_id.partner_id
        customer = self.invoice_id.partner_id
        NitOFE = supplier.identification_document
        NitAdq = customer.identification_document
        SoftwarePIN = False
        IdSoftware = self.company_id.software_id
        TipoAmbie = self.company_id.profile_execution_id

        if not ClTec:
            SoftwarePIN = self.company_id.software_pin

        if TipoAmbie == '1':
            QRCodeURL = DIAN['catalogo']
        else:
            QRCodeURL = DIAN['catalogo-hab']

        ValFac = self.invoice_id.amount_untaxed
        ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
        TaxInclusiveAmount = ValFac + ValImp1 + ValImp2 + ValImp3
        #El valor a pagar puede verse afectado, por anticipos, y descuentos y
        #cargos a nivel de factura
        #self.invoice_id.amount_total
        PayableAmount = TaxInclusiveAmount
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
            str('{:.2f}'.format(TaxInclusiveAmount)),#self.invoice_id.amount_total
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            TipoAmbie)
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            self.company_id.software_pin,
            ID)
        partition_key = 'co|' + IssueDate.split('-')[2] + '|' + cufe_cude['CUFE/CUDE'][:2]
        emission_date = IssueDate.replace('-', '')
        QRCodeURL = QRCodeURL.format(cufe_cude['CUFE/CUDE'], partition_key, emission_date)

        self.write({
            'invoice_url': QRCodeURL,
            'cufe_cude_uncoded': cufe_cude['CUFE/CUDEUncoded'],
            'cufe_cude': cufe_cude['CUFE/CUDE'],
            'software_security_code_uncoded':
                software_security_code['SoftwareSecurityCodeUncoded'],
            'software_security_code':
                software_security_code['SoftwareSecurityCode']})

        return {
            'ProviderIDschemeID': supplier.check_digit,
            'ProviderIDschemeName': supplier.document_type_id.code,
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'QRCodeURL': QRCodeURL,
            'ProfileExecutionID': TipoAmbie,
            'ID': ID,
            'UUID': cufe_cude['CUFE/CUDE'],
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'LineCountNumeric': len(self.invoice_id.invoice_line_ids),
            'DocumentCurrencyCode': self.invoice_id.currency_id.name,
            'AccountingSupplierParty': supplier._get_accounting_partner_party_values(),
            'AccountingCustomerParty': customer._get_accounting_partner_party_values(),
            #TODO: No esta completamente calro los datos de que tercero son
            'TaxRepresentativeParty': supplier._get_tax_representative_party_values(),
            'PaymentMeansID': self.invoice_id.payment_mean_id.code,
            'PaymentMeansCode': '10',
            'PaymentDueDate': self.invoice_id.date_due,
            'PaymentID': 'Efectivo',
            'TaxesTotal': einvoicing_taxes['TaxesTotal'],
            'WithholdingTaxesTotal': einvoicing_taxes['WithholdingTaxesTotal'],
            'LineExtensionAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(TaxInclusiveAmount),#ValTot
            'PayableAmount': '{:.2f}'.format(PayableAmount)}

    def _get_invoice_values(self):
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        xml_values = self._get_xml_values(active_dian_resolution['technical_key'])
        #Punto 14.1.5.1. del anexo tecnico version 1.8
        #10 Estandar *
        #09 AIU
        #11 Mandatos
        xml_values['CustomizationID'] = '10'
        #Tipos de factura
        #Punto 14.1.3 del anexo tecnico version 1.8
        #01 Factura de Venta
        #02 Factura de Exportación
        #03 Factura por Contingencia Facturador
        #04 Factura por Contingencia DIAN
        xml_values['InvoiceTypeCode'] = '01'
        xml_values['InvoiceAuthorization'] = active_dian_resolution['resolution_number']
        xml_values['StartDate'] = active_dian_resolution['date_from']
        xml_values['EndDate'] = active_dian_resolution['date_to']
        xml_values['Prefix'] = active_dian_resolution['prefix']
        xml_values['From'] = active_dian_resolution['number_from']
        xml_values['To'] = active_dian_resolution['number_to']
        xml_values['InvoiceLines'] = self.invoice_id._get_invoice_lines()

        return xml_values
    
    def _get_credit_note_values(self):
        xml_values = self._get_xml_values(False)
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        #Punto 14.1.5.2. del anexo tecnico version 1.8
        #20 Nota Crédito que referencia una factura electrónica.
        #22 Nota Crédito sin referencia a facturas*.
        #23 Nota Crédito para facturación electrónica V1 (Decreto 2242).
        xml_values['CustomizationID'] = '20'
        #Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #91 Nota Crédito
        xml_values['CreditNoteTypeCode'] = '91'
        billing_reference = self.invoice_id._get_billing_reference()
        xml_values['InvoiceAuthorization'] = active_dian_resolution['resolution_number']
        xml_values['StartDate'] = active_dian_resolution['date_from']
        xml_values['EndDate'] = active_dian_resolution['date_to']
        xml_values['Prefix'] = active_dian_resolution['prefix']
        xml_values['From'] = active_dian_resolution['number_from']
        xml_values['To'] = active_dian_resolution['number_to']
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['CreditNoteLines'] = self.invoice_id._get_invoice_lines()

        return xml_values
    
    def _get_debit_note_values(self):
        xml_values = self._get_xml_values(False)
        #Punto 14.1.5.3. del anexo tecnico version 1.8
        #30 Nota Débito que referencia una factura electrónica.
        #32 Nota Débito sin referencia a facturas*.
        #33 Nota Débito para facturación electrónica V1 (Decreto 2242).
        xml_values['CustomizationID'] = '32'
        #Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #92 Nota Débito 
        #TODO: Parece que este valor se informa solo en la factura de venta
        #parece que en exportaciones
        #xml_values['DebitNoteTypeCode'] = '92'
        #TODO: Es raro que tengamos el cufe de la factura de proveedor,
        #en odoo no se puede hacer notas debito a facturas de venta
        #desarrollo adicional para soportar esto
        #billing_reference = self.invoice_id._get_billing_reference()
        #xml_values['BillingReference'] = billing_reference
        #xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyReferenceID'] = self.invoice_id.origin
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['DebitNoteLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_xml_file(self):
        if self.invoice_id.type == "out_invoice":
            xml_without_signature = global_functions.get_template_xml(
                self._get_invoice_values(),
                'Invoice')
        elif self.invoice_id.type == "out_refund": 
            xml_without_signature = global_functions.get_template_xml(
                self._get_credit_note_values(),
                'CreditNote')
        elif self.invoice_id.type == "in_refund": 
            xml_without_signature = global_functions.get_template_xml(
                self._get_debit_note_values(),
                'DebitNote')

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

    def _set_files(self):
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

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']
        else:
            wsdl = DIAN['wsdl-hab']

        response = post(
            wsdl,
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

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']
        else:
            wsdl = DIAN['wsdl-hab']

        response = post(
            wsdl,
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
