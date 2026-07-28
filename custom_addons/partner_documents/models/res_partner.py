# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Moral/Física alineado al tipo estándar del contacto (Empresa/Individual)
    rating_company_type = fields.Selection(
        [
            ('moral', 'Moral'),
            ('fisica', 'Física'),
        ],
        string='Tipo de empresa',
        compute='_compute_rating_company_type',
        inverse='_inverse_rating_company_type',
        store=True,
        readonly=False,
    )
    legal_representative = fields.Char(
        string='Nombre del representante legal',
    )
    legal_representative_id = fields.Char(
        string='ID / Folio del representante legal',
    )
    official_id = fields.Char(
        string='Identificación oficial',
        help='INE, pasaporte u otra identificación del titular (persona física)',
    )
    curp = fields.Char(string='CURP')
    opening_date = fields.Date(string='Fecha de apertura / constitución')
    social_capital = fields.Char(string='Capital social')
    corporate_structure = fields.Text(
        string='Estructura corporativa',
        help='Nombre / cualificación de cada integrante',
    )
    contractual_object = fields.Text(string='Objeto contractual')
    bank_name = fields.Char(string='Banco')
    bank_account = fields.Char(string='Cuenta / CLABE')
    imss_number = fields.Char(string='Registro patronal IMSS')
    infonavit_number = fields.Char(string='Número INFONAVIT')

    document_ids = fields.One2many(
        'partner.document',
        'partner_id',
        string='Documentos',
    )

    @api.depends('is_company')
    def _compute_rating_company_type(self):
        for partner in self:
            partner.rating_company_type = 'moral' if partner.is_company else 'fisica'

    def _inverse_rating_company_type(self):
        for partner in self:
            partner.is_company = partner.rating_company_type == 'moral'

    def get_document_person_type(self):
        """Tipo usado para filtrar documentos digitalizados."""
        self.ensure_one()
        if self.rating_company_type:
            return self.rating_company_type
        return 'moral' if self.is_company else 'fisica'

    def action_open_document_upload_wizard(self):
        self.ensure_one()
        person_type = self.get_document_person_type()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subir documento',
            'res_model': 'partner.document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_rating_company_type': person_type,
            },
        }
