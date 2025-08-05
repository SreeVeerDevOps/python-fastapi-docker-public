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
from azure.mgmt.storage import StorageManagementClient
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
storage_client = StorageManagementClient(credential, retrieved_sub_id.value)
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
  return templates.TemplateResponse("rg.html", {"request": request, "subscription_id": subscription_id, "subscription_name": subscription_name, "name": "Resource Group Information",  "rg_dict": rg_dict})


@router.get("/listvnet", tags=["Azure"])
def azure_listvnet(request: Request):
  vnet_rg_list = []
  vnet_cidrs = []
  for vnet in network_client.virtual_networks.list_all():
   vnet_name_list = [ vnet.name for vnet in network_client.virtual_networks.list_all() ] 
   vnet_ids = [ vnet.id for vnet in network_client.virtual_networks.list_all() ]
   net_rg_list = [ vnet.split('/')[4] for vnet in vnet_ids ]
   address_space = vnet.address_space
   vnet_cidrs.append(address_space.address_prefixes[0])
  print(vnet_name_list)
  print(net_rg_list)
  print(vnet_cidrs)
  for a, b, c in zip(vnet_name_list, vnet_cidrs, net_rg_list):
   print(a,b,c)
  data = zip(vnet_name_list, vnet_cidrs, net_rg_list)
  return templates.TemplateResponse("vnet.html", {"request": request, "subscription_id": subscription_id, "subscription_name": subscription_name, "name": "Virtual Networks Information",  "data": data})


@router.get("/listsa", tags=["Azure"])
def azure_list_sa(request: Request):
  sa_sku = []
  storage_accounts = storage_client.storage_accounts.list()
  sa_accounts_name = [ account.name for account in storage_client.storage_accounts.list()]
  sa_accounts_loc = [ account.location for account in storage_client.storage_accounts.list()]
  for accounts in storage_client.storage_accounts.list():
    sku = accounts.sku
    sa_sku.append(sku.name)
  print(sa_accounts_name)
  print(sa_accounts_loc)
  print(sa_sku)
  for a, b, c in zip(sa_accounts_name, sa_accounts_loc, sa_sku):
   print(a,b,c)
  data = zip(sa_accounts_name, sa_accounts_loc, sa_sku)
  return templates.TemplateResponse("storage_accounts.html", {"request": request, "subscription_id": subscription_id, "subscription_name": subscription_name, "name": "Storage Account Information",  "data": data})
   
