# Import Libraries

import json
import uuid
import fastapi
import typing
import motor.motor_asyncio
import pandas
import pydantic
import uvicorn
import logging
import dateutil.parser
import datetime
import re
import os
import math
from bson import json_util
from fastapi import FastAPI
from concurrent.futures import ProcessPoolExecutor
from fastapi_cache import FastAPICache
import pydantic_settings
from fastapi_cache.backends.inmemory import InMemoryBackend


############################## MICROSERVICE SETUP ##############################

class Settings(pydantic_settings.BaseSettings):
    """
    Set the configurations for the microservice's functionality through the env file.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to setup the basic configuration from the env file.
    """

    # Default configuration values to be used if these parameters are not defined in the env file.
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "irctc_analyser_test"
    IP_ANALYZER_IPINFO_TOKENS: list = ["9856331fcaa070", "a5dd07db73b440","a9e668faf838b3", "96269c96436649"]
    IP_ANALYZER_IPREGISTRY_TOKENS:list = ["tlz6eacbhflzphhi", "glaf6rgqc8kfvdf5"]
    GCHAT_KEY: str = ""
    GCHAT_TOKEN: str = ""
    
    # Read the env file to construct a configuration for the microservice.
    model_config = pydantic_settings.SettingsConfigDict(env_file="../.env")


# Global variables to be used by the endpoints.

settings = Settings()

# Instance of class FastAPI that acts as a main point of interaction to create all API.
app = fastapi.FastAPI()

# Connect to MongoDB.
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)

# Get reference to the database `MONGO_DB`.
db = client[settings.MONGO_DB]

# Create a handle to the collection for uploaded report data.
report_handle = db.irctc_report
software_report = db.irctc_software_report

def setup_mount_folder(f_file):
    """Summary

    Returns:
        TYPE: Description
    """
    path = os.getcwd()
    # file Upload
    UPLOAD_FOLDER = os.path.join(path, f_file)
    # Make directory if "uploads" folder not exists
    if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    return UPLOAD_FOLDER

async def startup_event():
    setup_mount_folder('files')
    setup_mount_folder('download_reports')

async def shutdown_event():
    app.state.executor.shutdown()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


#################### REPORT ARCHIVE #############################

@app.post("/upload_report")
async def upload_report(request: fastapi.Request):
    """
    Upload the report file into the database.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Message that file uploaded successfully or not.
    :rtype: dict
    """

    # Get data from the request made.
    data = await request.json()

    # Get the date for the uploaded file.
    new_date = data['filedate']

    # Parse the date if provided and initialize it to `file_date` variable.
    if new_date != "null": file_date = dateutil.parser.parse(new_date)

    # If no date is provided then current date will be provided. 
    else: file_date = datetime.datetime.now()

    # Check if the file is already present.
    report_archive = await report_handle.count_documents({
        '$or' : [
            {
                'ref_hash' : data['hash'],
            },
            {
                'filename' : data['orig_filename']
            }
        ]
    })

    # Returns the message if file is already present
    if report_archive:
        return {
            "detail" : "File already exists"
        }
    
    # Insert the data related to the uploaded file into the database.
    report_handle.insert_one(
            {
               "ref_hash" : data['hash'],
               "file_date" : file_date,
               "filename" : data['pure_filename'],
               "filesize" : data['filesize'],
               "field" : data['ftype'],
               "created_date": datetime.datetime.utcnow()
            }
        )
    
    # Returns the message that the file is uploaded successfully.
    return {
            "detail": "File Uploaded Successfully"
        }


