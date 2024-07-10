from odoo import fields, api
from odoo import models
from odoo.tools.translate import _



class SaleOrder(models.Model):
    _inherit = 'sign.request.item'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation", compute="_change_formations")
    session_id = fields.Many2one('formations.sessions', string="Session")

    @api.depends('partner_id', 'formation_id', 'session_id')
    def _change_formations(self):
        for session in self:
            if session.partner_id:
                session.formation_id = session.partner_id.formation_id.id
            else:
                session.formation_id = False


    #@api.depends('signer_ids.partner_id', 'signer_id', 'signers_count')
    #def _compute_is_user_signer(self):
    #    super()._compute_is_user_signer()
    #    for record in self:
    #        if record.signer_ids.filtered(lambda s: s.role_id.name == 'Participants').participants:
    #            record.is_user_signer = True

class SignRequestInheritPhidias(models.Model):
    _inherit = 'sign.request'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation", compute="_change_formations")
    session_id = fields.Many2one('formations.sessions', string="Session")

    @api.depends('request_item_ids.partner_id', 'formation_id', 'session_id')
    def _change_formations(self):
        for session in self:
            if session.request_item_ids.partner_id:
                session.formation_id = session.request_item_ids.partner_id.formation_id.id
            else:
                session.formation_id = False


class SignSendRequestMixin(models.TransientModel):
    _inherit = 'sign.send.request.signer'
