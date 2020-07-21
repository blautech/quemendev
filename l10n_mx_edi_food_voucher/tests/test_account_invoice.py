import base64
from lxml import objectify
from odoo import fields
from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase


class TestL10nMxEdiInvoiceVoucher(InvoiceTransactionCase):

    def test_l10n_mx_edi_voucher_invoice(self):
        product_model = self.env['product.product']
        partner_model = self.env['res.partner']
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        iva_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= iva_tag
        detail = product_model.create({
            'name': 'Voucher Detail',
            'type': 'service',
            'categ_id': self.ref('product.product_category_all'),
            'l10n_mx_edi_code_sat_id': self.ref('l10n_mx_edi.prod_code_sat_01010101') # noqa
        })
        employee_lines = [
            partner_model.browse(self.ref('base.res_partner_address_4')),
            partner_model.browse(self.ref('base.res_partner_address_3'))]
        for employee in employee_lines:
            employee.parent_id.write({'country_id': self.ref('base.mx'), })
            employee.write({
                'vat': 'XAXX010101000',
                'ref': '4068010004070241',
                'l10n_mx_edi_curp': 'AAAA010101HCLJND07',
                'l10n_mx_edi_voucher_nss': '91234567890',
            })
        invoice = self.create_invoice()
        invoice.partner_id = self.ref('base.res_partner_12')
        invoice.line_ids.unlink()
        invoice.invoice_line_ids.unlink()
        invoice.invoice_line_ids = ([(0, 0, {
            'product_id': self.product.id,
            'name': self.product.name,
            'quantity': 1,
            'price_unit': 1500.00,
            'account_id': self.ref('l10n_mx.1_cuenta401_01'),
            'product_uom_id': self.ref('uom.product_uom_unit'),
            'tax_ids': [self.tax_positive.id]
        }), (0, 0, {
            'product_id': detail.id,
            'name': detail.name,
            'quantity': 0.0,
            'price_unit': 100.0,
            'account_id': self.ref('l10n_mx.1_cuenta401_01'),
            'l10n_mx_edi_voucher_id': self.ref('base.res_partner_address_4'),
            'product_uom_id': self.ref('uom.product_uom_unit')
        }), (0, 0, {
            'product_id': detail.id,
            'name': detail.name,
            'quantity': 0.0,
            'price_unit': 100.0,
            'account_id': self.ref('l10n_mx.1_cuenta401_01'),
            'l10n_mx_edi_voucher_id': self.ref('base.res_partner_address_3'),
            'product_uom_id': self.ref('uom.product_uom_unit')
        })])

        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml_str = base64.b64decode(
            invoice.l10n_mx_edi_retrieve_last_attachment().datas)
        xml = objectify.fromstring(xml_str)
        xml_expected = objectify.fromstring(
            '<valesdedespensa:ValesDeDespensa '
            'xmlns:valesdedespensa="http://www.sat.gob.mx/valesdedespensa" '
            'version="1.0" tipoOperacion="monedero electrónico" '
            'numeroDeCuenta="123456789" total="200.0">'
            '<valesdedespensa:Conceptos>'
            '<valesdedespensa:Concepto identificador="4068010004070241" '
            'fecha="%(voucher_date)s" rfc="XAXX010101000" '
            'curp="AAAA010101HCLJND07" nombre="Floyd Steward" '
            'numSeguridadSocial="91234567890" importe="100.0"/>'
            '<valesdedespensa:Concepto identificador="4068010004070241" '
            'fecha="%(voucher_date)s" rfc="XAXX010101000" '
            'curp="AAAA010101HCLJND07" nombre="Douglas Fletcher" '
            'numSeguridadSocial="91234567890" importe="100.0"/>'
            '</valesdedespensa:Conceptos>'
            '</valesdedespensa:ValesDeDespensa>' % {
                'voucher_date': ('T').join(
                    (fields.Date.to_string(invoice.invoice_date),
                     invoice.l10n_mx_edi_time_invoice))})
        namespaces = {
            'valesdedespensa': 'http://www.sat.gob.mx/valesdedespensa'}
        comp = xml.Complemento.xpath('//valesdedespensa:ValesDeDespensa',
                                     namespaces=namespaces)
        self.assertEqualXML(comp[0], xml_expected)
