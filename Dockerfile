FROM python:3.10.0

EXPOSE 443


WORKDIR /flask_crud

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /flask_crud


CMD [ "gunicorn", "--certfile", "self_signed/cert.pem", "--keyfile", "self_signed/key.pem", "-b", ":443", "app:app" ]
 
