# coding:utf-8
import rsa
from .import alipay_config
import base64
import urllib
import requests
import hashlib


def params_filter(params):
    """
    去掉不需要验证前面的参数
    """
    ret = {}
    for key, value in params.items():
        if key == 'sign' or key == 'sign_type' or value == '':
            continue
        ret[key] = value
    return ret


def query_to_dict(query):
    """
    将query string转换成字典
    """
    res = {}
    k_v_pairs = query.split('&')
    for item in k_v_pairs:
        sp_item = item.split('=', 1)
        key = sp_item[0]
        value = sp_item[1]
        res[key] = value
    return res


def params_to_query(params, quotes=False, reverse=False):
    """
     生成需要签名的字符串
    """
    query = ''
    for key in sorted(params.keys(), reverse=reverse):
        value = params[key]
        if quotes is True:
            query += str(key) + '=\"' + str(value) + '\"&'
        else:
            query += str(key) + '=' + str(value) + '&'
    query = query[0:-1]
    return query


def make_sign(message):
    """
    签名
    """
    private_key = rsa.PrivateKey._load_pkcs1_pem(alipay_config.RSA_PRIVATE)
    message = message.encode('utf-8')
    sign = rsa.sign(message, private_key, alipay_config.SIGN_TYPE)
    b64sing = base64.b64encode(sign)
    return b64sing


def check_sign(message, sign):
    """
    验证自签名
    """
    sign = base64.b64decode(sign)
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(alipay_config.RSA_PUBLIC)
    return rsa.verify(message, sign, pubkey)


def check_ali_sign(message, sign):
    """
    验证ali签名
    """
    sign = base64.b64decode(sign)
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(alipay_config.RSA_ALIPAY_PUBLIC)
    message = message.encode('utf-8')
    res = False
    try:
        res = rsa.verify(message, sign, pubkey)
    except Exception as e:
        print(e)
        res = False
    return res


def make_payment_request(params_dict):
    """
    构造一个支付请求的信息，包含最终结果里面包含签名
    """
    query_str = params_to_query(params_dict, quotes=True)  # 拼接签名字符串
    sign = make_sign(query_str)  # 生成签名
    sign = urllib.parse.quote_plus(sign)
    res = '%s&sign=\"%s\"&sign_type=\"RSA\"' % (query_str, sign)
    return res


def verify_alipay_request_sign(params_dict):
    """
    验证支付宝回调接口签名
    :param params_dict: 支付宝回调的参数列表
    :return:True or False
    """
    sign = params_dict['sign']
    params = params_filter(params_dict)
    message = params_to_query(params, quotes=False, reverse=False)
    check_res = check_ali_sign(message, sign)
    return check_res


def verify_from_gateway(params_dict):
    """
    从支付宝网关验证请求是否正确
    """
    ali_gateway_url = 'https://mapi.alipay.com/gateway.do?' \
                      'service=notify_verify&partner=%(partner)s&notify_id=%(notify_id)s'
    notify_id = params_dict['notify_id']
    partner = alipay_config.PID
    ali_gateway_url = ali_gateway_url % {'partner': partner, 'notify_id': notify_id}
    res = requests.get(ali_gateway_url)
    if res.text == 'true':
        return True
    return False
