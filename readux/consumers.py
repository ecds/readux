import json
from urlparse import parse_qs
from django.http import HttpResponse
from channels import Group, Channel
from channels.handler import AsgiHandler
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http


def http_consumer(message):
    # Make standard HTTP response - access ASGI path attribute directly
    response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
    # Encode that response into message format (ASGI)
    for chunk in AsgiHandler.encode_response(response):
        message.reply_channel.send(chunk)


@channel_session_user
def ws_message(message):
    # does this really need to be a group? can we just use the reply channel?
    notify = Group("notify-%s" % message.user.username)
    # check for volume export data (form submission)
    if 'volume_export' in message.content['text']:
        data = json.loads(message.content['text'])
        # parse_qs returns values as lists
        formdata = dict((key, val[0])
                        for key, val in parse_qs(data['volume_export']).iteritems())
        Channel('volume-export').send({
            # has to be json serializable, so send username rather than user
            'user': message.user.username,
            'formdata': formdata,
            # fixme: why is reply channel not automatically set?
            # 'reply_channel': message.reply_channel
        })
    else:
        notify.send({
            "text": "%s" % message.content['text'],
        })


@channel_session_user_from_http
def ws_add(message):
    # Connected to websocket.connect
    Group("notify-%s" % message.user.username).add(message.reply_channel)


@channel_session_user
def ws_disconnect(message):
    # Connected to websocket.disconnect
    Group("notify-%s" % message.user.username).discard(message.reply_channel)


