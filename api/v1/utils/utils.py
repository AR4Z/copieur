import falcon
import json

def req_to_dict(req):
  try:
    raw_json = req.stream.read()
  except Exception as ex:
    raise falcon.HTTPError(falcon.HTTP_400, 'Error', ex.message)

  try:
    result_dict = json.loads(raw_json, encoding='utf-8')
  except ValueError:
    raise falcon.HTTPError(
        falcon.HTTP_400,
        'Malformed JSON',
        'Could not decode the request body. The '
        'JSON was incorrect.'
    )

  return result_dict