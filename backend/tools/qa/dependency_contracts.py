"""Reviewed DRF 3.18.2 message deltas; preserve historical transport fixtures.

Only exact known messages change. Status, headers, error structure, authorization
and every other body value still compare in full. In particular, required dict
fields now report missing HTML form input, matching JSON validation; do not
restore the old omission of that validation error.
"""
from copy import deepcopy


_MESSAGES = {
    'Action: This field is required. Resource Id: This field is required. Resource Revision: This field is required.':
        'Action: This field is required. Resource Id: This field is required. Resource Revision: This field is required. Payload: This field is required.',
    'Action: هذا الحقل مطلوب. Resource Id: هذا الحقل مطلوب. Resource Revision: هذا الحقل مطلوب.':
        'Action: هذا الحقل مطلوب. Resource Id: هذا الحقل مطلوب. Resource Revision: هذا الحقل مطلوب. Payload: هذا الحقل مطلوب.',
}


def drf_318_contract(expected, *, required_payload=False):
    result = deepcopy(expected)
    body = result.get('body')
    if not isinstance(body, dict):
        return result
    message = body.get('message')
    if result.get('status') == 405:
        for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'):
            if message == f'الطريقة "{method}" غير مسموح بها.':
                body['message'] = f'طريقة "{method}" غير مسموح بها.'
                break
    elif (required_payload and result.get('status') == 400
          and isinstance(message, str) and message in _MESSAGES):
        body['message'] = _MESSAGES[message]
    return result
