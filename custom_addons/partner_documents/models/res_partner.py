# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    document_ids = fields.One2many(
        'partner.document',
        'partner_id',
        string='Documentos',
    )
