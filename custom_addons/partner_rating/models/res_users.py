# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_access_evaluations = fields.Boolean(
        string='Acceso a evaluaciones',
        compute='_compute_can_access_evaluations',
        inverse='_inverse_can_access_evaluations',
        help='Si está activo, el usuario puede ver Calificadora y Eval. Compras.',
    )

    @api.depends('groups_id')
    def _compute_can_access_evaluations(self):
        group = self.env.ref(
            'partner_rating.group_evaluation_user',
            raise_if_not_found=False,
        )
        for user in self:
            user.can_access_evaluations = bool(group and group in user.groups_id)

    def _inverse_can_access_evaluations(self):
        group = self.env.ref(
            'partner_rating.group_evaluation_user',
            raise_if_not_found=False,
        )
        if not group:
            return
        for user in self:
            if user.can_access_evaluations:
                user.sudo().write({'groups_id': [(4, group.id)]})
            else:
                user.sudo().write({'groups_id': [(3, group.id)]})
