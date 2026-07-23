# -*- coding: utf-8 -*-
import mimetypes

from odoo import api, fields, models


class PartnerDocument(models.Model):
    _name = 'partner.document'
    _description = 'Documento de contacto'
    _order = 'name, id'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    file = fields.Binary(string='Archivo', required=True, attachment=True)
    file_name = fields.Char(string='Nombre de archivo')
    mimetype = fields.Char(string='Tipo', readonly=True)

    is_image = fields.Boolean(compute='_compute_file_type')
    is_pdf = fields.Boolean(compute='_compute_file_type')
    is_excel = fields.Boolean(compute='_compute_file_type')
    image_preview = fields.Binary(
        string='Vista previa',
        compute='_compute_image_preview',
    )

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

    @api.onchange('file', 'file_name')
    def _onchange_file(self):
        if self.file_name:
            self.mimetype = self._guess_mimetype(self.file_name)
            if not self.name:
                self.name = self.file_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            file_name = vals.get('file_name')
            if file_name and not vals.get('mimetype'):
                vals['mimetype'] = self._guess_mimetype(file_name)
            if file_name and not vals.get('name'):
                vals['name'] = file_name
        return super().create(vals_list)

    def write(self, vals):
        file_name = vals.get('file_name')
        if file_name and 'mimetype' not in vals:
            vals['mimetype'] = self._guess_mimetype(file_name)
        return super().write(vals)
