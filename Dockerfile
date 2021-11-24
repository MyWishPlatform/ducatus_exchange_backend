FROM python:3.7.5

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# RUN pip install --upgrade pip==20.2.4

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app
