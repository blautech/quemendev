from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tests import tagged
from odoo.tests.common import Form


@tagged('post_install', '-at_install')
class TestL10nMxInvoiceTaxImportation(InvoiceTransactionCase):

    def setUp(self):
        super().setUp()
        self.imp_product = self.env.ref(
            'l10n_mx_import_taxes.product_tax_importation')
        self.imp_tax = self.env.ref('l10n_mx_import_taxes.tax_importation')
        self.journal_payment = self.env['account.journal'].search(
            [('code', '=', 'CSH1'),
             ('type', '=', 'cash'),
             ('company_id', '=', self.company.id)], limit=1)
        self.invoice_journal = self.env['account.journal'].search(
            [('code', '=', 'BILL'),
             ('type', '=', 'purchase'),
             ('company_id', '=', self.company.id)], limit=1)

    def test_case_with_tax_importation(self):
        foreign_invoice = self.create_invoice('in_invoice', self.mxn.id)
        foreign_invoice.invoice_line_ids.write({
            'tax_ids': False})
        self._validate_invoice(foreign_invoice, False)
        self.partner_agrolait.write({
            'country_id': self.env.ref('base.mx').id})
        invoice = self.create_invoice('in_invoice', self.mxn.id)
        invoice.line_ids.unlink()
        invoice.invoice_line_ids.unlink()
        invoice.write({'invoice_line_ids': [(0, 0, {
            'tax_ids': [(6, 0, self.imp_tax.ids)],
            'product_id': self.imp_product.id,
            'quantity': 0.0,
            'price_unit': 450.00,
            'l10n_mx_edi_invoice_broker_id': foreign_invoice.id,
        })]})
        self._validate_invoice(invoice)
        # Get DIOT report
        invoice.sudo().partner_id.commercial_partner_id.l10n_mx_type_of_operation = '85'  # noqa
        self.diot_report = self.env['l10n_mx.account.diot']
        options = self.diot_report._get_options()
        options.get('date', {})['date_from'] = invoice.invoice_date
        options.get('date', {})['date_to'] = invoice.invoice_date
        data = self.diot_report.get_txt(options)
        self.assertEqual(
            data, '05|85|||Deco Addict|US|Americano|||||||||450|||||||||\n',
            "Error with tax importation DIOT")

    def _validate_invoice(self, invoice, pay=True):
        invoice.action_post()
        if pay:
            payment_register = Form(self.env['account.payment'].with_context(
                active_model='account.move', active_ids=invoice.ids))
            payment_register.payment_date = invoice.invoice_date
            payment_register.l10n_mx_edi_payment_method_id = self.env.ref(
                'l10n_mx_edi.payment_method_efectivo')
            payment_register.payment_method_id = self.env.ref(
                "account.account_payment_method_manual_in")
            payment_register.journal_id = self.journal_payment
            payment_register.communication = invoice.name
            payment_register.amount = invoice.amount_total
            payment = payment_register.save()
            payment.post()
        return invoice
