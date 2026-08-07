# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_access_calificadora = fields.Boolean(
        string='Acceso a Calificadora',
        default=False,
        help='Habilita el módulo Calificadora (evaluación documental del proveedor).',
    )
    can_access_purchase_evaluation = fields.Boolean(
        string='Acceso a Eval. Compras',
        default=False,
        help='Habilita el módulo Eval. Compras (evaluación por compra/requisición).',
    )
    # Compat con vistas/DB que aún referencian el nombre anterior
    can_access_evaluations = fields.Boolean(
        string='Acceso a evaluaciones (legado)',
        related='can_access_calificadora',
        readonly=False,
        groups='base.group_no_one',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('can_access_evaluations') and 'can_access_calificadora' not in vals:
                vals['can_access_calificadora'] = vals['can_access_evaluations']
        users = super().create(vals_list)
        users._sync_evaluation_access_groups_from_flags()
        return users

    def write(self, vals):
        if self.env.context.get('skip_evaluation_flag_sync'):
            return super().write(vals)

        vals = dict(vals)
        if 'can_access_evaluations' in vals and 'can_access_calificadora' not in vals:
            vals['can_access_calificadora'] = vals.pop('can_access_evaluations')

        sync_from_flags = bool({
            'can_access_calificadora',
            'can_access_purchase_evaluation',
        }.intersection(vals))
        sync_from_groups = 'groups_id' in vals and not sync_from_flags

        res = super().write(vals)
        if sync_from_flags:
            self._sync_evaluation_access_groups_from_flags()
        elif sync_from_groups:
            self._sync_evaluation_flags_from_groups()
        return res

    def _sync_evaluation_access_groups_from_flags(self):
        """Aplica las banderas del usuario a los grupos (menús/apps)."""
        group_cal = self.env.ref(
            'partner_rating.group_evaluation_user',
            raise_if_not_found=False,
        )
        group_pur = self.env.ref(
            'purchase_evaluation.group_purchase_evaluation_user',
            raise_if_not_found=False,
        )
        for user in self:
            commands = []
            if group_cal:
                commands.append(
                    (4, group_cal.id) if user.can_access_calificadora else (3, group_cal.id)
                )
            if group_pur:
                commands.append(
                    (4, group_pur.id)
                    if user.can_access_purchase_evaluation
                    else (3, group_pur.id)
                )
            if commands:
                user.with_context(skip_evaluation_flag_sync=True).sudo().write({
                    'groups_id': commands,
                })

    def _sync_evaluation_flags_from_groups(self):
        """Si alguien marca el grupo en Derechos de acceso, refleja las banderas."""
        group_cal = self.env.ref(
            'partner_rating.group_evaluation_user',
            raise_if_not_found=False,
        )
        group_pur = self.env.ref(
            'purchase_evaluation.group_purchase_evaluation_user',
            raise_if_not_found=False,
        )
        for user in self:
            vals = {}
            if group_cal:
                vals['can_access_calificadora'] = group_cal in user.groups_id
            if group_pur:
                vals['can_access_purchase_evaluation'] = group_pur in user.groups_id
            if vals:
                user.with_context(skip_evaluation_flag_sync=True).sudo().write(vals)
