import boto3
from fastapi import APIRouter

router = APIRouter()

@router.get("/azuredemo", tags=["Azure"])
def azure_router():
    return {
        "message": "THIS IS AWS ROUTER IN FILE azure.py"
    }