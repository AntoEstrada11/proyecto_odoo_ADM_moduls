# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rating_ids = fields.One2many(
        'partner.rating',
        'partner_id',
        string='Evaluaciones',
    )
