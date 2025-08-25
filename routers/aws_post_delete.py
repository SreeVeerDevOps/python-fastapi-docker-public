import boto3
from fastapi import APIRouter
from fastapi import FastAPI, Request, UploadFile
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
router = APIRouter()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

templates = Jinja2Templates(directory="templates")

@router.get('/post/health', tags=["AWS-POST-DELETE"])
def post_health():
    return 'All Is Well With Post File....'
   

@router.post("/items/", tags=["AWS-POST-DELETE"])
def create_item(item: Item):
    return item

@router.post("/items2/", tags=["AWS-POST-DELETE"])
def create_item2(item: Item):
    keys = []
    values = []
    for k,v in item.items():
        keys.append(k)
        values.append(v)
    return keys

@router.get('/post/certs/{region}', tags=["AWS-RAW"])
def get_certs(request: Request, region: str):
    acm_conn = boto3.client('acm',region_name=region)
    all_certs = acm_conn.list_certificates().get('CertificateSummaryList')
    return all_certs

