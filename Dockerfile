FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
LABEL maintainer="Matthew Vincent <mattjvincent@gmail.com>" \
	  version="1.0.1"

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./ensimpl /app/ensimpl

#Export path for ensimpl
ENV ENSIMPL_DIR=/data
ENV MODULE_NAME="ensimpl.main"