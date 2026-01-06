import azure.functions as func
import logging
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger", auth_level=func.AuthLevel.FUNCTION)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.blob_trigger(arg_name="myblob", path="containerfuad",
                               connection="AzureWebJobsStorage") 
def BlobTrigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")


# This example uses SDK types to directly access the underlying BlobClient object provided by the Blob storage trigger.
# To use, uncomment the section below and add azurefunctions-extensions-bindings-blob to your requirements.txt file
# Ref: aka.ms/functions-sdk-blob-python
#
# import azurefunctions.extensions.bindings.blob as blob
# @app.blob_trigger(arg_name="client", path="mycontainer",
#                   connection="storageengdweu003_STORAGE")
# def BlobTrigger(client: blob.BlobClient):
#     logging.info(
#         f"Python blob trigger function processed blob \n"
#         f"Properties: {client.get_blob_properties()}\n"
#         f"Blob content head: {client.download_blob().read(size=1)}"
#     )


@app.route(route="readblob", auth_level=func.AuthLevel.ANONYMOUS)
def http_read_blob(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger processing a request.')

    # 1. Get the account URL (e.g., https://aaa.blob.core.windows.net)
    # Best practice: Store this in an App Setting
    account_url = os.environ.get("BLOB_STORAGE_ACCOUNT_URL")
    container_name = "mycontainer"
    blob_name = req.params.get('file')

    if not blob_name:
        return func.HttpResponse("Please pass a 'file' name in the query string", status_code=400)

    try:
        # 2. Setup Identity and Client
        # This will use the Managed Identity in Azure
        token_credential = DefaultAzureCredential()
        
        blob_service_client = BlobServiceClient(
            account_url, 
            credential=token_credential
        )

        # 3. Read the blob data
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_data = blob_client.download_blob().readall()

        return func.HttpResponse(blob_data, mimetype="application/octet-stream")

    except Exception as e:
        logging.error(f"Error reading blob: {e}")
        return func.HttpResponse(f"Failed to read blob: {str(e)}", status_code=500)