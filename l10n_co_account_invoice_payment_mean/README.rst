.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================================================
Formas y medios de pago para la localizacion Colombiana
=======================================================

Este módulo tiene las formas y medios de pago identificados por la DIAN para la
localizacion Colombiana, informacion obtenida del anexo tecnico para
facturacion electronica version 1.8, punto 14.3.4.

- Crea un campo en la factura para definir la forma de pago que tuvo, se creo
    una funcion 'onchange' que establece 'Contado' si la fecha de la factura es
    igual a la fecha de vencimiento, si no, establece 'Crédito'.

Known issues / Roadmap
======================

Future possible improvement:
Habilitar campo 'payment_mean_code_id' correspondiente al medio de pago, queda
pendiente porque hay que analizar si con este campo en tipo 'Many2one' es
suficiente para suplir el requerimiento o puede ser necesario establecer un
campo One2many ya que la factura podría tener 2 o mas pagos y cada uno podría
ser con un medio de pago diferente, o pensar en una solución mas avanzada que
este relacionada con el pago de las facturas en Odoo.

Credits
=======

Contributors
------------

* Juan Camilo Zuluaga Serna <https://github.com/camilozuluaga>
* Joan Marín <https://github.com/JoanMarin>
