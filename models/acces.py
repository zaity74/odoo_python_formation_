from odoo import fields, models, api
from datetime import date, datetime

class FormationsAccess(models.Model):
    _name = 'formations.access'
    _description = 'Acces '

    name = fields.Char(string="Nom du document", translate=True, required=True)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    slide_type = fields.Selection([
        ('url', "Url")],
        string='Type', required=True,
        index=True,
        default='url')
    formation_url = fields.Char(string="Url")
    documents_name = fields.Char(string='Lien')

    #session_id.formations == formation_id

    #@api.onchange('formation_id')
    #def _onchange_session_id(self):
    #    for session in self:
    #        return {'domain': {'session_id': [(self.session_id['formation_id'], '=', session.formation_id.id)]}}
    #        print('heyy')