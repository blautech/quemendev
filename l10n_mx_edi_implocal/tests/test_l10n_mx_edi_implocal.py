# coding: utf-8
import os

from lxml import objectify

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import misc


class TestL10nMxEdiInvoiceImpLocal(InvoiceTransactionCase):

    def setUp(self):
        super(TestL10nMxEdiInvoiceImpLocal, self).setUp()
        self.tag_model = self.env['account.account.tag']
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        self.tax_local = self.tax_positive.copy({
            'name': 'LOCAL(10%) VENTAS',
            'amount': 10.000000,
        })
        for rep_line in self.tax_local.invoice_repartition_line_ids:
            rep_line.tag_ids |= self.env.ref(
                'l10n_mx_edi_implocal.account_tax_local')
        self.product = self.env.ref("product.product_product_2")
        self.product.taxes_id = [self.tax_positive.id, self.tax_negative.id,
                                 self.tax_local.id]
        self.product.default_code = "TEST"
        self.product.l10n_mx_edi_code_sat_id = self.ref(
            'l10n_mx_edi.prod_code_sat_01010101')
        self.xml_expected = misc.file_open(os.path.join(
            'l10n_mx_edi_implocal', 'tests', 'expected.xml')).read().encode(
                'UTF-8')

    def test_l10n_mx_edi_implocal(self):
        iva_tag = (self.tag_model.search([('name', '=', 'IVA')]) or
                   self.tag_model.create({'name': 'IVA'}))
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= iva_tag
        invoice = self.create_invoice()
        invoice.company_id.sudo().name = 'YourCompany'
        invoice.line_ids.unlink()
        invoice.invoice_line_ids.unlink()
        invoice_line = invoice.invoice_line_ids.new({
            'product_id': self.product.id,
            'quantity': 1,
            'move_id': invoice.id,
        })
        invoice_line._onchange_product_id()
        invoice_line_dict = invoice_line._convert_to_write(invoice_line._cache)
        invoice_line_dict['price_unit'] = 450
        invoice.invoice_line_ids = [(0, 0, invoice_line_dict)]
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        namespaces = {'implocal': 'http://www.sat.gob.mx/implocal'}
        comp = xml.Complemento.xpath('//implocal:ImpuestosLocales',
                                     namespaces=namespaces)
        self.assertTrue(comp, 'Complement to implocal not added correctly')
        xml_expected = objectify.fromstring(self.xml_expected)
        self.xml_merge_dynamic_items(xml, xml_expected)
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        xml_expected.attrib['TipoCambio'] = xml.attrib['TipoCambio']
        self.assertEqualXML(xml, xml_expected)
