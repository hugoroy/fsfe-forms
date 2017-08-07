from bottle import route, request, redirect, abort
from common import exceptions
from common.configurator import configuration
from common.models import SendData
from common.services import SenderService


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.BadRequest as e:
            abort(400, e.message)
        except exceptions.NotFound as e:
            abort(404, e.message)

    return wrapper


@route('/email', method='GET')
@error_handler
def email_get():
    appid = request.GET.get('appid', None)
    if appid is None:
        raise exceptions.BadRequest
    config = configuration.get_config(appid)
    SenderService.validate_and_send_email(config, SendData.from_request(appid, request.GET, request.url))
    return redirect(config.redirect)


@route('/email', method='POST')
@error_handler
def email_post():
    appid = request.POST.get('appid', None)
    if appid is None:
        raise exceptions.BadRequest
    config = configuration.get_config(appid)
    SenderService.validate_and_send_email(config, SendData.from_request(appid, request.POST, request.url))
    return redirect(config.redirect)


@route('/confirm', method='GET')
@error_handler
def confirmation():
    id = request.GET.get('id', None)
    if id is None:
        raise exceptions.BadRequest
    config = SenderService.confirm_email(id)
    return redirect(config.redirect)
