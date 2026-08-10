# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # NO usar rating_ids/rating_id: chocan con mail.thread + módulo rating
    # (domain res_model) y provocan KeyError al crear partner.rating en release.
    partner_rating_ids = fields.One2many(
        'partner.rating',
        'partner_id',
        string='Evaluaciones Calificadora',
    )
    partner_rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación Calificadora',
        compute='_compute_rating_summary',
    )
    rating_summary_date = fields.Date(
        string='Fecha evaluación',
        compute='_compute_rating_summary',
    )
    rating_summary_state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('done', 'Finalizada'),
        ],
        string='Estado evaluación',
        compute='_compute_rating_summary',
    )
    rating_summary_level = fields.Selection(
        [
            ('failed', 'Fracasado'),
            ('not_recommended', 'No se recomienda'),
            ('reserved', 'Aprobado con reservas'),
            ('approved', 'Aprobado'),
        ],
        string='Rango',
        compute='_compute_rating_summary',
    )
    rating_summary_risk = fields.Selection(
        [
            ('low', 'Bajo'),
            ('medium', 'Medio'),
            ('high', 'Alto'),
        ],
        string='Riesgo',
        compute='_compute_rating_summary',
    )
    rating_summary_analysis = fields.Selection(
        [
            ('approved', 'Aprobado'),
            ('approved_reserved', 'Aprobado con reservas'),
            ('not_recommended', 'No se recomienda'),
            ('failed', 'Fracasado'),
        ],
        string='Estado del análisis',
        compute='_compute_rating_summary',
    )
    rating_viability_percent = fields.Float(
        string='% Viabilidad',
        compute='_compute_rating_summary',
    )
    rating_performance_percent = fields.Float(
        string='% Desempeño',
        compute='_compute_rating_summary',
    )
    rating_global_percent = fields.Float(
        string='% Global',
        compute='_compute_rating_summary',
    )
    has_rating = fields.Boolean(compute='_compute_rating_summary')

    @api.depends(
        'partner_rating_ids',
        'partner_rating_ids.date',
        'partner_rating_ids.state',
        'partner_rating_ids.rating_level',
        'partner_rating_ids.risk_level',
        'partner_rating_ids.analysis_status',
        'partner_rating_ids.viability_percent',
        'partner_rating_ids.performance_percent',
        'partner_rating_ids.score_percent',
    )
    def _compute_rating_summary(self):
        Rating = self.env['partner.rating'].sudo()
        for partner in self:
            rating = Rating.search([('partner_id', '=', partner.id)], limit=1)
            partner.partner_rating_id = rating
            partner.has_rating = bool(rating)
            partner.rating_summary_date = rating.date if rating else False
            partner.rating_summary_state = rating.state if rating else False
            partner.rating_summary_level = rating.rating_level if rating else False
            partner.rating_summary_risk = rating.risk_level if rating else False
            partner.rating_summary_analysis = rating.analysis_status if rating else False
            partner.rating_viability_percent = rating.viability_percent if rating else 0.0
            partner.rating_performance_percent = (
                rating.performance_percent if rating else 0.0
            )
            partner.rating_global_percent = rating.score_percent if rating else 0.0

    def action_open_partner_rating(self):
        self.ensure_one()
        if not self.env.user.has_group('partner_rating.group_evaluation_user'):
            raise AccessError(_(
                'No tiene permiso para abrir o crear evaluaciones de proveedor. '
                'Pida a un administrador que active "Acceso a Calificadora" en su usuario.'
            ))
        if self.partner_rating_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Evaluación',
                'res_model': 'partner.rating',
                'res_id': self.partner_rating_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva evaluación',
            'res_model': 'partner.rating',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
                'default_name': f'Evaluación - {self.name}',
            },
        }
