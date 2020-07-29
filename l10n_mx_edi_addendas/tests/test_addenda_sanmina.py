# See LICENSE file for full copyright and licensing details.

from .common import AddendasTransactionCase


class TestAddendaSanmina(AddendasTransactionCase):

    def setUp(self):
        super(TestAddendaSanmina, self).setUp()
        self.install_addenda('sanmina')

    def test_001_addenda_sanmina(self):
        invoice = self.create_invoice()
        invoice.ref = '5644544'
        invoice.name = "INV/2018/987456"
        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))

        # Check addenda has been appended and it's equal to the expected one
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")
        expected_addenda = self.get_expected_addenda('sanmina')
        self.assertEqualXML(xml.Addenda, expected_addenda)
