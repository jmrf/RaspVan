.PHONY: rpi-install print-audio-devices print-audio-cards build-nlu \
	run-relays run-ble-server run-hotword run-asr run-nlu \
	clean formatter lint types pyupgrade readme-toc test clean tag list
.SILENT: rpi-install print-audio-devices print-audio-cards build-nlu \
	run-relays run-ble-server run-hotword run-asr run-nlu \
	clean formatter lint types pyupgrade readme-toc test clean tag list


SHELL := /bin/bash


help:
	@echo "    rpi-install"
	@echo "        Install requirements"
	@echo "    print-audio-devices"
	@echo "        Print a list of detected audio devices"
	@echo "    print-audio-cards"
	@echo "        Print a list of detected audio cards"
	@echo "    build-nlu"
	@echo "        Build the NLU docker image"
	@echo "    run-relays"
	@echo "        Run a relay worker test control logic"
	@echo "    run-ble-server"
	@echo "        Run the Bluetooth server (plays with the Android app)"
	@echo "    run-hotword"
	@echo "        Run the hotword detection worker"
	@echo "    run-asr"
	@echo "        Run the ASR worker"
	@echo "    run-nlu"
	@echo "        Run the NLU worker"
	@echo "    clean"
	@echo "        Remove Python/build artifacts."
	@echo "    formatter"
	@echo "        Apply black formatting to code."
	@echo "    lint"
	@echo "        Lint code with flake8, and check if black formatter should be applied."
	@echo "    types"
	@echo "        Check for type errors using pytype."
	@echo "    pyupgrade"
	@echo "        Run pyupgrade tool"
	@echo "    readme-toc"
	@echo "        Create README Table of Contents (ToC)"
	@echo "    test"
	@echo "        Run python tests"
	@echo "    tag"
	@echo "        Create a git tag with the current version"
	@echo "    list"
	@echo "        List all of this Makefile targets"


.ONESHELL:
rpi-install:
	/usr/bin/python3 -m venv .venv/
	source .venv/bin/activate
	pip install requirements.txt

.ONESHELL:
print-audio-devices:
	source .venv/bin/activate
	python -m respeaker.get_audio_device_index

.ONESHELL:
print-audio-cards:
	cat /proc/asound/cards
	arecord -L
	aplay -L

.ONESHELL:
build-nlu:
	source .venv/bin/activate
	VERSION=$$( python -c 'from raspvan.version import __version__; print(__version__)' )
	echo "** Building image: jmrf/nlu-rpi:$$VERSION"
	docker build --squash --rm \
		-t jmrf/nlu-rpi:$$VERSION \
		-f ./nlu/dockerfiles/Dockerfile \
		./nlu

.ONESHELL:
run-relays:
	source .venv/bin/activate
	python -m raspvan.workers.relay

.ONESHELL:
run-ble-server:
	docker-compose up -d redis
	sudo hciconfig hci0 piscan
	sudo .venv/bin/python -m raspvan.ble_server

.ONESHELL:
run-hotword:
	source .venv/bin/activate
	docker-compose up -d rabbit
	python -m raspvan.workers.hotword -pt hotword.detected

.ONESHELL:
run-asr:
	source .venv/bin/activate
	docker-compose up -d rabbit asr-server
	python -m raspvan.workers.asr \
		-ct hotword.detected -pt asr.complete

run-nlu:
	source ./nlu/.venv/bin/activate \
		&& python -m raspvan.workers.nlu -ct asr.complete

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	find . -name 'README.md.*' -exec rm -f  {} +
	rm -rf build/
	rm -rf .pytype/
	rm -rf dist/
	rm -rf docs/_build
	# rm -rf *egg-info
	# rm -rf pip-wheel-metadata

formatter:
	black . --extend-exclude hotword/mycroft-precise/

lint:
	flake8 .
	black --check .  --exclude external

types:
	# https://google.github.io/pytype/
	pytype --keep-going . --exclude external

pyupgrade:
	find .  -name '*.py' | grep -v 'proto\|eggs\|docs' | xargs pyupgrade --py36-plus

readme-toc:
	# https://github.com/ekalinin/github-markdown-toc
	find . \
		! -path '.venv/*' \
		! -path './kaldi/*' \
		! -path './external/*' \
		! -path './hotword/mycroft-precise/*' \
		-name README.md \
		-exec gh-md-toc --insert {} \;

test: clean
	# OMP_NUM_THREADS can improve overral performance using one thread by process (on tensorflow), avoiding overload
	OMP_NUM_THREADS=1 pytest tests -n $(JOBS) --cov gnes

.ONESHELL:
tag:
	source .venv/bin/activate
	git tag $$( python -c "from raspvan.version import __version__; print(__version__)" )
	git push --tags

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
