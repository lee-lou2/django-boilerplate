# Django Project Makefile

# Activate virtual environment and set python executable
PYTHON = ../.venv/bin/python

.PHONY: run test load-test

# 1. Run development server
dev:
	@echo "Starting development server..."
	$(PYTHON) manage.py runserver

# 2. Run unit tests
test:
	@echo "Running unit tests..."
	$(PYTHON) manage.py test

# 3. Run server with test settings and perform load testing
load-test:
	@echo "Starting server with test settings for load testing..."
	$(PYTHON) manage.py migrate --settings=django_project.settings.test && \
	$(PYTHON) manage.py runserver --settings=django_project.settings.test & \
	SERVER_PID=$$! && \
	sleep 5 && \
	$(PYTHON) -m locust -f tests/locust/locustfile.py --headless -u 10 -r 5 -t 30s --host=http://127.0.0.1:8000 --html=locust_report.html && \
	pkill -P $$SERVER_PID && \
	rm -f db.test.sqlite3
	@echo "Load test finished. Report saved to locust_report.html"