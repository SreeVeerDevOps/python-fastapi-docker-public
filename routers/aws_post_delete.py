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


