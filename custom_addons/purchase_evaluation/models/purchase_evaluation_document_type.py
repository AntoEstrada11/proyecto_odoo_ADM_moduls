# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseEvaluationDocumentType(models.Model):
    _name = 'purchase.evaluation.document.type'
    _description = 'Tipo de documento de requisición/compra'
    _order = 'sequence, name'

    name = fields.Char(string='Documento', required=True, translate=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    required = fields.Boolean(
        string='Obligatorio',
        default=True,
        help='Si está activo, debe estar recibido/aprobado para pasar a evaluación.',
    )
    instructions = fields.Text(string='Instrucciones')

    _sql_constraints = [
        (
            'code_uniq',
            'unique(code)',
            'El código del tipo de documento de compra debe ser único.',
        ),
    ]
