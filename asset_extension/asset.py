from openerp.osv import osv, fields

class asset_asset(osv.osv):
	_inherit = "asset.asset"

	_columns = {
		'asset_id': fields.char('ID'),
		'hospital_id': fields.many2one('res.partner', 'Hospital'),
		'hospital_category_id': fields.related('hospital_id', 'hospital_category_id', 'name', string='Department', type='char', store=True),
		'category_id': fields.many2one('asset.asset.category', 'Category'),
		'mark': fields.char('Mark'),
		'manuf_year': fields.date('Manufacturing Year'),
		'state_operation': fields.selection([('1', 'Active'),('0','Inactive')], 'State Operation'),
		'notes': fields.text('Notes'),
	}

	def create(self, cr, uid, vals, context=None):
		seq = self.pool.get('ir.sequence').get(cr, uid, 'asset.asset') 
		asset_id = ''
		hospital_seq = ''
		if 'hospital_id' in vals and vals['hospital_id']:
			hospital_seq = self.pool.get('res.partner').browse(cr, uid, [vals['hospital_id']])[0].name[0:3]
		if len(vals['name']) <= 3:
			name = vals['name']
		else:
			name = vals['name'][0:3]
		asset_id = hospital_seq + name + str(seq)
		vals['asset_id'] = asset_id
		return super(asset_asset, self).create(cr, uid, vals, context)

	def onchange_hospital(self, cr, uid, ids, hospital_id, context=None):
		if not hospital_id:
			return {'value': {'hospital_category_id': False}}
		hospital_category_id = self.pool.get('res.partner').browse(cr, uid, [hospital_id])[0].hospital_category_id.name
		return {'value': {'hospital_category_id': hospital_category_id}}



class asset_asset_category(osv.Model):
	_name = "asset.asset.category"

	_columns = {
		'name': fields.char('Category Name', required=True, select=True),
		'code': fields.char('Code'),
	}
