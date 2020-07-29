import json
from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tools import float_compare
from odoo.tests.common import Form


class TestMxEdiAdvanceInvoice(InvoiceTransactionCase):
    def setUp(self):
        super(TestMxEdiAdvanceInvoice, self).setUp()
        self.payment = self.env['account.payment']
        self.advance_national = self.env.ref(
            'l10n_mx_edi_advance.product_product_advance')
        self.journal = self.env.ref(
            'l10n_mx_edi_advance.extra_advance_journal')
        self.company.write({
            'l10n_mx_edi_product_advance_id': self.advance_national.id,
            'l10n_mx_edi_journal_advance_id': self.journal.id,
        })
        self.bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank')], limit=1)
        self.cash = self.env.ref('l10n_mx_edi.payment_method_efectivo')
        self.payment_method_id = self.env.ref(
            "account.account_payment_method_manual_in")
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        iva_tag = self.env['account.account.tag'].search(
            [('name', '=', 'IVA')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag
        for rep_line in self.tax_positive.invoice_repartition_line_ids:
            rep_line.tag_ids |= iva_tag
        taxes = self.env['account.tax'].search([('type_tax_use', '=', 'sale')])
        taxes.write({'l10n_mx_cfdi_tax_type': 'Tasa'})
        # set account in product
        self._prepare_accounts()
        # set taxes in product
        self.advance_national.taxes_id = [self.tax_positive.id, self.tax_negative.id]  # noqa
        self.adv_amount = 150.0
        self.set_currency_rates(1, 0.052890)
        self.today_mx = (self.env['l10n_mx_edi.certificate'
                                  ].sudo().get_mx_current_datetime().date())

    def test_001_create_advance(self):
        """Create and use advance same currency"""
        # Create an advance with the same currency as the invoice
        advance = self.env['account.move'].advance(
            self.partner_agrolait, self.adv_amount, self.usd)
        self.assertEqual(advance.amount_total, self.adv_amount,
                         "The amount %s doesn't match with %s" % (
                             advance.amount_total, self.adv_amount))
        advance.action_post()
        self.assertEqual(advance.l10n_mx_edi_pac_status, 'signed',
                         advance.message_ids.mapped('body'))
        # pay the advance
        self.register_payment(advance)
        self.assertEqual(advance.invoice_payment_state, 'paid',
                         advance.message_ids.mapped('body'))
        # create another invoice to use the advance
        invoice = self.create_invoice()
        self.assertTrue(invoice.invoice_has_outstanding,
                        "This invoice doesn't have advances")
        # add advance
        aml_credit = self.search_advance_aml(invoice, advance)
        invoice.js_assign_outstanding_line(aml_credit.id)
        self.assertTrue(invoice._l10n_mx_edi_get_advance_uuid_related(),
                        "Error adding advance check CFDI origin")
        related = invoice.get_cfdi_related()
        self.assertEqual(related['type'], '07',
                         "Relation type must be 07 for advance")
        self.assertEqual(related['related'][0], advance.l10n_mx_edi_cfdi_uuid,
                         "Related uuid is not the same as the advance")
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, 'signed',
                         invoice.message_ids.mapped('body'))
        # add credit note
        refund = self.env['account.move'].search([
            ('reversed_entry_id', '=', invoice.id)])
        self.assertTrue(refund, "Error: credit note was not created.")

        related = refund.get_cfdi_related()
        self.assertEqual(related['type'], '07',
                         "Relation type must be 07 for advance")
        self.assertEqual(related['related'][0], invoice.l10n_mx_edi_cfdi_uuid,
                         "Related uuid is not the same as the invoice")
        self.assertEqual(refund.invoice_line_ids.product_id.id,
                         advance.invoice_line_ids.product_id.id,
                         "Refund product must be the same as the advance.")
        self.assertEqual(
            refund.amount_total, advance.amount_total,
            "the refund amount must be the same as the advance amount")
        self.assertEqual(
            refund.amount_tax, advance.amount_tax,
            "the refund amount for tax must be the same as the advance amount")

    def test_002_create_advance_multi_currency(self):
        """Create and use advance multi-currency"""
        # Create an advance same currency that the invoice
        advance = self.env['account.move'].advance(
            self.partner_agrolait, self.adv_amount, self.mxn)
        self.assertEqual(advance.amount_total, self.adv_amount,
                         "The amount %s doesn't match with %s" % (
                             advance.amount_total, self.adv_amount))
        advance.action_post()
        self.assertEqual(advance.l10n_mx_edi_pac_status, 'signed',
                         advance.message_ids.mapped('body'))
        # pay the advance
        self.register_payment(advance)
        self.assertEqual(advance.invoice_payment_state, 'paid',
                         advance.message_ids.mapped('body'))
        # create another invoice to use the advance
        invoice = self.create_invoice()
        self.assertTrue(invoice.invoice_has_outstanding,
                        "This invoice doesn't have advances")
        # add advance
        aml_credit = self.search_advance_aml(invoice, advance)
        invoice.js_assign_outstanding_line(aml_credit.id)
        self.assertTrue(invoice._l10n_mx_edi_get_advance_uuid_related(),
                        "Error adding advance check CFDI origin")
        related = invoice.get_cfdi_related()
        self.assertEqual(related['type'], '07',
                         "Relation type must be 07 for advance")
        self.assertEqual(related['related'][0], advance.l10n_mx_edi_cfdi_uuid,
                         "Related uuid is not the same as the advance")
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, 'signed',
                         invoice.message_ids.mapped('body'))
        # add credit note
        refund = self.env['account.move'].search([
            ('reversed_entry_id', '=', invoice.id)])
        self.assertTrue(refund, "Error: credit note was not created.")

        related = refund.get_cfdi_related()
        self.assertEqual(related['type'], '07',
                         "Relation type must be 07 for advance")
        self.assertEqual(related['related'][0], invoice.l10n_mx_edi_cfdi_uuid,
                         "Related uuid is not the same as the invoice")
        self.assertEqual(refund.invoice_line_ids.product_id.id,
                         advance.invoice_line_ids.product_id.id,
                         "Refund product must be the same as the advance.")
        advance_amount_total = advance.currency_id._convert(
            advance.amount_total, self.usd, invoice.company_id,
            invoice.date)
        refund_amount_total = advance.currency_id._convert(
            refund.amount_total, self.usd, invoice.company_id,
            invoice.date)
        self.assertFalse(refund.currency_id.compare_amounts(
            refund_amount_total, advance_amount_total),
            "The refund amount must be the same as the advance amount")

    def test_03_create_advance_from_payment(self):
        partner = self.partner_agrolait.create({'name': 'ADV'})
        payment = self.payment.create({
            'name': 'CUST.IN/2018/999',
            'payment_date': self.today_mx,
            'currency_id': self.mxn.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'l10n_mx_edi_payment_method_id': self.cash.id,
            'payment_method_id': self.payment_method_id.id,
            'journal_id': self.bank_journal.id,
            'communication': 'Payment ADV',
            'amount': 200000.00,
        })
        payment.post()
        invoice = payment.invoice_ids
        self.assertTrue(len(invoice) == 1, payment.message_ids.mapped('body'))
        self.assertEquals(invoice.l10n_mx_edi_pac_status, 'signed',
                          invoice.message_ids.mapped('body'))

        # Now cancel the payment, and must be cancelled the invoice
        payment.cancel()
        cus_invoice = self.create_invoice()
        cus_invoice.partner_id = partner
        cus_invoice.refresh()
        # don't have advance
        self.assertFalse(invoice.invoice_has_outstanding)

    def test_04_create_advance_from_payment_with_stamp_errors(self):
        """ Reconcile the advance with the payment and check if it's available
        """
        partner = self.partner_agrolait.copy({
            'name': 'ADV',
            'parent_id': False})
        # CFDI error
        self.tax_positive.write({'l10n_mx_cfdi_tax_type': False})

        payment = self.payment.create({
            'payment_date': self.today_mx,
            'currency_id': self.mxn.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'l10n_mx_edi_payment_method_id': self.cash.id,
            'payment_method_id': self.payment_method_id.id,
            'journal_id': self.bank_journal.id,
            'communication': 'Payment ADV',
            'amount': 2000.00,
        })
        payment.post()
        # search advance created in draft
        advance = self.env['account.move'].search([
            ('partner_id', '=', partner.id), ('type', '=', 'out_invoice')],
            limit=1)
        self.assertTrue(advance, payment.message_ids.mapped('body'))
        advance.refresh()
        self.assertEqual(advance.state, 'draft',
                         advance.message_ids.mapped('body'))
        # resolve error
        self.tax_positive.write({'l10n_mx_cfdi_tax_type': 'Tasa'})
        # stamp cfdi
        advance.action_post()
        self.assertEqual(advance.l10n_mx_edi_pac_status, 'signed',
                         advance.message_ids.mapped('body'))
        # reconcile advance and payment
        advance.refresh()
        line_id = payment.move_line_ids.filtered(
            lambda l: not l.reconciled and l.credit > 0.0)
        advance.js_assign_outstanding_line(line_id.id)
        self.assertEqual(advance.invoice_payment_state, 'paid',
                         advance.message_ids.mapped('body'))
        # check if there are advance available
        invoice = self.create_invoice()
        invoice.partner_id = partner
        self.assertTrue(invoice.invoice_has_outstanding,
                        "This invoice doesn't have advances")

    def test_05_advance_amounts_fields(self):
        """Test the compute fields for advance amounts"""
        # advance with the same currency and adv amount == inv amount
        invoice = self.create_invoice(currency_id=self.usd.id)
        adv_amount = invoice.amount_total
        self._create_advance_and_apply(invoice, self.usd, adv_amount)
        self.assertEqual(invoice.l10n_mx_edi_amount_advances, adv_amount,
                         "Advance amount is failing in draft state")
        self.assertEqual(invoice.l10n_mx_edi_amount_residual_advances,
                         invoice.amount_total - adv_amount,
                         "Advance Residual amount is failing in draft state")
        invoice.action_post()
        self.assertEqual(invoice.l10n_mx_edi_amount_advances,
                         invoice.amount_total - invoice.amount_residual,
                         "Advance amount is failing in open state")
        self.assertEqual(invoice.l10n_mx_edi_amount_residual_advances,
                         invoice.amount_residual,
                         "Advance Residual amount is failing in open state")

        # multi-advances with the same currency and adv amount > inv amount
        invoice = self.create_invoice(currency_id=self.usd.id)
        adv_amount = invoice.amount_total
        self._create_advance_and_apply(invoice, self.usd,
                                       invoice.amount_total / 2)
        self._create_advance_and_apply(invoice, self.usd,
                                       invoice.amount_total / 2)
        self.assertEqual(float_compare(
            invoice.l10n_mx_edi_amount_advances, adv_amount,
            precision_digits=0), 0,
            "Advance amount is failing in draft state")
        self.assertEqual(float_compare(
            invoice.l10n_mx_edi_amount_residual_advances,
            invoice.amount_total - adv_amount, precision_digits=0), 0,
            "Advance residual amount is failing in draft state")
        invoice.action_post()
        self.assertEqual(float_compare(
            invoice.l10n_mx_edi_amount_advances,
            invoice.amount_total - invoice.amount_residual,
            precision_digits=0), 0, "Advance amount is failing in open state")
        self.assertEqual(invoice.l10n_mx_edi_amount_residual_advances,
                         invoice.amount_residual,
                         "Advance residual amount is failing in open state")

        # advance with different currency and adv amount < inv amount
        invoice = self.create_invoice(currency_id=self.mxn.id)
        adv_amount = self.mxn._convert(
            invoice.amount_total / 2, self.usd, invoice.company_id,
            self.today_mx)
        advance = self._create_advance_and_apply(invoice, self.usd, adv_amount)
        adv_amount = self.usd._convert(advance.amount_total, self.mxn,
                                       invoice.company_id, self.today_mx)
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_advances, adv_amount),
            "Advance amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_advances, adv_amount))
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_residual_advances,
            invoice.amount_total - adv_amount),
            "Advance residual amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_residual_advances,
                invoice.amount_total - adv_amount))
        invoice.action_post()
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_advances,
            invoice.amount_total - invoice.amount_residual),
            "Advance amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_advances,
                invoice.amount_total - invoice.amount_residual))
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_residual_advances,
            invoice.amount_residual),
            "Advance residual amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_residual_advances,
                invoice.amount_residual))

        # multi-advances with different currency and adv amount == inv amount
        invoice = self.create_invoice(currency_id=self.usd.id)
        adv_amount = self.usd._convert(
            invoice.amount_total / 3, self.mxn, invoice.company_id,
            self.today_mx)
        advance = self._create_advance_and_apply(invoice, self.mxn, adv_amount)
        adv_amount = self.mxn._convert(advance.amount_total, self.usd,
                                       invoice.company_id, self.today_mx)
        self._create_advance_and_apply(invoice, self.usd,
                                       invoice.amount_total - adv_amount)
        adv_amount += invoice.amount_total - adv_amount
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_advances, adv_amount),
            "Advance amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_advances, adv_amount))
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_residual_advances,
            invoice.amount_total - adv_amount),
            "Advance residual amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_residual_advances,
                invoice.amount_total - adv_amount))
        invoice.action_post()
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_advances,
            invoice.amount_total - invoice.residual),
            "Advance amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_advances,
                invoice.amount_total - invoice.residual))
        self.assertFalse(invoice.currency_id.compare_amounts(
            invoice.l10n_mx_edi_amount_residual_advances, invoice.residual),
            "Advance residual amount is failing in draft state %s != %s" % (
                invoice.l10n_mx_edi_amount_residual_advances,
                invoice.residual))

    def test_06_bank_statement(self):
        """test bank statement"""
        partner = self.partner_agrolait._find_accounting_partner(
            self.partner_agrolait)
        bank_st = self.env['account.bank.statement']
        journal = bank_st.with_context(journal_type='bank')._default_journal()
        bank_st = bank_st.create({
            'name': 'Test advance with bank statement',
            'journal_id': journal.id,
            'date': self.today_mx,
            'line_ids': [(0, 0, {
                'name': '_',
                'date': self.today_mx,
                'statement_id': bank_st.id,
                'partner_id': partner.id,
                'amount': 1007.0,
            })],
        })
        bank_st.line_ids.process_reconciliation(new_aml_dicts=[{
            'analytic_tag_ids': [[6, None, []]],
            'account_id': 3,
            'debit': 0,
            'credit': 1007.0,
            'name': '_'}])
        payment = bank_st.line_ids.journal_entry_ids.mapped('payment_id')
        advance = payment.invoice_ids
        self.assertTrue(advance, payment.message_ids.mapped('body'))
        self.assertTrue(advance._l10n_mx_edi_is_advance())
        self.assertEqual(advance.l10n_mx_edi_pac_status, 'signed',
                         advance.message_ids.mapped('body'))
        # reconcile with outstanding payment
        advance._compute_payments_widget_to_reconcile_info()
        content = json.loads(
            advance.invoice_outstanding_credits_debits_widget)['content']
        amls = []
        for credit in content:
            amls += [int(credit['id'])]
        aml = self.env['account.move.line'].search([
            ('id', 'in', amls), ('payment_id', '=', payment.id)])
        advance.js_assign_outstanding_line(aml.id)
        # check if there are advance available
        invoice = self.create_invoice()
        self.assertTrue(invoice.invoice_has_outstanding,
                        "This invoice doesn't have advances")

    def test_07_apply_advance_partially(self):
        invoice = self.create_invoice(currency_id=self.mxn.id)
        self._create_advance_and_apply(invoice, self.mxn,
                                       invoice.amount_total + 5)
        invoice.action_post()
        invoice2 = self.create_invoice(currency_id=self.mxn.id)
        self.assertTrue(invoice2.invoice_has_outstanding,
                        "This invoice doesn't have advances to apply")

    def _create_advance_and_apply(self, invoice, adv_currency, adv_amount):
        advance = self.env['account.move'].advance(
            invoice.partner_id, adv_amount, adv_currency)
        advance.action_post()
        self.assertEqual(advance.l10n_mx_edi_pac_status, 'signed',
                         advance.message_ids.mapped('body'))
        self.register_payment(advance)
        # add advance
        aml_credit = self.search_advance_aml(invoice, advance)
        invoice.js_assign_outstanding_line(aml_credit.id)
        return advance

    def register_payment(self, invoice):
        ctx = {'active_model': 'account.move', 'active_ids': [invoice.id]}
        payment_register = Form(self.env['account.payment'].with_context(ctx))
        payment_register.payment_date = invoice.date
        payment_register.l10n_mx_edi_payment_method_id = self.cash
        payment_register.payment_method_id = self.payment_method_id
        payment_register.journal_id = self.bank_journal
        payment_register.communication = invoice.name
        payment_register.amount = invoice.amount_total
        payment_register.save().post()
        return invoice._get_reconciled_payments()

    def search_advance_aml(self, invoice, advance):
        amls = []
        invoice._compute_payments_widget_to_reconcile_info()
        content = json.loads(
            invoice.invoice_outstanding_credits_debits_widget)['content']
        for credit in content:
            amls += [int(credit['id'])]
        return self.env['account.move.line'].browse(amls)

    def _prepare_accounts(self):
        account_obj = self.env['account.account']
        tag_obj = self.env['account.account.tag']
        expense = account_obj.create({
            'name': 'Anticipo de clientes (Por cobrar)',
            'code': '206.01.02',
            'user_type_id': self.ref('account.data_account_type_receivable'),
            'tag_ids': tag_obj.search([
                ('name', '=', '206.01 Anticipo de cliente nacional')]),
            'reconcile': True,
        })
        income = account_obj.create({
            'name': 'Anticipo de clientes (Cuenta de Orden)',
            'code': '899.01.01',
            'user_type_id': self.ref('account.data_account_type_expenses'),
            'tag_ids': tag_obj.search([
                ('name', '=', '899.01 Otras cuentas de orden')]),
            'reconcile': True,
        })
        self.advance_national.property_account_income_id = income
        self.advance_national.property_account_expense_id = expense
