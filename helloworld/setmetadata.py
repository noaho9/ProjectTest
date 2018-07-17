import boto3 
from boto3.dynamodb.conditions import Key
import json
import decimal

def db_set_item(table, item):
    # create a session for boto to access the credentials that the ec2 holds
    #my_ses = boto3.Session(region_name = 'us-east-1')
    # connect to the resource dynmodb
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    # refer to the table
    table = dynamodb.Table(table)

    print(item)
    # insert the item
    table.put_item(Item=item)

    
def inc_page_by(country, page):
    # connect to the resource dynmodb 
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    # refer to the table
    table = dynamodb.Table('eb_sum_site')    
    response = table.update_item(
    Key={
        'country': country,
        'page': page
    },
    UpdateExpression="set cp_counter = cp_counter + :val",
    ExpressionAttributeValues={
        ':val': decimal.Decimal(1)
    },
    ReturnValues="UPDATED_NEW"
)