# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

CRITERIA_TEMPLATES = [
    'Precio / competitividad',
    'Calidad del producto o servicio',
    'Tiempo de entrega',
    'Atención y comunicación',
    'Cumplimiento contractual',
]


class PurchaseEvaluation(models.Model):
    _name = 'purchase.evaluation'
    _description = 'Evaluación de compra / requisición'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        default='Nueva evaluación de compra',
        tracking=True,
    )
    date = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        required=True,
        tracking=True,
        index=True,
    )
    company_type = fields.Selection(
        related='partner_id.rating_company_type',
        string='Tipo de persona',
        readonly=True,
    )
    amount_total = fields.Monetary(
        string='Monto estimado',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
    )
    description = fields.Text(string='Descripción de la compra / necesidad')

    # --- Hooks para ligar a Compras / requisición de producción ---
    source_model = fields.Char(
        string='Modelo origen',
        index=True,
        help='Ejemplo: purchase.order, purchase.requisition, o el modelo custom de producción.',
    )
    source_res_id = fields.Integer(
        string='ID origen',
        index=True,
        help='ID del registro de compra/requisición en el modelo origen.',
    )
    source_ref = fields.Char(
        string='Referencia origen',
        help='Número o nombre visible de la compra/requisición (PO0001, REQ-45, etc.).',
        tracking=True,
    )
    source_display = fields.Char(
        string='Origen vinculado',
        compute='_compute_source_display',
    )

    state = fields.Selection(
        [
            ('docs', 'Documentación'),
            ('evaluation', 'Evaluación'),
            ('done', 'Finalizada'),
            ('cancelled', 'Cancelada'),
        ],
        string='Estado',
        default='docs',
        required=True,
        tracking=True,
    )

    document_line_ids = fields.One2many(
        'purchase.evaluation.document.line',
        'evaluation_id',
        string='Documentos de la requisición',
    )
    docs_complete = fields.Boolean(
        string='Documentación completa',
        compute='_compute_docs_complete',
        store=True,
    )
    docs_notes = fields.Text(string='Notas de documentación')

    # Resumen del proveedor (desde calificadora)
    partner_rating_id = fields.Many2one(
        'partner.rating',
        string='Evaluación del proveedor',
        compute='_compute_partner_rating',
    )
    partner_rating_level = fields.Selection(
        related='partner_rating_id.rating_level',
        string='Rango proveedor',
        readonly=True,
    )
    partner_viability_percent = fields.Float(
        related='partner_rating_id.viability_percent',
        string='% Viabilidad proveedor',
        readonly=True,
    )
    partner_performance_percent = fields.Float(
        related='partner_rating_id.performance_percent',
        string='% Desempeño proveedor',
        readonly=True,
    )
    partner_global_percent = fields.Float(
        related='partner_rating_id.score_percent',
        string='% Global proveedor',
        readonly=True,
    )
    partner_rating_state = fields.Selection(
        related='partner_rating_id.state',
        string='Estado eval. proveedor',
        readonly=True,
    )

    criteria_line_ids = fields.One2many(
        'purchase.evaluation.criteria.line',
        'evaluation_id',
        string='Criterios de la compra',
    )
    criteria_notes = fields.Text(string='Notas de evaluación')
    recommendation = fields.Selection(
        [
            ('approve', 'Recomendar compra'),
            ('approve_reserved', 'Recomendar con reservas'),
            ('reject', 'No recomendar'),
        ],
        string='Recomendación',
        tracking=True,
    )
    recommendation_reason = fields.Text(string='Motivo de la recomendación')

    purchase_score_obtained = fields.Float(compute='_compute_purchase_score', store=True)
    purchase_score_max = fields.Float(compute='_compute_purchase_score', store=True)
    purchase_percent = fields.Float(
        string='% Evaluación de la compra',
        compute='_compute_purchase_score',
        store=True,
    )

    @api.depends('source_model', 'source_res_id', 'source_ref')
    def _compute_source_display(self):
        for rec in self:
            if rec.source_ref:
                rec.source_display = rec.source_ref
            elif rec.source_model and rec.source_res_id:
                rec.source_display = '%s,%s' % (rec.source_model, rec.source_res_id)
            else:
                rec.source_display = False

    @api.depends('partner_id', 'partner_id.rating_ids')
    def _compute_partner_rating(self):
        for rec in self:
            rec.partner_rating_id = rec.partner_id.rating_ids[:1] if rec.partner_id else False

    @api.depends('document_line_ids.situation', 'document_line_ids.required')
    def _compute_docs_complete(self):
        for rec in self:
            required_lines = rec.document_line_ids.filtered('required')
            if not required_lines:
                rec.docs_complete = bool(rec.document_line_ids) and all(
                    line.situation in ('received', 'approved')
                    for line in rec.document_line_ids
                )
            else:
                rec.docs_complete = all(
                    line.situation in ('received', 'approved')
                    for line in required_lines
                )

    @api.depends('criteria_line_ids.score')
    def _compute_purchase_score(self):
        for rec in self:
            lines = rec.criteria_line_ids
            score_max = len(lines) * 5.0
            score_obtained = sum(float(line.score or 0) for line in lines)
            rec.purchase_score_obtained = score_obtained
            rec.purchase_score_max = score_max
            rec.purchase_percent = (
                (score_obtained / score_max * 100.0) if score_max else 0.0
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._generate_default_lines()
        return records

    def _generate_default_lines(self):
        self.ensure_one()
        if not self.document_line_ids:
            doc_types = self.env['purchase.evaluation.document.type'].search([])
            if doc_types:
                self.env['purchase.evaluation.document.line'].create([
                    {
                        'evaluation_id': self.id,
                        'sequence': doc_type.sequence,
                        'document_type_id': doc_type.id,
                    }
                    for doc_type in doc_types
                ])
        if not self.criteria_line_ids:
            self.env['purchase.evaluation.criteria.line'].create([
                {
                    'evaluation_id': self.id,
                    'sequence': index,
                    'name': name,
                }
                for index, name in enumerate(CRITERIA_TEMPLATES, start=1)
            ])

    def action_load_checklists(self):
        for rec in self:
            rec._generate_default_lines()
        return True

    def action_start_evaluation(self):
        for rec in self:
            if not rec.docs_complete:
                raise UserError(_(
                    'No se puede iniciar la evaluación de la compra. '
                    'Faltan documentos obligatorios de la requisición '
                    '(deben estar en Recibido o Aprobado).'
                ))
            if not rec.partner_id:
                raise UserError(_('Seleccione un proveedor.'))
            rec.state = 'evaluation'
        return True

    def action_back_to_docs(self):
        self.write({'state': 'docs'})
        return True

    def action_set_done(self):
        for rec in self:
            if rec.state != 'evaluation':
                raise UserError(_(
                    'Solo se puede finalizar desde el estado Evaluación.'
                ))
            if not rec.recommendation:
                raise UserError(_('Indique una recomendación antes de finalizar.'))
            rated = any((line.score or '0') != '0' for line in rec.criteria_line_ids)
            if not rated:
                raise UserError(_(
                    'Califique al menos un rubro de desempeño comercial '
                    'antes de finalizar la evaluación de la compra.'
                ))
            rec.state = 'done'
        self._sync_partner_rating_performance()
        return True

    def action_set_cancelled(self):
        self.write({'state': 'cancelled'})
        self._sync_partner_rating_performance()
        return True

    def action_reset_docs(self):
        self.write({'state': 'docs'})
        self._sync_partner_rating_performance()
        return True

    def write(self, vals):
        res = super().write(vals)
        # Si cambia estado o se tocan criterios, refrescar desempeño del proveedor
        if 'state' in vals or any(k.startswith('criteria') for k in vals):
            self._sync_partner_rating_performance()
        return res

    def _sync_partner_rating_performance(self):
        """Actualiza el % de desempeño comercial en la Calificadora del proveedor."""
        Rating = self.env['partner.rating']
        partners = self.mapped('partner_id')
        for partner in partners:
            rating = Rating.search([('partner_id', '=', partner.id)], limit=1)
            if rating:
                rating._compute_score()

    def action_open_partner_rating(self):
        self.ensure_one()
        if not self.partner_rating_id:
            raise UserError(_(
                'Este proveedor aún no tiene evaluación en Calificadora. '
                'Créela primero desde Calificadora → Evaluaciones.'
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evaluación del proveedor',
            'res_model': 'partner.rating',
            'res_id': self.partner_rating_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_source(self):
        """Abre el documento de compra/requisición ligado (producción u Odoo estándar)."""
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            raise UserError(_(
                'Esta evaluación no está ligada a un documento origen. '
                'Complete Modelo origen + ID origen, o use link_to_record() '
                'desde el módulo de Compras de producción.'
            ))
        if self.source_model not in self.env:
            raise UserError(_(
                'El modelo "%s" no existe en esta base. '
                'Instale/active el módulo de Compras o requisiciones de producción.'
            ) % self.source_model)
        return {
            'type': 'ir.actions.act_window',
            'name': self.source_ref or _('Documento origen'),
            'res_model': self.source_model,
            'res_id': self.source_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def link_to_record(self, record, ref=None):
        """Liga esta evaluación a un recordset de compra/requisición de producción."""
        self.ensure_one()
        if not record:
            raise UserError(_('No hay registro para ligar.'))
        record.ensure_one()
        self.write({
            'source_model': record._name,
            'source_res_id': record.id,
            'source_ref': ref or record.display_name,
        })
        return True

    @api.model
    def create_from_record(self, record, partner=None, ref=None, extra_vals=None):
        """Crea una evaluación ya ligada a una compra/requisición de producción."""
        if not record:
            raise UserError(_('No hay registro origen.'))
        record.ensure_one()
        partner = partner or getattr(record, 'partner_id', False)
        vals = {
            'name': _('Evaluación compra - %s') % (ref or record.display_name),
            'partner_id': partner.id if partner else False,
            'source_model': record._name,
            'source_res_id': record.id,
            'source_ref': ref or record.display_name,
        }
        if extra_vals:
            vals.update(extra_vals)
        if not vals.get('partner_id'):
            raise UserError(_(
                'Se requiere un proveedor para crear la evaluación de compra.'
            ))
        return self.create(vals)
