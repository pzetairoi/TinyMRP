#FROM python:3.8-alpine as bigimage
FROM python:3.8.10-slim-buster

## Add repositories for mongodb alpine, this did not work
# RUN echo ‘http://dl-cdn.alpinelinux.org/alpine/v3.8/main’ >> /etc/apk/repositories
# RUN echo ‘http://dl-cdn.alpinelinux.org/alpine/v3.8/community’ >> /etc/apk/repositories

#RUN apk --update  add bash nano libxml2-dev libxslt-dev g++ gcc linux-headers musl-dev
#RUN apk --update  add mongodb
RUN apt-get update && apt-get install -y bash nano libxml2-dev libxslt-dev g++ gcc 
#linux-headers musl-dev

# Install MongoDB
RUN apt-get update && apt-get install -y gnupg curl
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add -
RUN echo "deb [arch=amd64] https://repo.mongodb.org/apt/debian buster/mongodb-org/4.2 main" | tee /etc/apt/sources.list.d/mongodb-org-4.2.list
RUN apt-get update && apt-get install -y mongodb-org
RUN apt-get install -y libgl1-mesa-glx libsm6 libxext6


ENV FLASK_APP flasky.py
ENV FLASK_CONFIG production

#RUN adduser -D flasky
#USER flasky

#WORKDIR /home/flasky

COPY docker_reqs.txt docker_reqs.txt

RUN pip install --upgrade pip setuptools wheel
RUN python -m venv venv
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r docker_reqs.txt

COPY . .

#COPY app app
#COPY migrations migrations
#COPY flasky.py config.py boot.sh ./


#RUN flask run --host=0.0.0.0

RUN pip install -U python-dotenv click flask_migrate flask_bootstrap
ENV FLASK_ENV=development
ENV FLASK_APP=flasky.py
RUN export FLASK_APP=flasky.py
RUN export FLASK_ENV=development

RUN chmod -R +777 data-dev.sqlite

COPY data-dev.sqlite data.sqlite


RUN apt-get install -y nginx git samba

# Import the collection template into the mongodb,
# the template is located on the project folder and it is in
# app\static\misc\TinyMRP_mongodb_template.zip . The database
# is called TinyMRP, import everything into the database
COPY app/static/misc/TinyMRP_mongodb_template.zip .
RUN apt-get install -y unzip
#RUN unzip TinyMRP_mongodb_template.zip -d /data/db
#RUN mongorestore --db TinyMRP /data/db/TinyMRP



#Run flask dev by now
#CMD [ "python3", "-m" , "flasky", "run", "--host=0.0.0.0"]
CMD [ "flask", "run", "--host=0.0.0.0","--debugger"]




# run-time configuration
EXPOSE 5000 80 8080 27017
#ENTRYPOINT ["./boot.sh"]
