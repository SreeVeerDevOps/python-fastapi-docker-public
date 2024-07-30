import boto3
import json
import os
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn
import mysql.connector
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.mgmt.compute import ComputeManagementClient
from platform import python_version

load_dotenv()

app = FastAPI()

con_name = os.getenv("HOSTNAME")
python_version = os.getenv("PYTHON_VERSION")

templates = Jinja2Templates(directory="templates")

@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "name": "Azure B45",
        "container_id": con_name,
        "python_version": python_version
        })

@app.get("/")
def homepage():
  return f'Your API Request Is Processed By The Container ID {con_name} running Python Version {python_version}.'

import requests

@app.get('/certs/{region}')
def get_certs(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_certs = acm_conn.list_certificates().get('CertificateSummaryList')
    return templates.TemplateResponse("certs.html", {"request": request, "name": "Certificates List", "all_certs": all_certs})

import datetime    
@app.get('/certs/{region}/expired')
def get_certs_expired(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_cert = acm_conn.list_certificates().get('CertificateSummaryList')
    expited_certs = [cert for cert in all_cert if cert['Status'] == 'EXPIRED']    
    return templates.TemplateResponse("certs.html", {"request": request, "name": "Expired Certificates List", "all_certs": expited_certs})
 
 
@app.get("/getvpc")
def get_vpc_id_list(region)->list:
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_vpcs()
    vpc_id_list = []
    for vpc in response['Vpcs']:
        vpc_id_list.append(vpc['VpcId'])
    print(vpc_id_list)
    return vpc_id_list

@app.get('/vpcs/{region}')
def get_vpcs(request: Request, region: str):
     ec2_conn = boto3.client('ec2',region_name=region)
     all_vpcs = ec2_conn.describe_vpcs().get('Vpcs')
     vpc_id = [VPC['VpcId'] for VPC in all_vpcs]
     vpc_cidr = [VPC['CidrBlock'] for VPC in all_vpcs]
     vpc_info = dict(zip(vpc_id, vpc_cidr))
     return templates.TemplateResponse("vpc.html", {"request": request, "name": "VPC INFO", "vpc_dict": vpc_info})
    
    
@app.get("/s3/{region}")
def get_s3_buckets(request: Request, region: str)->list:
    s3 = boto3.client('s3', region_name=region)
    bucket_list = s3.list_buckets().get('Buckets')
    total_bucket_count = len(bucket_list)
    return templates.TemplateResponse("s3.html", {"request": request, "total_bucket_count": total_bucket_count, "name": "S3 BUCKET INFO", "bucket_list": bucket_list})

@app.get("/checks3")
def check_bucket(bucket_name,region):
    s3 = boto3.client('s3', region_name=region)
    response = s3.list_buckets()
    print(response)
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    if bucket_name in buckets:
        return f"{bucket_name} exists"
    else:
        return f"{bucket_name} does not exist"
    
@app.get("/files")
def list_files_in_bucket(bucket_name, region):
    s3 = boto3.client('s3', region_name=region)
    response = s3.list_objects_v2(Bucket=bucket_name)
    file_list = []
    for obj in response['Contents']:
        file_list.append(obj['Key'])
    print(file_list)
    return file_list

@app.get('/pokemon')
def get_pokemon(request: Request):
    URL = requests.get('https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0')
    POKEMON_LIST = URL.json()['results']
    return templates.TemplateResponse("pokemon.html", {"request": request, "name": "Hello World", "POKEMON_LIST": POKEMON_LIST})
        

@app.get('/pokemon/{name}')
def get_pokemon_name(request: Request, name: str):
    URL = requests.get('https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0')
    POKEMON_LIST = URL.json()['results']
    POKEMON_LIST_NAME = [ pokemon['name'] for pokemon in POKEMON_LIST]
    #print(POKEMON_LIST_NAME)
    if name in POKEMON_LIST_NAME:
        print(f'Pokemon {name} Exists...')
        for pokemon in POKEMON_LIST:
            if pokemon['name'] == name:
                pokemon_name = pokemon['name']
                pokemon_url = pokemon['url']
                return templates.TemplateResponse("pokesingle.html", {"request": request, "name": "Hello World", "pokemon_name": pokemon_name, "pokemon_url": pokemon_url})
    else:
      print(f'Pokemon {name} Dont Exists...')
      return templates.TemplateResponse("pokesingle.html", {"request": request, "name": "Hello World", "pokemon_name": 'Pokemon Name Not Found', "pokemon_url": 'Pokemon URL Not Found'}) 

    
