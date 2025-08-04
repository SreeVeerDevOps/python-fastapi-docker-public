from fastapi import FastAPI, Request, UploadFile
from fastapi import APIRouter
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

key_vault_name = "blueboxvault"
key_vault_uri = f"https://blueboxvault.vault.azure.net"
secret_name1 = "aws-access-key"
secret_name2 = "aws-secret-key"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_uri, credential=credential)
retrieved_secret1 = client.get_secret(secret_name1)
retrieved_secret2 = client.get_secret(secret_name2)

os.environ['AWS_ACCESS_KEY_ID'] = retrieved_secret1.value
os.environ['AWS_SECRET_ACCESS_KEY'] = retrieved_secret2.value

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/awsdemo", tags=["AWS"])
def aws_router():
    return {
        "message": "THIS IS AWS ROUTER IN FILE aws.py"
    }
    
@router.get('/certs/{region}', tags=["AWS"])
def get_certs(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_certs = acm_conn.list_certificates().get('CertificateSummaryList')
    return templates.TemplateResponse("certs.html", {"request": request, "name": "Certificates List", "all_certs": all_certs})
    
@router.get('/certs/{region}/expired', tags=["AWS"])
def get_certs_expired(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_cert = acm_conn.list_certificates().get('CertificateSummaryList')
    expited_certs = [cert for cert in all_cert if cert['Status'] == 'EXPIRED']    
    return templates.TemplateResponse("certs.html", {"request": request, "name": "Expired Certificates List", "all_certs": expited_certs})
 
 
@router.get("/getvpc", tags=["AWS"])
def get_vpc_id_list(region)->list:
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_vpcs()
    vpc_id_list = []
    for vpc in response['Vpcs']:
        vpc_id_list.append(vpc['VpcId'])
    print(vpc_id_list)
    return vpc_id_list

@router.get('/vpcs/{region}', tags=["AWS"])
def get_vpcs(request: Request, region: str):
     ec2_conn = boto3.client('ec2',region_name=region)
     all_vpcs = ec2_conn.describe_vpcs().get('Vpcs')
     vpc_id = [VPC['VpcId'] for VPC in all_vpcs]
     vpc_cidr = [VPC['CidrBlock'] for VPC in all_vpcs]
     vpc_info = dict(zip(vpc_id, vpc_cidr))
     return templates.TemplateResponse("vpc.html", {"request": request, "name": "VPC INFO", "vpc_dict": vpc_info})
    
    
@router.get("/s3/{region}", tags=["AWS"])
def get_s3_buckets(request: Request, region: str)->list:
    s3 = boto3.client('s3', region_name=region)
    bucket_list = s3.list_buckets().get('Buckets')
    total_bucket_count = len(bucket_list)
    return templates.TemplateResponse("s3.html", {"request": request, "total_bucket_count": total_bucket_count, "name": "S3 BUCKET INFO", "bucket_list": bucket_list})

@router.get("/checks3", tags=["AWS"])
def check_bucket(bucket_name,region):
    s3 = boto3.client('s3', region_name=region)
    response = s3.list_buckets()
    print(response)
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    if bucket_name in buckets:
        return f"{bucket_name} exists"
    else:
        return f"{bucket_name} does not exist"
    
@router.get("/files", tags=["AWS"])
def list_files_in_bucket(bucket_name, region):
    s3 = boto3.client('s3', region_name=region)
    response = s3.list_objects_v2(Bucket=bucket_name)
    file_list = []
    for obj in response['Contents']:
        file_list.append(obj['Key'])
    print(file_list)
    return file_list
