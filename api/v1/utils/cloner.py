import os
import shutil
import subprocess
import celery
import falcon
from celery_singleton import Singleton
from dynaconf import settings
from .utils import extract_html, extract_name_directory_lo, get_all_files, process_css, process_html


app = celery.Celery('cloner',
                    broker=settings.get('CELERY_BROKER'),
                    backend=settings.get('CELERY_BACKEND'))


@app.task(base=Singleton)
def clone_lo(data):
    url_lo = data.get('url')
    name_lo = data.get('name').replace(' ', '')
    path_lo = '{0}{1}'.format(settings.get('PATH_LOS'), name_lo)
    command = 'httrack {0}'.format(url_lo)
    exist = exist_lo(path_lo)

    if not exist:
        os.mkdir(path_lo)
        os.chdir(path_lo)
        process = subprocess.Popen(command, shell=True)
        os.waitpid(process.pid, 0)

    html_httrack = extract_html(os.path.abspath('{0}/index.html'.format(path_lo)))

    try:
        main_file_lo = '{0}/{1}'.format(name_lo,
                                        extract_name_directory_lo(html_httrack))
    except FileNotFoundError:
        shutil.rmtree(path_lo, ignore_errors=True)
        return falcon.HTTP_404

    path_folder_lo = '{0}{1}'.format(settings.get(
        'PATH_LOS'), os.path.split(main_file_lo)[0])

    if not exist:
        css_files = get_all_files(path_folder_lo, '*.css')

        for css_file in css_files:
            process_css('{0}/{1}'.format(path_folder_lo, css_file))

        html_files = get_all_files(path_folder_lo, '*.html')

        for html_file in html_files:
            process_html('{0}/{1}'.format(path_folder_lo, html_file))

    return main_file_lo


def exist_lo(path_lo):
    return os.path.isdir(path_lo)
