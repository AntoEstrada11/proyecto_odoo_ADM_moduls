# -*- coding: utf-8 -*-
import mimetypes

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class PartnerDocument(models.Model):
    _name = 'partner.document'
    _description = 'Documento de contacto'
    _order = 'document_type_id, name, id'

    name = fields.Char(string='Nombre del documento', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    document_type_id = fields.Many2one(
        'partner.document.type',
        string='Tipo de documento',
        required=False,
        ondelete='restrict',
    )
    person_type = fields.Selection(
        [
            ('both', 'Moral y Física'),
            ('moral', 'Solo Persona Moral'),
            ('fisica', 'Solo Persona Física'),
        ],
        string='Aplica a',
        compute='_compute_person_type',
        store=True,
        readonly=False,
    )
    is_confidential = fields.Boolean(
        string='Confidencial',
        default=False,
        index=True,
        help='Si está activo, solo usuarios con acceso a documentos confidenciales '
             'pueden ver este archivo (también al evaluar en Calificadora).',
    )
    file = fields.Binary(string='Archivo', required=True, attachment=True)
    file_name = fields.Char(string='Nombre de archivo')
    mimetype = fields.Char(string='Tipo MIME', readonly=True)

    is_image = fields.Boolean(compute='_compute_file_type')
    is_pdf = fields.Boolean(compute='_compute_file_type')
    is_excel = fields.Boolean(compute='_compute_file_type')
    image_preview = fields.Binary(
        string='Vista previa',
        compute='_compute_image_preview',
    )

    @api.depends('document_type_id', 'document_type_id.person_type', 'partner_id', 'partner_id.rating_company_type')
    def _compute_person_type(self):
        for document in self:
            if document.document_type_id:
                document.person_type = document.document_type_id.person_type
            elif document.partner_id and document.partner_id.rating_company_type:
                document.person_type = document.partner_id.rating_company_type
            else:
                document.person_type = False

    @api.depends('mimetype', 'file_name')
    def _compute_file_type(self):
        excel_mimetypes = {
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.oasis.opendocument.spreadsheet',
        }
        excel_extensions = ('.xls', '.xlsx', '.ods', '.csv')
        for document in self:
            mimetype = (document.mimetype or '').lower()
            file_name = (document.file_name or '').lower()
            document.is_image = mimetype.startswith('image/')
            document.is_pdf = mimetype == 'application/pdf' or file_name.endswith('.pdf')
            document.is_excel = (
                mimetype in excel_mimetypes
                or file_name.endswith(excel_extensions)
            )

    @api.depends('file', 'is_image')
    def _compute_image_preview(self):
        for document in self:
            document.image_preview = document.file if document.is_image else False

    def _guess_mimetype(self, file_name):
        if not file_name:
            return 'application/octet-stream'
        return mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        if self.document_type_id and self.document_type_id.code != 'otro':
            self.name = self.document_type_id.name
        elif self.document_type_id and self.document_type_id.code == 'otro':
            self.name = False

    @api.onchange('file', 'file_name')
    def _onchange_file(self):
        if self.file_name:
            self.mimetype = self._guess_mimetype(self.file_name)
            if not self.name and self.document_type_id and self.document_type_id.code != 'otro':
                self.name = self.document_type_id.name
            elif not self.name:
                self.name = self.file_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_confidential') and not self.env.user.has_group(
                'partner_documents.group_confidential_documents'
            ):
                raise AccessError(_(
                    'No tiene permiso para marcar documentos como confidenciales. '
                    'Pida a un administrador que active "Acceso a documentos confidenciales" '
                    'en su usuario.'
                ))
            file_name = vals.get('file_name')
            if file_name and not vals.get('mimetype'):
                vals['mimetype'] = self._guess_mimetype(file_name)
            if not vals.get('name') and vals.get('document_type_id'):
                doc_type = self.env['partner.document.type'].browse(vals['document_type_id'])
                if doc_type.code != 'otro':
                    vals['name'] = doc_type.name
            elif file_name and not vals.get('name'):
                vals['name'] = file_name
        return super().create(vals_list)

    def write(self, vals):
        if 'is_confidential' in vals and not self.env.user.has_group(
            'partner_documents.group_confidential_documents'
        ):
            raise AccessError(_(
                'No tiene permiso para cambiar el estado confidencial de un documento. '
                'Pida a un administrador que active "Acceso a documentos confidenciales" '
                'en su usuario.'
            ))
        file_name = vals.get('file_name')
        if file_name and 'mimetype' not in vals:
            vals['mimetype'] = self._guess_mimetype(file_name)
        return super().write(vals)

    def action_delete_document(self):
        self.unlink()
        return True
