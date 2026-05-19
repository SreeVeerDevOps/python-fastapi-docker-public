"""
azure_routes.py
---------------
FastAPI routes for listing Azure resources:
  - Resource Groups
  - Storage Accounts
  - Virtual Machines

Mirrors the existing pattern used for AWS VPCs and S3 buckets.

Dependencies (add to requirements.txt):
    azure-identity>=1.15.0
    azure-mgmt-resource>=23.0.0
    azure-mgmt-storage>=21.0.0
    azure-mgmt-compute>=30.0.0

Environment variables required:
    AZURE_SUBSCRIPTION_ID   – your Azure subscription ID
    AZURE_TENANT_ID         – Azure AD tenant ID          (used by DefaultAzureCredential)
    AZURE_CLIENT_ID         – service principal client ID (used by DefaultAzureCredential)
    AZURE_CLIENT_SECRET     – service principal secret    (used by DefaultAzureCredential)

Authentication:
    Uses DefaultAzureCredential, which works with env vars, managed identity,
    Azure CLI login, and more — no changes needed per environment.
"""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.compute import ComputeManagementClient

# ── Router & templates ──────────────────────────────────────────────────────
router = APIRouter()
templates = Jinja2Templates(directory="templates")

SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "")


def _credential() -> DefaultAzureCredential:
    """Return a fresh DefaultAzureCredential instance."""
    return DefaultAzureCredential()


# ── Resource Groups ─────────────────────────────────────────────────────────
@router.get("/azure/resource-groups", response_class=HTMLResponse)
async def list_resource_groups(request: Request):
    """
    List all Resource Groups in the configured Azure subscription.
    Renders: templates/azure_resource_groups.html
    """
    client = ResourceManagementClient(_credential(), SUBSCRIPTION_ID)

    groups = [
        {
            "name": rg.name,
            "location": rg.location,
            "provisioning_state": rg.properties.provisioning_state
            if rg.properties
            else "N/A",
            "tags": rg.tags or {},
        }
        for rg in client.resource_groups.list()
    ]

    return templates.TemplateResponse(
        "azure_resource_groups.html",
        {
            "request": request,
            "resource_groups": groups,
            "count": len(groups),
            "subscription_id": SUBSCRIPTION_ID,
        },
    )


# ── Storage Accounts ────────────────────────────────────────────────────────
@router.get("/azure/storage-accounts", response_class=HTMLResponse)
async def list_storage_accounts(request: Request):
    """
    List all Storage Accounts in the configured Azure subscription.
    Renders: templates/azure_storage_accounts.html
    """
    client = StorageManagementClient(_credential(), SUBSCRIPTION_ID)

    accounts = [
        {
            "name": sa.name,
            "location": sa.location,
            "resource_group": sa.id.split("/")[4] if sa.id else "N/A",
            "kind": sa.kind,
            "sku": sa.sku.name if sa.sku else "N/A",
            "provisioning_state": sa.provisioning_state,
            "access_tier": sa.access_tier if hasattr(sa, "access_tier") else "N/A",
        }
        for sa in client.storage_accounts.list()
    ]

    return templates.TemplateResponse(
        "azure_storage_accounts.html",
        {
            "request": request,
            "storage_accounts": accounts,
            "count": len(accounts),
            "subscription_id": SUBSCRIPTION_ID,
        },
    )


# ── Virtual Machines ────────────────────────────────────────────────────────
@router.get("/azure/virtual-machines", response_class=HTMLResponse)
async def list_virtual_machines(request: Request):
    """
    List all Virtual Machines across all Resource Groups in the subscription.
    Renders: templates/azure_virtual_machines.html
    """
    client = ComputeManagementClient(_credential(), SUBSCRIPTION_ID)

    vms = [
        {
            "name": vm.name,
            "location": vm.location,
            "resource_group": vm.id.split("/")[4] if vm.id else "N/A",
            "vm_size": vm.hardware_profile.vm_size
            if vm.hardware_profile
            else "N/A",
            "os_type": vm.storage_profile.os_disk.os_type
            if vm.storage_profile and vm.storage_profile.os_disk
            else "N/A",
            "provisioning_state": vm.provisioning_state,
            "tags": vm.tags or {},
        }
        for vm in client.virtual_machines.list_all()
    ]

    return templates.TemplateResponse(
        "azure_virtual_machines.html",
        {
            "request": request,
            "virtual_machines": vms,
            "count": len(vms),
            "subscription_id": SUBSCRIPTION_ID,
        },
    )
