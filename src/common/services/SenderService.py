import uuid
from typing import Optional

from background import tasks
from common import exceptions
from common.config import CONFIRMATION_EXPIRATION_SECS
from common.configurator import AppConfig, configuration
from common.models import SendData
from common.services import SenderStorageService


def validate_and_send_email(config: AppConfig, data: SendData):
    if config is None:
        raise exceptions.NotFound('Configuration not found for this AppId')
    if config.send_from is None and data.send_from is None:
        raise exceptions.BadRequest('\"From\" is required')
    if (config.send_to is None or not config.send_to) and (data.send_to is None or not data.send_to):
        raise exceptions.BadRequest('\"To\" is required')
    if config.subject is None and data.subject is None:
        raise exceptions.BadRequest('\"Subject\" is required')
    if config.content is None and config.template is None and data.template is None and data.content is None:
        raise exceptions.BadRequest('\"Content\" or \"Template\" is required')

    if config.confirm:
        if data.confirm is None:
            raise exceptions.BadRequest('\"Confirm\" address is required')
        id = SenderStorageService.store_data(data, CONFIRMATION_EXPIRATION_SECS)
        deliver_confirmation(id)
    else:
        id = SenderStorageService.store_data(data)
        deliver_email(id)


def confirm_email(id: str) -> Optional[AppConfig]:
    id = uuid.UUID(id)
    data = SenderStorageService.resolve_data(id)
    if data is None:
        raise exceptions.NotFound('Confirmation ID is Not Found')
    if not data.confirmed:
        data.confirmed = True
        SenderStorageService.update_data(id, data)
        deliver_email(id)
    config = configuration.get_config(data.appid)
    if config is None:
        raise exceptions.NotFound('Configuration not found for this AppId')
    return config


def pingpong():
    id = uuid.uuid4()
    result = tasks.pingpong.apply_async((id.__str__(),))
    return result.get(timeout=10)


def deliver_confirmation(id: uuid.UUID):
    tasks.schedule_confirmation.apply_async((id.__str__(),))


def deliver_email(id: uuid.UUID):
    tasks.schedule_email.apply_async((id.__str__(),))
