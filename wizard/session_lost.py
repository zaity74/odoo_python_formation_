from odoo import fields, models, api

class SessionLost(models.TransientModel):
    _name = 'sessions.lost'

    lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason')
    # formation management
    #active = fields.Boolean('Annuler', default=True, tracking=True)
    session_restore = fields.Boolean('Restorer', default=True, tracking=True)

    def action_lost_session(self):
        session = self.env['formations.sessions'].browse(self.env.context.get('active_ids'))
        return session.action_set_lost_session()
