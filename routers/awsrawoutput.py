import boto3
from fastapi import APIRouter
from fastapi import FastAPI, Request, UploadFile
from fastapi.templating import Jinja2Templates
import requests
router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get('/raw/health', tags=["AWS-RAW"])
def health():
    return 'All Is Well'
   
@router.get('/raw/certs/{region}', tags=["AWS-RAW"])
def get_certs(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_certs = acm_conn.list_certificates().get('CertificateSummaryList')
    return all_certs
    
@router.get('/raw/certs/{region}/expired', tags=["AWS-RAW"])
def get_certs_expired(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_cert = acm_conn.list_certificates().get('CertificateSummaryList')
    expired_certs = [cert for cert in all_cert if cert['Status'] == 'EXPIRED']    
    return expired_certs
 
 
@router.get("/raw/getvpc/{region}", tags=["AWS-RAW"])
def get_vpc_id_list(region)->list:
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_vpcs()
    vpc_id_list = []
    for vpc in response['Vpcs']:
        vpc_id_list.append(vpc['VpcId'])
    print(vpc_id_list)
    return vpc_id_list

@router.get('/raw/pokemon',tags=["AWS-RAW"])
def get_pokemon(request: Request):
    URL = requests.get('https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0')
    POKEMON_LIST = URL.json()['results']
    return POKEMON_LIST
   


