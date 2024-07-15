FROM python:3.9

ENV PYTHONUNBUFFERED=1

RUN mkdir /code
WORKDIR /code

RUN apt-get update && apt-get install -y netcat-traditional
RUN pip install --upgrade pip

ENV PATH="/code/.venv/bin:$PATH"
RUN pip install --upgrade uv
RUN uv venv
RUN uv pip install setuptools
COPY requirements.txt /code/requirements.txt
RUN uv pip install -r requirements.txt

EXPOSE 8000

COPY . /code/