@app.post("/upload_software_procurement_report")
async def upload_software_procurement(request: fastapi.Request):
    """
    Upload the software procurement file into the database.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Message that file uploaded successfully or not.
    :rtype: dict
    """

    # Get data from the request made.
    data = await request.json()

    software_name = data['software_name']

    purpose = data['purpose']

    software_price = data["software_price"]

    approval_date = data['approval_date']

    purchase_date = data['purchase_date']

    current_status = data['current_status']

    remarks = data['remarks']

    # Parse the purchase date if provided and initialize it to `purchase_date` variable.
    if purchase_date != "null": purchase_date = dateutil.parser.parse(purchase_date)

    # If no date is provided then current date will be provided.
    else: purchase_date = datetime.datetime.now()

    # Parse the approval date if provided and initialize it to `approval_date` variable.
    if approval_date != "null": approval_date = dateutil.parser.parse(approval_date)

    # If no date is provided then current date will be provided.
    else: approval_date = datetime.datetime.now()

    # Check if the file is already present.
    report_archive = await software_report.count_documents({
        '$or' : [
            {
                'ref_hash' : data['hash'],
            },
            {
                'filename' : data['orig_filename']
            }
        ]
    })

    # Returns the message if file is already present
    if report_archive:
        return {
            "detail" : "File already exists"
        }
    
    # Insert the data related to the uploaded file into the database.
    software_report.insert_one(
            {
               "ref_hash" : data['hash'],
               "filename" : data['pure_filename'],
               "filesize" : data['filesize'],
               "software_name": software_name,
               'purpose' : purpose,
               'software_price' : software_price,
               'approval_date' : approval_date,
               'purchase_date' : purchase_date,
               'current_status' : current_status,
               'remarks' : remarks,
               "created_date": datetime.datetime.utcnow()
            }
        )
    
    # Returns the message that the file is uploaded successfully.
    return {
            "detail": "File Uploaded Successfully"
        }


