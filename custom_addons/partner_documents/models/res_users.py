# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_access_confidential_documents = fields.Boolean(
        string='Acceso a documentos confidenciales',
        default=False,
        help='Permite ver y administrar documentos de proveedor marcados como confidenciales.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_confidential_documents_group_from_flag()
        return users

    def write(self, vals):
        if self.env.context.get('skip_confidential_docs_flag_sync'):
            return super().write(vals)

        vals = dict(vals)
        sync_from_flag = 'can_access_confidential_documents' in vals
        sync_from_groups = 'groups_id' in vals and not sync_from_flag

        res = super().write(vals)
        if sync_from_flag:
            self._sync_confidential_documents_group_from_flag()
        elif sync_from_groups:
            self._sync_confidential_documents_flag_from_group()
        return res

    def _sync_confidential_documents_group_from_flag(self):
        group = self.env.ref(
            'partner_documents.group_confidential_documents',
            raise_if_not_found=False,
        )
        if not group:
            return
        for user in self:
            command = (
                (4, group.id)
                if user.can_access_confidential_documents
                else (3, group.id)
            )
            user.with_context(skip_confidential_docs_flag_sync=True).sudo().write({
                'groups_id': [command],
            })

    def _sync_confidential_documents_flag_from_group(self):
        group = self.env.ref(
            'partner_documents.group_confidential_documents',
            raise_if_not_found=False,
        )
        if not group:
            return
        for user in self:
            user.with_context(skip_confidential_docs_flag_sync=True).sudo().write({
                'can_access_confidential_documents': group in user.groups_id,
            })
