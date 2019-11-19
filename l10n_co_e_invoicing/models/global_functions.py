# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import os
from jinja2 import Environment, FileSystemLoader

def generate_cufe_cude(
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

    return CUFE_CUDE.hexdigest()

def generate_software_security_code(IdSoftware,Pin,NroDocumentos):
    uncoded_value = (IdSoftware + ' + ' + Pin + ' + ' + NroDocumentos)
    software_security_code = hashlib.sha384(IdSoftware + Pin + NroDocumentos)

    return software_security_code.hexdigest()

def get_template_xml(values, template_name):
        base_path = os.path.dirname(os.path.dirname(__file__))
        env = Environment(
            loader=FileSystemLoader(os.path.join(base_path, 'templates')))
        template = env.get_template('{}.xml'.format(template_name))
        xml = template.render(values)
        xml = xml.replace('&', '&amp;')

        return xml
