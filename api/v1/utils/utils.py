import falcon
import json
import os
import re
import glob
import cssutils
import requests
from bs4 import BeautifulSoup
import speech_recognition as sr
from pydub import AudioSegment
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from dynaconf import settings
import urllib
from dynaconf import settings


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


def extract_html(path_html_file):
    with open(path_html_file, 'r') as html_file:
        dom = html_file.read()

    return dom


def extract_name_directory_lo(html):
    soup = BeautifulSoup(html, 'html.parser')

    return soup.a['href']


def get_all_files(folder, ext):
    os.chdir(folder)
    files = []
    for file in glob.glob(ext):
        files.append(file)

    return files


def change_html(DOM):
    soup = BeautifulSoup(DOM, "html.parser")
    google_translate_html = """
    <style>.goog-te-banner-frame{display:none;}</style>
    <div id="google_translate_element" style="display:none"></div><script type="text/javascript">function googleTranslateElementInit(){new google.translate.TranslateElement({pageLanguage: 'es', layout: google.translate.TranslateElement.InlineLayout.SIMPLE, autoDisplay: false}, 'google_translate_element');}</script><script src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit" type="text/javascript"></script><script type="text/javascript">function translate(lang){var $frame=$('.goog-te-menu-frame:first'); if (!$frame.length){alert("Error: Could not find Google translate frame."); return false;}$frame.contents().find('.goog-te-menu2-item span.text:contains('+lang+')').get(0).click(); return false;}</script>
  """
    print(soup)
    soup.body.append(BeautifulSoup(google_translate_html, "html.parser"))
    for tag in soup.find_all():
        try:
            style = tag['style']
            css_parse = cssutils.parseStyle(style)
            css_parse['font-family'] = ''
            tag['style'] = css_parse.cssText
        except:
            pass

    return str(soup)


def all_rem_or_em_to_px(css_styles):
    base = 16
    for rule in css_styles:
        try:
            if rule.style['font-size']:
                if rule.selectorText == 'html':
                    base = rule.style['font-size']
                    if is_percentage(base):
                        number = [float(s) for s in re.findall(
                            r'-?\d+\.?\d*', base)][0]
                        base = 16 * (number/100)
                        rule.style['font-size'] = '{0}px;'.format(base)
                else:
                    old_font_size = rule.style['font-size']
                    if not is_px(old_font_size):
                        number = [float(s) for s in re.findall(
                            r'-?\d+\.?\d*', old_font_size)][0]
                        rem = number
                        px = base * rem
                        rule.style['font-size'] = '{0}px;'.format(px)
        except:
            pass

        try:
            if rule.style['font']:
                rule.style['font'] = ''

        except:
            pass

    return css_styles


def is_percentage(units):
    return units[-1] == '%'


def is_px(units):
    return units[-1] == 'x'


def is_rem_or_em(units):
    return units[-1] == 'm'


def to_rem(units, base=12):
    number = [float(s) for s in re.findall(r'-?\d+\.?\d*', units)][0]
    if is_px(units):
        px = number
        rem = px/base
        rem = '{0}rem;'.format(rem)
        return rem


def change_css(css_styles):
    css_styles = all_rem_or_em_to_px(css_styles)
    font_size_html = False
    for rule in css_styles:
        try:
            if rule.style['font-size']:
                if rule.selectorText == 'html':
                    rule.style['font-size'] = '12px;'
                    font_size_html = True
                else:
                    old_font_size = rule.style['font-size']
                    rule.style['font-size'] = to_rem(old_font_size)
        except:
            pass

    if not font_size_html:
        css_styles.insertRule('html {font-size: 12px;}')

    return css_styles


def unwrap_p(dom):
    soup = BeautifulSoup(dom, 'html.parser')

    for p_tag in soup.findAll('p'):
        for span_tag in p_tag.findAll('span'):
            span_tag.unwrap()
            try:
                if(not p_tag.get('style').isspace()):
                    p_tag['style'] = '{0};{1}'.format(
                        p_tag.get('style'), span_tag.get('style'))
                else:
                    p_tag['style'] = span_tag.get('style')
            except:
                pass

    return str(soup)


def hide_elements_without_description(html):
    soup = BeautifulSoup(html, 'html.parser')

    for img_tag in soup.findAll('img'):
        if not img_tag.get('alt') or img_tag.get('alt').strip() == '':
            img_tag['style'] = 'display:none;'

    for video_tag in soup.findAll('video'):
        if not video_tag.get('alt') or video_tag.get('alt').strip() == '':
            video_tag['style'] = 'display:none;'

    for audio_tag in soup.findAll('audio'):
        if not audio_tag.get('alt') or audio_tag.get('alt').strip() == '':
            audio_tag['style'] = 'display:none;'

    return str(soup)


