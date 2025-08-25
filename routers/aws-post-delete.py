import boto3
from fastapi import APIRouter
from fastapi import FastAPI, Request, UploadFile
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get('/post/health', tags=["AWS-POST-DELETE"])
def post_health():
    return 'All Is Well With Post File....'
   