@app.post("/report_list")
async def list_report(request: fastapi.Request):
    """
    Fetch all the data of the uploaded reports.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Reports data to be displayed and count of the records.
    :rtype: dict
    """

    """
    starting_date.date(): From the frontend the search filter is sending suspicious date(starting_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """

    # Get data from the request made.
    data = await request.json()

    # Get the keyword for which the data is to be searched.
    search = data['search']

    # Get the starting date form which the data is to be searched.
    starting_date = data['starting_date']

    # Parse the date.
    starting_date = dateutil.parser.parse(starting_date)

    # Get the ending date form which the data is to be searched.
    ending_date = data['ending_date']

    # Parse the date.
    ending_date = dateutil.parser.parse(ending_date)

    # Get only date from the starting date value and combine it with the 'min' time.
    new_starting_date = datetime.datetime.combine(starting_date.date(), datetime.time.min)

    if search == []:

        # if no starting date is provided in the daterange search box.
        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

            # Gets all the data of the report files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await report_handle.find(
                {}, {'_id' : 0}).sort('file_date', 1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await report_handle.count_documents({
                "filename": {
                    '$regex': re.compile(f'.*{""}.*', re.IGNORECASE)
                }
            })

        else:
               
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await report_handle.find({
                '$and': [{
                            'file_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'file_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0}).sort('file_date', 1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await report_handle.count_documents({
                '$and': [{
                            'file_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'file_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            })

    else:

        # if no starting date is provided in the daterange search box.
        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

            # Gets all the data of the report files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await report_handle.find(
                {
                    "field": {
                        "$in" : search
                    }
                }, {'_id' : 0}).sort('file_date', 1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await report_handle.count_documents({
                "field": {
                    "$in": search
                }
            })

        else:
               
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await report_handle.find({
                'field' : {
                    '$in' : search
                },
                '$and': [{
                            'file_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'file_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0}).sort('file_date', 1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await report_handle.count_documents({
                'field' : {
                    '$in' : search
                },
                '$and': [{
                        'file_date' : {
                            '$gte' : new_starting_date
                        }
                    }, {
                        'file_date' : {
                            '$lt' : ending_date
                        }
                    }
                ]
            })

    # Tracking list to store the filtered records.
    filtered_json = []

    # Iterate over the fetched data.
    for record in report_list:

        # Convert each record into JSON string.
        record_json = json.dumps(record, default=json_util.default)

        # Add the JSON to the tracking list.
        filtered_json.insert(0, record_json)

    # Return the dictionary containing filtered records and total page count of filtered records.
    return{
        "data_list" : filtered_json,
        "total_pages" : math.ceil(count_report_list/10),
        'total_rows':count_report_list
    }


@app.post("/software_procurement_list")
async def software_procurement_list(request: fastapi.Request):
    """
    Fetch all the data of the uploaded software procurement files.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Files data to be displayed and count of the records.
    :rtype: dict
    """

    """
    starting_date.date(): From the frontend the search filter is sending starting_date which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so default value is provided for the comparison when all the suspected user has to be displayed.
    """

    # Get data from the request made.
    data = await request.json()

    # Get the keyword for which the data is to be searched.
    search = data['search']

    # Get the starting date from which the data is to be searched.
    starting_date = data['starting_date']

    # Parse the date.
    starting_date = dateutil.parser.parse(starting_date)

    # Get the ending date for which the data is to be searched.
    ending_date = data['ending_date']

    # Parse the date.
    ending_date = dateutil.parser.parse(ending_date)

    # Get only date from the starting date value and combine it with the 'min' time.
    new_starting_date = datetime.datetime.combine(starting_date.date(), datetime.time.min)

    # If no search keyword is provided.
    if search == "":

        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

                # Gets all the data of the software procurement files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
                report_list = await software_report.find(
                    {}, {'_id' : 0}).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
                
                # Count total number of documents in the results of the filtered records.
                count_report_list = await software_report.count_documents({})

        else:
            
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await software_report.find({
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0}).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await software_report.count_documents({
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }]})
            
    # If search keyword is provided in the search box.    
    else:
        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

                # Gets all the data of the software procurement files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
                report_list = await software_report.find(
                    {
                        "software_name": {
                                '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                        }
                    }, {'_id' : 0}).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
                
                # Count total number of documents in the results of the filtered records.
                count_report_list = await software_report.count_documents({
                    "software_name": {
                                '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                            }
                })

        else:
            
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await software_report.find({
                "software_name": {
                            '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                        },
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0}).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            count_report_list = await software_report.count_documents({
                "software_name": {
                            '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                        },
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            })
    # Tracking list to store the filtered records.
    filtered_json = []

    # Iterate over the fetched data.
    for record in report_list:

        # Convert each record into JSON string.
        record_json = json.dumps(record, default=json_util.default)

        # Add the JSON to the tracking list.
        filtered_json.insert(0, record_json)

    # Return the dictionary containing filtered records and total page count of filtered records.
    return{
        "data_list" : filtered_json,
        "total_pages" : math.ceil(count_report_list/10),
        'total_rows':count_report_list
    }

@app.get("/report_delete")
async def list_report(request: fastapi.Request):
    """
    Delete the report file.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Message that the file is deleted successfully.
    :rtype: dict
    """
    
    # Get data from the request made.
    data = await request.json()

    # Delete the file form the database based on the keyword `ref_hash`
    report_handle.delete_one({
        "ref_hash": data['f_hash']
    })
    
    # Return the messgae that the file is deleted successfully.
    return{
        "detail":"File successfully deleted"
    }


@app.get("/delete_software_procurement")
async def delete_software_procurement(request: fastapi.Request):
    """
    Delete the software procurement file.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Message that the file is deleted successfully.
    :rtype: dict
    """
    
    # Get data from the request made.
    data = await request.json()

    # Delete the file form the database based on the keyword `ref_hash`
    software_report.delete_one({
        "ref_hash": data['f_hash']
    })
    
    # Return the messgae that the file is deleted successfully.
    return{
        "detail":"File successfully deleted"
    }


@app.get("/report_download")
async def list_report(request: fastapi.Request):
    """
    Download the report file.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Return the file if found otherwise  a message that the file is not found.
    :rtype: dict
    """

    # Get data from the request made.
    data = await request.json()

    # Find on keyword `ref_hash` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
    report_list = await report_handle.find({
        "ref_hash": data['f_hash']
    }, {'_id' : 0}).to_list(1)

    print(report_list)
    
    # Return the file if present.
    if report_list:
        return {
            "file": report_list[0]
        }
    
    # Return the message that the file not found if the file is not present.
    else:
        return {
            "detail": "File not found"
        }
    

@app.get("/report_zip_download")
async def list_report(request: fastapi.Request):
    """
    Download the report file.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Return the file if found otherwise  a message that the file is not found.
    :rtype: dict
    """

    # Get data from the request made.
    data = await request.json()

    # Find on keyword `ref_hash` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
    report_list = await report_handle.find({
        "ref_hash": data['f_hash']
    }, {'_id' : 0}).to_list(1)
    
    # Return the file if present.
    if report_list:
        return {
            "file": report_list[0]
        }
    
    # Return the message that the file not found if the file is not present.
    else:
        return {
            "detail": "File not found"
        }
    
    
@app.get("/software_procurement_download")
async def list_report(request: fastapi.Request):
    """
    Download the software procurement records.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Return the file if found otherwise  a message that the file is not found.
    :rtype: dict
    """

    # Get data from the request made.
    data = await request.json()

    # Find on keyword `ref_hash` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
    software_procurement_list = await software_report.find({
        "ref_hash": data['f_hash']
    }, {'_id' : 0}).to_list(1)
    
    # Return the file if present.
    if software_procurement_list:
        return {
            "file": software_procurement_list[0]
        }
    
    # Return the message that the file not found if the file is not present.
    else:
        return {
            "detail": "File not found"
        }


@app.post('/download_software_report')
async def software_procurement_download(request: fastapi.Request):
    """
    Fetch all the data of the uploaded software procurement files.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Files data to be displayed and count of the records.
    :rtype: dict
    """

    """
    starting_date.date(): From the frontend the search filter is sending starting_date which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so default value is provided for the comparison when all the suspected user has to be displayed.
    """

    # Get data from the request made.
    data = await request.json()

    # Get the keyword for which the data is to be searched.
    search = data['search']

    # Get the starting date from which the data is to be searched.
    starting_date = data['starting_date']

    # Parse the date.
    starting_date = dateutil.parser.parse(starting_date)

    # Get the ending date for which the data is to be searched.
    ending_date = data['ending_date']

    # Parse the date.
    ending_date = dateutil.parser.parse(ending_date)

    # Get only date from the starting date value and combine it with the 'min' time.
    new_starting_date = datetime.datetime.combine(starting_date.date(), datetime.time.min)

    # If no search keyword is provided.
    if search == "":

        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

                # Gets all the data of the software procurement files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
                report_list = await software_report.find(
                    {}, {'_id' : 0, 
                'ref_hash': 0,
                'filesize' : 0,
                'created_date' : 0
                }).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)

        else:
            
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await software_report.find({
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0, 
                'ref_hash': 0,
                'filesize' : 0,
                'created_date' : 0
                }).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
            
    # If search keyword is provided in the search box.    
    else:

        if starting_date.date() == datetime.datetime(1970, 1, 1).date():

                # Gets all the data of the software procurement files uploaded --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
                report_list = await software_report.find(
                    {
                        "filename": {
                                '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                        }
                    }, {'_id' : 0, 
                    'ref_hash': 0,
                    'filesize' : 0,
                    'created_date' : 0
                    }).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)

        else:
            
            # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
            report_list = await software_report.find({
                "filename": {
                            '$regex': re.compile(f'.*{search}.*', re.IGNORECASE)
                        },
                '$and': [{
                            'purchase_date' : {
                                '$gte' : new_starting_date
                            }
                        }, {
                            'purchase_date' : {
                                '$lt' : ending_date
                            }
                        }
                ]
            }, {'_id' : 0, 
                'ref_hash': 0,
                'filesize' : 0,
                'created_date' : 0
                }).sort('purchase_date', -1).skip((data['page_id'] - 1 ) * 10).to_list(10)
             
 
    # Converts the 'report list' into pandas dataframe.     
    df = pandas.DataFrame(report_list)
    df['purchase_date'] = df['purchase_date'].dt.strftime('%a %d %B %Y')
    df['approval_date'] = df['approval_date'].dt.strftime('%a %d %B %Y')
    
    # # Generate a unique '.xlsx' file name to store the data.
    f_name = uuid.uuid1().hex + '.xlsx'

    # Converts the pandas dataframe into a excel sheet.
    df.to_excel(f'download_folder/{f_name}',index=False)

    # Asynchronously streams a file as the response.
    # Return the file path directly from the path operation function.
    return fastapi.responses.FileResponse(f'download_folder/{f_name}')


@app.post("/overview_software_list")
async def software_list(request: fastapi.Request):
    """
    Fetch software name and its status for overview page.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Files data to be displayed and count of the records.
    :rtype: dict
    """
    try:
        # Find on keyword `file_date` --> remove `_id` from the filtered document --> sort by 'file_date' --> skip to results on `page_id` --> convert to list.
        report_list = await software_report.find({},{
            '_id' : 0,
            'software_name' : 1,
            'current_status' : 1
        }).sort('purchase_date', 1).to_list(length=None)

        total_rows = await software_report.count_documents({})

        # Tracking list to store the filtered records.
        filtered_json = []

        # Iterate over the fetched data.
        for record in report_list:

            record['software_name'] = record['software_name'].replace('Tatkal', '').replace('Booking','').replace('Software', '').replace('Ticket', '').strip()

            # Convert each record into JSON string.
            record_json = json.dumps(record, default=json_util.default)

            # Add the JSON to the tracking list.
            filtered_json.insert(0, record_json)

        # Return the dictionary containing filtered records and total page count of filtered records.
        return{
            "data_list" : filtered_json,
            "software_count" : total_rows
        }
    
    except Exception as e:
        print(e.msg())
        return{
            'detail' : 'Failed to get data'
        }


if __name__ == "__main__":
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=55571,
        reload=True
    )
