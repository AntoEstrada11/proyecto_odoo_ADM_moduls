# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_evaluation_ids = fields.One2many(
        'purchase.evaluation',
        'partner_id',
        string='Evaluaciones de compra',
    )
