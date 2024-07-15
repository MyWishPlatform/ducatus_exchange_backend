FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENV PATH="/app/.venv/bin:$PATH"
RUN pip install uv==0.1.42
RUN uv venv
RUN uv pip install setuptools

COPY requirements.txt /app/requirements.txt
RUN uv pip install -r requirements.txt

COPY . /app
