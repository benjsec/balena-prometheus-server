FROM python:3.7-stretch

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./discover.py" ]
