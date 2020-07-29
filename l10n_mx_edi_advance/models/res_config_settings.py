# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_mx_edi_product_advance_id = fields.Many2one(
        'product.product', 'Advance product', readonly=False,
        related='company_id.l10n_mx_edi_product_advance_id',
        help='This product will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')
    l10n_mx_edi_journal_advance_id = fields.Many2one(
        'account.journal', 'Advance Journal', readonly=False,
        related='company_id.l10n_mx_edi_journal_advance_id',
        help='This journal will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')

    def execute(self):
        self.ensure_one()
        prod = self.l10n_mx_edi_product_advance_id
        if prod and (not prod.property_account_expense_id or
                     not prod.property_account_income_id):
            raise UserError(_("The accounts for the advance product need to "
                              "be set up for any advance operation."))
        return super(ResConfigSettings, self).execute()
