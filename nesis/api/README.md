# Nesis API
Nesis API module
1. Allows you to chat with data
2. Chats with documents and enhances document knowledge retrival
3. Offers business insights

## Run migrations with
```commandline

alembic -x "url=postgresql://admin:password@localhost:65432/optimai" revision --autogenerate -m "migrations-"`cat version.txt`
```

## Build docker image with
```commandline
docker build -t ametnes/optimai:`cat version.txt` .
```

## Local Development
### Install required version of Python
Install pyenv, a tool the can help one manage multiple Python versions
```commandline
brew install pyenv
```
Using pyenv install python 3.11.5
```commandline
pyenv install 3.11.5
```
Browse to the opmtimAI source code location and set the python version locally using pyenv and create a python virtual environment and activate it.
```commandline
pyenv local 3.11.5
pyenv exec python -m venv .venv
source .venv/bin/activate
```
### Docker services
In a separate terminal window, Start docker services with 
```
docker-compose -f ../../deploy/compose.yml up
```

### Install project dependencies
While in the python virtual environment, run the following to install the required project dependencies
```commandline
pip install -r requirements.txt
```
Sometimes one will incur issues with the postgresSQL adapter, so we will uninstall it and re-install it to avoid any potential issues.
```commandline
pip uninstall psycopg2-binary
pip install psycopg2-binary
```

### Running unit tests
Run unit tests after starting docker services
```commandline
python -m unittest discover -s tests -t tests
```

## Running locally
### Start the service
```commandline
export OPENAI_API_KEY=<your-api-key>
python bin/main.py --config=deploy/config.yml
```

### Test
Set up the datasource settings
```commandline
curl -X POST http://localhost:6000/v1/modules/insights/settings -H 'Content-Type: application/json' -d '{"attributes": {"connection": {"database": "optimai", "host": "localhost", "password": "password", "port": "65432", "user": "admin"}, "engine": "postgres"}, "module": "data", "name": "Northwinds"}'
```
Run predictions query command
```commandline
curl -X POST http://localhost:6000/v1/modules/insights/predictions --header "Content-Type: application/json" --data '{"query": "Which top 15 cities has the most sales revenue"}'
```

