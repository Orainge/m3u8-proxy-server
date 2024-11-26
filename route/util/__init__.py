# 工具类
import json
from flask import Response


def response_json_ok(data=None, message="OK"):
    """json ok 响应"""
    return response_json(status=200, code=0, data=data, message=message)


def response_json_error(data=None, message=None):
    """json error 响应"""
    return response_json(status=500, code=-1, data=data, message=message)


def response_json(status=200, code=None, data=None, message=None):
    """json 响应"""
    json_dict = {}

    if code is not None:
        json_dict['code'] = code
    if message is not None:
        json_dict['message'] = message
    if data is not None:
        json_dict['data'] = data

    return Response(
        json.dumps(json_dict, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )


def judge_if_true(value) -> bool:
    """
    判断请求的值是否是 True
    :param value: 传入的值
    :return bool
    """
    if (value is not None and
            (value == 'true' or value is True)):
        return True
    else:
        return False
