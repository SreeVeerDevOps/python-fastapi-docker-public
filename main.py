from fastapi import FastAPI, Request, UploadFile
import uvicorn
import requests, socket, platform
from routers import aws, azure, pokemon
from fastapi.templating import Jinja2Templates
import boto3
import json
import os
import requests
import datetime
import mysql.connector
from dotenv import load_dotenv, find_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.mgmt.compute import ComputeManagementClient
from platform import python_version

key_vault_name = "azureb50kv"
key_vault_uri = f"https://azureb50kv.vault.azure.net"
secret_name1 = "aws-access-key"
secret_name2 = "aws-secret-key"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_uri, credential=credential)
retrieved_secret1 = client.get_secret(secret_name1)
retrieved_secret2 = client.get_secret(secret_name2)

os.environ['AWS_ACCESS_KEY_ID'] = retrieved_secret1.value
os.environ['AWS_SECRET_ACCESS_KEY'] = retrieved_secret2.value

load_dotenv()

app = FastAPI()

con_name = os.getenv("HOSTNAME")
b_name = os.getenv("DEPLOYMENT_BRANCH")
app_name = os.getenv("APP_NAME")
if b_name:
    branch_name = b_name
else:
    branch_name = 'NOT-A-GIT-REPO'

if app_name is None:
    app_name = "FASTAPI-DEMO-APP-DEFAULT"
else:
    app_name = app_name

python_version = os.getenv("PYTHON_VERSION")

IP = requests.get('https://api.ipify.org').content.decode('utf8')

templates = Jinja2Templates(directory="templates")

@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "name": app_name,
        "container_id": con_name,
        "python_version": python_version,
        "IP": IP,
        "branch_name": branch_name
        })

app.include_router(aws.router)
app.include_router(azure.router)
app.include_router(pokemon.router)
    
