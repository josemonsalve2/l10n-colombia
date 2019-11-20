# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import os
from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader

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

def get_template_xml(values, template_name):
    base_path = os.path.dirname(os.path.dirname(__file__))
    env = Environment(loader=FileSystemLoader(os.path.join(
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
