# time_keeper_webapp
# <img src="./src/static/images/qooqoowithwings_logo.png" width="80" height="45"> A Flask App



## Getting started
Follow the instruction will give you local dev environment


### prerequisite
* Flask
* Python version 3
* database -- mongodb
* webserver -- builtin development webserver
* see requirements.txt


### Installing

* start mongodb 
```
mongod --config /usr/local/etc/mongod.conf
```
* start flask application with https certificate
```
flask run --cert=adhoc
```
* start flask application without https certificate
```
flask run
```

### Running tests
* For test code coverage:
* pytest --cov-report term --cov=src tests/
* pytest --cov-report html --cov-report annotate --cov=src tests/


### Authors
* Jackie Liu
* Marianne Liu
* Larry Liu

## Acknowledgments
```
Give some more examples
```


