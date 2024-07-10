
from odoo import _, api, fields, models
from odoo.tools import format_datetime

class FormationsRegistration(models.Model):
    _name = 'formations.attendees'
    _description = 'Formations Registration'

    # Référence
    reference = fields.Boolean(default=False)
    # formations
    formation_id = fields.Many2many('formation.phi.bis', string="Formation", required=True)
    active = fields.Boolean(default=True)
    # attendee
    name = fields.Char(
        string='Nom du participants', index=True,
        readonly=False, store=True, tracking=10)
    email = fields.Char(string='Email', compute='_compute_email', readonly=False, store=True, tracking=11)
    phone = fields.Char(string='Phone', compute='_compute_phone', readonly=False, store=True, tracking=12)
    mobile = fields.Char(string='Mobile', compute='_compute_mobile', readonly=False, store=True, tracking=13)
    # organization
    date_open = fields.Datetime(string="Date d'enregistrement", readonly=True, default=lambda self: fields.Datetime.now())  # weird crash is directly now
    company_id = fields.Many2one('res.company', 'company', required=True, index=True,
                                 default=lambda self: self.env.company, store=True, readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(
        'res.partner', string='Réserver par')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    # state
    state = fields.Selection([
        ('draft', 'Non-confirmé'),
        ('open', 'Confirmé'),
        ('cancel', 'Annulé'),
        ('needsAction', 'Needs Action'),
        ('tentative', 'Uncertain'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted')],
        string='Status', default='draft', readonly=True, copy=False, tracking=True)
    states = fields.Selection([
        ('needsAction', 'Needs Action'),
        ('tentative', 'Uncertain'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted')],
        string='Status', default='needsAction', readonly=True, copy=False, tracking=True)
    # smart button -------------------------------------------------------------
    eval_count = fields.Integer(string='Evaluation', compute='_compute_formation_count')
    eval_acquis_count = fields.Integer(string='Evaluation', compute='_compute_eval_acquis_count')
    fiche_emargement_count = fields.Integer(string="Fiche d'émargement",
                                                   compute='_compute_fiche_emargement_count')
    session_count = fields.Integer(string='Session', compute='_compute_session_count')

    def _compute_session_count(self):
        for rec in self:
            session_count = self.env['formations.sessions'].search_count([('attendees', '=', rec.id),
                                                                          ('formation_id','=',rec.formation_id.id)])
            rec.session_count = session_count

    def _compute_fiche_emargement_count(self):
        for rec in self:
            fiche_emargement_count = rec.env['formations.presence'].search_count(
                [('formation_id', '=', rec.formation_id.id),
                 ('attendees', '=', rec.id)])
            rec.fiche_emargement_count = fiche_emargement_count

    def _compute_formation_count(self):
        for participant in self:
            eval_count = self.env['formations.eval'].search_count([('formation_id', '=', participant.formation_id.id),
                                                                   ('attendees', '=', participant.id)])
            participant.eval_count = eval_count

    def _compute_eval_acquis_count(self):
        for rec in self:
            eval_acquis_count = self.env['eval.acquis'].search_count([('attendees', '=', rec.id)])
            rec.eval_acquis_count = eval_acquis_count
    # -------------------------------------------------------------------------

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Keep an explicit onchange on partner_id. Rationale : if user explicitly
        changes the partner in interface, he want to update the whole customer
        information. If partner_id is updated in code (e.g. updating your personal
        information after having registered in website_event_sale) fields with a
        value should not be reset as we don't know which one is the right one.

        In other words
          * computed fields based on partner_id should only update missing
            information. Indeed automated code cannot decide which information
            is more accurate;
          * interface should allow to update all customer related information
            at once. We consider event users really want to update all fields
            related to the partner;
        """
        for registration in self:
            if registration.partner_id:
                registration.update(registration._synchronize_partner_values(registration.partner_id))


    @api.depends('partner_id')
    def _compute_email(self):
        for registration in self:
            if not registration.email and registration.partner_id:
                registration.email = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['email']
                ).get('email') or False

    @api.depends('partner_id')
    def _compute_phone(self):
        for registration in self:
            if not registration.phone and registration.partner_id:
                registration.phone = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['phone']
                ).get('phone') or False

    @api.depends('partner_id')
    def _compute_mobile(self):
        for registration in self:
            if not registration.mobile and registration.partner_id:
                registration.mobile = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['mobile']
                ).get('mobile') or False

    def _synchronize_partner_values(self, partner, fnames=None):
        if fnames is None:
            fnames = ['name', 'email', 'phone', 'mobile']
        if partner:
            contact_id = partner.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                return dict((fname, contact[fname]) for fname in fnames if contact[fname])
        return {}



    # ------------------------------------------------------------
    # ACTIONS / BUSINESS
    # ------------------------------------------------------------

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({'state': 'open'})

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

    def action_open_fiche_emargement(self):
        ctx = {
            'default_attendees': self.ids,
            'default_formation_id': self.formation_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.presence',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': "Fiche d'émargement",
            'domain': [('attendees', '=', self.ids),('formation_id','=',self.formation_id.id)],
            'context': ctx,
        }

    def action_open_evaluation(self):
        ctx = {
            'default_attendees': self.ids,
            'default_formation_id': self.formation_id.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.eval',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Sessions',
            'domain': [('attendees', '=', self.ids),('formation_id','=',self.formation_id.id)],
            'context': ctx,
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
            'domain': [('attendees', '=', self.id)],
        }

    def action_open_session(self):
        ctx = {
            'default_formation_id': self.formation_id.id,
            'default_attendees': self.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'formations.sessions',
            'view_mode': 'tree,form',
            'target': 'current',
            'name': 'Sessions',
            'domain': [('formation_id', '=', self.formation_id.id),('attendees','=',self.id)],
            'context': ctx,
        }
    # ------------------------------------------------------------
    # TOOLS
    # ------------------------------------------------------------

    def get_date_range_str(self):
        self.ensure_one()
        today = fields.Datetime.now()
        event_date = self.event_begin_date
        diff = (event_date.date() - today.date())
        if diff.days <= 0:
            return _('today')
        elif diff.days == 1:
            return _('tomorrow')
        elif (diff.days < 7):
            return _('in %d days') % (diff.days, )
        elif (diff.days < 14):
            return _('next week')
        elif event_date.month == (today + relativedelta(months=+1)).month:
            return _('next month')
        else:
            return _('on %(date)s', date=format_datetime(self.env, self.event_begin_date, tz=self.event_id.date_tz, dt_format='medium'))

    def _get_registration_summary(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'partner_id': self.partner_id.id,
            'ticket_name': self.event_ticket_id.name or _('None'),
            'event_id': self.event_id.id,
            'event_display_name': self.event_id.display_name,
            'company_name': self.event_id.company_id and self.event_id.company_id.name or False,
        }

    def action_do_tentative(self):
        # Synchronize event after state change
        res = super(FormationsRegistration, self).do_tentative()
        self._microsoft_sync_event('tentativelyAccept')
        return res

    def action_do_accept(self):
        # Synchronize event after state change
        res = super(FormationsRegistration, self).do_accept()
        self._microsoft_sync_event('accept')
        return res

    def action_do_decline(self):
        # Synchronize event after state change
        res = super(FormationsRegistration, self).do_decline()
        self._microsoft_sync_event('decline')
        return res