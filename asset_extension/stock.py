from openerp import api
from openerp import fields as fields
from openerp.osv import osv, fields as osv_fields
from openerp import exceptions
from openerp import tools
from openerp.tools.translate import _

class stock_location(osv.osv):
    _inherit = "stock.location"

    @api.one
    @api.depends('location_id')
    def onchange_location_id(self, location_id=False):
        if location_id:
           location = self.env['stock.location'].browse(location_id)
           return {
              'value': {
                  'street': location.street,
  				  'city': location.city,
				  'zip': location.zip,
			 	  'country': location.country.id or False,
         		  'island': location.island,
				  'county': location.county
               }
            }
        return {} 

    @api.multi
    def onchange_country(self, country_id=False):
        if country_id:
           country = self.env['res.country'].browse(country_id)
           return {
                  'value': {
  			   	     'city_id': False,
				     'county_id': False,
  			   	     'city': False,
				     'county': False,
                     'country_code': country.code
                    }
                }
        return {'value': {'country_code': ''}} 

    @api.multi
    def onchange_county(self, county_id=False):
        if county_id:
           county = self.env['res.country.county'].browse(county_id)
           return {
                  'value': {
				     'county': county.name,
                    }
                }
        return {} 

    @api.multi
    def onchange_city(self, city_id=False):
        if city_id:
           city = self.env['res.country.city'].browse(city_id)
           return {
                  'value': {
				     'city': city.name,
                    }
                }
        return {} 

    @api.model
    def get_default_country(self):
        #country = self.env['res.country'].search([('code','ilike','CV')]).id
        return self.env['res.country'].search([('code','ilike','CV')], limit=1)



    street = fields.Char(string='Street')
    city_id = fields.Many2one('res.country.city', string='City')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    country = fields.Many2one('res.country', string='Country', default=get_default_country)
    country_code = fields.Char(string='Country Code')
    island_id = fields.Many2one('res.country.island', string='Island')
    island = fields.Char(related='island_id.name', string='Island', store=True)
    county_id = fields.Many2one('res.country.county', string='County')
    county = fields.Char(string='County')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')

class stock_move(osv.osv):
	_inherit = "stock.move"

	_columns = {
		'from_hcv': osv_fields.boolean('From HCV'),
	}

	def print_move_hcv_report(self, cr, uid, ids, context=None):
		return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_stock_move', context=context)

	def default_get(self, cr, uid, fields, context=None):
		res = super(stock_move, self).default_get(cr, uid, fields, context)
		if context and 'from_hcv' in context:
			location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
			if location_id:
				res.update(location_id=location_id[1])
		return res

	def onchange_location_id(self, cr, uid, ids, from_hcv, location_id, context=None):
		vals = {}
		if from_hcv and from_hcv is True:
			location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
			if location_id:
				location_id=location_id[1]
				vals['location_id'] = location_id
		return {'value': vals}

