import json
import falcon
from celery.result import AsyncResult
from utils.cloner import clone_lo
from utils.utils import req_to_dict

class LearningObjectResource:
  def on_post(self, req, resp):
    req = req_to_dict(req)
    data = {
      'name': req.get('name'),
      'url': req.get('url')
    }

    task = clone_lo.delay(data)
    resp.status = falcon.HTTP_202
    resp.body = json.dumps({
      'path_lo': task.id
    })


  def on_get(self, req, resp, clone_lo_id):
    clone_result = AsyncResult(clone_lo_id)
    result = {
      'status': clone_result.status, 
      'result': clone_result.result
    }

    resp.status = falcon.HTTP_200
    resp.body = json.dumps(result)

