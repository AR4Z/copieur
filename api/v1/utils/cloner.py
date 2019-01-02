import os
import shutil
import subprocess
from celery import Celery
from falcon import status_codes as status
from celery_singleton import Singleton
from dynaconf import settings
from .utils import extract_html, extract_name_directory_lo, get_all_files, process_css, process_html
from .redis_service import RedisService

app = Celery('cloner',
                    broker=settings.get('CELERY_BROKER'),
                    backend=settings.get('CELERY_BACKEND'))

service = RedisService()


@app.task(base=Singleton)
def clone_lo(data):
    url_lo = data.get('url')
    name_lo = data.get('name')
    path_lo = '{0}{1}'.format(settings.get('PATH_LOS'), name_lo)
    command = 'httrack {0}'.format(url_lo)

    os.mkdir(path_lo)
    os.chdir(path_lo)
    process = subprocess.Popen(command, shell=True)
    os.waitpid(process.pid, 0)

    try:
        html_httrack = extract_html(
            os.path.abspath('{0}/index.html'.format(path_lo)))
        main_file_lo = '{0}/{1}'.format(name_lo,
                                        extract_name_directory_lo(html_httrack))
    except FileNotFoundError:
        shutil.rmtree(path_lo, ignore_errors=True)
        return status.HTTP_404

    path_folder_lo = '{0}{1}'.format(settings.get(
        'PATH_LOS'), os.path.split(main_file_lo)[0])

    css_files = get_all_files(path_folder_lo, '*.css')
    html_files = get_all_files(path_folder_lo, '*.html')

    for css_file in css_files:
        process_css('{0}/{1}'.format(path_folder_lo, css_file))

    for html_file in html_files:
        process_html('{0}/{1}'.format(path_folder_lo, html_file))

    service.set('{0}:{1}'.format(name_lo, url_lo), main_file_lo)

    return main_file_lo
