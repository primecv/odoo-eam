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
			elif rec.type == 'asset':
				result[rec.id] = rec.asset_id.name
			elif rec.type == 'accessory':
				result[rec.id] = rec.accessory_id.name
		return result

	_columns = {
		'name': fields.char('Name'),
		'reason': fields.text('Reason', track_visibility='onchange'),
		'created': fields.boolean('Create'),
		'type': fields.selection([('asset','Asset'),('accessory','Accessory'),('part', 'Parts')], 'Request Type'),
		'date': fields.date('Request Date'),
		'part_id': fields.many2one('product.product', 'Part', domain="[('product_type','=','part')]", track_visibility='onchange'),
		#'equipment_id': fields.many2one('asset.asset', 'Equipment', track_visibility='onchange'),
		'accessory_id': fields.many2one('asset.asset', 'Accessory', domain="[('is_accessory','=',True)]"),
		'asset_id': fields.many2one('asset.asset', 'Asset', domain="[('is_accessory','=',False)]"),
		'product': fields.function(get_product_desc, type="char", string="Product Description", store=True),
		'quantity': fields.integer('Quantity'),
		'department_id': fields.many2one('res.users', 'Department'),	
		'user_id': fields.many2one('res.users', 'User', track_visibility='onchange'),
		'state': fields.selection([('draft', 'Draft'), ('submit', 'Waiting Approval'), ('approve', 'Approved'), ('reject', 'Rejected'), ('cancel', 'Cancelled'),('transfer','Transfer Initiated')], 'State', track_visibility='onchange'),
		'move_id': fields.many2one('stock.move', 'Move'),
		'answer': fields.text('Answer', track_visibility='onchange'),
	}

	_defaults = {
		'user_id': lambda obj, cr, uid, context: uid,
		'date': fields.datetime.now,
		'state': 'draft',
		'quantity': 1,
	}

	def create(self, cr, uid, vals, context=None):
		vals['created'] = True
		name = self.pool.get('ir.sequence').get(cr, uid, 'registration.request') or '/'
		vals['name'] = name
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
		return self.write(cr, uid, ids, {'state': 'draft', 'answer': ''})

	def part_transfer(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
			if location_id:
				location_id = location_id[1]
			else:
				raise osv.except_osv(('Error!'), ('Source Location not found.\nPlease contact your administrator.'))
			picking_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'picking_type_internal')
			if picking_type_id:
				picking_type_id = picking_type_id[1]
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'asset_purchase_extension', 'view_stock_move_form_hcv')
			view_id = view_ref and view_ref[1] or False
			ctx = {
					'default_picking_type_id': picking_type_id,
					'default_invoice_state': 'none',
					'default_product_id': rec.part_id.id,
					'default_product_uom_qty': rec.quantity,
					'default_product_uos_qty': rec.quantity,
					'default_name': 'INT:HCV',
					'default_location_id': location_id,
					'default_state': 'draft',
					'default_product_uom': rec.part_id.product_tmpl_id.uom_id.id,
					'hcv': True,
					'register_id': rec.id,
					}
			return {
				'name': 'Parts Transfer',
				'type': 'ir.actions.act_window',
				'res_model': 'stock.move',
				'view_type': 'form',
				'view_mode': 'form',
				'view_id': view_id,
				'target': 'current',
				'context': ctx
			}

	def open_po(self, cr, uid, ids, context=None):
		return True

	def open_move(self, cr, uid, ids, context=None):
		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'asset_purchase_extension', 'view_stock_move_form_hcv')
		view_id = view_ref and view_ref[1] or False
		for rec in self.browse(cr, uid, ids):
			return {
				'name': 'Move',
				'type': 'ir.actions.act_window',
				'res_model': 'stock.move',
				'view_type': 'form',
				'view_mode': 'form',
				'view_id': view_id,
				'res_id': rec.move_id.id,
				'target': 'current',
			}


