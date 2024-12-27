from invoke import task

# =============== DEV Tasks ================


@task
def reformat(ctx):
    """Apply isort and ruff formatting"""
    ctx.run("isort .")
    ctx.run("ruff format .")


@task
def checks(ctx):
    """Run ruff and isort checks"""
    ctx.run(
        """
        echo "👀 Checking code formatting..."
        ruff format --check .
        echo "👀 Checking import formatting..."
        isort --check .
        echo "👀 Checking linting rules..."
        ruff check .
    """
    )


@task
def tests(ctx):
    """Run pytests"""
    ctx.run("pytest --cov --spec -n 2")


# =============== Base Tasks ================
@task
def print_audio_devices(ctx):
    """List available audio devices"""
    ctx.run("python -m respeaker print-audio-devices")


@task
def print_audio_cards(ctx):
    """List available audio devices"""
    print("CARDS: ")
    ctx.run("cat /proc/asound/cards")
    print("🎙️ Input Devices: ")
    ctx.run("arecord -L")
    print("🔊 Output Devices: ")
    ctx.run("aplay -L")


@task
def record(ctx, channels:int = 2, output_name:str = "output-$(date +%F).wav"):
    """Record a Signed 16 bit Little Endian, 16000 Hz WAV"""
    ctx.run(f"acrecord -f S16_LE -r 16000 -c {channels} -t wav {output_name}")


@task
def build_nlu(ctx):
    """Build NLU docker image [jmrf/nlu-rpi]"""
    from raspvan.version import __version__

    print(f"🔨 Building image: jmrf/nlu-rpi:{__version__}")
    ctx.run(
        f"docker build --rm -t jmrf/nlu-rpi:{__version__}"
        "-f ./nlu/dockerfiles/Dockerfile ./nlu"
    )


@task
def pixels(ctx):
    """Run the Respeaker respeaker.pixels:__main__"""
    ctx.run("python -m respeaker.pixels")


@task
def ble_server(ctx):
    """Start Redis and run the BLE (Bluetooth Low Energy) Server.
    First starts REDIS and configured the 1st bluetooth device mode to
    'Page and Inquiry Scan' to accept connections and scan for other devices.
    """
    # Start Redis
    ctx.run("docker-compose up -d redis")
    # Set BT device 0 to 'Page and Inquiry Scan':
    # Page: Respond to connection requests from other Bluetooth devices
    # Inquiry Scan: Actively scan for nearby Bluetooth devices to discover them.
    ctx.run("sudo hciconfig hci0 piscan")
    # Start the BLE server
    ctx.run("sudo python -m raspvan.ble_server")


@task
def relays(ctx):
    """Run the Relay worker"""
    ctx.run("python -m raspvan.workers.relay")


@task
def hot_word(ctx):
    """[DEPRECATED] Start RabbitMQ and run the hotword detection worker and publishes to 'hotword.detected'"""
    ctx.run("docker-compose up -d rabbit")
    ctx.run("python -m raspvan.workers.hotword -pt hotword.detected")


@task
def asr(ctx):
    """[DEPRECATED] Start RabbitMQ and run the ASR worker service.
    - Consuming from the topic 'hotword.detected'
    - Publishes to 'asr.complete'
    """
    ctx.run("docker-compose up -d rabbit asr-server")
    ctx.run("python -m raspvan.workers.asr -ct hotword.detected -pt asr.complete")


@task
def nlu(ctx):
    """[DEPRECATED] Run the NLU worker service listening to the ASR.complete trigger"""
    ctx.run("python -m raspvan.workers.nlu -ct asr.complete")


@task
def run(ctx, device: int = 5):
    """Run a simplified version of the system - no need for RabbitMQ"""
    print("🧑‍🏭 Starting ASR, NLU and Redis docker containers...")
    ctx.run("docker compose up -d asr nlu redis")
    print("🚀 Starting voice assistant pipeline...")
    ctx.run(f"source .venv/bin/activate; python -m raspvan -d {device}")


@task
def toc(ctx):
    """Gnerate a Table Of Contents for the README file"""
    # https://github.com/ekalinin/github-markdown-toc
    ctx.run(
        "find . "
        "! -path '.venv/*' "
        "! -path './kaldi/*' "
        "! -path './external/*' "
        "! -path './hotword/mycroft-precise/*' "
        r"-name README.md -exec gh-md-toc --insert {} \;"
    )
