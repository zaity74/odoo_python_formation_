from odoo import fields, models, api
from datetime import date, datetime

class FormationsEvaluationsGlobal(models.Model):
    _name = 'formations.eval.global'
    _description = 'store all the hot evaluations '

    name = fields.Char(string="Nom de l'évaluation", translate=True, required=True)
    formation_modules = fields.Many2many('formations.modules', string='Modules', required=True, index=True,
                                 default=lambda self: self.env['formations.modules'])
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    session_id = fields.Many2one('formations.sessions',string="Sessions", required=True, index=True)
    eval_date = fields.Date(string="Date de l évaluation")
    slide_type = fields.Selection([
        ('document', 'Document'),
        ('url', "Url")],
        string='Type', required=True,
        index=True,
        default='document')
    formation_url = fields.Char(string="Url")
    documents = fields.Binary(string='File')
    documents_name = fields.Char(string='Filename')
