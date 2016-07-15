from channels.routing import route
from readux.consumers import ws_message, ws_add, ws_disconnect
from readux.books.consumers import volume_export

channel_routing = [
    # django will handle http by default
    route("websocket.connect", ws_add),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
    route("volume-export", volume_export),
]