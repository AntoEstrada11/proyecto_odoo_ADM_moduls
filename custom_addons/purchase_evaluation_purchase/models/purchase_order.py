# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_evaluation_ids = fields.One2many(
        'purchase.evaluation',
        compute='_compute_purchase_evaluation_ids',
        string='Evaluaciones de compra',
    )
    purchase_evaluation_count = fields.Integer(
        compute='_compute_purchase_evaluation_ids',
    )

    def _compute_purchase_evaluation_ids(self):
        Evaluation = self.env['purchase.evaluation']
        for order in self:
            evaluations = Evaluation.search([
                ('source_model', '=', 'purchase.order'),
                ('source_res_id', '=', order.id),
            ])
            order.purchase_evaluation_ids = evaluations
            order.purchase_evaluation_count = len(evaluations)

    def action_open_purchase_evaluations(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Evaluaciones de compra'),
            'res_model': 'purchase.evaluation',
            'view_mode': 'tree,form',
            'domain': [
                ('source_model', '=', 'purchase.order'),
                ('source_res_id', '=', self.id),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_source_model': 'purchase.order',
                'default_source_res_id': self.id,
                'default_source_ref': self.name,
                'default_name': _('Evaluación compra - %s') % self.name,
                'default_amount_total': self.amount_total,
            },
        }
        if self.purchase_evaluation_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.purchase_evaluation_ids.id,
            })
        return action

    def action_create_purchase_evaluation(self):
        self.ensure_one()
        evaluation = self.env['purchase.evaluation'].create_from_record(
            self,
            partner=self.partner_id,
            ref=self.name,
            extra_vals={
                'amount_total': self.amount_total,
                'currency_id': self.currency_id.id,
            },
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Evaluación de compra'),
            'res_model': 'purchase.evaluation',
            'res_id': evaluation.id,
            'view_mode': 'form',
            'target': 'current',
        }
