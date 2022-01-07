FROM python:latest
WORKDIR /django
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .