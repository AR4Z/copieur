import json
import falcon
from celery.result import AsyncResult
from utils import clone_lo, req_to_dict, RedisService, hide_links_with_404

service = RedisService()


class LearningObjectResource(object):
    def on_post(self, req, resp):
        req = req_to_dict(req)
        data = {
            'name': req.get('name').replace(' ', ''),
            'url': req.get('url')
        }

        redis_key_lo = '{0}:{1}'.format(data.get('name'), data.get('url'))

        if service.exists(redis_key_lo):
            hide_links_with_404(service.get(redis_key_lo))
            resp.status = falcon.HTTP_200
            resp.body = json.dumps({
                'path_lo': service.get(redis_key_lo)
            })
        else:
            task_clone_lo = clone_lo.delay(data)
            resp.status = falcon.HTTP_202
            resp.body = json.dumps({
                'id_task_clone_lo': task_clone_lo.id
            })


class LearningObjectResourceItem(object):
    def on_get(self, req, resp, clone_lo_id):
        clone_result = AsyncResult(clone_lo_id)
        result = {
            'status': clone_result.status,
            'path_lo': clone_result.result
        }

        if(clone_result.result == falcon.HTTP_404):
            resp.status = falcon.HTTP_404
        else:
            resp.status = falcon.HTTP_200

        if (clone_result.status == 'SUCCESS'):
            hide_links_with_404(clone_result.result)

        resp.body = json.dumps(result)
