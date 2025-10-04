ARG BASE_IMAGE=python
ARG UBUNTU_VERSION=3.12-slim
FROM ${BASE_IMAGE}:${UBUNTU_VERSION}
LABEL author="Sreeharsha Veerapalli" email="demouser@gmail.com"
WORKDIR /app
RUN apt update && apt install -y python3-pip jq net-tools tree unzip
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
ADD templates templates
ADD routers routers
COPY main.py main.py
RUN apt-get update && \
    apt-get remove -y python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \
    rm -rf *.zip
EXPOSE 80
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]
CMD ["--port", "80"]
