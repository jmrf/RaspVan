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


train-lm:
	cd ASR && \
		# ./prepare_lm_data.sh && \
		./train_lm.sh && \
		cd ..

train-nlu:
	./scripts/bootstrap_nlu.sh

train-dialogue:
	./scripts/bootstrap_dialogue.sh

train-mai:
	./scripts/bootstrap_mai.sh

run-nlu:
	./scripts/launch_nlu_server.sh

run-dialogue:
	./scripts/launch_dialogue_server.sh

run-mai:
	./scripts/launch_mai_server.sh

run-actions:
	./scripts/launch_action_server.sh

run-response-server:
	./scripts/launch_response_server.sh

build-docker-actions:
	# Examples:
	# make build-docker-actions mode=dev version=0.1
	# make build-docker-actions mode=full version=0.1
	docker build --rm \
		-f actions/$(mode)Actions.Dockerfile \
		-t ${PROJECT}-$(mode)-actions:$(version) \
		-t ${PROJECT}-$(mode)-actions:latest \
		actions

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf .pytype/
	rm -rf dist/
	rm -rf docs/_build

formatter:
	black ASR hotword phiona scripts --exclude external

lint:
	flake8 ASR hotword phiona tests
	black --check ASR hotword phiona scripts  --exclude external

types:
	pytype --keep-going ASR hotword phiona scripts  --exclude external
