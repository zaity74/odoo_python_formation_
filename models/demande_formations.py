from odoo import fields, models, api
from datetime import date, datetime

class DemandeFormations(models.Model):
    _name = 'demande.formations'
    _description = 'store all formations ask by the clients '

    name = fields.Char(string="Nom du document", translate=True, required=True)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    formation_modules = fields.Many2many('formations.modules', string='Modules', required=True, index=True,
                                 default=lambda self: self.env['formations.modules'])
    formation_date = fields.Date(string="Date de la formation")
    slide_type = fields.Selection([
        ('document', 'Document'),
        ('url', "Url")],
        string='Type', required=True,
        index=True,
        default='document')
    formation_url = fields.Char(string="Url")
    documents = fields.Binary(string='Fichier')
    documents_name = fields.Char(string='Nom du fichier')

    #session_id.formations == formation_id

    #@api.onchange('formation_id')
    #def _onchange_session_id(self):
    #    for session in self:
    #        return {'domain': {'session_id': [(self.session_id['formation_id'], '=', session.formation_id.id)]}}
    #        print('heyy')