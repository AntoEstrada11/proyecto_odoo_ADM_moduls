# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PartnerRatingScoreHelpWizard(models.TransientModel):
    _name = 'partner.rating.score.help.wizard'
    _description = 'Ayuda de calificación y ponderación'

    rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación',
        required=True,
        readonly=True,
    )
    viability_percent = fields.Float(
        related='rating_id.viability_percent',
        string='% Viabilidad documental',
        readonly=True,
    )
    performance_percent = fields.Float(
        related='rating_id.performance_percent',
        string='% Desempeño comercial',
        readonly=True,
    )
    score_percent = fields.Float(
        related='rating_id.score_percent',
        string='% Global ponderado',
        readonly=True,
    )
    rating_state = fields.Selection(related='rating_id.state', readonly=True)
    weight_viability = fields.Float(string='Peso viabilidad %', required=True)
    weight_performance = fields.Float(string='Peso desempeño %', required=True)
    explanation = fields.Html(string='Cómo se calcula', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rating_id = res.get('rating_id') or self.env.context.get('default_rating_id')
        if rating_id:
            rating = self.env['partner.rating'].browse(int(rating_id))
            res['rating_id'] = rating.id
            res['weight_viability'] = rating.weight_viability
            res['weight_performance'] = rating.weight_performance
            res['explanation'] = self._build_explanation(rating)
        return res

    @api.model
    def _build_explanation(self, rating):
        return _(
            """
            <div>
              <p><b>1. %% Viabilidad documental</b></p>
              <ul>
                <li>Documentos: No recibido 0 · Recibido 1 · Aprobado 2</li>
                <li>Averiguaciones: Pendiente 0 · Realizada 1 · Favorable 2 · Con hallazgos 0</li>
                <li>Criterios internos: Sí suma 2 puntos al máximo y al obtenido</li>
              </ul>
              <p><b>2. %% Desempeño comercial</b></p>
              <ul>
                <li>Cada rubro: Sin calificar 0 … Excelente 5</li>
                <li>%% = puntos obtenidos / (rubros × 5) × 100</li>
              </ul>
              <p><b>3. %% Global ponderado</b></p>
              <p>
                Global = (Viabilidad × %(w_v)s%%) + (Desempeño × %(w_p)s%%)
              </p>
              <p>
                Si todavía no califica ningún rubro de desempeño, el global
                usa solo la viabilidad.
              </p>
              <p class="text-muted">
                Actual: Viabilidad %(v)s%% · Desempeño %(p)s%% · Global %(g)s%%
              </p>
            </div>
            """
        ) % {
            'w_v': int(rating.weight_viability or 60),
            'w_p': int(rating.weight_performance or 40),
            'v': round(rating.viability_percent or 0.0, 1),
            'p': round(rating.performance_percent or 0.0, 1),
            'g': round(rating.score_percent or 0.0, 1),
        }

    def action_apply_weights(self):
        self.ensure_one()
        total = (self.weight_viability or 0.0) + (self.weight_performance or 0.0)
        if abs(total - 100.0) > 0.01:
            raise UserError(_(
                'Los pesos deben sumar 100%%. Actual: %.1f%%.'
            ) % total)
        self.rating_id.write({
            'weight_viability': self.weight_viability,
            'weight_performance': self.weight_performance,
        })
        return {'type': 'ir.actions.act_window_close'}
