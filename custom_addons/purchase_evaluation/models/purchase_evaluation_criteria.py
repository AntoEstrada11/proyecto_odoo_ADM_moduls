# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseEvaluationCriteria(models.Model):
    _name = 'purchase.evaluation.criteria.line'
    _description = 'Criterio de evaluación de compra'
    _order = 'sequence, id'

    evaluation_id = fields.Many2one(
        'purchase.evaluation',
        string='Evaluación de compra',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='#', default=10)
    name = fields.Char(string='Criterio', required=True)
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

    def write(self, vals):
        res = super().write(vals)
        if 'score' in vals:
            self.mapped('evaluation_id')._sync_partner_rating_performance()
        return res
