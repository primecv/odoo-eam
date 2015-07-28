from openerp.osv import osv, fields


class product_product(osv.Model):
	_inherit = "product.product"

	_columns = {
		'product_type': fields.selection([('part','Part'),('accessory','Accessory')], 'Type'),
		'mark': fields.char('Mark'),
		'model': fields.char('Model'),
		'serial': fields.char('Serial No'),
		'purchase_date': fields.date('Purchase Date'),
		'manufacturing_year': fields.date('Manufacturing Year'),
		'equipment_id': fields.many2one('asset.asset', 'Equipment'),
		'barcode_label': fields.binary('Barcode'),
		'barcode_no': fields.char('Barcode No', track_visibility='onchange'),
		'part_location_id': fields.many2one('stock.location', 'Location'),
	
	}
