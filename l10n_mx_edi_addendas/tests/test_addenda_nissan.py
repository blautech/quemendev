# See LICENSE file for full copyright and licensing details.

import os

from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import misc


class MxEdiAddendaNissan(InvoiceTransactionCase):
    def setUp(self):
        super(MxEdiAddendaNissan, self).setUp()
        conf = self.env['res.config.settings'].create({
            'l10n_mx_addenda': 'nissan'})
        conf.install_addenda()
        self.partner_agrolait.l10n_mx_edi_addenda = self.env.ref(
            'l10n_mx_edi_addendas.nissan')
        self.partner_agrolait.street_number2 = '8098'
        nissan_expected = misc.file_open(os.path.join(
            'l10n_mx_edi_addendas', 'tests', 'nissan_expected.xml')
        ).read().encode('UTF-8')
        self.addenda_tree = fromstring(nissan_expected)

    def test_001_addenda_in_xml(self):
        """test addenda nissan"""
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        tax_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= tax_tag

        invoice = self.create_invoice()
        invoice.partner_shipping_id = self.partner_agrolait
        invoice.line_ids.unlink()
        invoice.invoice_line_ids.unlink()
        taxes = [self.tax_positive.id, self.tax_negative.id]
        invoice.invoice_line_ids = [(0, 0, {
            'account_id':
            self.product.product_tmpl_id.get_product_accounts()['income'].id,
            'product_id': self.product.id,
            'move_id': invoice.id,
            'quantity': 1,
            'price_unit': 450,
            'product_uom_id': self.product.uom_id.id,
            'name': self.product.display_name,
            'tax_ids': [(6, 0, taxes)],
        })]

        # wizard values
        invoice.x_addenda_nissan = '123|12|1234||10.00'
        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is not Addenda node")
        nissan_nodes = xml.Addenda.getchildren()
        nissan_nodes[0].attrib['cCadena'] = ""
        nissan_nodes[1].Detalle.attrib['SERIE'] = ''
        nissan_nodes[1].Detalle.attrib['DOCUMENTO'] = ''
        self.assertEqualXML(xml.Addenda, self.addenda_tree)
