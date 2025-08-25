from fastapi import FastAPI, HTTPException
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
table = dynamodb.Table('fastapidemotable')

@app.post("/items/fake/")
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

@app.get("/items/{item_id}")
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
