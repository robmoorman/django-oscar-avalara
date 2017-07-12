clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

install:
	pip install -r requirements.txt
	pip install -e .

sandbox: install
	python sandbox/manage.py migrate
	python sandbox/manage.py loaddata sandbox/fixtures/*.json
	python sandbox/manage.py oscar_import_catalogue sandbox/fixtures/books-catalogue.csv

release:
	python setup.py sdist upload
	git push --tags
