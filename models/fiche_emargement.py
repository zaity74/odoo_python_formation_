from odoo import fields, models, api
from datetime import date, datetime

class FormationsPresence(models.Model):
    _name = 'formations.presence'
    _description = 'Formations presence '

    name = fields.Char(string="Nom du document", translate=True, required=True)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    session_id = fields.Many2one('formations.sessions', string="Session", required=True)
    formation_modules = fields.Many2many('formations.modules', string='Modules', required=True, index=True,
                                 default=lambda self: self.env['formations.modules'])
    formation_date = fields.Date(string="Date de la formation")
    attendees = fields.Many2many('res.partner', string="Participants", required=True)
    slide_type = fields.Selection([
        ('document', 'Document'),
        ('url', "Url")],
        string='Type', required=True,
        index=True,
        default='document')
    formation_url = fields.Char(string="Url")
    documents = fields.Binary(string='File')
    documents_name = fields.Char(string='Filename')

    # state
    state = fields.Selection([
        ('open', 'Confirmé')],
        string='Status', default="open", readonly=True, copy=False, tracking=True)

    @api.onchange('formation_id')
    def _select_confirm_attendees(self):
        for rec in self:
            if rec.formation_id:
                return {
                    'domain': {'attendees': [('state', '=', 'open'), ('formation_id', '=', rec.formation_id.id)]}}

    #session_id.formations == formation_id

    #@api.onchange('formation_id')
    #def _onchange_session_id(self):
    #    for session in self:
    #        return {'domain': {'session_id': [(self.session_id['formation_id'], '=', session.formation_id.id)]}}
    #        print('heyy')