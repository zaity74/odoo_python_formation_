from odoo import fields, models, api
from datetime import date, datetime

class FormationsModules(models.Model):
    _name = 'formations.modules'
    _description = 'store all the modules'

    name = fields.Char(string="Nom du modules", translate=True, required=True)
    #session_id.formations == formation_id

    #@api.onchange('formation_id')
    #def _onchange_session_id(self):
    #    for session in self:
    #        return {'domain': {'session_id': [(self.session_id['formation_id'], '=', session.formation_id.id)]}}
    #        print('heyy')