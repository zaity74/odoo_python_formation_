from odoo import fields, models, api
from datetime import date, datetime

class FormationsFicheReclamation(models.Model):
    _name = 'fiche.reclamation'
    _inherit = 'mail.thread'
    _description = 'store all the reclamations '

    name = fields.Char(string="Nom du document", translate=True, required=True)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation")
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

    # chat field
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string="Followers", groups="base.groups_user"
    )
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities', auto_join=True, groups="base.group_user"
    )
    message_ids = fields.One2many(
        'mail.message', 'res_id', string="Messages", auto_join=True
    )

    def message_get_default_recipients(self):
        recipients = super(FormationsFicheReclamation, self).message_post()
        for record in self:
            if record.partner_id:
                recipients.append((record.partner_id.id, record.partner_id.name))
        return recipients
