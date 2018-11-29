import falcon
from resources.los import LearningObjectResource

api = falcon.API()

api.add_route('/v1/lo/', LearningObjectResource())
api.add_route('/v1/lo/{clone_lo_id}', LearningObjectResource())
