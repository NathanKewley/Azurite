.PHONY: rebuild
rebuild:
	pip3 uninstall dist/azurite-0.0.4-py3-none-any.whl -y && python3 -m build && pip3 install dist/azurite-0.0.4-py3-none-any.whl

.PHONY: build
build:
	python3 -m build && pip3 install dist/azurite-0.0.4-py3-none-any.whl

.PHONY: test
test:
	pytest

# Not packaging for PyPi for now at least
# .PHONY: uploadToPyPi
# uploadToPyPi:
# 	python3 -m twine upload --repository azurite --repository-url https://upload.pypi.org/legacy/ dist/*
