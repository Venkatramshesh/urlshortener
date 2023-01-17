from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_bootstrap import Bootstrap

import boto3
import random

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'jCOo4PAnmU6A0j2lpKeI-A'
hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])

# set up boto3 connection
AWS_region = 'us-east-1'
boto3.setup_default_session(profile_name='iamadmin-production')
dynamodb = boto3.resource(service_name='dynamodb')
tablename = "url"
# create dynamodb tale for storing url

def create_url_table(dynamodb):
    table_names = [table.name for table in dynamodb.tables.all()]

    if tablename in table_names:
        print('table', tablename, 'exists')

           # Table defination
    else: table = dynamodb.create_table(
            TableName=tablename,

            AttributeDefinitions=[
                {
                    'AttributeName': 'id',   #id for url
                    'AttributeType': 'N'
                },
                # {
                #     'AttributeName': 'org_url',  #original url
                #     'AttributeType': 'S'
                # },

            ],

            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                },
                # {
                #     'AttributeName': 'org_url',
                #     'KeyType': 'RANGE'  # Sort key
                # },

            ],
            ProvisionedThroughput={
                # ReadCapacityUnits set to 10 strongly consistent reads per second
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10  # WriteCapacityUnits set to 10 writes per second
            }
        )


@app.route('/', methods=('GET', 'POST'))
def index():

    if request.method == 'POST':
        url = request.form['url']
        custom_id = request.form['custom_id']

        newid = random.randrange(10000)
        if not url:
            flash('The URL is required!')
            return redirect(url_for('index.html'))

        # if cusomter enters cusot id
        if custom_id:
            output = []
            for character in custom_id:
                number = ord(character.lower()) - 96;
                output.append(number);
            outputnew=[str(x) for x in output]
            finalnum= ''.join(outputnew)
            newid = int(finalnum)

        # add url and unique id to dynamodb table
        url_inputs = dynamodb.Table('url')

        url_inputs.put_item(Item={'id': newid,
                                  'org_url': url
                                  })

        hashid = hashids.encode(newid)
        short_url = request.host_url + hashid
        #print(short_url)

        return render_template('index.html', short_url=short_url)

    return render_template('index.html')

@app.route('/<id>')
def url_redirect(id):
    #print(id)
    original_id = hashids.decode(id)
    #print(original_id)
    if original_id:
        original_id = original_id[0]
        url_inputs = dynamodb.Table('url')
        url_data=url_inputs.get_item(Key={'id': original_id})
        #print(url_data)
        original_url = url_data["Item"]['org_url']
        print(original_url)
        return redirect(original_url)
    else:
        flash('Invalid URL')
        return redirect(url_for('index'))


if __name__=="__main__":
   create_url_table(dynamodb)
   app.run()