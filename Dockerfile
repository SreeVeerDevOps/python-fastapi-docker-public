FROM python:3.11
LABEL author="Sreeharsha Veerapalli"
WORKDIR /app
COPY requirements.txt requirements.txt
COPY main.py main.py
ADD templates templates
RUN apt update && apt install -y python3-pip jq net-tools tree unzip
RUN pip install -r requirements.txt
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 80
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]
CMD ["--port", "80"]