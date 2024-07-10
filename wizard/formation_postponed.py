from odoo import fields, models, api

class SessionPostponed(models.TransientModel):
    _name = 'sessions.postponed'

    postponed_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason')
    # formation management
    #active = fields.Boolean('Annuler', default=True, tracking=True)
    def action_postponed_session(self):
        session = self.env['formations.sessions'].browse(self.env.context.get('active_ids'))
        return session.action_set_postponed_session()