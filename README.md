# Uploading to the DBpedia Databus

The requirement for uploading anything to the Databus is a Databus Account, you can create one at the [website](https://databus.dbpedia.org/auth/realms/databus/protocol/openid-connect/registrations?client_id=website&response_type=code&scope=openidemail&redirect_uri=https://databus.dbpedia.org&kc_locale=en).


## Option 1: Using the Web UI

The easiest way of deploying data to the Databus is by using the Web UI. It can be accessed [here](https://databus.dbpedia.org/system/upload).
It provides a straightforward UI for filling out the necessary URIs and other parameters to generate the DataID.


## Option 2: Using the API

### Step 1: Generating the DataID

If you want to submit content via API you need to create the DataID yourself. An example for the DataID can either be seen in the third step of Option 1 or in the example files in this repository. There are wo seperate files:

  - The `group-metadata`: This is only documentation for the group, no file information is included here. An example can be seen in `group_docu.jsonld`.
  - The actual `DataID`: This tells the Databus the necessary metadata to publish on the databus. An example for this can be seen in `dataid_example.jsonld`.

### Step 2: Deploying to the Databus

For this another two Steps are required:

1. Fetching a Bearer Token from the Databus. This can be done by setting the following HTTP headers in a GET request:
    - 'client_id': 'upload-api'
    - 'username': '<user>' with user being the accountname of your account (can be seeen in the URI e.g. https://databus.dbpedia.org/denis)
    - 'grant_type': 'password' 
    - 'password': '<password>' with the password of said Databus Account

Example with curl: ```TOKEN=$(curl -s -d 'client_id=upload-api' -d 'username=XXXXXX' -d 'password=XXXXXXXXXXX' -d 'grant_type=password' https://databus.dbpedia.org/auth/realms/databus/protocol/openid-connect/token | cut -d'"' -f 4)```.

**NOTE**: A token has a lifettime of around 30 seconds.

2. Using said bearer token for deploying to the Databus. Deploy requests are HTTP PUT requests with the following header:
    - 'Authorization': 'Bearer $TOKEN' with the Token being the string returned from **Step 1**

The Target URI depends here on the type of graph you want to deploy:
    - For the group its http://databus.dbpedia.org/$USER/$GROUP
    - For the version DataID it is http://databus.dbpedia.org/$USER/$GROUP/$ARTIFACT/$VERSION

The Data is in both cases the fitting graph as JSON-LD. For testing the rgraph can be minified with a tool like [this one](https://www.minifyjson.org/).

**Example with curl:**```curl -H '{Authorization: Bearer $TOKEN}' -X PUT <GROUP-OR-VERSION-URI> -d 'DATAID_JSONLD_CONTENT'```

## Option 3: Using the python3 script

A example implementation of using the API can be seen in `databus_api_example.py`. By modifying the veriables below line `if __name__ == "__main__":` a dataid can easily be generated and deployed, similar to the WebUI. the script consists of three classes:
