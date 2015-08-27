# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from openerp import models, fields, api
from openerp.osv import fields as osv_fields
from openerp.tools.translate import _
from openerp.tools import ustr


class mail_message(orm.Model):
    _inherit = 'mail.message'

    def compute_partner(self, cr, uid, active_model='res.partner', model='mail.message', res_id=1, context=None):
        if context is None:
            context = {}
        target_ids = []
        current_obj = self.pool.get(model)
        cr.execute("SELECT name FROM ir_model_fields WHERE relation='" + active_model + "' and model = '" + model + "' and ttype not in ('many2many', 'one2many');")
        for name in cr.fetchall():
            current_data = current_obj.read(cr, uid, res_id, [str(name[0])],context=context)
            if current_data.get(str(name[0])):
                var = current_data.get(str(name[0]))
                if var:
                    target_ids.append(var[0])

        cr.execute("select name, model from ir_model_fields where relation='" + model + "' and ttype in ('many2many') and model = '" + active_model + "';")
        for field, model in cr.fetchall():
            field_data = self.pool.get(model) and self.pool.get(model)._columns.get(field, False) \
                            and (isinstance(self.pool.get(model)._columns[field], fields.many2many) \
                            or isinstance(self.pool.get(model)._columns[field], fields.function) \
                            and self.pool.get(model)._columns[field].store) \
                            and self.pool.get(model)._columns[field] \
                            or False
            if field_data:
                model_m2m, rel1, rel2 = field_data._sql_names(self.pool.get(model))
                requete = "SELECT "+rel1+" FROM "+ model_m2m+" WHERE "+ rel2+" ="+str(res_id)+";"
                cr.execute(requete)
                sec_target_ids = cr.fetchall()
                for sec_target_id in sec_target_ids:
                    target_ids.append(sec_target_id[0])
        return target_ids

    @api.depends('model')
    def _get_object_name(self):

        model_obj = self.env['ir.model']

        for message in self:

            model_ids = model_obj.search(
                [('model', '=', message.model)], limit=1)

            if not model_ids:
                continue

            message.object_name = model_ids[0].name

    @api.depends('res_id')
    def _get_body_txt(self):

        for message in self:
            if not message.res_id:
                continue

            record_data = self.env[message.model].browse(message.res_id)
            if message.model in ['crm.meeting', 'crm.lead']:
                message.body_txt = record_data.description
            else:
                message.body_txt = record_data.name

    # Fields

    partner_ids = fields.Many2many(
        'res.partner',
        'message_partner_rel', 'message_id', 'partner_id',
        'Partners')

    object_name = fields.Char(
        string='Object Name', size=64, store=True, compute=_get_object_name)

    body_txt = fields.Text(
        string='Content', store=True, compute=_get_body_txt)

    _order = 'date desc'

    def create(self, cr, uid, vals, context=None):
        if not vals.get('partner_ids'):
            target_ids = []
            if vals.get('res_id') and vals.get('model'):
                target_ids = self.compute_partner(
                    cr, uid,
                    active_model='res.partner',
                    model=vals.get('model'), res_id=vals.get('res_id'),
                    context=context)

            vals.update({'partner_ids': [(6, 0, target_ids)], })
        return super(mail_message, self).create(cr, uid, vals, context=context)


class res_partner(models.Model):
    _inherit = 'res.partner'

    # Fields

    history_ids = fields.Many2many(
        'mail.message',
        'message_partner_rel', 'partner_id', 'message_id',
        'Related Messages'
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
