import os, sys
import time, requests
import re, shutil

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
    with  requests.get(file_idx, stream=True) as req_file:
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
    out_path = os.path.join(TMP_PATH, os.path.basename(file_idx))
    if os.path.isfile(file_idx):
        return file_idx
    file_url = get_url_from_str(file_idx)
    if not file_url:
        return file_idx
    file_ext = os.path.splitext(file_url[0])[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    with requests.get(file_idx, stream=True) as r:
        if r.status_code != 200:
            return file_idx
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        user_chown(out_path)
    return out_path


# DECODE DESOTA API MODELS REQUESTS 
#   > TEXT
def get_request_text(model_request_dict) -> str:
    _req_text = None
    if 'query' in model_request_dict["input_args"]:
        _req_text = download_file(model_request_dict["input_args"]['query'], get_file_content=True)
    
    if 'text_prompt' in model_request_dict["input_args"]:
        _req_text = download_file(model_request_dict["input_args"]['text_prompt'], get_file_content=True)
    
    if not _req_text and 'file' in model_request_dict["input_args"] and "file_url" in model_request_dict["input_args"]["file"]:
        _req_text = get_file_content(model_request_dict["input_args"]['file']['file_url'])

    return _req_text

#   > AUDIO
def get_request_audio(model_request_dict, target_dist) -> str:
    audio_file = None
    if 'audio' in model_request_dict["input_args"] and "file_url" in model_request_dict["input_args"]["audio"]:
        audio_file = download_file(model_request_dict["input_args"]["audio"]["file_url"])
    elif 'file' in model_request_dict["input_args"] and "file_url" in model_request_dict["input_args"]["file"]:
        audio_file = download_file(model_request_dict["input_args"]["file"]["file_url"])
    return audio_file

#   > QUESTION-ANSWER
def get_request_qa(model_request_dict) -> (str, str):
    _context, _question = None, None
    if "context" in model_request_dict["input_args"] and "question" in model_request_dict["input_args"]:
        _context = download_file(model_request_dict["input_args"]["context"], get_file_content=True)
        _question = download_file(model_request_dict["input_args"]["question"], get_file_content=True)

    return _context, _question

#   > URL
def get_url_from_file(file_idx):
    file_content = download_file(file_idx, get_file_content=True)
    return get_url_from_str(file_content)

def get_request_url(model_request_dict) -> str:
    _req_url = None
    if 'url' in model_request_dict["input_args"]:
        _req_url = get_url_from_str(model_request_dict["input_args"]['url'])
        if not _req_url:
            _req_url = get_url_from_file(model_request_dict["input_args"]['url'])
            
    if not _req_url and 'file' in model_request_dict["input_args"] and "file_url" in model_request_dict["input_args"]["file"]:
        _req_url = get_url_from_file(model_request_dict["input_args"]['file']['file_url'])

    if not _req_url and 'text_prompt' in model_request_dict["input_args"]:
        _req_url = get_url_from_str(model_request_dict["input_args"]['text_prompt'])
        if not _req_url:
            _req_url = get_url_from_file(model_request_dict["input_args"]['text_prompt'])
    
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
    if _search_in_file_idx != file_idx:
        return _search_in_file_idx, _encoding
        
    base_filename = os.path.basename(file_idx)
    file_path = os.path.join(TMP_PATH, base_filename)
    with  requests.get(file_idx, stream=True) as req_file:
        if req_file.status_code != 200:
            return None, None
        
        if req_file.encoding is None:
            req_file.encoding = 'utf-8'

        with open(file_path, 'w') as fw:
            fw.write("")
        with open(file_path, 'a', encoding=req_file.encoding) as fa:
            for line in req_file.iter_lines(decode_unicode=True):
                if line:
                    fa.write(f"{line}\n")
                    # shutil.copyfileobj(req_file.raw, fwb)
    
    return file_path, req_file.encoding

def get_request_html(model_request_dict, from_url=False) -> (str, str):
    html_file = None
    html_encoding = None
    if from_url and 'url' in model_request_dict["input_args"]:
        in_arg = model_request_dict["input_args"]["url"]
        html_file, html_encoding = get_html_from_file(in_arg)

    if not html_file and 'html' in model_request_dict["input_args"]:
        in_arg = model_request_dict["input_args"]["html"]
        html_file, html_encoding = get_html_from_file(in_arg)

    if not html_file and 'file' in model_request_dict["input_args"] and "file_url" in model_request_dict["input_args"]["file"]:
        html_file, html_encoding = get_html_from_file(model_request_dict["input_args"]["file"]["file_url"])
            
    if not html_file and 'text_prompt' in model_request_dict["input_args"]:
        html_file, html_encoding = get_html_from_file(model_request_dict["input_args"]['text_prompt'])
        
    return html_file, html_encoding