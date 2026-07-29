# -*- coding: utf-8 -*-
from odoo import fields, models


class PartnerRatingPerformanceLine(models.Model):
    _name = 'partner.rating.performance.line'
    _description = 'Rubro de desempeño comercial'
    _order = 'sequence, id'

    rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='#', default=10)
    name = fields.Char(string='Rubro', required=True)
    score = fields.Selection(
        [
            ('0', 'Sin calificar'),
            ('1', 'Malo'),
            ('2', 'Regular'),
            ('3', 'Bueno'),
            ('4', 'Muy bueno'),
            ('5', 'Excelente'),
        ],
        string='Calificación',
        default='0',
        required=True,
    )
    warnings = fields.Selection(
        [
            ('none', 'Sin advertencias'),
            ('minor', 'Menor'),
            ('major', 'Mayor'),
            ('critical', 'Crítica'),
        ],
        string='Advertencias',
        default='none',
        required=True,
    )
    notes = fields.Char(string='Detalle')
