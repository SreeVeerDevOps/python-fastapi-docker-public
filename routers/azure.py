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
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from platform import python_version

key_vault_name = "blueboxvault"
key_vault_uri = f"https://blueboxvault.vault.azure.net"
subscription_id = "subscriptionid"
subscription_name = "subscription-name"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_uri, credential=credential)
retrieved_sub_id = client.get_secret(subscription_id)
retrieved_sub_name = client.get_secret('subscription-name')
os.environ['AZURE_SUBSCRIPTION_ID'] = retrieved_sub_id.value
print(retrieved_sub_id.value)
subscription_id = retrieved_sub_id.value
subscription_name = retrieved_sub_name.value
resource_client = ResourceManagementClient(credential, retrieved_sub_id.value)
network_client = NetworkManagementClient(credential, retrieved_sub_id.value)
router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/azuredemo", tags=["Azure"])
def azure_router():
    return {
        "message": "THIS IS AWS ROUTER IN FILE azure.py"
    }


@router.get("/listrg", tags=["Azure"])
def azure_listrg(request: Request):
  group_list = [ group.name for group in resource_client.resource_groups.list()]
  group_loc = [ group.location for group in resource_client.resource_groups.list()]
  rg_dict   = dict(zip(group_list, group_loc))
  return templates.TemplateResponse("rg.html", {"request": request, "subscription_id": subscription_id, "subscription_name": subscription_name, "name": "Resource Group Information For Subscription",  "rg_dict": rg_dict})


@router.get("/listvnet", tags=["Azure"])
def azure_listvnet(request: Request):
  for vnet in network_client.virtual_networks.list_all():
   vnet_id = vnet.id
   print(vnet_id)
   rg_name = vnet_id.split('/')[4]
   address_space = vnet.address_space
   print(address_space)
   vnet_cidr = address_space.address_prefixes
   print(rg_name)
   print(vnet.name)
   #print(vnet.vnet_cidr)
   print("*"*90)
