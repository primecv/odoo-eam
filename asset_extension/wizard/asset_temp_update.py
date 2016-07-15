from openerp.osv import osv, fields
import xlrd, base64

class asset_temp_update(osv.osv):
	_name = "asset.temp.update"
	_description = "Asset Name Update"

	_columns = {
		'file': fields.binary('File', required=True),
		'filename': fields.char('Filename'),
		'state': fields.selection([('draft','New'), ('confirm','Done')], 'Status'),
		'name': fields.char('Name'),
	}

	_defaults = {
		'state': 'draft',
	}

	def update(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			if not rec.file:
				raise osv.except_osv(('Input Error!'), ('Please select valid file.\nAllowed formats: csv, xls & xlsx.'))
			else:
				filename = rec.filename
			fileext = filename.split('.')[-1]

			if fileext not in ('xls', 'xlsx'):
				raise osv.except_osv(('Input Error!'), ('Invalid / Unsupported File format.\nAllowed formats: xls & xlsx.'))

			if fileext in ('xls', 'xlsx'):
				try:
					data = base64.decodestring(rec.file)
					book = xlrd.open_workbook(file_contents = data)
					worksheet = book.sheet_names()
				except Exception,e:
					raise osv.except_osv(('Input Error!'), ('Invalid / Unsupported File format.\nPlease upload valid xls/xlsx file.\n%s\nTo see possible cause of this error, please check: https://github.com/hadley/readxl/issues/48'%(e)))

				count, success = 0, 0
				for worksheet_name in [worksheet[0]]:
					worksheet = book.sheet_by_name(worksheet_name)
					num_rows = worksheet.nrows - 1
					num_cells = worksheet.ncols - 1
					for curr_row in range(1, num_rows + 1):
						curr_cell = -1
						result = []
						while curr_cell < num_cells:
							curr_cell += 1
							cell_value = worksheet.cell_value(curr_row, curr_cell)
							result.append(cell_value)
						count = count + 1
						barcode_no = result[0]
						name = result[1]
						newname = result[2]
						if barcode_no and name != newname:
							asset = self.pool.get('asset.asset').search(cr, uid, [('barcode_no','=',str(barcode_no))])
							if asset:
								success = success + 1
								self.pool.get('asset.asset').write(cr, uid, [asset[0]], {'name': newname})
				print "Total rows : ",count
				print "Success : ",success
		return True
