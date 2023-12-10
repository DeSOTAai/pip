![Logo_DeSota](https://github.com/DeSOTAai/pip/assets/140865429/6fc2c7e2-bea0-4823-8ce2-4dfed8d974a6)
# DeSOTA Preferred Installer Program
```
pip install desota
```

# Packages
## detools
```
from desota import detools
```
### detools.get_model_req
Convert model request, from DeSOTA API the converted to YAML file in [DeRunner](https://github.com/DeSOTAai/DeRunner), into python dictionary format
```
def get_model_req(req_path: str) -> dict:
    """
    :param req_path: path to model request YAML file
    :return: model request arguments in dictionary format
    """ 
```
### detools.get_request_text
Get Text Arguments from DeSOTA Model request
```
def get_request_text(model_request_dict) -> list:
    """
    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with text arguments from model request
    """ 
```
### detools.get_request_audio
Get (download) Audio Arguments from DeSOTA Model request
```
def get_request_audio(model_request_dict: dict) -> list:
    """
    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with audio file paths downloaded from model request
    """ 
```
### detools.get_request_qa
Get Question-Answer Arguments from DeSOTA Model request
```
def get_request_qa(model_request_dict: dict) -> (list, list):
    """
    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: Tuple with model request `context` and `questions`, respectivaly
    """ 
```
### detools.get_request_url
Get URL Arguments from DeSOTA Model request
```
def get_request_url(model_request_dict: dict) -> list:
    """
    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :return: List with URL arguments from model request
    """ 
```
### detools.get_request_html
Get HTML Files from DeSOTA Model request
```
def get_request_html(model_request_dict: dict, from_url: bool = False) -> list((str, str)):
    """
    :param model_request_dict: model request retrieved from `detools.get_model_req`
    :param from_url: [OPTIONAL] Get HTLM file from URL
    :return: List with html arguments from model request as tuple (html_path, html_encoding)
    """ 
```