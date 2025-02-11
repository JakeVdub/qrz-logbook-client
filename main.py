from requests import Response, post
from typing import Final

BASE_URL: Final[str] = 'https://logbook.qrz.com/api'
API_KEY: Final[str] = '7267-1889-2DE8-9954' #TODO Change this, DON'T commit the API key

EOR_STRING: Final[str] = '&lt;eor&gt;'

""" Works, just need to validate and do something with the response data

TODO: Add options to constructor, validate option to make sure it is a valid choice
"""
def fetchRecords(limit: int = 100, offset: int = 0):
    ACTION: Final[str] = 'FETCH'

    if limit < 1 or limit > 1000:
        raise ValueError('Limit must be between 1 and 1000')

    if offset < 0:
        raise ValueError('Offset must be greater than or equal to 0')

    params = {
        'ACTION': ACTION,
        'OPTION': f"ALL,MAX:{limit},AFTERLOGID:{offset}"
    }

    response = sendRequest(ACTION, params)
    response_data = response.text
    print(response_data)

def insertRecord(adif_data):
    ACTION: Final[str] = 'INSERT'

    adif_data = adif_data.replace(" ", "")

    params = {
        'ACTION': ACTION,
        'ADIF': adif_data  #,
        #'OPTION': replace_duplicates
    }

    response = sendRequest(ACTION, params)
    response_data = response.text
    print(response_data)

def status():
    ACTION: Final[str] = 'STATUS'
    # TODO

def deleteRecord(log_ids: list):
    ACTION: Final[str] = 'DELETE'

    log_id_string = ",".join(map(str, log_ids))
    print(log_id_string)

    params = {
        'ACTION': ACTION,
        'LOGIDS': log_id_string
    }

    response = sendRequest(ACTION, params)
    response_data = response.text
    print(response_data)


# Should be denoted as a private function somehow with an underscore
def sendRequest(action: str, params) -> Response:
    headers = {
        'User-Agent': 'PythonUploadScript.py/0.0.1 (KE9AKI)'
    }

    default_params = {
        'KEY': API_KEY,
    }

    data = default_params | params
    return post(BASE_URL, data=data, headers=headers)

# if __name__ == '__main__':
#     fetchRecords(limit=5)
    #deleteRecord([1, 2, 3, 4, 5])
