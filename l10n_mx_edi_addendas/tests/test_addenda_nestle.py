# See LICENSE file for full copyright and licensing details.

from .common import AddendasTransactionCase


class TestAddendaNestle(AddendasTransactionCase):

    def setUp(self):
        super(TestAddendaNestle, self).setUp()
        self.install_addenda('nestle')
        self.partner_agrolait.write({
            'type': 'delivery',
            'city': 'City Test 1',
            'l10n_mx_edi_colony': 'Colony Test 1',
        })
        self.partner_agrolait.parent_id.write({
            'city': 'City Test 2',
            'l10n_mx_edi_colony': 'Colony Test 2',
        })

    def test_001_addenda_nestle(self):
        """Tests addenda for Nestle

        Tests both possible cases of the addenda for Nestle:
        - Customer invoice
        - Customer refund
        """
        # ---------------------
        # Test Customer Invoice
        # ---------------------
        invoice = self.create_invoice()
        invoice.ref = '369796'
        invoice.name = 'INV/2018/0932'
        invoice.invoice_line_ids.x_addenda_sap_code = 'SP-002'
        self.set_wizard_values(invoice, 'nestle', {
            'x_incoming_code': 'IC002',
        })

        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))

        # Check addenda has been appended and it's equal to the expected one
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")
        expected_addenda = self.get_expected_addenda('nestle')
        self.assertEqualXML(xml.Addenda, expected_addenda)

        # --------------------
        # Test Customer refund
        # --------------------
        ctx = {'active_ids': invoice.ids, 'active_model': 'account.move'}
        refund = self.env['account.move.reversal'].with_context(ctx).create({
            'refund_method': 'refund',
            'reason': 'Refund Test',
            'date': invoice.invoice_date,
        })
        result = refund.reverse_moves()
        refund_id = result.get('res_id')
        invoice_refund = self.env['account.move'].browse(refund_id)
        invoice_refund.name = 'INV/2018/0933'
        invoice_refund.invoice_origin = invoice.name
        invoice_refund.refresh()
        invoice_refund.action_post()
        self.assertEqual(invoice_refund.l10n_mx_edi_pac_status, "signed",
                         invoice_refund.message_ids.mapped('body'))

        # Check addenda has been appended and it's equal to the expected one
        invoice_refund.refresh()
        xml = invoice_refund.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")
        expected_addenda = self.get_expected_addenda('nestle_nc')
        self.assertEqualXML(xml.Addenda, expected_addenda)
