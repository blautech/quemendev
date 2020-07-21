# See LICENSE file for full copyright and licensing details.

import os

from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import misc


class MxEdiAddendaCalsonicKansei(InvoiceTransactionCase):
    def setUp(self):
        super(MxEdiAddendaCalsonicKansei, self).setUp()
        conf = self.env['res.config.settings'].create({
            'l10n_mx_addenda': 'calsonic_kansei'})
        conf.install_addenda()
        self.partner_agrolait.l10n_mx_edi_addenda = self.env.ref(
            'l10n_mx_edi_addendas.calsonickansei')
        calsonickansei_expected = misc.file_open(os.path.join(
            'l10n_mx_edi_addendas', 'tests', 'calsonickansei_expected.xml')
        ).read().encode('UTF-8')
        self.addenda_tree = fromstring(calsonickansei_expected)

    def test_001_addenda_in_xml(self):
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        invoice = self.create_invoice()
        invoice.currency_id = self.mxn.id
        invoice.ref = '0131'
        invoice.action_post()
        invoice.refresh()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        self.assertTrue(hasattr(xml, 'Addenda'), "There is not Addenda node")
        self.assertEqualXML(xml.Addenda, self.addenda_tree)
