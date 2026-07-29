# -*- coding: utf-8 -*-
from odoo import fields, models


class PartnerRatingDocumentLine(models.Model):
    _name = 'partner.rating.document.line'
    _description = 'Documento evaluado'
    _order = 'sequence, id'

    rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='#', default=10)
    document_type_id = fields.Many2one(
        'partner.document.type',
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
    person_type = fields.Selection(
        related='document_type_id.person_type',
        string='Aplica a',
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
    partner_document_id = fields.Many2one(
        'partner.document',
        string='Archivo digitalizado',
        help='Documento subido en la pestaña Documentos del contacto',
    )
