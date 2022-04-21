.PHONY: clean test lint init check-readme

help:
	@echo "    train-lm"
	@echo "        Train the speech language model"
	@echo "    train-nlu"
	@echo "        Train the NLU engine"
	@echo "    train-dialogue"
	@echo "        Train the dialogue-engine"
	@echo "    train-mai"
	@echo "        Train the MAI engine"
	@echo "    run-nlu"
	@echo "        Run the NLU engine"
	@echo "    run-dialogue"
	@echo "        Run the Dialogue engine"
	@echo "    run-mai"
	@echo "        Run the MAI engine"
	@echo "    run-actions"
	@echo "        Run the Action Server"
	@echo "    run-response-server"
	@echo "        Run the Response Server"
	@echo "    build-docker-actions"
	@echo "        Build Docker image for the Action Server"
	@echo "    clean"
	@echo "        Remove Python/build artifacts."
	@echo "    formatter"
	@echo "        Apply black formatting to code."
	@echo "    lint"
	@echo "        Lint code with flake8, and check if black formatter should be applied."
	@echo "    types"
	@echo "        Check for type errors using pytype."
	@echo "    test"
	@echo "        Run pytest on tests/."



rpi-install:
	/usr/bin/python3 -m venv .venv/
	source .venv/bin/activate
	pip install requirements.txt

print-audio-devices:
	python -m respeaker.get_audio_device_index

# print-audio-cards:
# 	cat /proc/asound/cards
# 	arecord -L
# 	aplay -L

run-hotword:
	docker-compose up -d rabbit
	python -m raspvan.workers.hotword -t hotword

run-asr:
	docker-compose up -d rabbit
	python -m raspvan.workers.asr -t hotword

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
	black common raspvan scripts respeaker \
		--exclude .venv/ \
		--exclude kaldi/ \
		--exclude external/ \
		--exclude hotword/mycroft-precise/

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

tag:
	git tag $$( python -c 'import src; print(raspvan.__version__)' )
	git push --tags

setup-dvc:
	# Configure https://mai-dvc.ams3.digitaloceanspaces.com as remote storage
	dvc init
	dvc remote add -d $(remote) s3://mai-dvc/$(remote)
	dvc remote modify $(remote) endpointurl https://ams3.digitaloceanspaces.com
