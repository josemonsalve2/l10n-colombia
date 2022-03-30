# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from urllib import request
from urllib.error import URLError, HTTPError
from requests import post, exceptions
from lxml import etree
import ssl
from . import global_functions
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

ssl._create_default_https_context = ssl._create_unverified_context


class ResCompany(models.Model):
    _inherit = "res.company"

    einvoicing_enabled = fields.Boolean(string='E-Invoicing Enabled')
    automatic_delivery_datetime = fields.Boolean(
        string='Automatic Delivery Datetime?')
    additional_hours_delivery_datetime = fields.Float(
        string='Additional Hours',
        help='Additional hours to invoice date for delivery date',
        digits=(12, 4),
        default=False)
    send_invoice_to_dian = fields.Selection(
        selection=[
            ('0', 'Immediately'),
            ('1', 'After 1 Day'),
            ('2', 'After 2 Days')],
        string='Send Invoice to DIAN?',
        default='0')
    profile_execution_id = fields.Selection(
        selection=[('1', 'Production'), ('2', 'Test')],
        string='Destination Environment of Document',
        default='2',
        required=True)
    have_technological_provider = fields.Boolean(
        string='Do you have a technological provider?')
    technological_provider_id = fields.Many2one(
        string='Technological Provider',
        comodel_name='res.partner')
    assignment_code = fields.Char(string='Assignment Code', size=3)
    test_set_id = fields.Char(string='Test Set ID')
    software_id = fields.Char(string='Software ID')
    software_pin = fields.Char(string='Software PIN')
    certificate_filename = fields.Char(string='Certificate Filename')
    certificate_file = fields.Binary(string='Certificate File')
    certificate_password = fields.Char(string='Certificate Password')
    certificate_date = fields.Date(string='Certificate Date Validity')
    certificate_remaining_days = fields.Integer(
        string='Certificate Remaining Days',
        default=False)
    signature_policy_url = fields.Char(
        string='Signature Policy URL',
        default='https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf')
    certificate_remaining_days = fields.Integer(
        string='Certificate Remaining Days', default=False)
    signature_policy_url = fields.Char(string='Signature Policy URL')
    signature_policy_description = fields.Char(
        string='Signature Policy Description',
        default='Política de firma para facturas electrónicas de la República de Colombia.')
    files_path = fields.Char(string='Files Path')
    einvoicing_email = fields.Char(
        string='E-Invoice Email, From:',
        help="Enter the e-invoice sender's email.")
    einvoicing_partner_no_email = fields.Char(
        string='Failed Emails, To:',
        help='Enter the email where the invoice will be sent when the customer does not have an email.')
    einvoicing_receives_all_emails = fields.Char(string='Email that receives all emails')
    report_template = fields.Many2one(
        string='Report Template',
        comodel_name='ir.actions.report')
    notification_group_ids = fields.One2many(
        comodel_name='einvoice.notification.group',
        inverse_name='company_id',
        string='Notification Group')
    get_numbering_range_response = fields.Text(string='GetNumberingRange Response')

    @api.multi
    def write(self, vals):
        msg = _('Invalid URL.')

        if vals.get('signature_policy_url'):
            try:
                for company in self:
                    response = request.urlopen(
                        vals.get('signature_policy_url'), timeout=2)

                    if response.getcode() != 200:
                        raise ValidationError(msg)
            except HTTPError as e:
                raise ValidationError(msg % e)
            except URLError as e:
                raise ValidationError(msg % e)
            else:
                raise ValidationError(msg % "No se sabe")

        rec = super(ResCompany, self).write(vals)

        if vals.get('certificate_file') or vals.get('certificate_password'):
            for company in self:
                pkcs12 = global_functions.get_pkcs12(
                    company.certificate_file, company.certificate_password)
                x509 = pkcs12.get_certificate()
                date = x509.get_notAfter()
                company.certificate_date = datetime.strptime(
                    date.decode("utf-8"), '%Y%m%d%H%M%SZ').date()

        return rec

    def _get_GetNumberingRange_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.certificate_file, self.certificate_password)

        xml_soap_values['accountCode'] = self.partner_id.identification_document
        xml_soap_values['accountCodeT'] = self.partner_id.identification_document
        xml_soap_values['softwareCode'] = self.software_id

        if self.have_technological_provider:
            xml_soap_values['accountCodeT'] = self.technological_provider_id.identification_document

        return xml_soap_values

    def action_GetNumberingRange(self):
        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s.")
        msg2 = _("Unknown Error: %s\n.")
        wsdl = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl'
        s = "http://www.w3.org/2003/05/soap-envelope"

        GetNumberingRange_values = self._get_GetNumberingRange_values()
        GetNumberingRange_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
             global_functions.get_template_xml(
                GetNumberingRange_values, 'GetNumberingRange'),
            GetNumberingRange_values['Id'],
            self.certificate_file,
            self.certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature))

            if response.status_code == 200:
                root = etree.fromstring(response.text)
                response = ''

                for element in root.iter("{%s}Body" % s):
                    response = etree.tostring(element, pretty_print=True)

                if response == '':
                    response = etree.tostring(root, pretty_print=True)

                self.write({'get_numbering_range_response': response})
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))

        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True

    @api.multi
    def action_process_dian_documents(self):
        for company in self:
            count = 0
            dian_documents = self.env['account.invoice.dian.document'].search(
                [('state', 'in', ('draft', 'sent')), ('company_id', '=', company.id)],
                 order='zipped_filename asc')

            for dian_document in dian_documents:
                today = fields.Date.context_today(self)
                date_from = dian_document.invoice_id.date_invoice
                days = (today - date_from).days

                if int(dian_document.invoice_id.send_invoice_to_dian) <= days:
                    dian_document.action_process()
                    count += 1

                if count == 10:
                    return True

        return True

    @api.model
    def cron_process_dian_documents(self):
        for company in self.search([]):
            company.action_process_dian_documents()
