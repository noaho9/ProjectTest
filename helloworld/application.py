#!flask/bin/python
import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0])))
import json
from flask import Flask, Response, render_template, request
from helloworld.flaskrun import flaskrun
import requests
import boto3 
sys.path.append('../.venv/include/python3.6')
from boto3.dynamodb.conditions import Key
from helloworld.setmetadata import db_set_item, inc_page_by
from werkzeug.utils import secure_filename
import datetime
#from app import app

application = Flask(__name__, template_folder='templates')

@application.route('/index')
def index():
   user = {'username': 'Miguel'}
   return render_template('index.html', title='Home', user=user)
   


@application.route('/', methods=['GET'])
def get():
    return Response(json.dumps({'Output': 'Hello World'}), mimetype='application/json', status=200)


@application.route('/get_ip', methods=['GET'])
def get_ip():
    # print(get_ip_meta())
    # return time and path to url to database
    return Response(json.dumps(get_ip_meta()), mimetype='application/json', status=200)

@application.route('/new_visitor/<site>', methods=['POST'])
def get_temp(site):
    # get ip metadata from the fuction
    response = get_ip_meta()
    # get json data from the post body
    post_data = request.get_json()
    # build request data
    Item = build_request_data(site, post_data, response)
    db_set_item('eb_try_logger', Item)
    # inc_page_by(response['country'], site)
    
    return Response(json.dumps(Item), mimetype='application/json', status=200)

@application.route('/bi', methods=['GET'])
def get_bi():
    my_ses = boto3.Session(region_name = 'us-east-2')
    dynamodb = my_ses.resource('dynamodb')
    table = dynamodb.Table('eb_try_logger')
    resp = table.scan()
    for item in resp['Items']:
        print(item)
    return Response(json.dumps(str(resp['Items'])), mimetype='application/json', status=200)
    #return render_template('index.html', response=json.dumps(resp['Items']), title='bi')

# get result for one site
@application.route('/bi/<db_key>/<db_value>', methods=['GET'])
def get_bi_site(db_key, db_value):
    my_ses = boto3.Session(region_name = 'us-east-2')
    dynamodb = my_ses.resource('dynamodb')
    table = dynamodb.Table('eb_try_logger')
    if db_key and db_value:
        resp = table.scan(FilterExpression=Key(db_key).eq(db_value))
    else:
        # when result not found, return table (presevent error handling in code...)
        resp = table.scan()
    # count the number of items in resp dict   
    obj_len = len(resp['Items'])
    print(type(resp['Items']))
    '''
    print('item count: ',str(obj_len))
    for item in resp['Items']:
        print(item['site'])
    
    res = []
    res = json.loads(resp['Items'][0])
    '''
    #return Response(json.dumps(str(resp['Items'])), mimetype='application/json', status=200)
    #return render_template('index.html', response=json.dumps(resp['Items']), title='bi')
    return render_template('index.html', response=resp['Items'], counter=obj_len, title='bi')


@application.route('/bi/graph')
def showgraph():
    data_provider = [
        {
            'category': 'אתר 1',
            'column-1': 8

        },
        {
            "category": "אתר 2",
            "column-1": 6
        },
        {
            "category": "אתר 3",
            "column-1": 2
        }
    ]
    return render_template('bi_graph.html', data=data_provider, chart_title='מה המצב אחי')

@application.route('/', methods=['POST'])
def post():
    return Response(json.dumps({'Output': 'Hello World'}), mimetype='application/json', status=200)

@application.route('/analyze/<bucket>/<image>', methods=['GET'])
def analyze(bucket='foodcal', image='dinner1'):
    return detect_labels(bucket, image)
    
    
def detect_labels(bucket, key, max_labels=10, min_confidence=50, region="us-east-2"):
    ####
    print('at begginingbucket name: {}, key: {}'.format(bucket, key))
    rekognition = boto3.client("rekognition", region)
    print('after recog')
    s3 = boto3.resource('s3', region_name = 'us-east-2')
    image = s3.Object(bucket, key) # Get an Image from S3
    print('bucket name: {}, key: {}'.format(bucket, key))
    img_data = image.get()['Body'].read() # Read the image
    if not img_data:
        print('no image data')
    response = rekognition.detect_labels(
        Image={
            'Bytes': img_data
        },
        MaxLabels=max_labels,
		MinConfidence=min_confidence,
    )
    
    return json.dumps(response['Labels'])
    
    '''
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	'''

def options():
    my_list = ["one", "two"]
    #my_dict = {'a' : 'addd','b' : 'dddd','c' :'llll'}
    return my_list
    
    
def get_ip_meta():
    user_ip = str(request.environ['REMOTE_ADDR'])
    service_url = 'http://ipinfo.io/{}'.format(user_ip) 
    res = requests.get(service_url).json()
    # arrange data so it won't be missing when entering dynamo
    if 'country' not in res:
        res['country'] = 'mock_country'
    if 'ip_geo' not in res:
        res['ip_geo'] = 'mock_geo'
    if 'loc' not in res:
        res['loc'] = 'mock_loc'
    if 'city' not in res:
        res['city'] = 'mock_city'
        
    return res


@application.route('/upload', methods=['GET','POST', 'PUT'])
def upload_s3():
    print('in function')
    bucket = 'foodcal'
    # file_name = 'temp.jpg'
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # if get show page for upload
    if request.method == 'GET':
        return render_template('upload.html')

    s3 = boto3.resource('s3', region_name = 'us-east-2')
    if request.files:
        print('in files')
        file = request.files['user_file']
        file_name = secure_filename(file.filename) + time
        print('file name {}'.format(file_name))
        #s3 = boto3.resource('s3')
        #object = s3.Object('bucket', Key=file_name)
        #object.put(Body=file)
        # my_s3 = s3.Bucket(bucket)
        # my_s3.put_object(Key=file_name, Body=file)
        client = boto3.client('s3')
        client.put_object(Body=file, Bucket=bucket, Key=file_name)
        
        print('add object: {}'.format(file_name))
    else:  
        response = request.get_json() 
        print(response)
        bucket = response['bucket'] # 'loggereast1'
        file_name = response['file_name'] + time # whatever name
        country = response['country']
        data = json.dumps(response)
        print(data)
        # to create a file the obdy needs to be of type bytes, hence the data.encode
        s3.Bucket(bucket).put_object(Key=file_name, Body=data.encode('utf-8'))
        print('after data load s3')

    return Response(detect_labels(bucket, file_name), mimetype='application/json', status=200)
    
    
    
# build item for logger
# site is in the url
# post data contains the page in the site 
# response is for ip metadata
def build_request_data(site, post_data, response):
    Item={
    'ip_addr': response['ip'], 
    'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'time': datetime.datetime.now().strftime("%H:%M:%S"),
    'site': site,
    'ip_geo' : response['loc'], # res_data
    'ip_country': response['country'],
    'ip_city': response['city'],
    'page': post_data['page']
    }
    
    return Item


if __name__ == '__main__':
    flaskrun(application)