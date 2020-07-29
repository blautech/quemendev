# See LICENSE file for full copyright and licensing details.

import os

from lxml.objectify import fromstring
from odoo import fields
from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import misc


class MxEdiAddendaMabe(InvoiceTransactionCase):
    def setUp(self):
        super(MxEdiAddendaMabe, self).setUp()
        conf = self.env['res.config.settings'].create({
            'l10n_mx_addenda': 'mabe'})
        conf.install_addenda()
        self.partner_agrolait.l10n_mx_edi_addenda = self.env.ref(
            'l10n_mx_edi_addendas.mabe')
        self.partner_agrolait.ref = '0107|0107'
        mabe_expected = misc.file_open(os.path.join(
            'l10n_mx_edi_addendas', 'tests', 'mabe_expected.xml')
        ).read().encode('UTF-8')
        self.addenda_tree = fromstring(mabe_expected)
        self.set_currency_rates(mxn_rate=21, usd_rate=1)

    def test_001_addenda_in_xml(self):
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        tax_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= tax_tag

        invoice = self.create_invoice()
        self.partner_agrolait.type = 'delivery'
        invoice.ref = 'PO002'
        # wizard values
        invoice.sudo().partner_id.lang = 'en_US'
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
        self.assertTrue(hasattr(xml, 'Addenda'), "There is not Addenda node")
        self.addenda_tree.getchildren()[0].attrib[
            'fecha'] = fields.Date.to_string(invoice.invoice_date)
        self.addenda_tree.getchildren()[0].attrib['folio'] = xml.get(
            'Serie') + xml.get('Folio')
        self.addenda_tree.getchildren()[0].attrib['referencia1'] = xml.get(
            'Serie') + xml.get('Folio')
        self.assertEqualXML(xml.Addenda, self.addenda_tree)