def process_html(path_html_file):
    print('PATH', path_html_file)
    html = unwrap_p(change_html(extract_html(path_html_file)))
    path = os.path.split(os.path.abspath(path_html_file))[0]
    html = add_video_cc(html, path)
    html = add_audio_cc(html, path)
    html = hide_elements_without_description(html)
    with open(path_html_file, 'w') as html_file:
        html_file.write(html)


def process_css(path_css_file):
    css = change_css(extract_css_rules(path_css_file)).cssText
    with open(path_css_file, 'wb') as css_file:
        css_file.write(css)


def extract_css_rules(path_css_file):
    sheet = cssutils.parseFile(path_css_file)
    return sheet


def download_video(url, path):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    video_path = f'{path}/{local_filename}'
    with open(video_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()

    return video_path


def add_video_cc(dom, path):
    SERVER_URL = settings.get('SERVER_URL')
    soup = BeautifulSoup(dom, 'html.parser')
    config_string = 'task_language=spa|is_text_type=plain|os_task_file_format=vtt'
    task = Task(config_string=config_string)
    print(path)

    for video_tag in soup.findAll('video'):
        sources = video_tag.findAll('source')

        if sources:
            source = sources[0]
            url_video = source.get('src')
            video_path = download_video(url_video, path)
            video_name = url_video.split('/')[-1][:-4]
            source['src'] = f'{SERVER_URL}{path[path.index("LOs"):]}/{url_video.split("/")[-1]}'

            sound = AudioSegment.from_file(f'{video_path}')
            sound.export('audio.wav', format='wav')
            r = sr.Recognizer()

            with sr.AudioFile('audio.wav') as source:
                audio = r.record(source)
                text = r.recognize_google(audio, language='es-ES')

            words = text.split()
            text_by_lines = ''
            cont = 0
            line = ''

            for word in words:
                line += f'{word} '
                cont += 1

                if cont == 6:
                    text_by_lines += f'{line}\n'
                    cont = 0
                    line = ''

            if cont != 0:
                text_by_lines += f'{line}\n'

            with open('text.txt', 'w', encoding='utf-8') as text_file:
                text_file.write(text_by_lines)

            task.audio_file_path_absolute = f'{path}/audio.wav'
            task.text_file_path_absolute = f'{path}/text.txt'
            task.sync_map_file_path_absolute = f'{path}/{video_name}.vtt'
            track_tag = soup.new_tag('track', label='Espanol', kind='subtitles',
                                     srclang='es', src=f'{SERVER_URL}{path[path.index("LOs"):]}/{video_name}.vtt')
            video_tag.append(track_tag)

            ExecuteTask(task).execute()
            # output sync map to file
            task.output_sync_map_file()
        else:
            continue
        print(video_tag)
    return str(soup)


def add_audio_cc(dom, path):
    SERVER_URL = settings.get('SERVER_URL')
    soup = BeautifulSoup(dom, 'html.parser')

    for audio_tag in soup.findAll('audio'):
        audio_source = audio_tag.get('src')

        if audio_source:
            #audio_path = download_video(audio_source, path)
            audio_name = audio_source.split('/')[-1][:-4]
            #audio_tag['src'] = f'{SERVER_URL}{path[path.index("LOs"):]}/{audio_source.split("/")[-1]}'

            sound = AudioSegment.from_file(f'{audio_source}')
            sound.export('audio.wav', format='wav')

            r = sr.Recognizer()

            with sr.AudioFile('audio.wav') as source:
                audio = r.record(source)
                try:
                    text = r.recognize_google(audio, language='es-ES')
                except Exception:
                    text = ''

            audio_text = {
                'text': text
            }

            with open(f'{audio_name}.json', 'w', encoding='utf-8') as json_file:
                json.dump(audio_text, json_file)
            audio_tag['data-text'] = f'{SERVER_URL}{path[path.index("LOs"):]}/{audio_name}.json'

        else:
            continue

    return str(soup)


def hide_links_with_404(main_file_lo):
    path_folder_lo = '{0}{1}'.format(settings.get(
        'PATH_LOS'), os.path.split(main_file_lo)[0])
    html_files = get_all_files(path_folder_lo, '*.html')

    for html_file in html_files:
        soup = BeautifulSoup(extract_html(html_file), 'html.parser')

        for a_tag in soup.find_all('a'):
            href = a_tag.get('href')

            if href:
                try:
                    urllib.request.urlopen(href)
                    a_tag['style'] = 'display:block;'
                except ValueError:
                    pass
                except (urllib.error.HTTPError, urllib.error.URLError) as e:
                    a_tag['style'] = 'display:none;'

        html = str(soup)
        with open(html_file, 'w') as html_file:
            html_file.write(html)
