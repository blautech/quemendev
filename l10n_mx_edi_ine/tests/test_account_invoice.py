# coding: utf-8

import os

from lxml import objectify

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import misc


class TestL10nMxEdiInvoiceINE(InvoiceTransactionCase):

    def create_invoice_ine_line(self, invoice_id):
        invoice_ine_line_model = self.env['l10n_mx_edi_ine.entity']
        self.country = self.env['res.country'].search([("code", "=", "MX")])
        state = self.env['res.country.state'].search([
            ('code', '=', 'COL'), ('country_id', '=', self.country.id)])
        lines2create = []
        ine_line = invoice_ine_line_model.new({
            'l10n_mx_edi_ine_entity_id': state.id,
            'l10n_mx_edi_ine_scope': 'local',
            'l10n_mx_edi_ine_accounting': '789',
            'invoice_id': invoice_id,
        })
        ine_line_dict = ine_line._convert_to_write({
            name: ine_line[name] for name in ine_line._cache})
        lines2create.append((0, 0, ine_line_dict))
        ine_line = invoice_ine_line_model.new({
            'l10n_mx_edi_ine_entity_id': state.id,
            'l10n_mx_edi_ine_scope': 'local',
            'l10n_mx_edi_ine_accounting': '123,456',
            'invoice_id': invoice_id,
        })
        ine_line_dict = ine_line._convert_to_write({
            name: ine_line[name] for name in ine_line._cache})
        lines2create.append((0, 0, ine_line_dict))
        invoice_ine_line_model.create(ine_line_dict)

    def test_l10n_mx_edi_simple_ine(self):
        xml_expected_simple_str = misc.file_open(os.path.join(
            'l10n_mx_edi_ine', 'tests', 'expected_simple_ine.xml')).read(
            ).encode('UTF-8')
        invoice = self.create_invoice()
        invoice.company_id.sudo().name = 'YourCompany'
        invoice.l10n_mx_edi_ine_process_type = 'ordinary'
        invoice.l10n_mx_edi_ine_committee_type = 'national_executive'
        invoice.l10n_mx_edi_ine_accounting = '123456'
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        namespaces = {'ine': 'http://www.sat.gob.mx/ine'}
        ine = xml.Complemento.xpath('//ine:INE', namespaces=namespaces)
        self.assertTrue(ine, 'Complement to INE not added correctly')
        xml_expected = objectify.fromstring(xml_expected_simple_str)
        self.xml_merge_dynamic_items(xml, xml_expected)
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        xml_expected.attrib['TipoCambio'] = xml.attrib['TipoCambio']
        self.assertEqualXML(xml, xml_expected)

    def test_l10n_mx_edi_complex_ine(self):
        xml_expected_complex_str = misc.file_open(os.path.join(
            'l10n_mx_edi_ine', 'tests', 'expected_complex_ine.xml')).read(
            ).encode('UTF-8')
        invoice = self.create_invoice()
        invoice.company_id.sudo().name = 'YourCompany'
        self.create_invoice_ine_line(invoice.id)
        invoice.l10n_mx_edi_ine_process_type = 'precampaign'
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        namespaces = {'ine': 'http://www.sat.gob.mx/ine'}
        ine = xml.Complemento.xpath('//ine:INE', namespaces=namespaces)
        self.assertTrue(ine, 'Complement to INE not added correctly')
        xml_expected = objectify.fromstring(xml_expected_complex_str)
        self.xml_merge_dynamic_items(xml, xml_expected)
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        xml_expected.attrib['TipoCambio'] = xml.attrib['TipoCambio']
        self.assertEqualXML(xml, xml_expected)
