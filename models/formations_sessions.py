from odoo import fields, models, api
from datetime import date, datetime
from datetime import timedelta
from odoo.exceptions import UserError
import tempfile
import base64
import pytz



class FormationsSessions(models.Model):
    _name = "formations.sessions"
    _description = "create sessions for each formations"
    _inherit = "mail.thread"

    # session
    name = fields.Char(string="Nom de la session", translate=True, required=True)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True)
    session_date_begin = fields.Date(string='Date de début')
    session_date_end = fields.Date('Date de fin')
    date_open = fields.Datetime(string="Date d'enregistrement", readonly=True,
                                default=lambda self: fields.Datetime.now())  # weird crash is directly now
    teacher = fields.Many2many('hr.employee', string='Organisé par', required=True, index=True,
                                 default=lambda self: self.env['hr.employee'])
    completion_time_start = fields.Float('Durée de la session', help="The estimated completion time for this slide")
    completion_time_end = fields.Float('Durée de la session', help="The estimated completion time for this slide")



    # Référence
    reference_records = fields.Reference([('hr.employee', 'Référent')], string="Référence")
    # formations
    active = fields.Boolean(default=True, string="Toute la journée")
    formation_modules = fields.Many2one('formations.modules', string='Modules', required=True, index=True,
                                         default=lambda self: self.env['formations.modules'])
    session_restore = fields.Boolean('Restorer', default=True, tracking=True)
    # organization
    company_id = fields.Many2one('res.company', 'company', required=True, index=True,
                                 default=lambda self: self.env.company, store=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(
        'res.partner', string='Réserver par')
    address_id = fields.Many2one('res.partner',string="Lieu", compute='_compute_address_id')
    formation_url = fields.Char(string="Url")

    # timing
    start = fields.Datetime(
        'Start', required=True, tracking=True, default=fields.Date.today,
        help="Start date of an event, without time for full days events")
    stop = fields.Datetime(
        'Stop', required=True, tracking=True, default=lambda self: fields.Datetime.today() + timedelta(hours=1),
        compute='_compute_stop', readonly=False, store=True,
        help="Stop date of an event, without time for full days events")
    display_time_start = fields.Char('Event Time', compute='_compute_display_time')
    display_time_stop = fields.Char('Event Time', compute='_compute_display_time')
    allday = fields.Boolean('Toute la journée', default=False)
    start_date = fields.Date(
        'Start Date', store=True, tracking=True,
        compute='_compute_dates', inverse='_inverse_dates')
    stop_date = fields.Date(
        'End Date', store=True, tracking=True,
        compute='_compute_dates', inverse='_inverse_dates')
    duration = fields.Float('Durée', compute='_compute_duration', store=True, readonly=False)
    acces_link = fields.Many2one('formations.access',string="Lien d'acces", compute="_access_link")
    start_time = fields.Char('Start Time', compute='_compute_start_time')
    stop_time = fields.Char('Stop Time', compute='_compute_stop_time')


    @api.depends('formation_id')
    def _access_link(self):
        for session in self:
            if session.formation_id:
                access_records = self.env['formations.access'].search([('formation_id', '=', session.formation_id.id)])
                session.acces_link = access_records
            else:
                session.acces_link = False

    # -------------------------------------------------------------------------
    # SESSION TIME AND DAYTIME FUNCTION
    # -------------------------------------------------------------------------
    @api.depends('start')
    def _compute_start_time(self):
        for session in self:
            if session.start:
                session.start_time = session.start.strftime('%H:%M')
            else:
                session.start_time = 1

    @api.depends('stop')
    def _compute_stop_time(self):
        for session in self:
            if session.stop:
                session.stop_time = session.stop.strftime('%H:%M')
            else:
                session.stop_time = ''

    @api.depends('start', 'stop')
    def _compute_display_time(self):
        for record in self:
            tz = self.env.user.tz  # Récupérer le fuseau horaire de l'utilisateur connecté
            if record.start and record.stop and tz:
                start_localized = fields.Datetime.from_string(record.start).astimezone(pytz.timezone(tz))
                stop_localized = fields.Datetime.from_string(record.stop).astimezone(pytz.timezone(tz))
                record.display_time_start = start_localized.strftime('%H:%M')
                record.display_time_stop = stop_localized.strftime('%H:%M')
            else:
                record.display_time_start = ''
                record.display_time_stop = ''

    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        """ Adapt the value of start_date(time)/stop_date(time)
            according to start/stop fields and allday. Also, compute
            the duration for not allday meeting ; otherwise the
            duration is set to zero, since the meeting last all the day.
        """
        for meeting in self:
            if meeting.allday and meeting.start and meeting.stop:
                meeting.start_date = meeting.start.date()
                meeting.stop_date = meeting.stop.date()
            else:
                meeting.start_date = False
                meeting.stop_date = False

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)

    @api.depends('stop', 'start')
    def _compute_duration(self):
        for event in self:
            event.duration = self._get_duration(event.start, event.stop)

    @api.depends('start', 'duration')
    def _compute_stop(self):
        # stop and duration fields both depends on the start field.
        # But they also depends on each other.
        # When start is updated, we want to update the stop datetime based on
        # the *current* duration. In other words, we want: change start => keep the duration fixed and
        # recompute stop accordingly.
        # However, while computing stop, duration is marked to be recomputed. Calling `event.duration` would trigger
        # its recomputation. To avoid this we manually mark the field as computed.
        duration_field = self._fields['duration']
        self.env.remove_to_compute(duration_field, self)
        for event in self:
            # Round the duration (in hours) to the minute to avoid weird situations where the event
            # stops at 4:19:59, later displayed as 4:19.
            event.stop = event.start and event.start + timedelta(minutes=round((event.duration or 1.0) * 60))
            if event.allday:
                event.stop -= timedelta(seconds=1)

    def _inverse_dates(self):
        """ This method is used to set the start and stop values of all day events.
            The calendar view needs date_start and date_stop values to display correctly the allday events across
            several days. As the user edit the {start,stop}_date fields when allday is true,
            this inverse method is needed to update the  start/stop value and have a relevant calendar view.
        """
        for meeting in self:
            if meeting.allday:

                # Convention break:
                # stop and start are NOT in UTC in allday event
                # in this case, they actually represent a date
                # because fullcalendar just drops times for full day events.
                # i.e. Christmas is on 25/12 for everyone
                # even if people don't celebrate it simultaneously
                enddate = fields.Datetime.from_string(meeting.stop_date)
                enddate = enddate.replace(hour=18)

                startdate = fields.Datetime.from_string(meeting.start_date)
                startdate = startdate.replace(hour=8)  # Set 8 AM

                meeting.write({
                    'start': startdate.replace(tzinfo=None),
                    'stop': enddate.replace(tzinfo=None)
                })

    # lang
    lang = fields.Selection([
        ('en_US', 'English'),
        ('fr_FR', 'French'),
        ('es_ES', 'Spanish'),
        # add more languages as needed
    ], string='Language', default='en_US')
    # state
    state = fields.Selection([
        ('draft', 'Non-confirmée'),
        ('open', 'Confirmé'),
        ('end','Terminée'),
        ('cancel', 'Annulé'),
        ('reported','Reporté')],
        string='Status', default='draft', readonly=False, copy=False, tracking=True)

    # smart button -------------------------------------------------------------
    eval_count = fields.Integer(string='Evaluation(s)', compute='_compute_eval_count')
    attendees = fields.Many2many('res.partner',
                                 string="Participant(s)",
                                 required=True,
                                 computed="_select_confirm_attendees")
    attendees2 = fields.Many2many('res.partner', string="Participant(s)", compute="_add_attendees")
    email = fields.Char(string='Email', compute='_compute_email')
    list_name = fields.Char(string='Email', compute='_compute_name_attendees')
    fiche_emargement_count = fields.Integer(string="Fiche(s) d'émargement",
                                            compute='_compute_fiche_emargement_count')
    sondage_count = fields.Integer(string="Sondage(s)", compute="_compute_sondage_count")
    support_formation_count = fields.Integer(string="Support(s)", compute="_compute_support_formation_count")
    signature_count = fields.Integer(string="Signature(s)", compute="_compute_signature_count")
    formation_debrief_count = fields.Integer(string='Compte-rendu', compute='_compute_formation_debrief_count')

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

    @api.onchange('attendees')
    def _add_attendees(self):
        for session in self:
            if session.attendees:
                session.attendees2 = session.attendees

    # session attendees invitation
    survey_ids = fields.Many2many('survey.survey', help="Sent out surveys")
    def action_send_survey(self):
        self.ensure_one()
        # if an applicant does not already has associated partner_id create it
        template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
        local_context = dict(
            self.env.context,
            default_survey_id=self.survey_ids.id,
            default_use_template=bool(template),
            default_session_id= self.id,
            default_partner_ids=self.attendees.ids,
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



    @api.depends('attendees')
    def _compute_email(self):
        for session in self:
            email_list = [attendee.email for attendee in session.attendees]
            session.email = ", ".join(email_list) if email_list else False

    @api.depends('attendees')
    def _compute_name_attendees(self):
        for session in self:
            list_name = [attendee.name for attendee in session.attendees]
            session.list_name = list_name

    # message post
    def message_get_default_recipients(self):
        recipients = super(FormationsSessions, self).message_post()
        for record in self:
            if record.partner_id:
                recipients.append((record.partner_id.id, record.partner_id.name))
        return recipients

    # -------------------------------------------------------------------------
    # EMAIL
    # -------------------------------------------------------------------------
    def action_sendmail(self):
        email = self.env.user.email
        if email:
            for meeting in self:
                meeting.attendee_ids._send_mail_to_attendees(
                    self.env.ref('calendar.calendar_template_meeting_invitation', raise_if_not_found=False)
                )
        return True

    def action_open_composer(self):
        if not self.attendees:
            raise UserError(_("There are no attendees on these events"))
        template_id = self.env['ir.model.data']._xmlid_to_res_id('calendar.calendar_template_meeting_update', raise_if_not_found=False)
        # The mail is sent with datetime corresponding to the sending user TZ
        composition_mode = self.env.context.get('composition_mode', 'comment')
        compose_ctx = dict(
            default_composition_mode=composition_mode,
            default_model='formations.sessions',
            default_res_ids=self.ids,
            default_use_template=bool(template_id),
            default_template_id=template_id,
            default_partner_ids=self.partner_ids.ids,
            mail_tz=self.env.user.tz,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contact Attendees'),
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': compose_ctx,
        }

    # -------------------------------------------------------------------------
    # HEADER BUTTON ACTION
    # -------------------------------------------------------------------------
    def action_set_lost_session(self):
        """ Lost semantic: probability = 0 or active = False """
        self.active = False
        self.session_restore = self.active
        self.state = 'cancel'

    def action_end_session(self):
        self.write({'state': 'end'})

    def action_set_postponed_session(self):
        """ Lost semantic: probability = 0 or active = False """
        self.active = False
        self.session_restore = self.active
        self.state = 'reported'

    def action_restore_session(self):
        """ Lost semantic: probability = 0 or active = False """
        self.active = True
        self.session_restore = self.active
        self.state = 'draft'

    # -------------------------------------------------------------------------
    # SMART BUTTON COMPUTE
    # -------------------------------------------------------------------------
    def _compute_formation_debrief_count(self):
        for rec in self:
            formation_debrief_count = self.env['formations.debrief'].search_count([
                ('formation_id', '=', rec.formation_id.id),
                ('session_id', '=', rec.id)
            ])
            rec.formation_debrief_count = formation_debrief_count

    def _compute_eval_count(self):
        for session in self:
            eval_count = self.env['formations.eval'].search_count([('formation_id', '=', session.formation_id.id),
                                                                   ('session_id','=', session.id)])
            session.eval_count = eval_count

    def _compute_fiche_emargement_count(self):
        for rec in self:
            fiche_emargement_count = rec.env['formations.presence'].search_count([('formation_id', '=', rec.formation_id.id),
                                                                                  ('session_id','=', rec.id)])
            rec.fiche_emargement_count = fiche_emargement_count

    def _compute_signature_count(self):
        for session in self:
            signature = self.env['sign.request'].search_count(
                [('formation_id', '=', session.formation_id.id),
                 ('session_id', '=', session.id)])
            session.signature_count = signature

    def _compute_sondage_count(self):
        for session in self:
            sondage = self.env['survey.user_input'].search_count(
                [('formation_id', '=', session.formation_id.id),
                 ('session_id', '=', session.id)])
            session.sondage_count = sondage

    def _compute_support_formation_count(self):
        for session in self:
            support = self.env['support.formations'].search_count(
                [('formation_id', '=', session.formation_id.id), ('session_id', '=', session.id)])
            session.support_formation_count = support
    @api.depends('company_id', 'partner_id', 'address_id')
    def _compute_address_id(self):
        for record in self:
            if record.formation_id:
                for formation in record.formation_id:
                    if formation.location == 'phidias':
                        record.address_id = record.company_id.partner_id
                        break
                    if formation.location == 'url':
                        record.address_id = False
                        record.formation_url = formation.formation_url
                        break
                else:
                    record.address_id = formation.partner_id

    @api.onchange('formation_id')
    def _select_confirm_attendees(self):
        for session in self:
            if session.formation_id:
                return {'domain': {'attendees': [('formation_id','=', session.formation_id.id)]}}
    # -------------------------------------------------------------------------

    # ------------------------------------------------------------
    # ACTIONS / BUSINESS
    # ------------------------------------------------------------

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({'state': 'open'})

    def confirm_records(self, record_ids):
        self.env['formations.sessions'].browse(record_ids).write({'state': 'open'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_send_badge_email(self):
        """ Open a window to compose an email, with the template - 'event_badge'
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('Phidias_formation.session_template_email', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='formations.sessions',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id,
            default_composition_mode='comment',
            custom_layout="mail.mail_notification_light",
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

    import tempfile
    import os

    def action_send_formation_access(self):
        """ Open a window to compose an email, with the template - 'event_badge'
                    message loaded by default
                """
        self.ensure_one()
        template = self.env.ref('Phidias_formation.session_template_acces_link', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='formations.sessions',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id,
            default_composition_mode='comment',
            custom_layout="mail.mail_notification_light",
        )
        return {
            'name': ('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx
        }

    def action_send_formation_support(self):
        self.ensure_one()
        template = self.env.ref('Phidias_formation.session_template_email_support_formation', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        # Recherche du support de formation correspondant à la session
        support = self.env['support.formations'].search([('formation_id', '=', self.formation_id.id),('session_id', '=', self.id)], limit=1)

        # Créer un fichier temporaire pour stocker les données du PDF
        # Créer un fichier temporaire pour stocker les données du PDF
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(support.documents)
            temp_file.close()
            attachment_path = temp_file.name

            # Lire les données du fichier temporaire
            with open(attachment_path, 'rb') as file:
                attachment_data = file.read()

            # Ajouter le fichier temporaire en tant que pièce jointe
            attachment = self.env['ir.attachment'].create({
                'name': support.documents_name,  # Nom du fichier joint
                'datas': base64.b64encode(attachment_data),
                'mimetype': 'application/pdf',  # Type MIME du fichier PDF
                'res_model': 'formations.sessions',
                'res_id': self.id,
            })

        ctx = dict(
            default_model='formations.sessions',
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

    def action_open_fiche_emargement(self):
        ctx = {
            'default_session_id': self.id,
            'default_attendees' : self.attendees.ids,
            'default_formation_id': self.formation_id.id,
            'default_formation_date': self.formation_id.formation_date_begin,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.presence',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Fiche d'émargement",
            'domain': [('formation_id', '=', self.formation_id.id),('session_id','=', self.id)],
            'context': ctx,
        }

    def action_open_evaluation(self):
        ctx = {
            'default_session_id': self.id,
            'default_attendees': self.attendees.ids,
            'default_formation_id': self.formation_id.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.eval',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Evaluations',
            'domain': [('formation_id', '=', self.formation_id.id),('session_id','=', self.id)],
            'context': ctx,
        }
    createdContact = fields.Boolean('active')

    def action_open_sondage(self):
        self.createdContact = True
        partner_count = len(self.attendees)
        ctx = {
            'default_session_id': self.id,
            'default_formation_id': self.formation_id.id,
            'default_createdContact': self.createdContact
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Evaluations',
            'domain': [('formation_id', '=', self.formation_id.id),
                 ('session_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_signature(self):
        ctx = {
            'default_session_id': self.id,
            'default_formation_id': self.formation_id.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sign.request',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Signature',
            'domain': [('formation_id', '=', self.formation_id.id),
                 ('session_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_support_formation(self):
        ctx = {
            'default_formation_id': self.formation_id.id,
            'default_partner_id': self.partner_id.id,
            'default_session_id': self.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'support.formations',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Support de formation',
            'domain': [('formation_id', '=', self.formation_id.id),('session_id', '=', self.id)],
            'context': ctx,
        }

    def action_open_formation_debrief(self):
        ctx = {
            'default_formation_id': self.formation_id.id,
            'default_session_id': self.id,
            'default_formation_date': self.formation_id.formation_date_begin,
            'default_teacher': self.teacher.ids
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.debrief',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Compte-rendu',
            'domain': [('formation_id', '=', self.formation_id.id),('session_id','=',self.id)],
            'context': ctx,
        }
#    def get_date_range_str(self):
#        self.ensure_one()
#        today = fields.Datetime.now()
#        event_date = self.event_begin_date
#        diff = (event_date.date() - today.date())
#        if diff.days <= 0:
#            return _('today')
#        elif diff.days == 1:
#            return _('tomorrow')
#        elif (diff.days < 7):
#            return _('in %d days') % (diff.days, )
#        elif (diff.days < 14):
#            return _('next week')
#        elif event_date.month == (today + relativedelta(months=+1)).month:
#            return _('next month')
#        else:
#            return _('on %(date)s', date=format_datetime(self.env, self.event_begin_date, tz=self.event_id.date_tz, dt_format='medium'))

#    def _get_registration_summary(self):
#        self.ensure_one()
#        return {
#            'id': self.id,
#            'name': self.name,
#            'partner_id': self.partner_id.id,
#            'ticket_name': self.event_ticket_id.name or _('None'),
#            'event_id': self.event_id.id,
#            'event_display_name': self.event_id.display_name,
#            'company_name': self.event_id.company_id and self.event_id.company_id.name or False,
#        }