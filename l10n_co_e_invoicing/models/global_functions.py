# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import xmlsig
from os import path
from lxml import etree
from uuid import uuid4
from xades import XAdESContext, template
from xades.policy import GenericPolicyId
from OpenSSL import crypto
from base64 import b64decode
from StringIO import StringIO
from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader
#from mock import patch

def get_cufe_cude(
    NumFac,
    FecFac,
    HorFac,
    ValFac,
    CodImp1,
    ValImp1,
    CodImp2,
    ValImp2,
    CodImp3,
    ValImp3,
    ValTot,
    NitOFE,
    NumAdq,
    ClTec,
    SoftwarePIN,
    TipoAmbie):
    #CUFE = SHA-384(NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 +
    # CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
    # ClTec + TipoAmbie)
    #CUDE = SHA-384(NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 +
    # CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
    # Software-PIN + TipoAmbie)
    uncoded_value = (NumFac + ' + ' + FecFac + ' + ' + HorFac + ' + ' +
        ValFac + ' + ' + CodImp1 + ' + ' + ValImp1 + ' + ' + CodImp2 + ' + ' +
        ValImp2 + ' + ' + CodImp3 + ' + ' +  ValImp3 + ' + ' + ValTot + ' + ' +
        NitOFE + ' + ' + NumAdq + ' + ' + ClTec if ClTec else SoftwarePIN +
        ' + ' + TipoAmbie)
    CUFE_CUDE = hashlib.sha384(
        NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 + CodImp2 +
        ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
        ClTec if ClTec else SoftwarePIN + TipoAmbie)

    return {
        'CUFE/CUDEUncoded': uncoded_value,
        'CUFE/CUDE': CUFE_CUDE.hexdigest()}

def get_software_security_code(IdSoftware,Pin,NroDocumentos):
    uncoded_value = (IdSoftware + ' + ' + Pin + ' + ' + NroDocumentos)
    software_security_code = hashlib.sha384(IdSoftware + Pin + NroDocumentos)

    return {
        'SoftwareSecurityCodeUncoded': uncoded_value,
        'SoftwareSecurityCode': software_security_code.hexdigest()}

#https://stackoverflow.com/questions/38432809/dynamic-xml-template-generation-using-get-template-jinja2
def get_template_xml(values, template_name):
    base_path = path.dirname(path.dirname(__file__))
    env = Environment(loader=FileSystemLoader(path.join(
        base_path,
        'templates')))
    template = env.get_template('{}.xml'.format(template_name))
    xml = template.render(values) 

    return xml.replace('&', '&amp;')

def get_period_dates(base_date):
    split_date = base_date.split('-')
    current_year = int(split_date[0])
    current_month = int(split_date[1])

    if current_month == 12:
        year = current_year + 1
        month = 1
    else:
        year = current_year
        month = current_month + 1
        
    period_start_date = date(current_year, current_month, 1)
    period_end_date = date(year, month, 1) - timedelta(days=1)

    return {
        'PeriodStartDate': period_start_date.strftime("%Y-%m-%d"),
        'PeriodEndDate': period_end_date.strftime("%Y-%m-%d")}

#https://github.com/xoe-labs/python-xades
def get_xml_with_signature(
    xml_without_signature,
    signature_policy_url,
    signature_policy_description,
    certificate_file,
    certificate_password):
    ##https://github.com/etobella/python-xades/blob/master/test/base.py
    #base_path = path.dirname(path.dirname(__file__))
    #root = etree.parse(path.join(base_path, name)).getroot()
    #https://lxml.de/tutorial.html#the-parse-function
    root = etree.XML(
        xml_without_signature,
        parser=etree.XMLParser(encoding='utf-8'))
    #https://github.com/etobella/python-xades/blob/master/test/test_xades.py
    signature_id = "xmldsig-{}".format(uuid4())
    signature = xmlsig.template.create(
        xmlsig.constants.TransformInclC14N,
        xmlsig.constants.TransformRsaSha512,
        signature_id)
    ref = xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="",
        name=signature_id + "-ref0")
    xmlsig.template.add_transform(
        ref,
        xmlsig.constants.TransformEnveloped)
    xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="#" + signature_id + "-keyinfo")
    xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="#" + signature_id + "-signedprops",
        uri_type="http://uri.etsi.org/01903#SignedProperties")
    ki = xmlsig.template.ensure_key_info(
        signature,
        name=signature_id + "-keyinfo")
    data = xmlsig.template.add_x509_data(ki)
    xmlsig.template.x509_data_add_certificate(data)
    serial = xmlsig.template.x509_data_add_issuer_serial(data)
    xmlsig.template.x509_issuer_serial_add_issuer_name(serial)
    xmlsig.template.x509_issuer_serial_add_serial_number(serial)
    xmlsig.template.add_key_value(ki)
    qualifying = template.create_qualifying_properties(signature)
    props = template.create_signed_properties(
        qualifying,
        name=signature_id + "-signedprops")
    template.add_claimed_role(props, "supplier")
    policy = GenericPolicyId(
        signature_policy_url,
        signature_policy_description,
        xmlsig.constants.TransformSha512)
    root.append(signature)
    ctx = XAdESContext(policy)
    ctx.load_pkcs12(crypto.load_pkcs12(
        b64decode(certificate_file),
        certificate_password))
    #with patch("xades.policy.urllib.urlopen") as mock:
    #    mock.return_value = b64decode(signature_policy_file).read()
    ctx.sign(signature)
    #ctx.verify(signature)

    #Complememto para corregir errores y posicionar bien los valores
    root.remove(signature)
    ext = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    ds = "http://www.w3.org/2000/09/xmldsig#"
    position = 0
    #https://lxml.de/tutorial.html#the-parse-function
    for element in root.iter("{%s}ExtensionContent" % ext):
        if position == 1:
            element.append(signature)
        position += 1
    
    for element in root.iter("{%s}SignatureValue" % ds):
        element.attrib['Id'] = signature_id + "-sigvalue"
    #https://www.decalage.info/en/python/lxml-c14n
    output = StringIO()
    root.getroottree().write_c14n(output)
    root = output.getvalue()

    return root
