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

    score_obtained = fields.Float(compute='_compute_score', store=True)
    score_max = fields.Float(compute='_compute_score', store=True)
    score_percent = fields.Float(
        string='Calificación %',
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

    @api.depends(
        'document_line_ids.situation',
        'meets_internal_criteria',
        'analysis_status',
    )
    def _compute_score(self):
        for rating in self:
            lines = rating.document_line_ids
            score_max = len(lines) * 2.0 if lines else 0.0
            score_map = {
                'not_received': 0.0,
                'received': 1.0,
                'approved': 2.0,
            }
            score_obtained = sum(
                score_map.get(line.situation, 0.0) for line in lines
            )
            if rating.meets_internal_criteria == 'yes':
                score_obtained += 2.0
                score_max += 2.0
            elif rating.meets_internal_criteria == 'no':
                score_max += 2.0

            percent = (score_obtained / score_max * 100.0) if score_max else 0.0
            if rating.analysis_status == 'failed' or percent < 50:
                level = 'failed'
            elif rating.analysis_status == 'not_recommended' or percent < 70:
                level = 'not_recommended'
            elif rating.analysis_status == 'approved_reserved' or percent < 90:
                level = 'reserved'
            else:
                level = 'approved'

            rating.score_obtained = score_obtained
            rating.score_max = score_max
            rating.score_percent = percent
            rating.rating_level = level

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

    def action_load_checklist(self):
        for rating in self:
            if rating.document_line_ids:
                continue
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
