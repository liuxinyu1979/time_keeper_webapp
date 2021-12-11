FROM python:3.6.5

# Run: docker build -t time_keeper_webapp -f docker/Dockerfile . in time_keeper_webapp directory
# then run: docker run time_keeper_webapp

# docker run -d -p 27019:27017 -v /Users/xiliu/sandpit/pypit/screen_time_keeper/database:/data/db mvertes/alpine-mongo
# docker-compose -f docker/docker-compose.yml up --build

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "main.py"]

