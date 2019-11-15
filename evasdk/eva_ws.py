import websockets


async def ws_connect(host_ip, session_token, data_mode="object"):
    """
    Connect is an async function that returns a connected Eva websocket

    Connect needs to be run from a asyncio event_loop and retuns a
    websockets.Websocket object. Using this you can manually call .recv()
    and .send(), make sure to also .close() when you are finished to clean
    up the websocket connection.
    """
    host_uri = 'ws://{}/api/v1/data/stream'.format(host_ip)
    subprotocols = ['SessionToken_{}'.format(session_token), data_mode]

    ws = await websockets.client.connect(host_uri, subprotocols=subprotocols)
    return ws
