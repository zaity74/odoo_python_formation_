from odoo import fields, models, api
from datetime import date, datetime
from odoo.exceptions import UserError
import tempfile
import base64

class FormationsPhiBis(models.Model):
    _name = "formation.phi.bis"
    _inherit = 'mail.thread'
    _description = "identification of customer requirements"

    # formation
    name = fields.Char(string="Nom de l'événement", translate=True, required=True, readonly=1)
    odoo_version = fields.Many2one("odoo.version",string="Version Odoo", required=False, index=True,
                                 default=lambda self: self.env['odoo.version'])
    formation_date_begin = fields.Date(string='Date de début')
    formation_date_end = fields.Date('Date de fin')
    teacher = fields.Many2many('hr.employee', string='Formateur', required=False, index=True,
                                 default=lambda self: self.env['hr.employee'])

    # company
    company_id = fields.Many2one('res.company', 'company', required=True, index=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner',string="Société",trakcking=True)
    location = fields.Selection([
        ('phidias', 'Locaux Phidias'),
        ('client', 'Locaux client'),
        ('url', 'distance'),
    ], tracking=True, string="Lieu de formation", required=False)
    formation_url = fields.Char(string="Url")
    address_id = fields.Many2one('res.partner',string="Adresse", compute='_compute_address_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

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

    # messaging
    activity_ids = fields.One2many('mail.activity', 'calendar_event_id', string='Activities')

    # -------------------------------------------------------------------------
    # SMART BUTTON COUNT VARIABLE
    # -------------------------------------------------------------------------
    session_count = fields.Integer(string='Session(s)', compute='_compute_session_count')
    eval_count = fields.Integer(string='Evaluation(s)', compute='_compute_formation_count')
    formation_folder_count = fields.Integer(string='Dossier formation', compute='_compute_formation_folder_count')
    formation_support_count = fields.Integer(string='Support(s) de formation', compute='_compute_formation_support_count')
    formation_debrief_count = fields.Integer(string='Compte-rendu', compute='_compute_formation_debrief_count')
    formation_reclamation_count = fields.Integer(string='Fiche(s) de réclamation', compute='_compute_formation_reclamation_count')
    formation_application_count = fields.Integer(string='Sondage(s)',
                                                 compute='_compute_formation_application_count')
    formation_prerequisites_count = fields.Integer(string='Pré-requis',
                                                 compute='_compute_formation_prerequisites_count')
    fiche_emargement_count = fields.Integer(string="Fiche(s) d'émargement",
                                            compute='_compute_fiche_emargement_count')
    access_count = fields.Integer(string="Accès",
                                            compute='_compute_access_count')
    total_attendees_count = fields.Integer(string="Participants",
                                  compute='_compute_attendees_count')
    total_invoiced_count = fields.Monetary(string="Devis Total", compute='_compute_invoice_total')
    invoice_count = fields.Integer(string="Facture(s)",compute='_compute_factures_count')
    eval_acquis_count = fields.Integer(string="Evaluation des acquis",compute='_compute_eval_acquis_count')
    plan_formation_count = fields.Integer(string="Plan de formation",compute='_compute_plan_formation')

    # formation management
    active = fields.Boolean('Annuler', default=True, tracking=True)
    formation_restore = fields.Boolean('Restorer', default=True, tracking=True)

    # programme formation
    programme = fields.Many2one('programme.formation', string="Programme de base", required=True,
                                inverse_name='child_ids')
    programme_ids = fields.One2many('programme.formation', 'formation_ids', string='Child Tags')
    programme_name = fields.Char(string="Nom du programme",  store=True)

    def action_add_programme_formation(self):
        new_records = []
        for record in self:
            if record.programme:
                print(record.programme)
                new_record = self.create({
                    'programme': record.programme.id,
                    'programme_name': record.programme.name,
                    'name': record.programme.name,
                    # ... autres champs ...
                })
                new_records.append(new_record.id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formation.phi.bis',
            'view_mode': 'kanban',
            'res_id': new_records,
        }

    # lang
    lang = fields.Selection([
        ('en_US', 'English'),
        ('fr_FR', 'French'),
        ('es_ES', 'Spanish'),
        # add more languages as needed
    ], string='Language', default='en_US')
    # -------------------------------------------------------------------------
    # STATE
    # -------------------------------------------------------------------------
    state = fields.Selection([
        ('1_new', '1. Nouveau'),
        ('2_in_progress', '2. En cours'),
        ('3_done', '3. Terminé'),
        ('4_cancel', '4. Annulée')
    ], 'Status', index=True, copy=False, default='1_new', tracking=True)

    def action_change_state(self):
        for rec in self:
            if rec.state == 'new':
                message_body = f"Letape change 1 - State: {rec.state}"
                recipients = self.message_post(body=message_body)
                return recipients
            elif rec.state == 'in progress':
                message_body = f"Letape change - State: {rec.state}"
                recipients = self.message_post(body=message_body)
                return recipients
            elif rec.state == 'done':
                message_body = f"Letape change - State: {rec.state}"
                recipients = self.message_post(body=message_body)
                return recipients
            elif rec.state == 'cancel':
                message_body = f"Letape change - State: {rec.state}"
                recipients = self.message_post(body=message_body)
                return recipients
            else:
                recipients = False

    # -------------------------------------------------------------------------
    # HEADER BUTTON ACTION
    # -------------------------------------------------------------------------
    def action_set_lost_formation(self):
        """ Lost semantic: probability = 0 or active = False """
        self.active = False
        self.formation_restore = self.active
        self.state = '4_cancel'

    def action_restore_formation(self):
        """ Lost semantic: probability = 0 or active = False """
        self.active = True
        self.formation_restore = self.active
        self.state = '1_new'

    def message_get_default_recipients(self):
        recipients = super(FormationsPhiBis, self).message_post()
        for record in self:
            if record.partner_id:
                recipients.append((record.partner_id.id, record.partner_id.name))
        return recipients

    def action_send_formation_plan(self):
        self.ensure_one()
        template = self.env.ref('Phidias_formation.session_template_email_support_formation', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        # Recherche du support de formation correspondant à la session
        support = self.env['plan.formations'].search([('formation_id', '=', self.id)], limit=1)

        # Créer un fichier temporaire pour stocker les données du PDF
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(support.documents)
            temp_file.close()
            attachment_path = temp_file.name

            print(temp_file.name,'here we goo')
            # Lire les données du fichier temporaire
            with open(attachment_path, 'rb') as file:
                attachment_data = file.read()

            # Décoder les données binaires en base64 en données binaires normales
            attachment_data_decoded = base64.b64decode(attachment_data)

            # Ajouter le fichier temporaire en tant que pièce jointe
            attachment = self.env['ir.attachment'].create({
                'name': support.documents_name,  # Nom du fichier joint
                'datas': attachment_data,
                'mimetype': 'application/pdf',  # Type MIME du fichier PDF
                #'res_model': 'formation.phi.bis',
                #'res_id': self.id,
            })

        ctx = dict(
            default_model='formation.phi.bis',
            default_res_id=self.id,
            default_partner_ids=[(self.partner_id.id)],
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

    survey_ids = fields.Many2many('survey.survey', help="Sent out surveys")

    def action_send_survey(self):
        self.ensure_one()
        # if an applicant does not already has associated partner_id create it
        template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
        local_context = dict(
            self.env.context,
            default_survey_id=self.survey_ids.id,
            default_use_template=bool(template),
            default_partner_ids=self.partner_id.ids,
            default_template_id=template and template.id or False,
            notif_layout='mail.mail_notification_light',
        )
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context,
        }

    # -------------------------------------------------------------------------
    # SMART BUTTON COMPUTE
    # -------------------------------------------------------------------------
    def _compute_factures_count(self):
        for rec in self:
            invoice_count = self.env['account.move'].search_count([('invoice_line_ids.name', '=', rec.name)])
            rec.invoice_count = invoice_count

    def _compute_plan_formation(self):
        for rec in self:
            invoice_count = self.env['plan.formations'].search_count([('formation_id', '=', rec.id)])
            rec.plan_formation_count = invoice_count

    def _compute_session_count(self):
        for rec in self:
            session_count = self.env['formations.sessions'].search_count([('formation_id', '=', rec.id)])
            rec.session_count = session_count

    def _compute_formation_folder_count(self):
        for rec in self:
            formation_folder_count = self.env['dossier.formations'].search_count([('formation_id', '=', rec.id)])
            rec.formation_folder_count = formation_folder_count

    def _compute_formation_support_count(self):
        for rec in self:
            formation_support_count = self.env['support.formations'].search_count([('formation_id', '=', rec.id)])
            rec.formation_support_count = formation_support_count

    def _compute_formation_debrief_count(self):
        for rec in self:
            formation_debrief_count = self.env['formations.debrief'].search_count([('formation_id', '=', rec.id)])
            rec.formation_debrief_count = formation_debrief_count

    def _compute_formation_reclamation_count(self):
        for rec in self:
            formation_reclamation_count = self.env['fiche.reclamation'].search_count([('formation_id', '=', rec.id)])
            rec.formation_reclamation_count = formation_reclamation_count

    def _compute_formation_application_count(self):
        for rec in self:
            formation_application_count = self.env['survey.user_input'].search_count([('partner_id', '=', rec.partner_id.id)])
            rec.formation_application_count = formation_application_count

    def _compute_formation_prerequisites_count(self):
        for rec in self:
            formation_prerequisites_count = self.env['formations.prerequis'].search_count([('formation_id', '=', rec.id)])
            rec.formation_prerequisites_count = formation_prerequisites_count

    def _compute_fiche_emargement_count(self):
        for rec in self:
            signature = self.env['sign.request'].search_count(
                [('request_item_ids.partner_id.formation_id', '=', rec.id)])
            rec.fiche_emargement_count = signature

    def _compute_access_count(self):
        for rec in self:
            access_count = self.env['formations.access'].search_count([('formation_id', '=', rec.id)])
            rec.access_count = access_count

    def _compute_formation_count(self):
        for rec in self:
            sondage = self.env['survey.user_input'].search_count(
                [('partner_id.formation_id', '=', rec.id),('formation_id','=', rec.id)])
            print('sondage :',sondage, rec.id)
            rec.eval_count = sondage

    def _compute_invoice_total(self):
        for rec in self:
            total_invoiced_count = self.env['sale.order'].search_count([('order_line.name', '=', rec.name)])
            rec.total_invoiced_count = total_invoiced_count

    def _compute_attendees_count(self):
        for rec in self:
            attendees_count = self.env['res.partner'].search_count([('formation_id', '=', rec.id)])
            rec.total_attendees_count = attendees_count

    # Smart button action ---------------------------------------------------
    def action_open_session(self):
        ctx = {
            'default_formation_id': self.id,
            'default_partner_id': self.partner_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.sessions',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Sessions',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_plan_formation(self):
        ctx = {
            'default_formation_id': self.id,
            'default_partner_id': self.partner_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'plan.formations',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Plan de formation',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_formation_support(self):
        ctx = {
            'default_formation_id': self.id,
            'default_partner_id': self.partner_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'support.formations',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Support de formation',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_evaluation(self):
        ctx = {
            'default_formation_id': self.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Evaluations',
            'domain': [('partner_id.formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_formation_folder(self):
        ctx = {
            'default_formation_id': self.id,
            'default_partner_id': self.partner_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dossier.formations',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Dossier de formation',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx
        }

    def action_open_factures(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Factures',
            'domain': [('invoice_line_ids.name', '=', self.name)],
        }

    #Smart button compte-rendu
    def action_open_formation_debrief(self):
        ctx = {
            'default_formation_id': self.id,
            'default_formation_date': self.formation_date_begin,
            'default_teacher': self.teacher.ids
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.debrief',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Compte-rendu',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_formation_reclamation(self):
        ctx = {
            'default_formation_id': self.id,
            'default_formation_date': self.formation_date_begin
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fiche.reclamation',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Fiche réclamation',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_formation_application(self):
        ctx = dict(self.env.context or {})
        ctx['default_formation_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Sondages',
            'domain': [('partner_id', '=', self.partner_id.id),('formation_id','=', self.id)],
        }

    def action_open_eval_acquis(self):
        ctx = dict(self.env.context or {})
        ctx['default_formation_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'eval.acquis',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Evaluation des acquis',
            'domain': [('formation_id', '=', self.id)],
        }

    def action_open_formation_prerequisites(self):
        ctx = {
            'default_formation_id': self.id,
            'default_formation_date': self.formation_date_begin,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.prerequis',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Pré-requis',
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_fiche_emargement(self):
        ctx = {
            'default_formation_id': self.id,
            'default_formation_date': self.formation_date_begin,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sign.request',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Fiche d'émargement",
            'domain': [('request_item_ids.partner_id.formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_access(self):
        ctx = dict(self.env.context or {})
        ctx['default_formation_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.access',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Lien d'accès",
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    def action_view_partner_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,graph,form',
            'target': 'current',
            'name': "Devis",
            'domain': [('order_line.name', '=', self.name)],
        }

    def action_view_attendees(self):
        ctx = {
            'default_formation_id': self.id,
            'default_parent_id': self.partner_id.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Participants",
            'domain': [('formation_id', '=', self.id)],
            'context': ctx,
        }

    # api functions ---------------------------------------------------
    @api.onchange('company_id','partner_id', 'location')
    def _compute_address_id(self):
        for record in self:
            if record.location == 'phidias':
                record.address_id = record.company_id.partner_id
            elif record.location == 'client':
                record.address_id = record.partner_id
            else:
                record.address_id = False
