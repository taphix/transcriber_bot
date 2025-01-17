FROM python:3.11

WORKDIR /cozebot
COPY ./ ./

RUN apt-get -y update
#RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo "Europe/Moscow" > /etc/timezone

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","-u", "main.py"]
