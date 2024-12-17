import json
import logging
import sys
from typing import Optional

import bluetooth
import click
import coloredlogs

logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level=logging.DEBUG)


@click.command()
@click.option("--uuid", default="616d3aa1-689e-4e71-8fed-09f3c7c4ad91")
@click.option("--addr")
def main(uuid: str, addr: Optional[str] = None):
    if addr:
        logger.info(f"Searching for BT Server with address={addr}...")
    else:
        logger.info("Searching all nearby bluetooth devices for the BT Server")

    # search for the BT Server service
    service_matches = bluetooth.find_service(uuid=uuid, address=addr)

    if len(service_matches) == 0:
        logger.info("Couldn't find the SampleServer service.")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    logger.info(f"Connecting to {name} @ {host}:{port}")

    # Create the client socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))

    logger.info("Connected!")
    while True:
        channels = input("Input channels\t").strip()
        channels = list(map(int, channels.split(" ")))

        mode = input("Input ON (1) / OFF (0)\t")

        sock.send(
            json.dumps({"cmd": "/switch", "channels": channels, "mode": int(mode)})
        )
        res = sock.recv(1024)
        print(res)
        print("-" * 40)

    sock.close()


if __name__ == "__main__":
    main()
