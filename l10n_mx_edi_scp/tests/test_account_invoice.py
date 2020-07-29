# coding: utf-8

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase


class TestL10nMxEdiInvoiceSCP(InvoiceTransactionCase):

    def test_l10n_mx_edi_invoice_scp(self):
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        invoice = self.create_invoice()
        invoice.write({
            'l10n_mx_edi_property': self.partner_agrolait.id,
        })
        self.partner_agrolait.write({
            'zip': '37440',
            'state_id': self.env.ref('base.state_mx_jal').id,
            'l10n_mx_edi_property_licence': '1234567',
        })
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        namespaces = {
            'servicioparcial': 'http://www.sat.gob.mx/servicioparcialconstruccion'}  # noqa
        scp = xml.Complemento.xpath('//servicioparcial:parcialesconstruccion',
                                    namespaces=namespaces)
        self.assertTrue(scp, 'Complement to SCP not added correctly')
