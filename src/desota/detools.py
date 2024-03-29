import os, sys
import time, requests
import re, shutil
import yaml
from yaml.loader import SafeLoader


from requests.adapters import HTTPAdapter, Retry

s = requests.Session()

retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

s.mount('https://', HTTPAdapter(max_retries=retries))

# inspired inhttps://stackoverflow.com/a/13874620
def get_platform():
    _platform = sys.platform
    _win_res=["win32", "cygwin", "msys"]
    _lin_res=["linux", "linux2"]
    _user_sys = "win" if _platform in _win_res else "lin" if _platform in _lin_res else None
    if not _user_sys:
        raise EnvironmentError(f"Plataform `{_platform}` can not be parsed to DeSOTA Options: Windows={_win_res}; Linux={_lin_res}")
    return _user_sys
USER_SYS=get_platform()
# DeSOTA PATHS
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(CURRENT_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(CURRENT_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        os.system(f"chown -R {USER} {path}")
    return
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
    user_chown(TMP_PATH)

# UTILS
def get_url_from_str(string) -> list:
    # retrieved from https://www.geeksforgeeks.org/python-check-url-string/
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
#
def retrieve_file_content(file_idx) -> str:
    if os.path.isfile(file_idx):
            with open(file_idx, 'r') as fr:
                return fr.read()
    file_url = get_url_from_str(file_idx)
    if len(file_url)==0:
        return file_idx
    file_url = file_url[0]
    file_ext = os.path.splitext(file_url)[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    file_content = ""
    with  s.get(file_idx, stream=True) as req_file:
        if req_file.status_code != 200:
            return file_idx
        
        if req_file.encoding is None:
            req_file.encoding = 'utf-8'

        for line in req_file.iter_lines(decode_unicode=True):
            if line:
                file_content += line
    return file_content
#
def download_file(file_idx, get_file_content=False) -> str:
    if get_file_content:
        return retrieve_file_content(file_idx)
    out_path = os.path.join(TMP_PATH, str(os.path.basename(file_idx).split('/')[-1].split('?')[0]))
    if os.path.isfile(file_idx):
        return file_idx
    file_url = get_url_from_str(file_idx)
    if not file_url:
        return file_idx
    file_ext = os.path.splitext(file_url[0])[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    with s.get(file_idx, stream=True) as r:
        if r.status_code != 200:
            return file_idx
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        user_chown(out_path)
    return out_path

# TOOLS
def get_model_req(req_path: str) -> dict:
    """
    Convert model request, from DeSOTA API the converted to YAML file in [DeRunner](https://github.com/DeSOTAai/DeRunner), into python dictionary format
    
    :param req_path: path to model request YAML file 9
    :return: model request arguments in dictionary format
    """
    # About Output
    '''
    {
        "task_type": None,      # TASK VARS
        "task_model": None,
        "task_dep": None,
        "task_args": None,
        "task_id": None,
        "filename": None,       # FILE VARS
        "file_url": None,
        "text_prompt": None     # TXT VAR
    }
    '''
    if not os.path.isfile(req_path):
        exit(1)
    with open(req_path) as f:
        return yaml.load(f, Loader=SafeLoader)
#
def get_model_args(model_req: dict) -> dict:
    try:
        assert model_req['input_args']['model_args']
        return model_req['input_args']['model_args']
    except Exception:
        return None
    

# MODELS
# TODO: Get Deps Args
#   > TEXT
def get_request_text(model_request_dict: dict) -> list:
    """
    Get Text Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with text arguments from model request
    """
    _req_text = None
    if 'query' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['query']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_text = []
            for query in _input_target:
                _req_text.append(download_file(query, get_file_content=True))
    
    if not _req_text and 'text_prompt' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['text_prompt']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_text = []
            for text_prompt in _input_target:
                _req_text.append(download_file(text_prompt, get_file_content=True))
    
    if not _req_text and 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_text = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    _req_text.append(download_file(file_idx["file_url"], get_file_content=True))
    
    return _req_text

#   > FILE
def get_request_file(model_request_dict: dict) -> list:
    """
    Get (download) File Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with General file file paths downloaded from model request
    """
    file_file = None
    if 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            file_file = []
            for file in _input_target:
                if "file_url" in file:
                    file_file.append(download_file(file["file_url"]))
    return file_file

#   > IMAGE
def get_request_image(model_request_dict: dict) -> list:
    """
    Get (download) Image Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with image file paths downloaded from model request
    """
    image_file = None
    if 'image' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['image']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            image_file = []
            for image in _input_target:
                if "file_url" in image:
                    image_file.append(download_file(image["file_url"]))
    elif 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            image_file = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    image_file.append(download_file(file_idx["file_url"]))
    return image_file

#   > AUDIO
def get_request_audio(model_request_dict: dict) -> list:
    """
    Get (download) Audio Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with audio file paths downloaded from model request
    """
    audio_file = None
    if 'audio' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['audio']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            audio_file = []
            for audio in _input_target:
                if "file_url" in audio:
                    audio_file.append(download_file(audio["file_url"]))
    elif 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            audio_file = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    audio_file.append(download_file(file_idx["file_url"]))
    return audio_file

#   > VIDEO
def get_request_video(model_request_dict: dict) -> list:
    """
    Get (download) Video Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with video file paths downloaded from model request
    """
    video_file = None
    if 'video' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['video']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            video_file = []
            for video in _input_target:
                if "file_url" in video:
                    video_file.append(download_file(video["file_url"]))
    elif 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            video_file = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    video_file.append(download_file(file_idx["file_url"]))
    return video_file


#   > QUESTION-ANSWER
def get_request_qa(model_request_dict: dict) -> (list, list):
    """
    Get Question-Answer Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: Tuple with model request `context` and `questions`, respectivaly
    """
    _context, _question = None, None
    # Get Context
    if "context" in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['context']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _context = []
            for question in _input_target:
                _context.append(download_file(question, get_file_content=True))   
    if not _context and 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _context = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    _context.append(download_file(file_idx["file_url"], get_file_content=True))
    
    # Get Question
    if "question" in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['question']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _question = []
            for question in _input_target:
                _question.append(download_file(question, get_file_content=True))    
    if not _question and 'text_prompt' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['text_prompt']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _question = []
            for text_prompt in _input_target:
                _question.append(download_file(text_prompt, get_file_content=True))

    return _context, _question


#   > URL
def get_url_from_file(file_idx):
    file_content = download_file(file_idx, get_file_content=True)
    return get_url_from_str(file_content)

def get_request_url(model_request_dict: dict) -> list:
    """
    Get URL Arguments from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with URL arguments from model request
    """
    _req_url = None
    if 'url' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['url']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_url = []
            for curr_url in _input_target:
                inst_url = get_url_from_str(curr_url)
                print("UTILS:", inst_url)
                if not inst_url:
                    inst_url = get_url_from_file(curr_url)
                if inst_url:
                    _req_url += inst_url
            
    if not _req_url and 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_url = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    _req_url = get_url_from_file(file_idx["file_url"])

    if not _req_url and 'text_prompt' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['text_prompt']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_url = []
            for text_prompt in _input_target:
                inst_url = get_url_from_str(text_prompt)
                if not _req_url:
                    inst_url = get_url_from_file(text_prompt)
                if inst_url:
                    _req_url += inst_url
    return _req_url

#   > HTML
def get_html_from_str(string):
    # retrieved from https://stackoverflow.com/a/3642850 & https://stackoverflow.com/a/32680048
    pattern = re.compile(r'<html((.|[\n\r])*)\/html>')
    _res = pattern.search(string)
    if not _res:
        return None, None
    
    _html_content = f"<html{_res.group(1)}/html>"
    _tmp_html_path = os.path.join(TMP_PATH, f"tmp_html{int(time.time())}.html")
    with open(_tmp_html_path, "w") as fw:
        fw.write(_html_content)
    return _tmp_html_path, 'utf-8'

def get_html_from_file(file_idx) -> (str, str):
    _search_in_file_idx, _encoding = get_html_from_str(file_idx)
    if _search_in_file_idx:
        return _search_in_file_idx, _encoding
        
    base_filename = os.path.basename(file_idx)
    file_path = os.path.join(TMP_PATH, base_filename)
    file_tmp_path = os.path.join(TMP_PATH, "tmp_"+base_filename)
    if not file_path.endswith(".html"):
        file_path += ".html"
        file_tmp_path += ".html"
    with  requests.get(file_idx, stream=True) as req_file:
        if req_file.status_code != 200:
            return None, None
        
        if req_file.encoding is None:
            req_file.encoding = 'utf-8'

        with open(file_tmp_path, 'w') as fw:
            fw.write("")
        with open(file_tmp_path, 'a', encoding=req_file.encoding) as fa:
            for line in req_file.iter_lines(decode_unicode=True):
                if line:
                    fa.write(f"{line}\n")
                    # shutil.copyfileobj(req_file.raw, fwb)
        
        if req_file.encoding != 'utf-8':
            # inspired in https://stackoverflow.com/a/191455
            # alternative: https://superuser.com/a/1688176
            try:
                with open(file_tmp_path, 'rb') as source:
                    with open(file_path, "w") as recode:
                        recode.write(str(source.read().decode(req_file.encoding).encode("utf-8").decode("utf-8")))
                req_file.encoding = 'utf-8'
            except:
                file_path = file_tmp_path
    return file_path, req_file.encoding

def get_request_html(model_request_dict: dict, from_url: bool = False) -> list((str, str)):
    """
    Get HTML Files from DeSOTA Model request

    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :param from_url: [OPTIONAL] Get HTLM file from URL
    :return: List with html arguments from model request as tuple (html_path, html_encoding)
    """
    _req_html = None

    if not _req_html and 'html' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['html']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_html = []
            for html in _input_target:
                _req_html.append(get_html_from_file(html))

    if not _req_html and 'file' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['file']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_html = []
            for file_idx in _input_target:
                if "file_url" in file_idx:
                    _req_html.append(get_html_from_file(file_idx["file_url"]))

    if not _req_html and 'url' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['url']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_html = []
            for url in _input_target:
                _req_html.append(get_html_from_file(url))

    if not _req_html and 'text_prompt' in model_request_dict["input_args"]:
        _input_target = model_request_dict["input_args"]['text_prompt']
        if isinstance(_input_target, str):
            _input_target = [_input_target]
        if isinstance(_input_target, list):
            _req_html = []
            for text_prompt in _input_target:
                _req_html.append(get_html_from_file(text_prompt))
    
    return _req_html



def upload_request_files(file_paths: list, send_task_url: str, delete_files:bool =True) -> requests.Response:
    """
    Upload Model Result to DeSOTA and then OPTIONALLY delete temp files

    :param file_paths: list - valid filepaths to all results from the model
    :param send_task_url: string - model request retrieved from init
    :param delete_files: [OPTIONAL] bool - default true
    :return: desota api request response 
    """
    saved_file_names = []
    media_file_names = []
    text_files_to_upload = []
    

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        file_extension = file_name.split('.')[-1].lower()

        if file_extension in ['txt', 'md', 'srt']:
            text_files_to_upload.append((file_name, file_path))
            continue
        media_file_names.append(file_name)

    if media_file_names:
        # Get presigned URL for all media files
        payload = {
            'getPresignedUrl': 1,
            'saveFileName': ','.join(media_file_names)
        }
        send_task = s.post(url=send_task_url, data=payload)
        presigned_urls = send_task.json()

        for file_name, presigned_url in presigned_urls['index'].items():
            if presigned_url != 'fileTypeError':
                for file_path in file_paths:
                    if file_name != os.path.basename(file_path):
                        continue
                    with open(file_path, 'rb') as fr:
                        # Upload file using presigned URL
                        response = s.put(presigned_url, data=fr)
                        if response.status_code == 200:
                            saved_file_names.append(file_name)
                            print(f"Upload successful for {file_name}!")
                        else:
                            print(f"Upload failed for {file_name} with status code: {response.status_code}")
                                

    # Prepare text files for final upload
    text_files_payload = []
    for file_name, file_path in text_files_to_upload:
        with open(file_path, 'rb') as fr:
            text_files_payload.append(('upload[]', (file_name, fr.read())))

    # Upload text files with the final request
    payload2 = {
        'saveFileName': ','.join(saved_file_names)
    }
    send_task_final = s.post(url=send_task_url, data=payload2, files=text_files_payload)
    
    print(f"[INFO] DeSOTA API Upload Response:\n{json.dumps(send_task_final.json(), indent=2)}")


    # Delete temporary files if delete_files is True
    if delete_files:
        for file_path in file_paths:
            os.remove(file_path)
    return send_task_final