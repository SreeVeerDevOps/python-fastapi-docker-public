from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from faker import Faker
import boto3
from botocore.exceptions import ClientError

router = APIRouter()
fake = Faker()

# Define the Pydantic model
class Item(BaseModel):
    id: str
    name: str
    email: str
    address: str
    phone: str

# Initialize boto3 DynamoDB resource and table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('fastapidemotable001')

@router.post("/items/fake/")
def create_fake_item():
    # Generate fake item data
    item = {
        "id": fake.unique.uuid4(),
        "name": fake.name(),
        "email": fake.unique.email(),
        "address": fake.address(),
        "phone": fake.phone_number()
    }
    try:
        # Post fake item to DynamoDB
        table.put_item(Item=item)
        return {"message": "Fake item created", "item": item}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

@router.get("/items/{item_id}")
def get_item(item_id: str):
    try:
        # Query DynamoDB for item by id
        response = table.get_item(Key={"id": item_id})
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

@router.get("/items/")
def list_all_items():
    try:
        # Use scan to retrieve all items
        response = table.scan()
        items = response.get('Items', [])
        return {"items": items}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan table: {e.response['Error']['Message']}")

@router.get("/allid/")
def list_all_items():
    try:
        # Use scan to retrieve all items
        response = table.scan()
        items = response.get('Items', [])
        ids = [ item['id'] for item in items ]
        return {"items": ids}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan table: {e.response['Error']['Message']}")


@router.get("/allemail/")
def list_all_email():
    try:
        # Use scan to retrieve all items
        response = table.scan()
        items = response.get('Items', [])
        ids = [ item['email'] for item in items ]
        return {"items": ids}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan table: {e.response['Error']['Message']}")

@router.delete("/deleteall/")
def delete_all_items():
    try:
        # Scan to get all items
        response = table.scan()
        items = response.get('Items', [])

        # Batch delete items using primary key(s)
        with table.batch_writer() as batch:
            for item in items:
                # Extract the primary key(s) from item
                # Assumes 'id' is the partition key, adjust keys if you have a composite key
                key = {'id': item['id']}
                batch.delete_item(Key=key)

        return {"message": f"Deleted {len(items)} items successfully."}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete items: {e.response['Error']['Message']}")