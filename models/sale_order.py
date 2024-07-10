from odoo import fields
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation")
    formation_count = fields.Integer(string="Formation", compute='_compute_formation_count')

    # Smart button compute -------------------------------
    def _compute_formation_count(self):
        for order in self:
            for line in order.order_line:
                formation_count = self.env['formation.phi.bis'].search_count([('name', '=', line.name)])
                order.formation_count = formation_count

    # Confirm button action ----------------------------
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                if line.product_id and line.product_id.create_formation:
                    self.env['formation.phi.bis'].create({
                        'name': line.name,
                        'partner_id': order.partner_id.id
                    })
            pass
        return res

    # Action Open smart button
    def action_open_formation(self):
        formation_name = self.order_line.name
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formation.phi.bis',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Formations',
            'domain': [('name', '=', formation_name)],
        }
