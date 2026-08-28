# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


CAPTURE_FIELDS = [
    'vat',
    'legal_representative',
    'legal_representative_id',
    'official_id',
    'curp',
    'opening_date',
    'social_capital',
    'corporate_structure',
    'bank_name',
    'bank_account',
    'imss_number',
    'infonavit_number',
    'contractual_object',
]


class PartnerDocumentUploadWizard(models.TransientModel):
    _name = 'partner.document.upload.wizard'
    _description = 'Asistente para subir documento de contacto'

    partner_id = fields.Many2one('res.partner', string='Contacto', required=True)
    # Campo concreto (no related) para que el dominio del Many2one sí filtre
    rating_company_type = fields.Selection(
        [
            ('moral', 'Moral'),
            ('fisica', 'Física'),
        ],
        string='Tipo de empresa',
        required=True,
        readonly=True,
    )
    document_type_id = fields.Many2one(
        'partner.document.type',
        string='Tipo de documento',
        required=False,
        domain="['|', ('person_type', '=', 'both'), ('person_type', '=', rating_company_type)]",
    )
    is_custom_document = fields.Boolean(
        compute='_compute_is_custom_document',
        string='Es documento personalizado',
    )
    document_name = fields.Char(
        string='Nombre del documento',
        required=True,
        help='Puede elegir un tipo de la lista o escribir el nombre si es otro documento.',
    )
    instructions = fields.Text(
        related='document_type_id.instructions',
        readonly=True,
    )
    file = fields.Binary(string='Archivo', required=True, attachment=False)
    file_name = fields.Char(string='Nombre de archivo')
    is_confidential = fields.Boolean(
        string='Documento confidencial',
        default=False,
        help='Solo usuarios con "Acceso a documentos confidenciales" podrán verlo.',
    )
    show_vat = fields.Boolean(compute='_compute_show_fields', string='Show VAT')
    show_legal_representative = fields.Boolean(compute='_compute_show_fields', string='Show Rep Name')
    show_legal_representative_id = fields.Boolean(compute='_compute_show_fields', string='Show Rep ID')
    show_official_id = fields.Boolean(compute='_compute_show_fields', string='Show Official ID')
    show_curp = fields.Boolean(compute='_compute_show_fields', string='Show CURP')
    show_opening_date = fields.Boolean(compute='_compute_show_fields', string='Show Opening Date')
    show_social_capital = fields.Boolean(compute='_compute_show_fields', string='Show Capital')
    show_corporate_structure = fields.Boolean(compute='_compute_show_fields', string='Show Structure')
    show_bank_name = fields.Boolean(compute='_compute_show_fields', string='Show Bank')
    show_bank_account = fields.Boolean(compute='_compute_show_fields', string='Show Account')
    show_imss_number = fields.Boolean(compute='_compute_show_fields', string='Show IMSS')
    show_infonavit_number = fields.Boolean(compute='_compute_show_fields', string='Show INFONAVIT')
    show_contractual_object = fields.Boolean(compute='_compute_show_fields', string='Show Object')

    vat = fields.Char(string='RFC')
    legal_representative = fields.Char(string='Nombre del representante legal')
    legal_representative_id = fields.Char(string='ID / Folio del representante')
    official_id = fields.Char(string='Identificación oficial')
    curp = fields.Char(string='CURP')
    opening_date = fields.Date(string='Fecha de apertura / constitución')
    social_capital = fields.Char(string='Capital social')
    corporate_structure = fields.Text(string='Estructura corporativa')
    bank_name = fields.Char(string='Banco')
    bank_account = fields.Char(string='Cuenta / CLABE')
    imss_number = fields.Char(string='Registro patronal IMSS')
    infonavit_number = fields.Char(string='Número INFONAVIT')
    contractual_object = fields.Text(string='Objeto contractual')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        partner_id = res.get('partner_id') or self.env.context.get('default_partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(int(partner_id))
            person_type = (
                self.env.context.get('default_rating_company_type')
                or partner.get_document_person_type()
            )
            res['partner_id'] = partner.id
            res['rating_company_type'] = person_type
            for fname in CAPTURE_FIELDS:
                res[fname] = partner[fname]
        return res

    @api.depends('document_type_id', 'document_type_id.code')
    def _compute_is_custom_document(self):
        for wizard in self:
            wizard.is_custom_document = (
                not wizard.document_type_id
                or wizard.document_type_id.code == 'otro'
            )

    @api.depends('document_type_id', 'document_type_id.capture_fields')
    def _compute_show_fields(self):
        for wizard in self:
            fields_list = (
                wizard.document_type_id.get_capture_field_list()
                if wizard.document_type_id else []
            )
            for fname in CAPTURE_FIELDS:
                wizard[f'show_{fname}'] = fname in fields_list

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.document_type_id = False
        self.document_name = False
        if self.partner_id:
            self.rating_company_type = self.partner_id.get_document_person_type()
            self._load_partner_values()

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        self._load_partner_values()
        if self.document_type_id and self.document_type_id.code != 'otro':
            self.document_name = self.document_type_id.name
        else:
            # Otro / sin tipo: dejar que la persona escriba el nombre
            self.document_name = False

    def _load_partner_values(self):
        partner = self.partner_id
        if not partner:
            return
        for fname in CAPTURE_FIELDS:
            self[fname] = partner[fname]

    def action_confirm(self):
        self.ensure_one()
        partner = self.partner_id
        person_type = self.rating_company_type or partner.get_document_person_type()
        if not person_type:
            raise UserError(_(
                'No se pudo determinar si el contacto es Persona Moral o Física.'
            ))

        document_name = (self.document_name or '').strip()
        if not document_name:
            raise UserError(_('Escriba el nombre del documento.'))

        if self.is_confidential and not self.env.user.has_group(
            'partner_documents.group_confidential_documents'
        ):
            raise UserError(_(
                'No tiene permiso para marcar documentos como confidenciales. '
                'Pida a un administrador que active "Acceso a documentos confidenciales" '
                'en su usuario.'
            ))

        doc_type = self.document_type_id
        if doc_type and not doc_type.applies_to_person_type(person_type):
            raise UserError(_(
                'El documento "%(doc)s" no aplica para persona %(ptype)s.'
            ) % {
                'doc': doc_type.name,
                'ptype': 'Moral' if person_type == 'moral' else 'Física',
            })

        partner_vals = {}
        if self.vat:
            partner_vals['vat'] = self.vat
        if self.curp:
            partner_vals['curp'] = self.curp
        if doc_type:
            for fname in doc_type.get_capture_field_list():
                if fname in ('vat', 'curp'):
                    continue
                value = self[fname]
                if value:
                    partner_vals[fname] = value
        if partner_vals:
            partner.write(partner_vals)

        document = self.env['partner.document'].create({
            'partner_id': partner.id,
            'document_type_id': doc_type.id if doc_type else False,
            'name': document_name,
            'file': self.file,
            'file_name': self.file_name,
            'person_type': doc_type.person_type if doc_type else person_type,
            'is_confidential': self.is_confidential,
        })

        if doc_type and doc_type.code != 'otro' and 'partner.rating.document.line' in self.env:
            lines = self.env['partner.rating.document.line'].search([
                ('rating_id.partner_id', '=', partner.id),
                ('rating_id.state', '=', 'draft'),
                ('document_type_id', '=', doc_type.id),
                ('situation', '=', 'not_received'),
            ])
            if lines:
                lines.write({
                    'situation': 'received',
                    'partner_document_id': document.id,
                })

        return {'type': 'ir.actions.act_window_close'}
