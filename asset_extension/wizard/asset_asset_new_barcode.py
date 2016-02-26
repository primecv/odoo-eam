# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class asset_asset_new_barcode(osv.osv_memory):
	_name = "asset.asset.new.barcode"

	_description = "Asset Barcode Update"

	_columns = {
		'barcode_no': fields.char('New Barcode No', size=9),
	}

	def update(self, cr, uid, ids, context=None):
		asset_id = context and context['asset_id'] or None
		if asset_id:
			for rec in self.browse(cr, uid, ids):
				barcode_no = str(rec.barcode_no)
				flag = False
				for bcode in barcode_no:
					if ord(bcode) not in (48, 49, 50, 51, 52, 53, 54, 55, 56, 57):
						flag = True
				if len(barcode_no) != 9:
					raise osv.except_osv(('Alert!'), ('Barcode No must have 9 digits.'))
				if flag:
					raise osv.except_osv(('Alert!'), ('Barcode No can only contain numbers 0-9.'))
				asset = self.pool.get('asset.asset').search(cr, uid, [('barcode_no','=', barcode_no)])
				if asset:
					raise osv.except_osv(('Duplicate Barcodes'), ('You cannot have more than one asset with same Barcode No.'))
			return self.pool.get('asset.asset').write(cr, uid, asset_id, {'barcode_no': barcode_no})
		return False
