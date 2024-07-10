from odoo import fields, models, api
from datetime import date, datetime

class EvalAcquis(models.Model):
    _name = 'eval.acquis'
    _description = 'store all the evaluations for the differents sesssions'

    name = fields.Char(string="Nom de l'évaluation", translate=True, required=True)
    formation_modules = fields.Many2many('formations.modules', string='Modules', required=True, index=True,
                                 default=lambda self: self.env['formations.modules'])
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    session_id = fields.Many2one('formations.sessions',string="Sessions", required=True, index=True)
    eval_date = fields.Date(string="Date de l évaluation")
    attendees = fields.Many2many('formations.attendees', string="Participants", required=True, computed="_select_confirm_attendees")
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

    #session_id.formations == formation_id


    @api.onchange('session_id')
    def _select_sessions(self):
        for res in self:
            return {'domain': {'session_id': [('formation_id', '=', res.formation_id.id)]}}

    @api.onchange('attendees')
    def _select_confirm_attendees(self):
        return {'domain': {'attendees': [('state','=', 'open')]}}