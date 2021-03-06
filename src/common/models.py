import json


class Serializable:
    def toJSON(self):
        pass

    @classmethod
    def fromJSON(cls, data):
        pass


class SendData(Serializable):
    def __init__(self, appid, send_from, send_to, reply_to, subject, template, confirm, confirmed,
                 request_data, url):
        self.url = url
        self.request_data = request_data
        self.confirmed = confirmed
        self.appid = appid
        self.send_from = send_from
        self.send_to = send_to
        self.reply_to = reply_to
        self.subject = subject
        self.template = template
        self.confirm = confirm

    @classmethod
    def from_request(cls, appid: str, data: dict, url: str):
        send_from = data.get('from', None)
        send_to = data.get('to', None)
        if send_to is not None:
            send_to = send_to.split(',')
        reply_to = data.get('replyto', None)
        subject = data.get('subject', None)
        template = data.get('template', None)
        confirm = data.get('confirm', None)
        request_data = dict()
        for name in data:
            if name in ['from', 'to', 'replyto', 'subject', 'template', 'appid']:
                continue
            request_data[name] = getattr(data, name)
        return cls(appid, send_from, send_to, reply_to, subject, template, confirm, False, request_data, url)

    def toJSON(self):
        return json.dumps(self.__dict__)

    @classmethod
    def fromJSON(cls, data):
        json_data = json.loads(data)
        appid = json_data.get('appid', None)
        send_from = json_data.get('send_from', None)
        send_to = json_data.get('send_to', None)
        reply_to = json_data.get('reply_to', None)
        subject = json_data.get('subject', None)
        template = json_data.get('template', None)
        confirm = json_data.get('confirm', None)
        delivered = json_data.get('delivered', False)
        request_data = json_data.get('request_data', None)
        url = json_data.get('url', None)
        return cls(appid, send_from, send_to, reply_to, subject, template, confirm, delivered, request_data, url)
