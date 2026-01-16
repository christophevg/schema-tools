-include .env

# colors

GREEN=\033[0;32m
RED=\033[0;31m
BLUE=\033[0;34m
NC=\033[0m

# test envs

PYTHON_VERSIONS ?= 3.9.18 3.10.13 3.11.12 3.12.10
RUFF_PYTHON_VERSION ?= py311

# base env to create non-test envs from, e.g.: -docs -run
PYTHON_BASE ?= 3.11.12

PROJECT=$(shell basename $(CURDIR))

# by default we assume a project environment with the project/folder name
# this can be overridden using an enrionment variable
ifeq ($(PROJECT_ENV),)
PROJECT_ENV := $(PROJECT)
endif

PACKAGE_NAME=`cat .pypi-template | grep "^package_module_name" | cut -d":" -f2 | xargs`

LOG_LEVEL?=INFO
SILENT?=yes

# if we're inside our own repo folder, use the local module folder, else cli cmd
ifeq ($(wildcard pypi_template),) 
	PYPI_TEMPLATE = pypi-template
else 
	PYPI_TEMPLATE = python -m pypi_template
endif

RUN_CMD?=LOG_LEVEL=$(LOG_LEVEL) python -m $(PACKAGE_NAME)
RUN_ARGS?=

TEST_ENVS=$(addprefix $(PROJECT)-test-,$(PYTHON_VERSIONS))

install: install-envs
	
install-envs: install-env-run install-env-docs install-env-test env
	@echo "👷‍♂️ $(BLUE)installing requirements in $(PROJECT)$(NC)"
	@pyenv local $(PROJECT_ENV)
	@pip install -U pip > /dev/null
	@pip install -U pypi-template > /dev/null
	@pip install -U wheel twine setuptools build > /dev/null

install-env-run:
	@echo "👷‍♂️ $(BLUE)creating virtual environment $(PROJECT)-run$(NC)"
	@pyenv local --unset
	@-pyenv virtualenv $(PYTHON_BASE) $(PROJECT)-run > /dev/null
	@pyenv local $(PROJECT)-run
	@pip install -U pip > /dev/null
	@pip install -r requirements.txt > /dev/null
	@[ -f requirements.run.txt ] && pip install -r requirements.run.txt > /dev/null || true

install-env-docs:
	@echo "👷‍♂️ $(BLUE)creating virtual environment $(PROJECT)-docs$(NC)"
	@pyenv local --unset
	@-pyenv virtualenv $(PYTHON_BASE) $(PROJECT)-docs > /dev/null
	@pyenv local $(PROJECT)-docs
	@pip install -U pip > /dev/null
	@pip install -r requirements.docs.txt > /dev/null
	
install-env-test: $(TEST_ENVS)

$(PROJECT)-test-%:
	@echo "👷‍♂️ $(BLUE)creating virtual test environment $@$(NC)"
	@pyenv local --unset
	@-pyenv virtualenv $* $@ > /dev/null
	@pyenv local $@
	@pip install -U pip > /dev/null
	@pip install -U ruff tox coverage > /dev/null

uninstall: uninstall-envs

uninstall-envs: uninstall-env-test uninstall-env-docs uninstall-env-run env

uninstall-env-test: $(addprefix uninstall-env-test-,$(PYTHON_VERSIONS))

$(addprefix uninstall-env-test-,$(PYTHON_VERSIONS)) uninstall-env-docs uninstall-env-run: uninstall-env-%:
	@echo "👷‍♂️ $(RED)deleting virtual environment $(PROJECT)-$*$(NC)"
	@-pyenv virtualenv-delete -f $(PROJECT)-$*

reinstall: uninstall install

clean-env:
	@echo "👷‍♂️ $(RED)deleting all packages from current environment$(NC)"
	@pip freeze | cut -d"@" -f1 | cut -d'=' -f1 | xargs pip uninstall -y > /dev/null

upgrade:
	@echo "👷‍♂️ $(BLUE)upgrading outdated packages$(NC)"
	@pip list --outdated | tail +3 | cut -d " " -f 1 | xargs -n1 pip install -U

# apply current pypi-template configuration, typically after upgrading it
ifeq ($(wildcard pypi_template),)
apply: env
	$(PYPI_TEMPLATE) verbose apply
else
apply: RUN_CMD=$(PYPI_TEMPLATE)
apply: RUN_ARGS=verbose apply
apply: run
endif

# apply and reinstall
update: apply uninstall-env-run install-env-run

# env switching

env-%:
	@echo "👷‍♂️ $(BLUE)activating $* environment$(NC)"
	@pyenv local $(PROJECT)-$*

env:
	@echo "👷‍♂️ $(BLUE)activating project environment$(NC)"
	@pyenv local $(PROJECT_ENV)
	@$(PYPI_TEMPLATE) status > /dev/null

env-test:
	@echo "👷‍♂️ $(BLUE)activating test environments$(NC)"
	@pyenv local $(TEST_ENVS)
	
# functional targets

run: env-run
	@echo "👷‍♂️ $(BLUE)running$(GREEN) $(RUN_CMD) $(RUN_ARGS)$(NC)"
	@$(RUN_CMD) $(RUN_ARGS)

test: lint tox env
coverage: lint tox coverage-report env

tox: env-test
	@echo "👷‍♂️ $(BLUE)performing tests$(NC)"
ifeq ($(SILENT),yes)
	@tox -q
else
	@tox
endif

coverage-report: env-test
	@echo "👷‍♂️ $(BLUE)creating coverage reports$(NC)"
	@coverage report
	@coverage html
	@coverage lcov

lint: env-test
	@ruff check --target-version=$(RUFF_PYTHON_VERSION) .

docs: env-docs
	@echo "👷‍♂️ $(BLUE)building documentation$(NC)"
	@cd docs; make html
	@open docs/_build/html/index.html

# packaging targets

publish-test: env dist
	@echo "👷‍♂️ $(BLUE)publishing to PyPI test$(NC)"
	@twine upload --repository testpypi dist/*

publish: env dist
	@echo "👷‍♂️ $(BLUE)publishing to PyPI$(NC)"
	@twine upload dist/*

dist: env dist-clean
	@echo "👷‍♂️ $(BLUE)building distribution$(NC)"
	@python -m build > /dev/null

dist-clean: clean
	@rm -rf dist build *.egg-info

clean:
	@find . -type f -name "*.backup" | xargs rm

.PHONY: dist docs test

# include optional a personal/local touch

-include Makefile.mak
