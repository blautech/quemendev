# See LICENSE file for full copyright and licensing details.

from .common import AddendasTransactionCase


class TestAddendaEnvases(AddendasTransactionCase):

    def test_001_addenda_envases(self):
        self.install_addenda('envases')
        self.namespaces = {
            "eu": "http://factura.envasesuniversales.com/addenda/eu"
        }
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        tax_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= tax_tag

        invoice = self.create_invoice()
        self.set_wizard_values(invoice, 'envases', {
            'x_incoming_code': '12345',
        })

        invoice.ref = "PO456"
        invoice.name = "INV/2019/987456"
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

        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")

        expected_addenda = self.get_expected_addenda('envases')
        xml.xpath('//eu:TipoFactura/eu:FechaMensaje',
                  namespaces=self.namespaces)[0]._setText('2018-12-06')

        self.assertEqualXML(xml.Addenda, expected_addenda)
