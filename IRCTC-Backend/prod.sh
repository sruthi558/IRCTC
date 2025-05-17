source env/bin/activate
waitress-serve --port=8000 --call 'wsgi:create_app'
