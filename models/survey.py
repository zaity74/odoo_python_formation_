from odoo import fields, api, tools
from odoo import models
from odoo.tools.translate import _
from odoo.exceptions import UserError
import re
import logging

_logger = logging.getLogger(__name__)


emails_split = re.compile(r"[;,\n\r]+")
class SurveyPhidias(models.TransientModel):
    _inherit = 'survey.invite'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation")
    session_id = fields.Many2one('formations.sessions', string="Session")
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')

    @api.onchange('formation_id', 'session_id')
    def _select_confirm_sessions(self):
        for session in self:
            if session.formation_id:
                return {
                    'domain': {
                        'session_id': [('formation_id', '=', session.formation_id.id)],
                        'partner_ids': [('formation_id', '=', session.formation_id.id),
                                        ('id', 'in', session.session_id.attendees.ids)],
                    }
                }


class SurveyUserInputPhidias(models.Model):
    _inherit = 'survey.user_input'

    formation_id = fields.Many2one('formation.phi.bis', string="Formation", compute="_change_formations")
    session_id = fields.Many2one('formations.sessions', string="Session")
    name_partner = fields.Char('Email', compute="_change_name")

    @api.depends('partner_id')
    def _change_name(self):
        for session in self:
            list_name = [attendee.attendees.name for attendee in session.session_id]
            session.name_partner = list_name



    @api.depends('partner_id','formation_id','session_id')
    def _change_formations(self):
        for session in self:
            if session.partner_id:
                session.formation_id = session.partner_id.formation_id.id
            else:
                session.formation_id = False



class SurveySurveyInheritPhidias(models.Model):
    _inherit = 'survey.survey'

    session_id = fields.Many2one('formations.sessions', string="Session")