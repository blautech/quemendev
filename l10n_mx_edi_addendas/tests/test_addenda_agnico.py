# See LICENSE file for full copyright and licensing details.

from .common import AddendasTransactionCase


class TestAddendaAgnico(AddendasTransactionCase):

    def setUp(self):
        super(TestAddendaAgnico, self).setUp()
        self.install_addenda('agnico')

    def test_001_addenda_agnico(self):
        invoice = self.create_invoice()
        invoice.ref = '0131'
        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))

        # Check addenda has been appended and it's equal to the expected one
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")
        expected_addenda = self.get_expected_addenda('agnico')
        self.assertEqualXML(xml.Addenda, expected_addenda)