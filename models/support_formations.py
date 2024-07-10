from odoo import fields, models, api
from datetime import date, datetime
from lxml import etree

class SupportFormations(models.Model):
    _name = 'support.formations'
    _description = 'store all the formations folders '

    name = fields.Char(string="Nom du support de formation", translate=True, required=True)
    company_id = fields.Many2one('res.company', 'company', required=True, index=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner',string="Client",trakcking=True, readonly=False)
    formation_id = fields.Many2one('formation.phi.bis', string="Formation", required=True, readonly=False)
    session_id = fields.Many2one('formations.sessions', string="Session", required=True, readonly=False)
    slide_type = fields.Selection([
        ('document', 'Document'),
        ('url', "Url")],
        string='Type', required=True,
        index=True,
        default='document')
    formation_url = fields.Char(string="Url")
    documents = fields.Binary(string='Fichier')
    documents_name = fields.Char(string='Nom du fichier')

    @api.model
    def fields_view_get(self, view_id='view_suport_formations_form', view_type='form', toolbar=False, submenu=False):
        res = super(SupportFormations, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                   submenu=submenu)

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('readonly', '1')
            res['arch'] = etree.tostring(doc)
        return res
