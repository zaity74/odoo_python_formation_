from odoo import fields, models, api

class ProgrammeFormation(models.Model):
    _name = "programme.formation"
    _description = "specify the odoo version for the formations"

    name = fields.Char(string="Nom du programme", translate=True, required=True)

    # description du programme
    objectif = fields.Char(string="Objectif pédagogique", translate=True, required=True)
    durée = fields.Char(string="Durée de la formation", translate=True, required=True)
    evaluation = fields.Char(string="Evaluation des acquis", translate=True, required=True)
    # Champs inverse pour la relation avec formation.phi.bis
    formation_ids = fields.Many2one('programme.formation', string='Formations liées')