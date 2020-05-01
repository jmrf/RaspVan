#/bin/bash
docker run -t --rm --name snips \
    --log-driver none \
    -p 9898:1883 \
    -v /home/pi/.asoundrc:/root/.asoundrc \
    -v /opt/snips/config:/opt/snips/config \
    --privileged \
    -v /dev/snd:/dev/snd snipsdocker/platform | grep "ASR captured:"
