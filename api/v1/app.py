import falcon
from falcon_cors import CORS
from resources import LearningObjectResource

api = falcon.API(middleware=[
    CORS(
        allow_all_origins=True,
        allow_all_methods=True,
        allow_all_headers=True
    ).middleware
])

api.add_route('/v1/lo/{clone_lo_id}', LearningObjectResource())
