VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

build:
	docker compose build

svc: build
	docker compose up -d
	echo "Wait for services to come up..."
	sleep 5

test: svc $(VENV)/bin/activate
	. $(VENV)/bin/activate
	SMTP_PORT=9025 $(PYTHON) test.py
	docker compose down --remove-orphans --volumes

clean:
	rm -rf $(VENV)
