# -*- coding: utf-8 -*-
from odoo import fields, models


class PartnerRatingResearchLine(models.Model):
    _name = 'partner.rating.research.line'
    _description = 'Pesquisa de evaluación'
    _order = 'sequence, id'

    rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='#', default=10)
    name = fields.Char(string='Pesquisa', required=True)
    situation = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('done', 'Realizada'),
            ('approved', 'Favorable'),
            ('unfavorable', 'Con hallazgos'),
        ],
        string='Situación',
        default='pending',
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
    notes = fields.Char(
        string='Detalle',
        help='Comentario libre sobre la pesquisa o la advertencia.',
    )
    evidence = fields.Binary(string='Evidencia', attachment=True)
    evidence_filename = fields.Char(string='Nombre evidencia')
