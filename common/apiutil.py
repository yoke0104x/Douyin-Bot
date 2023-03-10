# -*- coding: UTF-8 -*-
import hashlib

from urllib import parse

import base64

import json

from tencentcloud.iai.v20180301 import iai_client

from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.iai.v20180301 import models

from tencentcloud.common import credential
from tencentcloud.common.profile.http_profile import HttpProfile



url_preffix = "iai.tencentcloudapi.com"


def setParams(array, key, value):
    array[key] = value


def genSignString(parser):
    uri_str = ''
    for key in sorted(parser.keys()):
        if key == 'app_key':
            continue
        uri_str += "%s=%s&" % (key, parse.quote(str(parser[key]), safe=''))
    sign_str = uri_str + 'app_key=' + parser['app_key']

    hash_md5 = hashlib.md5(sign_str.encode('utf-8'))
    return hash_md5.hexdigest().upper()


class AiPlat(object):
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.data = {}
        self.url_data = ''

    def invoke(self, params):
        try:

            cred = credential.Credential(self.app_id, self.app_key)
            # 实例化一个http选项，可选的，没有特殊需求可以跳过
            httpProfile = HttpProfile()
            httpProfile.endpoint = "iai.tencentcloudapi.com"

            # 实例化一个client选项，可选的，没有特殊需求可以跳过
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            # 实例化要请求产品的client对象,clientProfile是可选的
            client = iai_client.IaiClient(cred, "", clientProfile)

            # 识别图片
            req = models.DetectFaceRequest()
            image_data = base64.b64encode(self.data["image"]).decode("utf-8")

            params = {
                "Image": image_data,
                "NeedFaceAttributes": 1
            }
            req.from_json_string(json.dumps(params))

            # 返回的resp是一个DetectFaceResponse的实例，与请求对象对应
            resp = client.DetectFace(req)

            resp_dict = json.loads(resp.to_json_string())
            resp_dict["ret"] = 0
            return resp_dict
        except Exception as e:
            print(e)
            return {'ret': -1}

    def face_detectface(self,image):

        self.url = url_preffix
        setParams(self.data, 'app_id', self.app_id)
        setParams(self.data, 'app_key', self.app_key)

        image_data = base64.b64encode(image).decode("utf-8")
        setParams(self.data, 'image', image)

        return self.invoke(self.data)

