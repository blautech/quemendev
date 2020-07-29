# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_product_advance_id = fields.Many2one(
        'product.product', 'Advance product', help='This product will be used '
        'in the advance invoices that are created automatically when is '
        'registered a payment without documents related or with a difference '
        'in favor of the customer.')
    l10n_mx_edi_journal_advance_id = fields.Many2one(
        'account.journal', 'Advance Journal',
        help='This journal will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')
