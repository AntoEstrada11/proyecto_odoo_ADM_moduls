# -*- coding: utf-8 -*-
from odoo import fields, models


class PartnerDocumentType(models.Model):
    _name = 'partner.document.type'
    _description = 'Tipo de documento de proveedor'
    _order = 'sequence, name'

    name = fields.Char(string='Documento', required=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    person_type = fields.Selection(
        [
            ('both', 'Moral y Física'),
            ('moral', 'Solo Persona Moral'),
            ('fisica', 'Solo Persona Física'),
        ],
        string='Aplica a',
        required=True,
        default='both',
    )
    # Campos del contacto a capturar en el wizard (separados por coma)
    capture_fields = fields.Char(
        string='Campos a capturar',
        help='Códigos separados por coma: vat, legal_representative, '
             'legal_representative_id, opening_date, social_capital, '
             'corporate_structure, bank_name, bank_account, imss_number, '
             'infonavit_number, official_id, curp',
    )
    instructions = fields.Text(string='Instrucciones del wizard')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del tipo de documento debe ser único.'),
    ]

    def get_capture_field_list(self):
        self.ensure_one()
        if not self.capture_fields:
            return []
        return [f.strip() for f in self.capture_fields.split(',') if f.strip()]

    def applies_to_person_type(self, person_type):
        self.ensure_one()
        if self.person_type == 'both':
            return True
        return bool(person_type) and self.person_type == person_type
