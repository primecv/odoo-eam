from openerp import api
from openerp import fields as fields
from openerp.osv import osv

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

    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    country = fields.Many2one('res.country', string='Country')
    island = fields.Char(string='Island')
    county = fields.Char(string='County')
