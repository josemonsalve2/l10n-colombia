# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    send_zip_code = fields.Boolean(string='Send Zip Code?')
    is_einvoicing_agent = fields.Selection(
        [('yes', 'Yes'),
         ('no_but', 'No, but has email'),
         ('no', 'No'),
         ('unknown', 'Unknown')],
        string='Is an E-Invoicing Agent?',
        default=False)
    einvoicing_email = fields.Char(string='E-Invoicing Email')
    view_einvoicing_email_field = fields.Boolean(
        string="View 'E-Invoicing Email' Fields",
        compute='_get_view_einvoicing_email_field',
        store=False)
    edit_is_einvoicing_agent_field = fields.Boolean(
        string="Edit 'Is an E-Invoicing Agent?' Field",
        compute='_get_edit_is_einvoicing_agent_field',
        store=False)

    @api.onchange('person_type')
    def onchange_person_type(self):
        super(ResPartner, self).onchange_person_type()

        if self.person_type == '1':
            self.is_einvoicing_agent = 'yes'

        self.property_account_position_id = False

    @api.multi
    def _get_view_einvoicing_email_field(self):
        user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        view_einvoicing_email_field = False

        if user.has_group('l10n_co_account_e_invoicing.group_view_einvoicing_email_fields'):
            view_einvoicing_email_field = True

        for partner in self:
            partner.view_einvoicing_email_field = view_einvoicing_email_field

    @api.multi
    def _get_edit_is_einvoicing_agent_field(self):
        user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        edit_is_einvoicing_agent_field = False

        if user.has_group('l10n_co_account_e_invoicing.group_edit_is_einvoicing_agent_field'):
            edit_is_einvoicing_agent_field = True

        for partner in self:
            partner.edit_is_einvoicing_agent_field = edit_is_einvoicing_agent_field

    @api.constrains('einvoicing_email')
    @api.onchange('einvoicing_email')
    def validate_mail(self):
        if self.einvoicing_email:
            match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", self.einvoicing_email)

            if match is None:
                raise ValidationError(_("The field 'E-Invoicing Email' is not correctly filled.\n\n"
                                        "Please add @ and dot (.)"))

    def _get_accounting_partner_party_values(self):
        msg1 = _("'%s' does not have a person type established.")
        msg2 = _("'%s' does not have a city established.")
        msg3 = _("'%s' does not have a state established.")
        msg4 = _("'%s' does not have a country established.")
        msg5 = _("'%s' does not have a verification digit established.")
        msg6 = _("'%s' does not have a DIAN document type established.")
        msg7 = _("The document type of '%s' does not seem to correspond with the person type.")
        msg8 = _("'%s' does not have a identification document established.")
        msg9 = _("'%s' does not have a fiscal position correctly configured.")
        msg10 = _("'%s' does not have a fiscal position established.")
        msg11 = _("E-Invoicing Agent: '%s' does not have a E-Invoicing Email.")
        name = self.name
        zip_code = False
        identification_document = self.identification_document
        telephone = False

        if not self.person_type:
            raise UserError(msg1 % self.name)

        if self.country_id:
            if self.country_id.code == 'CO':
                if not self.zip_id:
                    raise UserError(msg2 % self.name)
                elif not self.state_id:
                    raise UserError(msg3 % self.name)
        else:
            raise UserError(msg4 % self.name)

        if self.document_type_id:
            document_type_code = self.document_type_id.code

            if document_type_code == '31' and not self.check_digit:
                raise UserError(msg5 % self.name)

            # Punto 6.2.1. Documento de identificación (Tipo de Identificador Fiscal):
            # cbc:CompanyID.@schemeName; sts:ProviderID.@schemeName del anexo técnico version 1.7
            if document_type_code not in ('11', '12', '13', '21', '22', '31', '41', '42', '50', '91'):
                if self.person_type == '1':
                    raise UserError(msg6 % self.name)
                else:
                    name = 'consumidor final'
                    document_type_code = '13'
                    identification_document = '222222222222'
        else:
            raise UserError(msg6 % self.name)

        if ((self.person_type == '1' and document_type_code not in ('31', '50'))
                or (self.person_type == '2' and document_type_code in ('31', '50'))):
            raise UserError(msg7 % self.name)

        if not identification_document:
            raise UserError(msg8 % self.name)

        if self.property_account_position_id:
            if (not self.property_account_position_id.tax_level_code_ids
                    or not self.property_account_position_id.tax_group_type_id
                    or not self.property_account_position_id.listname):
                raise UserError(msg9 % self.name)

            tax_level_codes = ''
            tax_scheme_code = self.property_account_position_id.tax_group_type_id.code
            tax_scheme_name = self.property_account_position_id.tax_group_type_id.name
        else:
            raise UserError(msg10 % self.name)

        if ((self.is_einvoicing_agent in ('yes', 'not_but') or not self.is_einvoicing_agent)
                and not self.einvoicing_email):
            raise UserError(msg11 % self.name)

        if self.send_zip_code:
            if self.zip_id:
                zip_code = self.zip_id.name

        for tax_level_code_id in self.property_account_position_id.tax_level_code_ids:
            if tax_level_codes == '':
                tax_level_codes = tax_level_code_id.code
            else:
                tax_level_codes += ';' + tax_level_code_id.code

        if self.phone and self.mobile:
            telephone = self.phone + " / " + self.mobile
        elif self.lastname:
            telephone = self.phone
        elif self.lastname2:
            telephone = self.mobile

        if identification_document == '222222222222':
            tax_level_codes = 'R-99-PN'
            tax_scheme_code = 'ZY'
            tax_scheme_name = 'No causa'

            if self.property_account_position_id.listname != '49':
                raise UserError(msg8 % self.name)

        return {
            'AdditionalAccountID': self.person_type,
            'PartyName': self.commercial_name,
            'Name': name,
            'AddressID': self.zip_id.code or '',
            'AddressCityName': self.zip_id.city or '',
            'AddressPostalZone': zip_code,
            'AddressCountrySubentity': self.state_id.name or '',
            'AddressCountrySubentityCode': self.state_id.code or '',
            'AddressLine': self.street or '',
            'CompanyIDschemeID': self.check_digit,
            'CompanyIDschemeName': document_type_code,
            'CompanyID': identification_document,
            'listName': self.property_account_position_id.listname,
            'TaxLevelCode': tax_level_codes,
            'TaxSchemeID': tax_scheme_code,
            'TaxSchemeName': tax_scheme_name,
            'CorporateRegistrationSchemeName': self.coc_registration_number,
            'CountryIdentificationCode': self.country_id.code,
            'CountryName': self.country_id.name,
            'Telephone': telephone,
            'Telefax': self.fax,
            'ElectronicMail': self.einvoicing_email}

    def _get_delivery_values(self):
        msg1 = _("'%s' does not have a city established.")
        msg2 = _("'%s' does not have a state established.")
        msg3 = _("'%s' does not have a country established.")
        zip_code = False

        if self.country_id:
            if self.country_id.code == 'CO':
                if not self.zip_id:
                    raise UserError(msg1 % self.name)
                elif not self.state_id:
                    raise UserError(msg2 % self.name)
        else:
            raise UserError(msg3 % self.name)

        if self.send_zip_code:
            if self.zip_id:
                zip_code = self.zip_id.name

        return {
            'AddressID': self.zip_id.code or '',
            'AddressCityName': self.zip_id.city or '',
            'AddressPostalZone': zip_code,
            'AddressCountrySubentity': self.state_id.name or '',
            'AddressCountrySubentityCode': self.state_id.code or '',
            'AddressLine': self.street or '',
            'CountryIdentificationCode': self.country_id.code,
            'CountryName': self.country_id.name}

    def _get_tax_representative_party_values(self):
        msg1 = _("'%s' does not have a verification digit established.")
        msg2 = _("'%s' does not have a document type established.")
        msg3 = _("'%s' does not have a identification document established.")

        if self.document_type_id:
            if self.document_type_id.code == '31' and not self.check_digit:
                raise UserError(msg1 % self.name)
        else:
            raise UserError(msg2 % self.name)

        if not self.identification_document:
            raise UserError(msg3 % self.name)

        return {
            'IDschemeID': self.check_digit,
            'IDschemeName': self.document_type_id.code,
            'ID': self.identification_document}
