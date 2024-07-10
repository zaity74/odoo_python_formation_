from odoo import fields
from odoo import models


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation")
    session_id = fields.Many2one('formations.sessions', string="Session")
    createdContact = fields.Boolean('isCreated')

    # -------------------------------------------------------------------------
    # SMART BUTTON VARIABLE
    # -------------------------------------------------------------------------
    session_count = fields.Integer(string="Session(s)",compute='_compute_session')

    # -------------------------------------------------------------------------
    # SMART BUTTON COMPUTE
    # -------------------------------------------------------------------------
    def _compute_session(self):
        for rec in self:
            session_count = self.env['formations.sessions'].search_count([('formation_id', '=', rec.formation_id.id),
                                                                          ('attendees', '=', rec.id)])
            rec.session_count = session_count

    # -------------------------------------------------------------------------
    # ACTION
    # -------------------------------------------------------------------------
    def action_open_session(self):
        ctx = {
            'default_formation_id': self.formation_id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.sessions',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Sessions",
            'domain': [('formation_id', '=', self.formation_id.id),('attendees', '=', self.id)],
            'context': ctx,
        }