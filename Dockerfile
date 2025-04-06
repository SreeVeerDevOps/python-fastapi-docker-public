FROM python:3.12
LABEL author="Sreeharsha Veerapalli" email="itsreeharsha@gmail.com"
WORKDIR /app
RUN apt update && apt install -y python3-pip jq net-tools tree unzip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD templates templates
ADD routers routers
COPY main.py main.py
EXPOSE 80
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]
CMD ["--port", "80"]
