import os
import subprocess
from dynaconf import settings
import celery
from celery_singleton import Singleton

CELERY_BROKER =  'redis://localhost:6379/0'
CELERY_BACKEND =  'redis://localhost:6379/0'

app = celery.Celery('cloner', 
  broker=settings.get('CELERY_BROKER'), 
  backend=settings.get('CELERY_BACKEND'))

@app.task(base=Singleton)
def clone_lo(data):
  url_lo = data.get('url')
  name_lo = data.get('name').replace(' ', '')
  path_lo = '{0}{1}'.format(settings.get('PATH_LOS'), name_lo)
  command = 'httrack {0}'.format(url_lo)

  if exist_lo(path_lo):
    return get_main_file_lo(path_lo)
  else:
    os.mkdir(path_lo)
    os.chdir(path_lo)
    process = subprocess.Popen(command, shell=True)
    os.waitpid(process.pid, 0)


def exist_lo(path_lo):
  return False


def get_main_file_lo(sw):
  return ''
