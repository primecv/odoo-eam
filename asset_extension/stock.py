from openerp import api
from openerp import fields as fields
from openerp.addons.base_geoengine import fields as geo_fields
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

    @api.model
    def get_default_country(self):
        #country = self.env['res.country'].search([('code','ilike','CV')]).id
        return self.env['res.country'].search([('code','ilike','CV')], limit=1)



    @api.one
    def geocode_address(self):
        self.write({
            'latitude': self.latitude,
            'longitude': self.longitude,
            })

    @api.one
    def geo_localize(self):
        self.geocode_address()
        return True

    @api.one
    @api.depends('latitude', 'longitude')
    def _get_geo_point(self):
        if not self.latitude or not self.longitude:
            self.geo_point = False
        else:
            try:
                self.geo_point = geo_fields.GeoPoint.from_latlon(
                    self.env.cr, self.latitude, self.longitude)
            except Exception, e:
                #self.latitude, self.longitude = 0.0, 0.0
                raise osv.except_osv(('Alert!'), ('Invalid Latitude or Longitude. \n%s'%(e)))

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
    geo_point = geo_fields.GeoPoint(string='Addresses Coordinate', readonly=True, store=False, compute='_get_geo_point')

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

    def create(self, cr, uid, vals, context=None):
        try:
            res = super(stock_location, self).create(cr, uid, vals, context)
            geo = geo_fields.GeoPoint.from_latlon(cr, vals['latitude'], vals['longitude'])
            return res 
        except Exception, e:
            if 'latitude or longitude exceeded limits' in str(e):
                raise osv.except_osv(('Alert!'), ('Invalid Latitude or Longitude. \n%s'%(e)))
            else:
                raise osv.except_osv(('Error!'), ('%s'%(e)))

    def write(self, cr, uid, ids, vals, context=None):
        try:
            res = super(stock_location, self).write(cr, uid, ids, vals, context)
        except Exception, e:
            if 'latitude or longitude exceeded limits' in str(e):
                raise osv.except_osv(('Alert!'), ('Invalid Latitude or Longitude. \n%s'%(e)))
            else:
                raise osv.except_osv(('Error!'), ('%s'%(e)))
        return True
