build:
	docker compose build

clean:
	docker rmi -f dcagatay/emailrelay
