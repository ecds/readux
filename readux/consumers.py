'''
Standard websocket consumer methods for use with django channels.

'''
import json
from urlparse import parse_qs
from channels import Group, Channel
from channels.auth import http_session_user, channel_session_user, \
    channel_session_user_from_http


@channel_session_user
def ws_message(message):
    '''Send a message via web sockets.  Currently uses a group identified by
    notify-username.  When a volume export form submission is received,
    the message is handed off to the volume-export channel, which is handled
    by :mod:`readux.books.consumers`.  Otherwise, messages are routed to the
    user notification channel.'''
    # does this really need to be a group? can we just use the reply channel?
    notify = Group("notify-%s" % message.user.username)
    # check for volume export data (form submission)
    if 'volume_export' in message.content['text']:
        data = json.loads(message.content['text'])
        # parse_qs returns values as lists
        formdata = dict((key, val[0])
                        for key, val in parse_qs(data['volume_export']).iteritems())
        # breaking changes as of channels 1.0
        # need to specify immediately=True to send messages before the consumer completes to the end
        Channel('volume-export').send({
            # has to be json serializable, so send username rather than user
            'user': message.user.username,
            'formdata': formdata,
            # fixme: why is reply channel not automatically set?
            # 'reply_channel': message.reply_channel
        }, immediately=True)
    else:
        notify.send({
            "text": "%s" % message.content['text'],
        }, immediately=True)


@channel_session_user_from_http
def ws_add(message):
    # Backward compatability
    # https://channels.readthedocs.io/en/stable/releases/1.0.0.html
    # Accept connection
    '''Connected to websocket.connect'''
    message.reply_channel.send({"accept": True})
    Group("notify-%s" % message.user.username).add(message.reply_channel)


@channel_session_user
def ws_disconnect(message):
    '''Connected to websocket.disconnect'''
    Group("notify-%s" % message.user.username).discard(message.reply_channel)
