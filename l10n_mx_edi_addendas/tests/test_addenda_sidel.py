# See LICENSE file for full copyright and licensing details.

from .common import AddendasTransactionCase


class TestAddendaSidel(AddendasTransactionCase):

    def setUp(self):
        super(TestAddendaSidel, self).setUp()
        self.install_addenda('sidel')

    def test_001_addenda_sidel(self):
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        tax_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= tax_tag

        invoice = self.create_invoice()
        invoice.ref = '5644544'
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
            'name': self.product.name,
            'tax_ids': [(6, 0, taxes)],
        })]

        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))

        # Check addenda has been appended and it's equal to the expected one
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")
        expected_addenda = self.get_expected_addenda('sidel')
        self.assertEqualXML(xml.Addenda, expected_addenda)
