import logging
import sys

import bluetooth
import coloredlogs


logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level=logging.DEBUG)

if __name__ == "__main__":
    addr = None

    if len(sys.argv) < 2:
        logger.info(
            "No device specified. Searching all nearby bluetooth devices for "
            "the SampleServer service..."
        )
    else:
        addr = sys.argv[1]
        logger.info("Searching for SampleServer on {}...".format(addr))

    # search for the SampleServer service
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    service_matches = bluetooth.find_service(uuid=uuid, address=addr)

    if len(service_matches) == 0:
        logger.info("Couldn't find the SampleServer service.")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    logger.info('Connecting to "{}" on {}'.format(name, host))

    # Create the client socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))

    logger.info("Connected!")
    while True:
        data = input("Type something...\t")
        if not data:
            break
        sock.send(data)

    sock.close()
