from odoo import fields, models, api

class FormationLost(models.TransientModel):
    _name = 'formations.lost'

    lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason')
    # formation management
    #active = fields.Boolean('Annuler', default=True, tracking=True)
    formation_restore = fields.Boolean('Restorer', default=True, tracking=True)

    def action_lost_formation(self):
        formation = self.env['formation.phi.bis'].browse(self.env.context.get('active_ids'))
        return formation.action_set_lost_formation()

    #def action_restore_formation(self):
    #    """ Lost semantic: probability = 0 or active = False """
    #    self.active = True
    #    self.formation_restore = self.active
    #    self.state = 'new'