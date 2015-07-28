from openerp import api
from openerp import fields as fields
from openerp.osv import osv
from openerp import exceptions
from openerp import tools
from openerp.tools.translate import _

try:
    import simplejson as json
except ImportError:
    import json
import urllib

def geo_find(addr):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
    url += urllib.quote(addr.encode('utf8'))

    try:
        result = json.load(urllib.urlopen(url))
    except Exception, e:
        raise osv.except_osv(_('Network error'),
                             _('Cannot contact geolocation servers. Please make sure that your internet connection is up and running (%s).') % e)
    if result['status'] != 'OK':
        return None

    try:
        geo = result['results'][0]['geometry']['location']
        return float(geo['lat']), float(geo['lng'])
    except (KeyError, ValueError):
        return None


def geo_query_address(street=None, zip=None, city=None, county=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street,
                                              ("%s %s" % (zip or '', city or '')).strip(),
                                              county,
                                              country])))

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

    street = fields.Char(string='Street')
    city_id = fields.Many2one('res.country.city', string='City')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    country = fields.Many2one('res.country', string='Country')
    country_code = fields.Char(string='Country Code')
    island = fields.Char(string='Island')
    county_id = fields.Many2one('res.country.county', string='County')
    county = fields.Char(string='County')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')

    def geo_localize(self, cr, uid, ids, context=None):
        for product in self.browse(cr, uid, ids):
            if not product:
                continue
            result = geo_find(geo_query_address(street=product.street,
                                                zip=product.zip,
                                                city=product.city,
												county=product.county,
                                                country=product.country.name))
            if result:
                self.write(cr, uid, [product.id], {
                    'latitude': result[0],
                    'longitude': result[1],
                }, context=context)
        return True
