# coding:utf-8
from rest_framework.exceptions import APIException
from .import alipay_config
from .import alipay_core


def make_payment_info(notify_url=None, out_trade_no=None, subject=None, total_fee=None, body=None):
    order_info = {'partner': alipay_config.PID,
                  'service': 'mobile.securitypay.pay',
                  '_input_charset': 'utf-8',
                  'notify_url': notify_url,
                  'payment_type': '1',
                  'seller_id': alipay_config.ALIPAY_ACCOUNT,
                  'out_trade_no': out_trade_no,
                  'subject': subject,
                  'total_fee': total_fee,
                  'body': body}
    return order_info


def make_payment_request_ali(notify_url, out_trade_no, total_fee):
    if float(total_fee) < 0.01:
        raise APIException('充值金额不能小于0.01')
    subject = '余额充值'
    body = '余额可用于支付充电费用'
    payment_info = make_payment_info(notify_url=notify_url, out_trade_no=out_trade_no,
                                     subject=subject, total_fee=total_fee, body=body)
    res = alipay_core.make_payment_request(payment_info)
    return res


def alipay_call_back(request):
    """
    支付宝异步回调
    """
    args = request.data
    check_sign = alipay_core.params_to_query(args)
    params = alipay_core.query_to_dict(check_sign)
    sign = params['sign']
    params = alipay_core.params_filter(params)
    message = alipay_core.params_to_query(params, quotes=False, reverse=False)
    # 验证平台签名
    check_res = alipay_core.check_ali_sign(message, sign)
    if check_res is False:
        print('check_wrong')
        return
    # 验证回调信息真实性
    res = alipay_core.verify_from_gateway({'partner': alipay_config.PID, 'notify_id': params['notify_id']})
    if res is False:
        print('gateway_wrong')
        return
    # 付款完成业务逻辑处理
    trade_status = params['trade_status']
    trade_no = params['out_trade_no']
    if trade_status == 'TRADE_SUCCESS':
        return trade_no
