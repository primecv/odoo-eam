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

class rfq_hcv(osv.osv):
	_name = "rfq.hcv"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "RFQ for HCV"

	_columns = {
		'name': fields.char('RFQ No.'),
		'type': fields.selection([('asset','Asset'), ('accessory', 'Accessory'), ('parts', 'Parts')], 'RFQ for', track_visibility='onchange'),
		'created': fields.boolean('Create'),
		'supplier_line': fields.one2many('rfq.suppliers.hcv', 'rfq_id', 'Suppliers'),
		'product_id': fields.many2one('product.product', 'Part', domain="[('product_type','=','part')]"),
		'accessory_id': fields.many2one('asset.asset', 'Accessory', domain="[('is_accessory','=',True)]"),
		'asset_id': fields.many2one('asset.asset', 'Asset', domain="[('is_accessory','=',False)]"),
		'product_qty': fields.integer('Quantity'),
		'taxes_id': fields.many2many('account.tax', 'rfq_hcv_taxes', 'rfq_id', 'tax_id', 'Taxes'),
		'state': fields.selection([
									('draft', 'Draft'),
									('rfq', 'RFQ'),
									('bid', 'Bid Received'),
									('confirmed', 'Waiting Approval'),
									('approved', 'Purchase Confirmed'),
									('except_picking', 'Shipping Exception'),
									('except_invoice', 'Invoice Exception'),
									('done', 'Done'),
									('cancel', 'Cancelled')], 'State', track_visibility='onchange'),
		'note': fields.text('Notes'),
		'date_order':fields.datetime('Order Date'),
		'picking_type_id': fields.many2one('stock.picking.type', 'Deliver To', help="This will determine picking type of incoming shipment"),

        'minimum_planned_date': fields.date('Expected Date'),
        'location_id': fields.many2one('stock.location', 'Destination', domain=[('usage','<>','view'),('usage','<>','asset')]),
		'update_check': fields.boolean('Document Update'),
		'po_id': fields.many2one('purchase.order', 'Purchase Order'),
		'shipped': fields.related('po_id', 'shipped', type='boolean', string='Shipped', store=False),
        'invoice_method': fields.selection([('manual','Based on Purchase Order lines'),('order','Based on generated draft invoice'),('picking','Based on incoming shipments')], 'Invoicing Control'),
		'create_asset': fields.boolean('Create Asset?'),
		'create_accessory': fields.boolean('Create Accessory?'),
		'new_asset_id': fields.many2one('asset.asset', 'Related Asset'),
		'new_accessory_id': fields.many2one('asset.asset', 'Related Accessory'),
	}

	def _get_picking_in(self, cr, uid, context=None):
		obj_data = self.pool.get('ir.model.data')
		type_obj = self.pool.get('stock.picking.type')
		user_obj = self.pool.get('res.users')
		company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
		types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], context=context)
		if not types:
			types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
			if not types:
				raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))
		return types[0]


	_defaults = {
		'state': 'draft',
        'date_order': fields.datetime.now,
        'picking_type_id': _get_picking_in,
		'product_qty': 1,
		'invoice_method': 'manual',
	}

	def create(self, cr, uid, vals, context=None):
		name = self.pool.get('ir.sequence').get(cr, uid, 'rfq.hcv') or '/'
		vals['name'] = name
		vals['created'] = True
		return super(rfq_hcv, self).create(cr, uid, vals, context)

	def write(self, cr, uid, ids, vals, context=None):
		for rec in self.browse(cr, uid, ids):
			if 'state' in vals and rec.state in ('draft', 'rfq'):
				vals['update_check'] = False
			elif 'state' not in vals and rec.state in ('draft', 'rfq'):
				vals['update_check'] = False
		return super(rfq_hcv, self).write(cr, uid, ids, vals, context)

	def confirm_rfq(self, cr, uid, ids, context=None):
		self.check_suppliers(cr, uid, ids)

		self.validate_po(cr, uid, ids)

		suppliers = []
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				suppliers.append(line.supplier_id.id)
		return {
			'type': 'ir.actions.act_window',
			'name': 'Confirm RFQ',
			'res_model': 'rfq.hcv.print.confirm',
			'view_type': 'form',
			'view_mode': 'form',	
			'target': 'new',
			'context': {'rfq_id': ids, 'default_supplier_ids': [[6,0, suppliers]], 'default_confirm_rfq':True }
		}

	def bid_received(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				if line.po_id:
					self.pool.get('purchase.order').signal_workflow(cr, uid, [line.po_id.id], 'bid_received')
		return self.write(cr, uid, ids, {'state': 'bid'})

	def view_picking(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.po_id:
				return self.pool.get('purchase.order').view_picking(cr, uid, [rec.po_id.id], context)

	def action_cancel(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				if line.po_id:
					self.pool.get('purchase.order').action_cancel(cr, uid, [line.po_id.id])
		return self.write(cr, uid, ids, {'state':'cancel'})

	def action_cancel_draft(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				if line.po_id:
					self.pool.get('purchase.order').action_cancel_draft(cr, uid, [line.po_id.id])
		return self.write(cr, uid, ids, {'state': 'draft'})

	def print_rfq(self, cr, uid, ids, context=None):
		self.check_suppliers(cr, uid, ids)

		self.validate_po(cr, uid, ids)
		
		suppliers = []
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				suppliers.append(line.supplier_id.id)
		vals = {
			'type': 'ir.actions.act_window',
			'name': 'Print RFQ',
			'res_model': 'rfq.hcv.print.confirm',
			'view_type': 'form',
			'view_mode': 'form',	
			'target': 'new',
			'context': {'rfq_id': ids, 'default_supplier_ids': [[6,0, suppliers]], 'default_print_rfq':True}
		}		
		return vals

	def print_po(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				if line.state == 'done':
					return self.pool['report'].get_action(cr, uid, [line.po_id.id], 'purchase.report_purchaseorder')

	def send_rfq(self, cr, uid, ids, context=None):
		self.check_suppliers(cr, uid, ids)

		self.validate_po(cr, uid, ids)

		#send RFQ to each supplier :
		for rec in self.browse(cr, uid, ids):
			for line in rec.supplier_line:
				if not context:
					context = {'partner_id': line.supplier_id.id}
				else:
					context['partner_id'] = line.supplier_id.id
				ctx = {}
				ir_model_data = self.pool.get('ir.model.data')
				try:
					template_id = ir_model_data.get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase')[1]
				except ValueError:
					template_id = False
				try:
					compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
				except ValueError:
					compose_form_id = False 
				ctx = dict(ctx)
				ctx.update({
					'default_model': 'purchase.order',
					'default_res_id': line.po_id.id,
					'default_use_template': bool(template_id),
					'default_template_id': template_id,
					'default_composition_mode': 'comment',
				})
				mail_id = self.pool.get('mail.compose.message').create(cr, uid, {'name':line.supplier_id.id}, context=ctx)
				self.pool.get('mail.compose.message').send_mail(cr, uid, [mail_id])

		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'rfq'})

		return True

	def check_suppliers(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			suppliers = []
			if not rec.supplier_line:
				raise osv.except_osv(('Input Error!'), ('Please add Supplier(s) in RFQ.'))
			for supplier in rec.supplier_line:
				suppliers.append(supplier.supplier_id.id)
		suppliers2 = list(set(suppliers))
		if len(suppliers) != len(suppliers2):
			raise osv.except_osv(('Input Error!'), ('You cannot add same supplier more than once in RFQ.'))
		return True

	def validate_po(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):		
			#delete old purchase orders :
			if rec.update_check is False:
				for line in rec.supplier_line:
					if line.po_id:
						self.pool.get('purchase.order').action_cancel(cr, uid, [line.po_id.id])
						self.pool.get('purchase.order').unlink(cr, uid, [line.po_id.id])
			#create new updated purchase orders:
			product = rec.product_id.id
			for line in rec.supplier_line:
				if not line.po_id:	
					pricelist_id = line.supplier_id.property_product_pricelist_purchase.id
					vals = {
						'name': rec.name,	
						'partner_id': line.supplier_id.id,
						'date_order': rec.date_order,
						'location_id': rec.location_id.id,
						'pricelist_id': pricelist_id,
						'bid_date': line.bid_date,
						'bid_validity': line.bid_expiry_date,
						'picking_type_id': rec.picking_type_id.id,
						'rfq_hcv_id': rec.id,
						'invoice_method': rec.invoice_method,
					}

					taxes = []
					t = [taxes.append(tax.id) for tax in rec.taxes_id]
					if rec.type == 'asset': 
						desc = rec.asset_id.name
						uom = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
						uom_id = uom and uom[1] or False
						if not uom:
							uom_id = self.pool.get('product.uom').search(cr, uid, [('id','>',0)])[0]
					if rec.type == 'parts': 
						desc = rec.product_id.name
						uom_id = rec.product_id.product_tmpl_id.uom_po_id and rec.product_id.product_tmpl_id.uom_po_id.id or \
								rec.product_id.product_tmpl_id.uom_id.id
					if rec.type == 'accessory': 
						desc = rec.accessory_id.name
						uom = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
						uom_id = uom and uom[1] or False
						if not uom:
							uom_id = self.pool.get('product.uom').search(cr, uid, [('id','>',0)])[0]
					line_data = [[0, False, {'name': desc,
											'product_id': rec.product_id and rec.product_id.id or False,
											'product_qty': rec.product_qty,
											'product_uom': uom_id,
											'price_unit': line.price_unit,
											'date_planned': line.bid_date or dt.today(),
											'taxes_id': [[6, 0, taxes]],
											'rfq_line_id': line.id,
											}]]
					vals.update({'order_line': line_data})
					po_id = self.pool.get('purchase.order').create(cr, uid, vals, context)
					#update po reference in suppliers line :
					self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'po_id': po_id})
		return self.write(cr, uid, ids, {'update_check': True})

	def open_asset(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'asset_stock', 'assets_form_view_stock')
			view_id = view_ref and view_ref[1] or False,
			if rec.create_asset:
				return {
					'type': 'ir.actions.act_window',
					'res_model': 'asset.asset',
					'view_type': 'form',
					'view_mode': 'form',
					'view_id': view_id or False,
					'res_id': False,
					'context': {'po_asset': True, 'rfq_id': rec.id, 'default_is_accessory':False},
					'target': 'current'
				}				
			else:
				return {
					'type': 'ir.actions.act_window',
					'res_model': 'asset.asset',
					'view_type': 'form',
					'view_mode': 'form',
					'res_id': int(rec.new_asset_id.id),
					'context': {'po_asset': True},
					'target': 'current'
				}

	def open_accessory(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'asset_extension', 'asset_accessories_form_view')
			view_id = view_ref and view_ref[1] or False,
			if rec.create_accessory:
				return {
					'type': 'ir.actions.act_window',
					'res_model': 'asset.asset',
					'view_type': 'form',
					'view_mode': 'form',
					'view_id': view_id or False,
					'res_id': False,
					'context': {'po_asset': True, 'rfq_id': rec.id, 'default_is_accessory': True},
					'target': 'current'
				}				
			else:
				return {
					'type': 'ir.actions.act_window',
					'res_model': 'asset.asset',
					'view_type': 'form',
					'view_mode': 'form',
					'res_id': int(rec.new_accessory_id.id),
					'context': {'po_asset': True, 'rfq_id': rec.id},
					'target': 'current'
				}

	def onchange_picking_type_id(self, cr, uid, ids, picking_type_id, context=None):
		value = {}
		if picking_type_id:
			picktype = self.pool.get("stock.picking.type").browse(cr, uid, picking_type_id, context=context)
			if picktype.default_location_dest_id:
				value.update({'location_id': picktype.default_location_dest_id.id, 'related_usage': picktype.default_location_dest_id.usage})
			value.update({'related_location_id': picktype.default_location_dest_id.id})
		return {'value': value}

class rfq_suppliers_hcv(osv.osv):
	_name = "rfq.suppliers.hcv"

	_description = "RFQ Suppliers"

	_rec_name = 'supplier_id'

	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		for line in self.browse(cr, uid, ids, context=context):
			if not line.rfq_id:
				return res

			taxes = tax_obj.compute_all(cr, uid, line.rfq_id.taxes_id, line.price_unit, line.rfq_id.product_qty, line.rfq_id.product_id, line.supplier_id)
			res[line.id] = 0.0
			if taxes['total_included']:
				res[line.id] = float(taxes['total_included'])
		return res
	
	_columns = {
		'rfq_id': fields.many2one('rfq.hcv', 'RFQ'),
		'po_id': fields.many2one('purchase.order', 'Purchase Order'),
		'supplier_id': fields.many2one('res.partner', 'Supplier', domain="[('supplier','=',True)]"),
		'product_id': fields.related('rfq_id', 'product_id', type='many2one', relation='product.product', string='Product'),
		'price_unit': fields.float('Unit Price'),
		'bid_date': fields.date('Bid Received On'),
		'bid_expiry_date': fields.date('Bid Expiry Date'),
		'hours_of_operation': fields.float('Hours of Operation'),
		'planned_amount': fields.float('Amounts of Planned Tests'),
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
		'state': fields.selection([('done','Done'),('cancel','Cancel')], 'State'),
	}

	def onchange_supplier_id(self, cr, uid, ids, ptype=False, asset_id=False, part_id=False, accessory_id=False, context=None):
		if ptype:
			if ptype == 'accessory' and not accessory_id:
				raise osv.except_osv(('No Accessory Defined!'), ('Before adding Suppliers, select Accessory in RFQ form.'))
			if ptype == 'asset' and not asset_id:
				raise osv.except_osv(('No Asset Defined!'), ('Before adding Suppliers, select Asset in RFQ form.'))
			if ptype == 'parts' and not part_id:
				raise osv.except_osv(('No Parts Defined!'), ('Before adding Suppliers, select Part in RFQ form.'))
		return True

	def onchange_price_unit(self, cr, uid, ids, prodid=False, supplier_id=False, product_qty=0, price_unit=0.0,
							taxes_id=False,context=None):
		taxlist = []
		if taxes_id and taxes_id[0] and taxes_id[0][2]:
			taxlist = taxes_id[0][2]
		taxes = self.pool.get('account.tax').browse(cr, uid, taxlist)
		taxes = self.pool.get('account.tax').compute_all(cr, uid, taxes, price_unit, product_qty, prodid, supplier_id)
		total = 0.0
		if taxes['total_included']:
			total = float(taxes['total_included'])
		return {'value': {'price_subtotal': total}}
		

class rfq_hcv_print(osv.osv):
	_name = "rfq.hcv.print.confirm"
	_description = "Print RFQ"

	_columns = {
		'name': fields.char('Name'),
		'supplier_ids': fields.many2many('res.partner', 'rfq_partners', 'print_id', 'partner_id', 'Suppliers'),
		'supplier_id': fields.many2one('res.partner', 'Supplier'),
		'print_rfq': fields.boolean('Print RFQ?'),
		'confirm_rfq': fields.boolean('Confirm RFQ'),
	}

	def print_report(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			rfq_id = context and 'rfq_id' in context and context['rfq_id'] or False
			if not rfq_id:
				raise osv.except_osv(('Error!'), ('RFQ reference not found!\nPlease contact your administartor.'))

			supplier_id = rec.supplier_id.id
			po_id = False
			#1. Print RFQ for selected Supplier :
			if rec.print_rfq:
				for rfq in self.pool.get('rfq.hcv').browse(cr, uid, rfq_id):
					for line in rfq.supplier_line:
						if line.supplier_id.id == supplier_id:
							po_id = line.po_id.id
					if rfq.state == 'draft':
						self.pool.get('rfq.hcv').write(cr, uid, rfq_id, {'state': 'rfq'})
				return self.pool['report'].get_action(cr, uid, [po_id], 'purchase.report_purchasequotation', context=context)
			#2. Confirm rfq for with selected supplier :
			if rec.confirm_rfq:
				for rfq in self.pool.get('rfq.hcv').browse(cr, uid, rfq_id):
					if rfq.type == 'parts':
						for line in rfq.supplier_line:
							if line.supplier_id.id == supplier_id:
								po_id = line.po_id.id
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'done'})
							elif line.po_id:
								self.pool.get('purchase.order').action_cancel(cr, uid, [line.po_id.id])
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'cancel'})
					elif rfq.type == 'accessory':
						for line in rfq.supplier_line:
							self.pool.get('purchase.order').action_cancel(cr, uid, [line.po_id.id])
							if line.supplier_id.id == supplier_id:
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'done'})
							elif line.po_id:
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'cancel'})
							#update flag to allow creating new Accessory :
							self.pool.get('rfq.hcv').write(cr, uid, rfq_id, {'create_accessory': True})
					elif rfq.type == 'asset':
						for line in rfq.supplier_line:
							self.pool.get('purchase.order').action_cancel(cr, uid, [line.po_id.id])
							if line.supplier_id.id == supplier_id:
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'done'})
							elif line.po_id:
								self.pool.get('rfq.suppliers.hcv').write(cr, uid, [line.id], {'state':'cancel'})
							#update flag to allow creating new Asset :
							self.pool.get('rfq.hcv').write(cr, uid, rfq_id, {'create_asset': True})
				#confirm po:
				if po_id:
					name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order') or '/'
					self.pool.get('purchase.order').write(cr, uid, [po_id], {'name': name})
					self.pool.get('purchase.order').signal_workflow(cr, uid, [po_id], 'purchase_confirm')
					self.pool.get('rfq.hcv').write(cr, uid, rfq_id, {'po_id': po_id})
			return self.pool.get('rfq.hcv').write(cr, uid, rfq_id, {'state': 'approved'})

