# coding: utf-8

import base64
import os

from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.exceptions import ValidationError


class TestAttachment(InvoiceTransactionCase):
    def setUp(self):
        super(TestAttachment, self).setUp()
        self.product.l10n_mx_edi_code_sat_id = self.ref(
            'l10n_mx_edi.prod_code_sat_01010101')
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        self.tax_negative.l10n_mx_cfdi_tax_type = 'Tasa'
        self.tax_positive.l10n_mx_cfdi_tax_type = 'Tasa'
        self.company.partner_id.write({
            'vat': 'EKU9003173C9',
        })

    def test_001_(self):
        invoice = self.create_invoice()
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml_attachment = self.env['ir.attachment'].search([
            ('res_id', '=', invoice.id),
            ('res_model', '=', 'account.move'),
            ('name', '=', invoice.l10n_mx_edi_cfdi_name)])
        error_msg = "You cannot delete documents which contain legal info"
        with self.assertRaisesRegexp(ValidationError, error_msg):
            xml_attachment.unlink()
        # Creates a dummy PDF to attach it and then try to delete it
        pdf_filename = '%s.pdf' % os.path.splitext(xml_attachment.name)[0]
        pdf_attachment = self.env['ir.attachment'].with_context({}).create({
            'name': pdf_filename,
            'res_id': invoice.id,
            'res_model': 'account.move',
            'datas': base64.b64encode(b'%PDF-1.3'),
        })
        with self.assertRaisesRegexp(ValidationError, error_msg):
            pdf_attachment.unlink()
