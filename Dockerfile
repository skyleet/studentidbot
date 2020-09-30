FROM python:3.8-slim
LABEL maintainer="Massimo Santini santini@di.unimi.it"

RUN mkdir /app
ADD requirements.txt studentidbot.py /app/
WORKDIR /app
RUN python3 -m pip install -r requirements.txt

CMD ["python", "studentidbot.py"]