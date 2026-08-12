# -*- coding: utf-8 -*-
from odoo import api, fields, models


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

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        if not self.document_type_id or not self.rating_id.partner_id:
            return
        uploaded = self.rating_id.partner_id.document_ids.filtered(
            lambda d: d.document_type_id == self.document_type_id
        )[:1]
        if uploaded:
            self.partner_document_id = uploaded
            if self.situation == 'not_received':
                self.situation = 'received'
        else:
            self.partner_document_id = False
