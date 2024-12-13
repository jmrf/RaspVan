from invoke import task

# =============== Base Tasks ================


@task
def print_audio_devices(ctx):
    """List available audio devices"""
    ctx.run("python -m respeaker.get_audio_device_index")

@task
def print_audio_cards(ctx):
    """List available audio devices"""
    ctx.run("cat /proc/asound/cards")
    ctx.run("arecord -L")
    ctx.run("aplay -L")


@task
def build_nlu(ctx):
    from raspvan.version import __version__
    print(f"🔨 Building image: jmrf/nlu-rpi:{__version__}")
    ctx.run(
        f"docker build --rm -t jmrf/nlu-rpi:{__version__}"
        "-f ./nlu/dockerfiles/Dockerfile ./nlu"
    )


@task
def run_pixels(ctx):
    """Run the Respeaker respeaker.pixels:__main__ """
    ctx.run("python -m respeaker.pixels")


@task
def run_relays(ctx):
    """Run the raspvan.workers.relay:__main__"""
    ctx.run("python -m raspvan.workers.relay")


@task
def run_ble_server(ctx):
    ctx.run("docker-compose up -d redis")
    ctx.run("sudo hciconfig hci0 piscan")
    ctx.run("sudo python -m raspvan.ble_server")


@task
def run_hot_word(ctx):
    ctx.run("docker-compose up -d rabbit")
    ctx.run("python -m raspvan.workers.hotword -pt hotword.detected")


@task
def run_asr(ctx):
    """Run the ASR service.
        - Consuming from the topic 'hotword.detected'
        - Publishes to 'asr.complete'
    """
    ctx.run("docker-compose up -d rabbit asr-server")
    ctx.run("python -m raspvan.workers.asr -ct hotword.detected -pt asr.complete")


@task
def run_nlu(ctx):
    """Run the NLU service listening to the ASR.complete trigger"""
    ctx.run("python -m raspvan.workers.nlu -ct asr.complete")
