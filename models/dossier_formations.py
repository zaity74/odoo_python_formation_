from odoo import fields, models, api
from datetime import date, datetime
from odoo.exceptions import ValidationError
import tempfile
import base64

class DossierFormations(models.Model):
    _name = 'dossier.formations'
    _inherit = 'mail.thread'
    _description = 'store all the formations folders '

    name = fields.Char(string="Nom du dossier de formation", translate=True, required=True)
    company_id = fields.Many2one('res.company', 'Société', required=True, index=True,
                                 default=lambda self: self.env.company)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation")
    partner_id = fields.Many2one('res.partner',string="Client",trakcking=True)
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
        recipients = super(DossierFormations, self).message_post()
        for record in self:
            if record.partner_id:
                recipients.append((record.partner_id.id, record.partner_id.name))
        return recipients

    @api.constrains('formation_id')
    def _check_formation_id(self):
        for record in self:
            if not record.formation_id:
                raise ValidationError("Le champ 'Formation' est obligatoire.")

    def action_send_formation_folder(self):
        template = self.env.ref('Phidias_formation.session_template_email_support_formation', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        self.ensure_one()

        # Recherche du support de formation correspondant à la formation
        support = self.documents

        # Créer un fichier temporaire pour stocker les données du PDF
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(support)
            temp_file.close()
            attachment_path = temp_file.name

            # Lire les données du fichier temporaire
            with open(attachment_path, 'rb') as file:
                attachment_data = file.read()

            # Ajouter le fichier temporaire en tant que pièce jointe
            attachment = self.env['ir.attachment'].create({
                'name': self.documents_name,  # Nom du fichier joint
                'datas': base64.b64encode(attachment_data),
                'mimetype': 'application/pdf',  # Type MIME du fichier PDF
                'res_model': 'dossier.formations',
                'res_id': self.id,
            })

        ctx = dict(
            default_model='dossier.formations',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id,
            default_composition_mode='comment',
            custom_layout="mail.mail_notification_light",
            # Ajouter les pièces jointes au contexte
            default_attachment_ids=[attachment.id],
        )

        return {
            'name': ('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
