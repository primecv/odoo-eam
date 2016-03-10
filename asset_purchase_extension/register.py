# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Prime Consulting (<http://prime.cv>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from datetime import date as dt
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class registration_request_hcv(osv.osv):
	_name = "registration.request.hcv"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Parts/Equipment Registration"

	def get_product_desc(self, cr, uid, ids, field_name, arg, context=None):
		desc = ''
		result={}
		for rec in self.browse(cr,uid,ids):
			result[rec.id] = ''
			if rec.type == 'part': 
				result[rec.id] = rec.part_id.name
			elif rec.type == 'equipment':
				result[rec.id] = rec.equipment_id.name
		return result

	_columns = {
		'name': fields.text('Reason', track_visibility='onchange'),
		'created': fields.boolean('Create'),
		'type': fields.selection([('part', 'Parts'), ('equipment', 'Equipment')], 'Product Type'),
		'date': fields.date('Request Date'),
		'part_id': fields.many2one('product.product', 'Part', domain="[('product_type','=','part')]", track_visibility='onchange'),
		'equipment_id': fields.many2one('asset.asset', 'Equipment', track_visibility='onchange'),
		'product': fields.function(get_product_desc, type="char", string="Product Description", store=True),
		'department_id': fields.many2one('res.users', 'Department'),	
		'user_id': fields.many2one('res.users', 'User', track_visibility='onchange'),
		'state': fields.selection([('draft', 'Draft'), ('submit', 'Waiting Approval'), ('approve', 'Approved'), ('reject', 'Rejected'), ('cancel', 'Cancelled')], 'State', track_visibility='onchange'),
	}

	_defaults = {
		'user_id': lambda obj, cr, uid, context: uid,
		'date': fields.datetime.now,
		'state': 'draft',
	}

	def create(self, cr, uid, vals, context=None):
		vals['created'] = True
		return super(registration_request_hcv, self).create(cr, uid, vals, context)

	def action_confirm(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'submit'})

	def action_approve(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'approve'})

	def action_reject(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'reject'})

	def action_cancel(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'cancel'})

	def action_reset(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'draft'})

