FROM python:3.6.5

# Run: "docker build -t time_keeper_webapp -f docker/Dockerfile ."" in time_keeper_webapp directory
# eg: (time_keeper_webapp) xiliu-macOS:time_keeper_webapp xiliu$ docker build -t time_keeper_webapp -f docker/Dockerfile .
# then run: docker run -d -p 5000:5000 <docker image>
# (time_keeper_webapp) xiliu-macOS:src xiliu$ docker run -d -p 5000:5000 5c6c7a8cc323

# docker run -d -p 27019:27017 -v /Users/xiliu/sandpit/pypit/screen_time_keeper/database:/data/db mvertes/alpine-mongo
# docker-compose -f docker/docker-compose.yml up --build

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt
RUN apt-get update -y
RUN apt-get install -y vim
RUN apt-get install -y net-tools

EXPOSE 5000
ENV FLASK_APP=src/app.py
# need the "--host", "0.0.0.0" so that access from localhost is possible
CMD ["flask", "run", "--host", "0.0.0.0"]


