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


credential = DefaultAzureCredential()

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
    
