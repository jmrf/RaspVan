import json
import logging

import bluetooth as bt
import coloredlogs

from raspvan.workers.relay import Relayer


logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level=logging.DEBUG)


def process_request(data, relayer):
    logger.debug(f"Rx data: {data}")

    payload = json.loads(data.decode("utf-8"))
    cmd = payload.get("cmd", None)

    if cmd == "disconnect":
        logger.info("Client wanted to disconnect")
        raise KeyboardInterrupt
    elif cmd == "switch":
        c = payload.get("channels", [])
        s = int(payload.get("mode", False))
        return relayer.switch(c, s)
    elif cmd == "read":
        return relayer.state


def advertise():
    server_sock = bt.BluetoothSocket(bt.RFCOMM)
    server_sock.bind(("", bt.PORT_ANY))
    server_sock.listen(1)

    # TODO: Change this UUID
    uuid = "616d3aa1-689e-4e71-8fed-09f3c7c4ad91"

    bt.advertise_service(
        server_sock,
        "RPI-BT-Server",
        service_id=uuid,
        service_classes=[uuid, bt.SERIAL_PORT_CLASS],
        profiles=[bt.SERIAL_PORT_PROFILE],
    )

    return server_sock


def accept_connection(port: int) -> bt.BluetoothSocket:
    logger.info(f"Waiting for connection on RFCOMM channel: {port}")
    # Accept a connection
    client_sock, client_info = server_sock.accept()
    logger.info(f"Accepted connection from {client_info}")

    return client_sock


if __name__ == "__main__":
    """
    For an example for RFCOMM server form pybluez:
    # https://github.com/pybluez/pybluez/blob/master/examples/simple/rfcomm-server.py
    """

    # TODO: Go back to accepting connections after client closes
    # TODO: Accept more than 1 connection

    # Advertise the server
    server_sock = advertise()
    # Wait for an incoming connection
    port = server_sock.getsockname()[1]
    client_sock = accept_connection(port)

    # init the relay controler
    relayer = Relayer()

    while True:
        # TODO: Handle reconnections!
        try:
            data = client_sock.recv(1024)
            ret = process_request(data, relayer)
            client_sock.send(json.dumps(ret))
        except bt.BluetoothError as be:

            if be.errno == 104:
                logger.warning(f"Connection reset by peer...")
                client_sock.close()
                # Accept a new connection
                client_sock = accept_connection(port)
            else:
                logger.debug(be.errno)
                logger.error(f"Something wrong with bluetooth: {be}")

        except KeyboardInterrupt:
            logger.warning("\nDisconnected")
            client_sock.close()
            server_sock.close()
            break
