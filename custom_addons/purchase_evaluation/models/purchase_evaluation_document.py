# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseEvaluationDocument(models.Model):
    _name = 'purchase.evaluation.document.line'
    _description = 'Documento de requisición/compra'
    _order = 'sequence, id'

    evaluation_id = fields.Many2one(
        'purchase.evaluation',
        string='Evaluación de compra',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='#', default=10)
    document_type_id = fields.Many2one(
        'purchase.evaluation.document.type',
        string='Tipo de documento',
        required=True,
        ondelete='restrict',
    )
    name = fields.Char(
        related='document_type_id.name',
        string='Documento',
        store=True,
        readonly=True,
    )
    required = fields.Boolean(
        related='document_type_id.required',
        string='Obligatorio',
        store=True,
    )
    situation = fields.Selection(
        [
            ('not_received', 'No recibido'),
            ('received', 'Recibido'),
            ('approved', 'Aprobado'),
        ],
        string='Situación',
        default='not_received',
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
    file = fields.Binary(string='Archivo', attachment=True)
    file_name = fields.Char(string='Nombre de archivo')
    notes = fields.Char(string='Notas')
