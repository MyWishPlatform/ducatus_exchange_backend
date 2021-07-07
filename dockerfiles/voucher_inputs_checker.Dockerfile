FROM python:3.7.2

WORKDIR /www

ENV PYTHONUNBUFFERED=1

COPY requirements.txt /www/requirements.txt
RUN pip install -r requirements.txt

COPY . /www
CMD ["python", "inputs_checker.py"]