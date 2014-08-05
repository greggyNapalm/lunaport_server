.PHONY: all test redis-db-truncate db-schema-truncate db-schema-populate db-dev-init release clean-pyc docs

VENVNAME = lunaport-ci-test-$(shell date +%s)
GIT_REF = $(shell git show-ref refs/heads/master | cut -d " " -f 1 | cut -c 31-40)
TEST_ENV_VARS = LUNAPORT_ENV='testing' LUNAPORT_CFG='../deploy/lunaport_server.default.cfg' LUNAPORT_WORKER_CFG_PATH='../deploy/lunaport_worker.testing.yaml' MPLCONFIGDIR='/tmp'

PG_DB_NAME = 'lunaport_testing'
REDIS_DB_NUM = '1'
DEB_VERSION = $(shell cat debian/changelog | grep "^python-lunaport-server" | head -1 | tr -d '(|)' | awk '{print $2}')

all: clean-pyc test


redis-db-truncate:
	redis-cli -n $(REDIS_DB_NUM) KEYS '*' | xargs redis-cli -n $(REDIS_DB_NUM) DEL >/dev/null

db-schema-truncate:
	sudo -u postgres psql -d $(PG_DB_NAME) -a -f deploy/sql/drop_schema.sql >/dev/null

db-schema-populate:
	sudo -u postgres psql -d $(PG_DB_NAME) -a -f deploy/sql/schema.sql >/dev/null

db-init: db-schema-truncate db-schema-populate redis-db-truncate
	sudo -u postgres psql -d $(PG_DB_NAME) -a -f deploy/sql/test_data.sql >/dev/null

release:
	python deploy/make-release.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	$(MAKE) -C docs html

pkg:
	VER_EQUALS=$(shell ./deploy/build_scripts/check_versions_consistency.py)
	@echo Someth $(VER_EQUALS)
	#debuild

lint:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 . --max-line-length=99
	@echo ""

test:
	bash -c "cd test/; \
	export $(TEST_ENV_VARS); \
	py.test *;"

ci-test:
	bash -c "python /usr/share/pyshared/virtualenv.py --system-site-packages $(VENVNAME)"
	bash -c ". $(VENVNAME)/bin/activate; \
	pip install pytest; \
	pip install -e git+http://git@github.domain.ru/gkomissarov/lunaport_worker.git#egg=lunaport_worker; \
	pip install -e .; \
	printf '=%.s' {1..100}; echo; \
	echo -e 'VENV: $(VENVNAME)'; \
	python -c \"import lunaport_server; import sys; sys.stdout.write('lunaport_server: ' + lunaport_server.__version__)\"; \
	python -c \"import lunaport_worker; print 'lunaport_worker: ' + lunaport_worker.__version__\"; \
	printf '=%.s' {1..100}; echo; \
	export $(TEST_ENV_VARS); \
	cd test; py.test *;"
