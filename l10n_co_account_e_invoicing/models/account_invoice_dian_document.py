# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
from StringIO import StringIO
from datetime import datetime
from base64 import b64encode, b64decode
from validators import url
from zipfile import ZipFile
import global_functions
from pytz import timezone
from requests import post, exceptions
from lxml import etree
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request


DIAN = {
    'wsdl-hab': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
    'wsdl': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
    'catalogo-hab': 'https://catalogo-vpfe-hab.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}',
    'catalogo': 'https://catalogo-vpfe.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}'}

class AccountInvoiceDianDocument(models.Model):
    ''''''
    _name = "account.invoice.dian.document"

    def go_to_dian_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dian Document', 
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current'}

    @api.one
    def _get_qr_code(self):
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
        ValFac = self.invoice_id.amount_untaxed
        ValOtroIm = ValImp2 - ValImp3
        ValTolFac = ValFac + ValImp1 + ValOtroIm
        create_date = datetime.strptime(self.invoice_id.create_date, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        create_date = create_date.astimezone(timezone('America/Bogota'))
        qr_data = "NumFac: " + (self.invoice_id.number or _('WITHOUT VALIDATE'))
        qr_data += "\nFecFac: " + (self.invoice_id.date_invoice or '')
        qr_data += "\nHorFac: " + create_date.strftime('%H:%M:%S-05:00')
        qr_data += "\nNitFac: " + (self.company_id.partner_id.identification_document or '')
        qr_data += "\nNitAdq: " + (self.invoice_id.partner_id.identification_document or '')
        qr_data += "\nValFac: " + '{:.2f}'.format(ValFac)
        qr_data += "\nValIva: " + '{:.2f}'.format(ValImp1)
        qr_data += "\nValOtroIm: " + '{:.2f}'.format(ValOtroIm)
        qr_data += "\nValTolFac: " + '{:.2f}'.format(ValTolFac)

        if self.invoice_id.type == "out_invoice" and self.cufe_cude:
            qr_data += "\nCUFE: " + self.cufe_cude
        elif self.invoice_id.type == "out_refund" and self.cufe_cude: 
            qr_data += "\nCUDE: " + self.cufe_cude

        qr_data += "\n\n" + (self.invoice_url or '')
        self.qr_image = global_functions.get_qr_code(qr_data)

    state = fields.Selection(
        [('draft', 'Draft'),
         ('sent', 'Sent'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
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
    profile_execution_id = fields.Selection(
        string='Destination Environment of Document',
        related='company_id.profile_execution_id',
        store=False)
    xml_filename = fields.Char(string='Invoice XML Filename')
    xml_file = fields.Binary(string='Invoice XML File')
    zipped_filename = fields.Char(string='Zipped Filename')
    zipped_file = fields.Binary(string='Zipped File')
    ar_xml_filename = fields.Char(string='ApplicationResponse XML Filename')
    ar_xml_file = fields.Binary(string='ApplicationResponse XML File')
    mail_sent = fields.Boolean(string='Mail Sent?')
    zip_key = fields.Char(string='ZipKey')
    get_status_zip_status_code = fields.Selection(
        [('00', 'Processed Correctly'),
         ('66', 'NSU not found'),
         ('90', 'TrackId not found'),
         ('99', 'Validations contain errors in mandatory fields'),
         ('other', 'Other')],
        string='Status Code',
        default=False)
    get_status_zip_response = fields.Text(string='Response')
    qr_image = fields.Binary("QR Code", compute='_get_qr_code')
    dian_document_line_ids = fields.One2many(
		comodel_name='account.invoice.dian.document.line',
		inverse_name='dian_document_id',
		string='DIAN Document Lines')

    def _set_filenames(self):
        msg1 = _("The document type of '%s' is not NIT")
        msg2 = _("'%s' does not have a document type established.")
        msg3 = _("'%s' does not have a identification document established.")
        msg4 = _('There is no date range corresponding to the date of your invoice.')
        date_invoice = self.invoice_id.date_invoice

        if self.company_id.partner_id.document_type_id:
			if self.company_id.partner_id.document_type_id.code != '31':
				raise UserError(msg1 % self.company_id.partner_id.name)
        else:
			raise UserError(msg2 % self.company_id.partner_id.name)

        if not self.company_id.partner_id.identification_document:
            raise UserError(msg3)

        if not date_invoice:
            date_invoice = fields.Date.today()

        param = [('date_start', '<=', date_invoice), ('date_end', '>=', date_invoice)]
        daterange = self.env['date.range'].search(param)

        if (not daterange
                or daterange.company_id != self.company_id
                or not daterange.type_id
                or not daterange.type_id.fiscal_year):
            raise UserError(msg4)
        else:
            # Regla: el consecutivo se iniciará en “00000001” cada primero de enero.
            out_invoice_sent = daterange.out_invoice_sent
            out_refund_credit_sent = daterange.out_refund_credit_sent
            out_refund_debit_sent = daterange.out_refund_debit_sent
            zip_sent = out_invoice_sent + out_refund_credit_sent + out_refund_debit_sent

        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        nnnnnnnnnn = self.company_id.partner_id.identification_document.zfill(10)
        #El Código “ppp” es 000 para Software Propio
        ppp = '000'
        #aa: Dos (2) últimos dígitos año calendario
        aa = date_invoice[2:4]
        #dddddddd: consecutivo del paquete de archivos comprimidos enviados;
        # de ocho (8) dígitos decimales alineados a la derecha y ajustado a la
        # izquierda con ceros; en el rango:
        #   00000001 <= 99999999

        if self.invoice_id.type == 'out_invoice':
            xml_filename_prefix = 'fv'
            daterange.out_invoice_sent += 1
            dddddddd = str(daterange.out_invoice_sent).zfill(8)
        elif self.invoice_id.type == 'out_refund' and self.invoice_id.refund_type == 'credit':
            xml_filename_prefix = 'nc'
            daterange.out_refund_credit_sent += 1
            dddddddd = str(daterange.out_refund_credit_sent).zfill(8)
        elif self.invoice_id.type == 'out_refund' and self.invoice_id.refund_type == 'debit':
            xml_filename_prefix = 'nd'
            daterange.out_refund_debit_sent += 1
            dddddddd = str(daterange.out_refund_debit_sent).zfill(8)
        else:
            raise ValidationError("ERROR: TODO 2.0")

        #TODO 2.0
        #arnnnnnnnnnnpppaadddddddd.xml
        #adnnnnnnnnnnpppaadddddddd.xml

        zdddddddd = str(zip_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        zarnnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + zarnnnnnnnnnnpppaadddddddd + '.zip',
            'ar_xml_filename': 'ar' + zarnnnnnnnnnnpppaadddddddd + '.xml'})

        return True

    def _get_xml_values(self, ClTec):
        msg1 = _("'%s' does not have a valid isic code")
        msg2 = _("'%s' does not have a isic code established.")
        msg3 = _("'%s' does not have a identification document established.")
        supplier = self.company_id.partner_id

        if supplier.isic_id:
			if supplier.isic_id.code == '0000':
				raise UserError(msg1 % supplier.name)
        else:
			raise UserError(msg2 % supplier.name)

        NitOFE = supplier.identification_document
        IdSoftware = self.company_id.software_id
        SoftwarePIN = self.company_id.software_pin
        ID = self.invoice_id.number
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            SoftwarePIN,
            ID)
        TipoAmbie = self.company_id.profile_execution_id
        customer = self.invoice_id.partner_id
        NitAdq = customer.identification_document
        document_type_code = False

        if customer.document_type_id:
            document_type_code = customer.document_type_id.code

        if document_type_code not in ('11', '12', '13', '21', '22', '31', '41', '42', '50', '91'):
            if customer.person_type == '2':
                NitAdq = '2222222222'
            else:
                raise UserError(msg3 % customer.name)

        if TipoAmbie == '1':
            QRCodeURL = DIAN['catalogo']
        else:
            QRCodeURL = DIAN['catalogo-hab']

        create_date = datetime.strptime(self.invoice_id.create_date, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        IssueDate = self.invoice_id.date_invoice
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        ValFac = self.invoice_id.amount_untaxed
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
        ValOtroIm = ValImp2 - ValImp3
        TaxInclusiveAmount = ValFac + ValImp1 + ValImp2 + ValImp3
        #El valor a pagar puede verse afectado, por anticipos, y descuentos y
        #cargos a nivel de factura
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
            str('{:.2f}'.format(TaxInclusiveAmount)),
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            TipoAmbie)
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
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'NitAdquiriente': NitAdq,
            'QRCodeURL': QRCodeURL,
            'ProfileExecutionID': TipoAmbie,
            'ID': ID,
            'UUID': cufe_cude['CUFE/CUDE'],
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'ValIva': '{:.2f}'.format(ValImp1),
            'ValOtroIm': '{:.2f}'.format(ValOtroIm),
            'DueDate': self.invoice_id.date_due,
            'DocumentCurrencyCode': self.invoice_id.currency_id.name,
            'LineCountNumeric': len(self.invoice_id.invoice_line_ids),
            'IndustryClassificationCode': supplier.isic_id.code,
            'AccountingSupplierParty': supplier._get_accounting_partner_party_values(),
            'AccountingCustomerParty': customer._get_accounting_partner_party_values(),
            'Delivery': customer._get_delivery_values(),
            'DeliveryTerms': {'LossRiskResponsibilityCode': False, 'LossRisk': False},
            'PaymentMeansID': self.invoice_id.payment_mean_id.code,
            'PaymentMeansCode': self.invoice_id.payment_mean_code_id.code,
            'PaymentDueDate': self.invoice_id.date_due,
            'PaymentExchangeRate': self.invoice_id._get_payment_exchange_rate(),
            'TaxesTotal': einvoicing_taxes['TaxesTotal'],
            'WithholdingTaxesTotal': einvoicing_taxes['WithholdingTaxesTotal'],
            'LineExtensionAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(TaxInclusiveAmount),
            'PayableAmount': '{:.2f}'.format(PayableAmount)}

    def _get_invoice_values(self):
        msg1 = _("Your journal: %s, has no a invoice sequence")
        msg2 = _("Your active dian resolution has no technical key, "
				 "contact with your administrator.")
        msg3 = _("Your journal: %s, has no a invoice sequence with type equal to E-Invoicing")
        msg4 = _("Your journal: %s, has no a invoice sequence with type equal to "
                 "Contingency Checkbook E-Invoicing")
        msg5 = _("The invoice type selected is not valid to this invoice.")
        sequence = self.invoice_id.journal_id.sequence_id
        ClTec = False

        if not sequence:
            raise UserError(msg1 % self.invoice_id.journal_id.name)

        active_dian_resolution = self.invoice_id._get_active_dian_resolution()

        if self.invoice_id.invoice_type_code in ('01', '02'):
            ClTec = active_dian_resolution['technical_key']

            if not ClTec:
				raise UserError(msg2)

        if self.invoice_id.invoice_type_code != '03':
            if sequence.dian_type != 'e-invoicing':
                raise UserError(msg3 % self.invoice_id.journal_id.name)
        else:
            if sequence.dian_type != 'contingency_checkbook_e-invoicing':
                raise UserError(msg4 % self.invoice_id.journal_id.name)

        if self.invoice_id.operation_type not in ('10', '11'):
            raise UserError(msg5)

        xml_values = self._get_xml_values(ClTec)
        xml_values['InvoiceControl'] = active_dian_resolution
        #Tipos de operacion
        #Punto 14.1.5.1. del anexo tecnico version 1.8
        #10 Estandar *
        #09 AIU
        #11 Mandatos
        xml_values['CustomizationID'] = self.invoice_id.operation_type
        #Tipos de factura
        #Punto 14.1.3 del anexo tecnico version 1.8
        #01 Factura de Venta
        #02 Factura de Exportación
        #03 Factura por Contingencia Facturador
        #04 Factura por Contingencia DIAN
        xml_values['InvoiceTypeCode'] = self.invoice_id.invoice_type_code
        xml_values['InvoiceLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_credit_note_values(self):
        msg = _("Your journal: %s, has no a credit note sequence")

        if not self.invoice_id.journal_id.refund_sequence_id:
            raise UserError(msg % self.invoice_id.journal_id.name)

        xml_values = self._get_xml_values(False)
        billing_reference = self.invoice_id._get_billing_reference()
        #Punto 14.1.5.2. del anexo tecnico version 1.8
        #20 Nota Crédito que referencia una factura electrónica.
        #22 Nota Crédito sin referencia a facturas*.
        #23 Nota Crédito para facturación electrónica V1 (Decreto 2242).
        if billing_reference:
            xml_values['CustomizationID'] = '20'
            self.invoice_id.operation_type = '20'
        else:
            xml_values['CustomizationID'] = '22'
            self.invoice_id.operation_type = '22'
            billing_reference = {
                'ID': False,
                'UUID': False,
                'IssueDate': False,
                'CustomizationID': False}
        #TODO 2.0: Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #91 Nota Crédito
        xml_values['CreditNoteTypeCode'] = '91'
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['CreditNoteLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_debit_note_values(self):
        msg = _("Your journal: %s, has no a credit note sequence")

        if not self.invoice_id.journal_id.refund_sequence_id:
            raise UserError(msg % self.invoice_id.journal_id.name)

        xml_values = self._get_xml_values(False)
        billing_reference = self.invoice_id._get_billing_reference()
        #Punto 14.1.5.3. del anexo tecnico version 1.8
        #30 Nota Débito que referencia una factura electrónica.
        #32 Nota Débito sin referencia a facturas *.
        #33 Nota Débito para facturación electrónica V1 (Decreto 2242).
        if billing_reference:
            xml_values['CustomizationID'] = '30'
            self.invoice_id.operation_type = '30'
        else:
            xml_values['CustomizationID'] = '32'
            self.invoice_id.operation_type = '32'
            billing_reference = {
                'ID': False,
                'UUID': False,
                'IssueDate': False,
                'CustomizationID': False}
        #Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #92 Nota Débito 
        #TODO 2.0: DebitNoteTypeCode no existe en DebitNote
        #xml_values['DebitNoteTypeCode'] = '92'
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['DebitNoteLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_xml_file(self):
        if self.invoice_id.type == "out_invoice":
            xml_without_signature = global_functions.get_template_xml(
                self._get_invoice_values(),
                'Invoice')
        elif self.invoice_id.type == "out_refund" and self.invoice_id.refund_type == "credit": 
            xml_without_signature = global_functions.get_template_xml(
                self._get_credit_note_values(),
                'CreditNote')
        elif self.invoice_id.type == "out_refund" and self.invoice_id.refund_type == "debit": 
            xml_without_signature = global_functions.get_template_xml(
                self._get_debit_note_values(),
                'DebitNote')

        if not url(self.company_id.signature_policy_url):
            return False

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

    def action_set_files(self):
        if self.invoice_id.warn_inactive_certificate:
            raise ValidationError(_("There is no an active certificate."))

        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()

        xml_file = self._get_xml_file()

        if xml_file:
            self.write({'xml_file': b64encode(xml_file)})
            self.write({'zipped_file': b64encode(self._get_zipped_file())})
        else:
            return xml_file

        return True

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

    def _get_pdf_file(self):
        template = self.env['ir.actions.report.xml'].browse(self.company_id.report_template.id)
        pdf = self.env['report'].sudo().get_pdf([self.invoice_id.id], template.report_name)

        return b64encode(pdf)

    @api.multi
    def action_send_mail(self):
        msg = _("Your invoice has not been validated")
        template_id= self.env.ref('l10n_co_account_e_invoicing.email_template_for_einvoice').id
        template = self.env['mail.template'].browse(template_id)

        if not self.invoice_id.number:
            raise UserError(msg)

        xml_attachment = self.env['ir.attachment'].create({
            'name': self.xml_filename,
            'datas_fname': self.xml_filename,
            'datas': self.xml_file})
        pdf_attachment = self.env['ir.attachment'].create({
            'name': self.invoice_id.number + '.pdf',
            'datas_fname': self.invoice_id.number + '.pdf',
            'datas': self._get_pdf_file()})

        if self.invoice_id.invoice_type_code in ('01', '02'):
            ar_xml_attachment = self.env['ir.attachment'].create({
                'name': self.ar_xml_filename,
                'datas_fname': self.ar_xml_filename,
                'datas': self.ar_xml_file})

            template.attachment_ids = [(6, 0, [
                (xml_attachment.id),
                (pdf_attachment.id),
                (ar_xml_attachment.id)])]
        else:
            template.attachment_ids = [(6, 0, [(xml_attachment.id), (pdf_attachment.id)])]

        template.send_mail(self.invoice_id.id, force_send=True)
        self.write({'mail_sent': True})
        xml_attachment.unlink()
        pdf_attachment.unlink()

        if self.invoice_id.invoice_type_code in ('01', '02'):
            ar_xml_attachment.unlink()

        return True

    @api.multi
    def send_failure_email(self):
        msg1 = _("The notification group for e-invoice failures is not set.\n"+
                 "You won't be notified if something goes wrong.\n"+
                 "Please go to Settings > Company > Notification Group.")
        subject = _('ALERT! Invoice %s was not sent to DIAN.') % self.invoice_id.number
        msg_body = _('''Cordial Saludo,<br/><br/>La factura ''' + self.invoice_id.number +
                     ''' del cliente ''' + self.invoice_id.partner_id.name + ''' no pudo ser ''' +
                     '''enviada a la Dian según el protocolo establecido previamente. Por '''
                     '''favor revise el estado de la misma en el menú Documentos Dian e '''
                     '''intente reprocesarla según el procedimiento definido.'''
                     '''<br/>''' + self.company_id.name + '''.''')
        email_ids = self.company_id.notification_group_ids

        if email_ids:
            email_to = ''

            for mail_id in email_ids:
                email_to += mail_id.email.strip() + ','
        else:
            raise UserError(msg1) 

        mail_obj = self.env['mail.mail']
        msg_vals = {
            'subject': subject,
            'email_to': email_to, 
            'body_html': msg_body}
        msg_id = mail_obj.create(msg_vals)
        msg_id.send()

        return True

    def _get_status_response(self, response, send_mail):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        c = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
        s = "http://www.w3.org/2003/05/soap-envelope"
        to_return = True
        strings = ''
        status_code = 'other'
        root = etree.fromstring(response.content)

        for element in root.iter("{%s}StatusCode" % b):
            if element.text in ('0', '00', '66', '90', '99'):
                if element.text == '00':
                    self.write({'state': 'done'})

                status_code = element.text

        if status_code == '0':
            return self._get_GetStatus(send_mail)

        if status_code == '00':
            for element in root.iter("{%s}StatusMessage" % b):
                strings = element.text

            for element in root.iter("{%s}XmlBase64Bytes" % b):
                self.write({'ar_xml_file': element.text})

            if not self.mail_sent and send_mail:
                self.action_send_mail()
            
            to_return = True
        else:
            if send_mail:
                self.send_failure_email()

            to_return = False

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

        return to_return

    def _get_GetStatusZip_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.zip_key

        return xml_soap_values

    def action_GetStatusZip(self):
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        GetStatusZip_values = self._get_GetStatusZip_values()
        GetStatusZip_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatusZip_values, 'GetStatusZip'),
            GetStatusZip_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature))

        if response.status_code == 200:
            self._get_status_response(response, True)
        else:
            raise ValidationError(response.status_code)

        return True

    def action_send_zipped_file(self):
        if self._get_GetStatus(False):
            return True

        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s,\n\nContact with your administrator "
                "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
                "and change the Invoice Type to 'Biller Contingency Invoice'.")
        msg2 = _("Unknown Error: %s\n\nContact with your administrator "
                "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
                "and change the Invoice Type to 'Biller Contingency Invoice'.")
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']
            SendBillAsync_values = self._get_SendBillAsync_values()
            SendBillAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendBillAsync_values, 'SendBillSync'),
                SendBillAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)
        else:
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            SendTestSetAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendTestSetAsync_values, 'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature))

            if response.status_code == 200:
                self.write({'state': 'sent'})

                if self.company_id.profile_execution_id == '1':
                    self._get_status_response(response, True)
                else:
                    root = etree.fromstring(response.text)

                    for element in root.iter("{%s}ZipKey" % b):
                        self.write({'zip_key': element.text})
                        self.action_GetStatusZip()
            elif response.status_code in (500, 503, 507):
                dian_document_line_obj = self.env['account.invoice.dian.document.line']
                dian_document_line_obj.create({
                    'dian_document_id': self.id,
                    'send_async_status_code': response.status_code,
                    'send_async_reason': response.reason,
                    'send_async_response': response.text})
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))
        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True

    def _get_GetStatus_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.cufe_cude

        return xml_soap_values

    def _get_GetStatus(self, send_mail):
        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s"
                 "\n\nContact with your administrator.")
        msg2 = _("Unknown Error: %s\n\nContact with your administrator.")
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
            GetStatus_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature))

            if response.status_code == 200:
                return self._get_status_response(response, send_mail)
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))
        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

    def action_GetStatus_without_send_mail(self):
        return self._get_GetStatus(False)

    def action_process(self):
        if self.action_set_files():
            self.action_send_zipped_file()
        else:
            self.send_failure_email()

        return True

    #TODO: 2.0
    def _get_SendBillAttachmentAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)
        output = StringIO()
        zipfile = ZipFile(output, mode='w')
        zipfile_content = StringIO()
        zipfile_content.write(b64decode(self.xml_file))
        zipfile.writestr(self.xml_filename, zipfile_content.getvalue())
        zipfile_content = StringIO()
        zipfile_content.write(b64decode(self.ar_xml_file))
        zipfile.writestr(self.ar_xml_filename, zipfile_content.getvalue())
        zipfile.close()
        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = b64encode(output.getvalue())

        return xml_soap_values

    def action_SendBillAttachmentAsync(self):
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        SendBillAttachmentAsync_values = self._get_SendBillAttachmentAsync_values()
        SendBillAttachmentAsync_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(
                SendBillAttachmentAsync_values,
                'SendBillAttachmentAsync'),
            SendBillAttachmentAsync_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature))
            
        if response.status_code == 200:
            root = etree.fromstring(response.text)

            #raise Warning(response.text)

        return True
