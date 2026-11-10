"""Azure resource views (resource groups, VNets, storage accounts).

Authentication uses the server's managed identity.
For a *user-assigned* identity, set the App Setting AZURE_CLIENT_ID to the identity's
client ID. It can't come from Key Vault, because this identity is what reads Key Vault.

The identity needs:
  - "Key Vault Secrets User" (or a Get-secret access policy) on the Key Vault
  - "Reader" on the subscription, to list resource groups and storage accounts
  - For /networks: "Reader" on every subscription (or management group) it should show
"""
import os
from concurrent.futures import ThreadPoolExecutor

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient
try:  # azure-mgmt-resource >= 26 moved this into azure-mgmt-resource-subscriptions
    from azure.mgmt.resource.subscriptions import SubscriptionClient
except ImportError:  # older azure-mgmt-resource
    from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

key_vault_name = "azureb61kv"
key_vault_uri = f"https://azureb61kv.vault.azure.net"
secret_subscription_id = "subscriptionid"
secret_subscription_name = "subscription-name"

# Client ID of the user-assigned managed identity (App Setting). None = system-assigned.
managed_identity_client_id = os.getenv("AZURE_CLIENT_ID")
print(f"Azure router using {'user-assigned identity ' + managed_identity_client_id if managed_identity_client_id else 'system-assigned identity'}")

credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
client = SecretClient(vault_url=key_vault_uri, credential=credential)
subscription_id = client.get_secret(secret_subscription_id).value
subscription_name = client.get_secret(secret_subscription_name).value
os.environ['AZURE_SUBSCRIPTION_ID'] = subscription_id
print(f'The retrieved Value From Key Vault For Subscription ID is {subscription_id}.')
print(f'The retrieved Value From Key Vault For Subscription Name is {subscription_name}.')

resource_client = ResourceManagementClient(credential, subscription_id)
storage_client = StorageManagementClient(credential, subscription_id)

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def _azure_error(exc: Exception) -> HTMLResponse:
    """Show a readable error instead of a bare 'Internal Server Error'."""
    if isinstance(exc, ClientAuthenticationError):
        hint = ("The managed identity could not get a token. Check that the user-assigned identity is "
                "attached to this App Service and that AZURE_CLIENT_ID is set to its client ID.")
    elif isinstance(exc, HttpResponseError) and exc.status_code == 403:
        hint = (f"The managed identity is not allowed to read this. Give it the 'Reader' role on "
                f"subscription {subscription_name} ({subscription_id}).")
    else:
        hint = "Unexpected error while calling Azure."
    detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    print(f"Azure call failed: {exc!r}")
    return HTMLResponse(
        f"<h2>Azure request failed</h2><p>{hint}</p><pre>{detail}</pre><p><a href='/'>Back to home</a></p>",
        status_code=502,
    )


def _page(request: Request, template: str, title: str, **context):
    return templates.TemplateResponse(
        request,
        template,
        {"subscription_id": subscription_id, "subscription_name": subscription_name, "name": title,
         "identity": managed_identity_client_id or "system-assigned", **context},
    )


@router.get("/azuredemo", tags=["Azure"])
def azure_router():
    return {
        "message": "THIS IS AZURE ROUTER IN FILE azure.py"
    }


@router.get("/listrg", tags=["Azure"])
def azure_listrg(request: Request):
    try:
        rg_dict = {group.name: group.location for group in resource_client.resource_groups.list()}
    except Exception as exc:
        return _azure_error(exc)
    return _page(request, "rg.html", "Resource Group Information", rg_dict=rg_dict)


@router.get("/listsa", tags=["Azure"])
def azure_list_sa(request: Request):
    try:
        data = [
            # sku.name is an enum; .value gives "Standard_LRS" instead of "SkuName.STANDARD_LRS"
            (account.name, account.location, getattr(account.sku.name, "value", account.sku.name) if account.sku else "")
            for account in storage_client.storage_accounts.list()
        ]
    except Exception as exc:
        return _azure_error(exc)
    return _page(request, "storage_accounts.html", "Storage Account Information", data=data)


def _vnets_in_subscription(sub):
    """List every VNet in one subscription. Errors are returned, not raised, so one bad
    subscription doesn't hide the others."""
    result = {"id": sub.subscription_id, "name": sub.display_name or sub.subscription_id,
              "state": str(sub.state or ""), "vnets": [], "error": None}
    try:
        client = NetworkManagementClient(credential, sub.subscription_id)
        for vnet in client.virtual_networks.list_all():
            prefixes = (vnet.address_space.address_prefixes if vnet.address_space else None) or []
            result["vnets"].append({
                "name": vnet.name,
                "resource_group": vnet.id.split('/')[4],
                "location": vnet.location,
                "address_space": prefixes,
                "subnets": len(vnet.subnets or []),
                "peerings": len(vnet.virtual_network_peerings or []),
            })
        result["vnets"].sort(key=lambda v: (v["resource_group"].lower(), v["name"].lower()))
    except Exception as exc:
        if isinstance(exc, HttpResponseError) and exc.status_code == 403:
            result["error"] = "No permission to list VNets here. Give the identity the Reader role on this subscription."
        else:
            result["error"] = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        print(f"/networks: subscription {sub.subscription_id} failed: {exc!r}")
    return result


@router.get("/networks", tags=["Azure"])
def azure_networks(request: Request):
    """Virtual networks in every subscription the managed identity can see."""
    try:
        subscriptions = list(SubscriptionClient(credential).subscriptions.list())
    except Exception as exc:
        return _azure_error(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_vnets_in_subscription, subscriptions))
    results.sort(key=lambda r: r["name"].lower())

    total_vnets = sum(len(r["vnets"]) for r in results)
    print(f"/networks: {total_vnets} VNet(s) across {len(results)} subscription(s) for identity "
          f"{managed_identity_client_id or 'system-assigned'}")
    return templates.TemplateResponse(
        request,
        "networks.html",
        {
            "subscriptions": results,
            "total_vnets": total_vnets,
            "total_regions": len({v["location"] for r in results for v in r["vnets"]}),
            "identity": managed_identity_client_id or "system-assigned",
        },
    )
