# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

RESEARCH_TEMPLATES = [
    'Buró Comercial (PROFECO)',
    'Quién es Quién',
    'Portal SAT',
    'Calificación y página oficial',
    'Domicilio',
]

PERFORMANCE_TEMPLATES = [
    'Precio / competitividad',
    'Calidad del producto o servicio',
    'Tiempo de entrega',
    'Atención y comunicación',
    'Cumplimiento contractual',
]


class PartnerRating(models.Model):
    _name = 'partner.rating'
    _description = 'Evaluación de proveedor'
    _order = 'date desc, id desc'

    name = fields.Char(string='Referencia', required=True, default='Nueva evaluación')
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor / Contacto',
        required=True,
        index=True,
    )
    date = fields.Date(
        string='Fecha de evaluación',
        default=fields.Date.context_today,
        required=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('done', 'Finalizada'),
        ],
        string='Estado',
        default='draft',
        required=True,
    )

    _sql_constraints = [
        (
            'partner_rating_partner_uniq',
            'unique(partner_id)',
            'Solo puede existir una evaluación por contacto/proveedor.',
        ),
    ]

    @api.constrains('partner_id')
    def _check_unique_partner_rating(self):
        for rating in self:
            domain = [('partner_id', '=', rating.partner_id.id), ('id', '!=', rating.id)]
            if self.search_count(domain):
                raise UserError(_(
                    'Ya existe una evaluación para "%s". '
                    'Solo se permite una evaluación por contacto/proveedor.'
                ) % rating.partner_id.display_name)


    # Datos del contacto (capturados en Contactos / wizard de documentos)
    company_name = fields.Char(related='partner_id.name', readonly=True)
    vat = fields.Char(related='partner_id.vat', string='RFC', readonly=True)
    company_type = fields.Selection(
        related='partner_id.rating_company_type',
        string='Tipo de empresa',
        readonly=True,
    )
    legal_representative = fields.Char(
        related='partner_id.legal_representative',
        readonly=True,
    )
    legal_representative_id = fields.Char(
        related='partner_id.legal_representative_id',
        readonly=True,
    )
    official_id = fields.Char(related='partner_id.official_id', readonly=True)
    curp = fields.Char(related='partner_id.curp', readonly=True)
    opening_date = fields.Date(related='partner_id.opening_date', readonly=True)
    social_capital = fields.Char(related='partner_id.social_capital', readonly=True)
    corporate_structure = fields.Text(
        related='partner_id.corporate_structure',
        readonly=True,
    )
    contractual_object = fields.Text(
        related='partner_id.contractual_object',
        readonly=True,
    )
    bank_name = fields.Char(related='partner_id.bank_name', readonly=True)
    bank_account = fields.Char(related='partner_id.bank_account', readonly=True)
    imss_number = fields.Char(related='partner_id.imss_number', readonly=True)
    infonavit_number = fields.Char(related='partner_id.infonavit_number', readonly=True)

    meets_internal_criteria = fields.Selection(
        [
            ('yes', 'Sí'),
            ('no', 'No'),
        ],
        string='Cumple con los criterios internos',
    )
    analysis_status = fields.Selection(
        [
            ('approved', 'Aprobado'),
            ('approved_reserved', 'Aprobado con reservas'),
            ('not_recommended', 'No se recomienda'),
            ('failed', 'Fracasado'),
        ],
        string='Estado del análisis',
    )
    status_reason = fields.Text(string='Razón de estatus')

    document_line_ids = fields.One2many(
        'partner.rating.document.line',
        'rating_id',
        string='Documentos evaluados',
    )
    document_line_count = fields.Integer(
        string='Documentos en checklist',
        compute='_compute_document_line_stats',
    )
    document_approved_count = fields.Integer(
        string='Documentos aprobados',
        compute='_compute_document_line_stats',
    )
    document_pending_count = fields.Integer(
        string='Documentos pendientes',
        compute='_compute_document_line_stats',
    )
    documents_notes = fields.Text(string='Notas de documentos')
    post_hire_notes = fields.Text(
        string='Al ser contratado será necesario presentar',
    )

    research_line_ids = fields.One2many(
        'partner.rating.research.line',
        'rating_id',
        string='Averiguaciones',
    )
    research_notes = fields.Text(string='Notas de averiguaciones')
    risk_level = fields.Selection(
        [
            ('low', 'Bajo'),
            ('medium', 'Medio'),
            ('high', 'Alto'),
        ],
        string='Riesgo',
    )

    performance_line_ids = fields.One2many(
        'partner.rating.performance.line',
        'rating_id',
        string='Desempeño comercial (legado)',
        help='Ya no se usa para calificar. El desempeño viene del historial de compras.',
    )
    performance_notes = fields.Text(string='Notas de desempeño')
    purchase_evaluation_count = fields.Integer(
        string='Compras evaluadas',
        compute='_compute_score',
        store=True,
    )
    weight_viability = fields.Float(
        string='Peso viabilidad %',
        default=60.0,
        help='Peso de viabilidad jurídica/documental + averiguaciones en el global.',
    )
    weight_performance = fields.Float(
        string='Peso desempeño %',
        default=40.0,
        help='Peso del desempeño comercial (historial de compras finalizadas).',
    )

    viability_score_obtained = fields.Float(compute='_compute_score', store=True)
    viability_score_max = fields.Float(compute='_compute_score', store=True)
    viability_percent = fields.Float(
        string='% Viabilidad jurídica / documental',
        compute='_compute_score',
        store=True,
    )
    performance_score_obtained = fields.Float(compute='_compute_score', store=True)
    performance_score_max = fields.Float(compute='_compute_score', store=True)
    performance_percent = fields.Float(
        string='% Desempeño comercial (historial compras)',
        compute='_compute_score',
        store=True,
    )
    score_obtained = fields.Float(compute='_compute_score', store=True)
    score_max = fields.Float(compute='_compute_score', store=True)
    score_percent = fields.Float(
        string='% Global ponderado',
        compute='_compute_score',
        store=True,
    )
    rating_level = fields.Selection(
        [
            ('failed', 'Fracasado'),
            ('not_recommended', 'No se recomienda'),
            ('reserved', 'Aprobado con reservas'),
            ('approved', 'Aprobado'),
        ],
        string='Rango de calificación',
        compute='_compute_score',
        store=True,
    )

    @api.depends('document_line_ids', 'document_line_ids.situation')
    def _compute_document_line_stats(self):
        for rating in self:
            lines = rating.document_line_ids
            rating.document_line_count = len(lines)
            rating.document_approved_count = len(lines.filtered(lambda l: l.situation == 'approved'))
            rating.document_pending_count = len(lines.filtered(
                lambda l: l.situation == 'not_received'
            ))

    @api.constrains('weight_viability', 'weight_performance')
    def _check_weights(self):
        for rating in self:
            total = (rating.weight_viability or 0.0) + (rating.weight_performance or 0.0)
            if abs(total - 100.0) > 0.01:
                raise UserError(_(
                    'Los pesos de viabilidad y desempeño deben sumar 100%%. '
                    'Actual: %.1f%%.'
                ) % total)

    @api.depends(
        'document_line_ids.situation',
        'research_line_ids.situation',
        'meets_internal_criteria',
        'analysis_status',
        'weight_viability',
        'weight_performance',
        'partner_id',
    )
    def _compute_score(self):
        doc_score_map = {
            'not_received': 0.0,
            'received': 1.0,
            'approved': 2.0,
        }
        research_score_map = {
            'pending': 0.0,
            'done': 1.0,
            'approved': 2.0,
            'unfavorable': 0.0,
        }
        for rating in self:
            doc_lines = rating.document_line_ids
            research_lines = rating.research_line_ids

            viability_max = (len(doc_lines) * 2.0) + (len(research_lines) * 2.0)
            viability_obtained = sum(
                doc_score_map.get(line.situation, 0.0) for line in doc_lines
            )
            viability_obtained += sum(
                research_score_map.get(line.situation, 0.0)
                for line in research_lines
            )
            if rating.meets_internal_criteria == 'yes':
                viability_obtained += 2.0
                viability_max += 2.0
            elif rating.meets_internal_criteria == 'no':
                viability_max += 2.0

            viability_percent = (
                (viability_obtained / viability_max * 100.0) if viability_max else 0.0
            )

            (
                performance_obtained,
                performance_max,
                performance_percent,
                purchase_count,
            ) = rating._get_purchase_performance_stats()

            w_v = rating.weight_viability or 0.0
            w_p = rating.weight_performance or 0.0
            if abs(w_v + w_p - 100.0) > 0.01:
                w_v, w_p = 60.0, 40.0

            if not purchase_count:
                global_percent = viability_percent
            else:
                global_percent = (
                    (viability_percent * w_v / 100.0)
                    + (performance_percent * w_p / 100.0)
                )

            if rating.analysis_status == 'failed' or global_percent < 50:
                level = 'failed'
            elif rating.analysis_status == 'not_recommended' or global_percent < 70:
                level = 'not_recommended'
            elif rating.analysis_status == 'approved_reserved' or global_percent < 90:
                level = 'reserved'
            else:
                level = 'approved'

            rating.viability_score_obtained = viability_obtained
            rating.viability_score_max = viability_max
            rating.viability_percent = viability_percent
            rating.performance_score_obtained = performance_obtained
            rating.performance_score_max = performance_max
            rating.performance_percent = performance_percent
            rating.purchase_evaluation_count = purchase_count
            rating.score_obtained = viability_obtained + performance_obtained
            rating.score_max = viability_max + performance_max
            rating.score_percent = global_percent
            rating.rating_level = level

    def _get_purchase_performance_stats(self):
        """Desempeño = puntos acumulados de compras finalizadas del proveedor."""
        self.ensure_one()
        if 'purchase.evaluation' not in self.env or not self.partner_id:
            return 0.0, 0.0, 0.0, 0
        purchases = self.env['purchase.evaluation'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'done'),
        ])
        if not purchases:
            return 0.0, 0.0, 0.0, 0
        obtained = sum(purchases.mapped('purchase_score_obtained'))
        maximum = sum(purchases.mapped('purchase_score_max'))
        percent = (obtained / maximum * 100.0) if maximum else 0.0
        return obtained, maximum, percent, len(purchases)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = f'Evaluación - {self.partner_id.name}'

    def action_open_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contacto',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_score_help(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cómo se calcula el %',
            'res_model': 'partner.rating.score.help.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_rating_id': self.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        Partner = self.env['res.partner']
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id and self.search_count([('partner_id', '=', partner_id)]):
                partner = Partner.browse(partner_id)
                raise UserError(_(
                    'Ya existe una evaluación para "%s". '
                    'Solo se permite una evaluación por contacto/proveedor. '
                    'Ábrela desde Calificadora o desde la ficha del contacto.'
                ) % partner.display_name)
        ratings = super().create(vals_list)
        for rating in ratings:
            rating._generate_default_lines()
        return ratings

    def write(self, vals):
        if 'partner_id' in vals:
            for rating in self:
                if rating.partner_id and vals['partner_id'] != rating.partner_id.id:
                    raise UserError(_(
                        'No se puede cambiar el contacto/proveedor de una evaluación ya creada. '
                        'Si necesita evaluar a otro proveedor, cree una evaluación nueva.'
                    ))
        return super().write(vals)

    def _get_applicable_document_types(self):
        self.ensure_one()
        person_type = self.partner_id.rating_company_type
        if not person_type:
            return self.env['partner.document.type']
        return self.env['partner.document.type'].search([
            '|',
            ('person_type', '=', 'both'),
            ('person_type', '=', person_type),
        ])

    def _generate_default_lines(self):
        self.ensure_one()
        if not self.partner_id.rating_company_type:
            raise UserError(_(
                'El contacto debe tener Tipo de empresa (Moral/Física) '
                'antes de crear la evaluación.'
            ))
        if not self.document_line_ids:
            doc_types = self._get_applicable_document_types()
            uploaded = {
                doc.document_type_id.id: doc
                for doc in self.partner_id.document_ids
                if doc.document_type_id
            }
            line_vals = []
            for doc_type in doc_types:
                uploaded_doc = uploaded.get(doc_type.id)
                line_vals.append({
                    'rating_id': self.id,
                    'sequence': doc_type.sequence,
                    'document_type_id': doc_type.id,
                    'situation': 'received' if uploaded_doc else 'not_received',
                    'partner_document_id': uploaded_doc.id if uploaded_doc else False,
                })
            if line_vals:
                self.env['partner.rating.document.line'].create(line_vals)
        if not self.research_line_ids:
            self.env['partner.rating.research.line'].create([
                {
                    'rating_id': self.id,
                    'sequence': index,
                    'name': name,
                }
                for index, name in enumerate(RESEARCH_TEMPLATES, start=1)
            ])

    def action_open_purchase_evaluations(self):
        self.ensure_one()
        if 'purchase.evaluation' not in self.env:
            raise UserError(_(
                'Instale el módulo "Evaluación de Compras / Requisiciones" '
                'para consultar el historial de desempeño.'
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial de compras evaluadas'),
            'res_model': 'purchase.evaluation',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'done'),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_load_checklist(self):
        for rating in self:
            rating._generate_default_lines()
        return True

    def action_reload_checklist(self):
        """Regenera el checklist según el tipo de persona actual del contacto."""
        for rating in self:
            rating.document_line_ids.unlink()
            rating._generate_default_lines()
        return True

    def action_set_done(self):
        self.write({'state': 'done'})
        return True

    def action_set_draft(self):
        self.write({'state': 'draft'})
        return True
