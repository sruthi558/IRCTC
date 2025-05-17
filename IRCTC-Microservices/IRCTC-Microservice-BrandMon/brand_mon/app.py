# Import libraries
import os
import re
import io
import PIL
import json
import uuid
import math
import numpy as np
import pandas
import typing
import fastapi
import hashlib
import uvicorn
import logging
import datetime
import requests
import openpyxl
import pydantic
import bson.objectid
import dateutil.parser
import pydantic_settings
from bson import json_util
import motor.motor_asyncio
import openpyxl_image_loader
from fastapi_cache import FastAPICache
from concurrent.futures import ProcessPoolExecutor
from fastapi_cache.backends.inmemory import InMemoryBackend


# Logger function.
def BrandMonitoringLogger():

    # Create a logger.
    logger = logging.getLogger("BrandMonitoring")

    # The level of the logger is set to 'INFO'
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(threadName)s:%(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('bradmon.log')

    # Set the format for the logged data.
    file_handler.setFormatter(formatter)

    # Add the handler to the logger.
    logger.addHandler(file_handler)

    # Return the logger.
    return logger

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


client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)

# Get reference to the database `MONGO_DB`.
db = client[settings.MONGO_DB]



class BrandMonitoring(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data to be shown on Brand Monitoring page.
    """
    # Page ID with initial value '1'.
    page_id: typing.Optional[int] = 1

    # Default value as '0'.
    status: typing.Optional[int] = 0

    # Starting date with default value as current date.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Ending date with default value as current date.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

    # Default value as empty string.
    search: typing.Optional[str] = ''

    # Default value as 'False'.
    visibility: typing.Optional[bool] = False



class BrandMonitoringVisible(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data for brand monitoring visibility.
    """

    # Default value set to 'False.'.
    show: typing.Optional[bool] = False

    # Cell id with default value as empty string.
    cellid: typing.Optional[str] = ''



class BrandMonitoringStatus(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data for brand monitoring status.
    """
    # Default value as '0'.
    status: typing.Optional[int] = 0

    # Cell id with default value as empty string.
    cellid: typing.Optional[str] = ''

    # Takedown date with default value as current date.
    takedown_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

    # Default value as empty string.
    username: typing.Optional[str] = ''



class BrandMonitoringTakeDown(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data for brand monitoring takedown.
    """
    # Page ID with initial value '1'.
    page_number: typing.Optional[int] = 1

    # Status with initial value '0'.
    status: typing.Optional[int] = 0

    # Starting date with default value as current date.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Ending date with default value as current date.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

    # Default value as empty string.
    search: typing.Optional[str] = ''

    # Default value as 'False'.
    visibility: typing.Optional[bool] = False


class cardModal(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data to be shown on cards of brand monitoring page.
    """
    # Page ID with initial value '1'.
    page_id: typing.Optional[int] = 1

    severity: typing.Optional[list] = []

    threatSource: typing.Optional[list] = []

    takedownAction: typing.Optional[str] = ''
 
    # Starting date with default value as current date.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Ending date with default value as current date.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

class ToutCardData(pydantic.BaseModel):

    # Page ID with initial value '1'.
    page_id: typing.Optional[int] = 1

    search : typing.Optional[str] = ''


class SuspiciousMobile(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data to be shown table on suspected mobile numbers page.
    """
    page_id : typing.Optional[int] = 1

    month : typing.Optional[str] = ""

async def get_file_size_in_MB(filepath):
    """Summary

    Args:
        filepath (TYPE): Description

    Returns:
        TYPE: Description
    """
    filesize = os.path.getsize(filepath)
    filesize_in_MB = filesize / 1024 / 1024
    filesize_in_MB = round(filesize_in_MB, 2)
    return filesize_in_MB

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

def format_string(str_data):
    str_data = re.sub(r'\n+', ',', str_data)
    str_data = re.sub(r',+', ',', str_data)
    return str_data.split(',')
    
# Create a collection for brand monitoring page.
brandmonitoring_collection_handle = db.irctc_brand_mon_test_new
sus_mobile_num = db.irctc_sus_mobile_numbers_test_1
col_overdash = db.irctc_over_dash_const_1
col_tout_handle = db.irctc_tout_data


KEYWORDS = ["tatkal software", "tatkal", "nexus", "sikka", "disha", "super ts", "ticket", "train", "railway", "irctc", "blackberry", "pnr", "gadar", "bullet", "eagle", "mirchi"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def check_keywords(text):
    # Create all the paterns of the list keywords along which check ismade.
    pattern = re.compile('|'.join(KEYWORDS), re.IGNORECASE)

    # Stores all the matches found 
    matches = pattern.findall(text)
    return matches


def check_web_status(websites: list):

    # Loop through the list of the websites.
    for web in websites:
        check_web = str(web)

        # Check if website contains any scheme or not --> Update if no scheme is found.
        if any(scheme in check_web for scheme in ['http', 'https', 'www']):pass
        else: check_web = 'http://'+check_web

        try:

            # Get the response from the website.
            response = requests.get(check_web, headers=HEADERS)
            response.raise_for_status()

            # Check if the status code of the response is 200.
            if response.status_code == 200:

                # Set to stores unique keywords found on the website from the keyword list.
                finalKeywordList = set()
                
                # Get the keywords found frot the response.
                keywordsFound = check_keywords(response.text)

                # Update the unique keyword set.
                for key in keywordsFound: 
                    if str(key).lower() not in finalKeywordList: finalKeywordList.add(key)

                # Update the collection with the status `ACTIVE`and the keywords found.
                brandmonitoring_collection_handle.update_one({
                    'Link': web
                    },{
                        "$set": {
                            'presentStatus': "Active",
                            'keywordsFound': ", ".join(finalKeywordList)
                        }
                })
      
            else:
                # Update the collection with the status `ACTIVE`and the keywords found.
                brandmonitoring_collection_handle.update_one({
                    'Link': web
                    },{
                        "$set": {
                            'presentStatus': "Active",
                            'keywordsFound': ""
                            
                        }
                })
        except:
            # If no response if found then update the collection with `Inactive` status.
            brandmonitoring_collection_handle.update_one({
                    'Link': web
                    },{
                        "$set": {
                            'presentStatus': "Inactive",
                            'keywordsFound': ""   
                        }
                })


@app.post('/upload_brand_data', response_description="Fetch the data from the uploaded file")
async def sus_mobile_upload(file: fastapi.UploadFile, response: fastapi.Response, background_task: fastapi.BackgroundTasks) -> dict:
    """
    Analyse the uploaded file.

    :param file: Stores the uploaded file.
    :ptype: fastapi.UploadFile.

    :returns: Filename and its saved location.
    :rtype: dict
    """
    # logger = BrandMonitoringLogger()

    try:

        file_location = f"files/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        df = pandas.read_excel(file_location)

        # Sort the dataFrame header names.
        FILE_HEADERS = df.columns.values.tolist().sort()
        CHECK_HEADER = ['Threat_Source','Severity','Urls', 'Title', 'Takedown_Action', 'Requested_Date', 'Present_Status', 'Remarks'].sort()

        # Checking for valid headers in the file
        if FILE_HEADERS != CHECK_HEADER:
            response.status_code = 406 
            return {'detail': f'Headers format incorrect in file !'}
        
        # rename the columns according to the database fields
        df.rename(columns={'Threat_Source': 'threatSource', 'Severity' : 'Severity', 'Urls' : 'Links', 'Title':'Title', 'Takedown_Action':'takedownAction', 'Requested_Date':'requestedDate', 'Present_Status':'presentStatus', 'Remarks':'Remarks'}, inplace=True)

        df = df.fillna('')

        # Stores the list of urls along the variable links.
        links = df['Links'].to_list()

        # Iterate over the rows of the dataframe one by one.
        for index, row in df.iterrows():

            # Update the brandmon collection with the uploaded data.
            brandmonitoring_collection_handle.update_one({
                'Link': row['Links'].strip()
            },{
                "$set": {
                    'threatSource': row['threatSource'].strip(),
                    'Severity': row['Severity'].strip(),
                    'title': row['Title'].strip(),
                    'takedownAction': row['takedownAction'].strip(),
                    'requestedDate':  row['requestedDate'],
                    'presentStatus': row['presentStatus'].strip(),
                    'Remarks': row['Remarks'].strip()
                }
            }, upsert=True)

        # Run background task to check the active/inactive status of the website.
        background_task.add_task(check_web_status, links)

        return {
            "detail": "File Uploaded Successfully"
        }

    except Exception as e:
        return{
            "status": 500,
            "msg": "Failed to upload File"
        }


# NOT IN USE
@app.get('/bm_card_count')
async def card_count(request: fastapi.Request):
    """
    Displays count of takedown requested, takedown initiated, takedown completed.

    :return: Data to be displayed.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        
        # Total count of documents with `td_status` as 1.
        takedown1 = await brandmonitoring_collection_handle.count_documents({
            'td_status': 1,
            'visible': True
        })

        # Total count of documents with `td_status` as 2.
        takedown2 = await brandmonitoring_collection_handle.count_documents({
            'td_status': {
                '$in': [2,5]
            },
            'visible': True
        })

        # Total count of documents with `td_status` as 3.
        takedown3 = await brandmonitoring_collection_handle.count_documents({
            'td_status': 3,
            'visible': True
        })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        return {
            'takedown_req': takedown1, 
            'takedown_init': takedown2, 
            'takedown_comp': takedown3
        }

    except:
        
        # Log error message in the log file.
        logger.error(f"Failed to get card count data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get card count data"
        }


# NOT I  USE
@app.post('/bm_all_count', response_description="Fetch all brand monitoring data count")
async def list_bm_count(brand_monitoring: BrandMonitoring, request: fastapi.Request):
    """
    Displays count of total number of documents in data collection.

    :param brand: Gives the received data based on BrandMonitoring model.
    :ptype: BrandMonitoring model

    :return: Count of documents.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        
        # Checks for visibility.
        if (brand_monitoring.visibility):

            # Total count of documents.
            data_count = await brandmonitoring_collection_handle.estimated_document_count()

        else:

            # Total count of documents with `visible` as True.
            data_count = await brandmonitoring_collection_handle.count_documents({'visible': True})

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        return {
            'page_count': data_count
        }

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get total count data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get total count data"
        }


@app.post('/bm_all', response_description="List all brand monitoring data")
async def list_bm(brand_monitoring: BrandMonitoring, request: fastapi.Request) -> dict:
    """
    Displays list of brand monitoring data.

    :param brand: Gives the received data based on BrandMonitoring model.
    :ptype: BrandMonitoring

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:

        # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.
        if brand_monitoring.search == "":

            if brand_monitoring.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                bm_data = await brandmonitoring_collection_handle.find(
                    {},{
                        "_id":0
                    }).sort('requestedDate', -1).skip((brand_monitoring.page_id - 1) * 10).to_list(10)

                document_count = await brandmonitoring_collection_handle.count_documents({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    }
                })
            
            else:

                # Find on (keyword search) --> check if `created_dt` less than `ending_date` --> skip to results on `page_number` --> convert to list.
                bm_data = await brandmonitoring_collection_handle.find({
                    '$and': [
                        {
                            'requestedDate' : {
                                '$gte' : brand_monitoring.starting_date
                            }
                        }, {
                            'requestedDate': {
                                '$lte': brand_monitoring.ending_date
                            }
                        }
                    ]},{
                        "_id":0
                    }).sort('requestedDate', -1).skip((brand_monitoring.page_id - 1) * 10).to_list(10)
                
                document_count = await brandmonitoring_collection_handle.count_documents({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    },
                    '$and': [
                        {
                            'requestedDate' : {
                                '$gte' : brand_monitoring.starting_date
                            }
                        }, {
                            'requestedDate': {
                                '$lte': brand_monitoring.ending_date
                            }
                        }
                    ]
                })
            
        else:

            if brand_monitoring.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                bm_data = await brandmonitoring_collection_handle.find({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    }
                },{
                    "_id":0
                }).sort('requestedDate', -1).skip((brand_monitoring.page_id - 1)*10).to_list(10)

                document_count = await brandmonitoring_collection_handle.count_documents({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    }
                })
                
            else:

                # Check if `created_dt` less than `ending_date` --> skip to results on `page_number` --> convert to list.
                bm_data = await brandmonitoring_collection_handle.find({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    },
                    '$and' : [
                        {
                            'requestedDate' : {
                                '$gte' : brand_monitoring.starting_date
                            }
                        },
                        {
                            'requestedDate': {
                                '$lte': brand_monitoring.ending_date
                            }
                        }
                    ]},{
                        "_id":0
                    }).sort('requestedDate', -1).skip((brand_monitoring.page_id-1)*10).to_list(10)
                
                document_count = await brandmonitoring_collection_handle.count_documents({
                    'title': {
                            '$regex': re.compile(f'.*{brand_monitoring.search}.*', re.IGNORECASE)
                    },
                    '$and' : [
                        {
                            'requestedDate' : {
                                '$gte' : brand_monitoring.starting_date
                            }
                        },
                        {
                            'requestedDate': {
                                '$lte': brand_monitoring.ending_date
                            }
                        }
                    ]
                })

        # List to store data in the form of json string.
        filtered_records_json = []

        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in bm_data:
            # Convert each record into json string.
            record_json = json.dumps(record, default=json_util.default)

            # Store json string record in the list.
            filtered_records_json.insert(0, record_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        page_count = math.ceil(document_count/10)

        takedown_initiated = await brandmonitoring_collection_handle.count_documents({
            'takedownAction': {
                '$in' : ["Takedown Initiated", "Takedown Completed"]
            },
        })

        takedown_completed = await brandmonitoring_collection_handle.count_documents({
            'takedownAction': "Takedown Completed",
        })

        col_overdash.update_one({
            "NAME" : "OVER_DATA"
        },{
            "$set": {
                "TAKEDOWN_INITIATED": takedown_initiated,
                "TAKEDOWN_COMPLETED": takedown_completed
            }
        })

        
        # Returns the data to be displayed.
        return {
            'data_list': filtered_records_json, 
            'total_pages': page_count,
            'total_rows': document_count,
            'takedown_initiated': takedown_initiated,
            'takedown_completed': takedown_completed
        }

    except Exception as e:

        logger.error(f"Failed to get brandmonitoring data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get Brandmon data"
        }


@app.post('/bm_card_modal', response_description="List brand monitoring cards")
async def bm_card_modal(card_modal: cardModal, request: fastapi.Request):
    """
    Displays the data on card model for brand monitoring page.

    :param cardbrandmonModal: Gives the received data based on cardModal model.
    :ptype: cardModal model

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        card_modal.starting_date = datetime.datetime.combine(card_modal.starting_date.date(), datetime.time.min) 

        if card_modal.takedownAction != 'Takedown Completed': card_modal.takedownAction = ["Takedown Completed", "Takedown Initiated"]
        else: card_modal.takedownAction = ["Takedown Completed"]
        
        if card_modal.severity == [] and card_modal.threatSource == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    }
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(10)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                })

            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction':{
                        '$in' : card_modal.takedownAction
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(1000)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                })

        elif card_modal.severity == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    }
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(10)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                            '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    }
                })

            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': {
                            '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(1000)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                })

        elif card_modal.threatSource == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    }
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(10)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                })

            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(1000)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                })
        
        else:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    }
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(10)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                })

            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).skip((card_modal.page_id-1)*10).to_list(1000)

                
                # Store the total number of documents present in the results of the filtered data.
                data_count = await brandmonitoring_collection_handle.count_documents({
                    'takedownAction': {
                        '$in' : card_modal.takedownAction
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                })
            
        # List to store data in the form of json string.
        filtered_records_json = []

        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in data:
            # Convert each record into json string.
            record_json = json.dumps(record, default=json_util.default)

            # Store json string record in the list.
            filtered_records_json.insert(0, record_json)
        
        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Returns the data to be displayed.
        page_count = math.ceil(data_count/10)
            
        # Returns the data to be displayed.
        return {
            'data_list': filtered_records_json, 
            'total_pages': page_count,
            'total_rows': data_count
        }

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get brandmonitoring data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get brandmon modal data"
        }
    

@app.post('/brand_card_download', response_description="List brand monitoring cards")
async def bm_card_modal_download(card_modal: cardModal, request: fastapi.Request):
    """
    Displays the data on card model for brand monitoring page.

    :param cardbrandmonModal: Gives the received data based on cardModal model.
    :ptype: cardModal model

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        card_modal.starting_date = datetime.datetime.combine(card_modal.starting_date.date(), datetime.time.min) 
        
        if card_modal.severity == [] and card_modal.threatSource == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': card_modal.takedownAction
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)


            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': card_modal.takedownAction,
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)


        elif card_modal.severity == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'takedownAction': card_modal.takedownAction
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)
                

            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': card_modal.takedownAction,
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)


        elif card_modal.threatSource == []:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    'takedownAction': card_modal.takedownAction
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)


            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': card_modal.takedownAction,
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)

        
        else:

            # To Filter all the brand monitoring card modebm_carl data.
            if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            
                data = await brandmonitoring_collection_handle.find({
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'takedownAction': card_modal.takedownAction
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)


            # To Filter all the brand monitoring card model data when date range is provided.
            else:

                # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
                data = await brandmonitoring_collection_handle.find({
                    'takedownAction': card_modal.takedownAction,
                    'threatSource':{
                        '$in': card_modal.threatSource
                    },
                    'Severity':{
                        '$in': card_modal.severity
                    },
                    '$and' : [
                            {
                                'requestedDate' : {
                                    '$gte' : card_modal.starting_date
                                }
                            },
                            {
                                'requestedDate': {
                                    '$lte': card_modal.ending_date
                                }
                            }
                    ]
                },{
                    "_id":0
                }).sort('requestedDate',-1).to_list(10000)
            
        df = pandas.DataFrame(data)
        df['requestedDate'] = df['requestedDate'].dt.strftime('%a %d %B %Y')

        print(df)

        # # Generate a unique '.xlsx' file name to store the data.
        f_name = uuid.uuid1().hex + '.xlsx'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}',index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get brandmonitoring data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get brandmon modal data"
        }
    

@app.post('/bm_card_download', response_description="List brand monitoring cards")
async def bm_card_download(card_modal: cardModal, request: fastapi.Request):
    """
    Displays the data on card model for brand monitoring page.

    :param cardbrandmonModal: Gives the received data based on cardModal model.
    :ptype: cardModal model

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:

        card_modal.starting_date = datetime.datetime.combine(card_modal.starting_date.date(), datetime.time.min) 

        # To Filter all the brand monitoring card model data.
        if card_modal.starting_date.date() == datetime.datetime(1970, 1, 1).date():
        
            # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
            data = await brandmonitoring_collection_handle.find({
                '$and': [
                    {
                        'visible': True
                    }, {
                        'td_status': {
                            '$in': card_modal.status
                        }
                    }
                ]}, {
                    '_id': 0, 
                    'threatSource': 1, 
                    'category': 1,  
                    'created_dt': 1, 
                    'threatSeverity': 1, 
                    'threat_score': 1, 
                    'Link': 1, 
                    'ProfileName': 1, 
                    'td_status': 1, 
                    'Snapshot' : 1, 
                    'visible': 1
                }).sort('td_req_dt',-1).to_list(1000)
            
        # To Filter all the brand monitoring card model data when date range is provided.
        else:

            # Find on (visible) and (td_status) --> sort by `td_req_dt` in descending order --> convert to list.
            data = await brandmonitoring_collection_handle.find({
                '$and': [
                    {
                        'visible': True
                    }, {
                        'td_status': {
                            '$in': card_modal.status
                        }
                    }, {
                        'created_dt' : {
                            '$gte' : card_modal.starting_date
                        }
                    }, {
                        'created_dt': {
                            '$lte' : card_modal.ending_date
                        }
                    }  
                ]}, {
                    '_id': 0, 
                    'threatSource': 1, 
                    'category': 1,  
                    'created_dt': 1, 
                    'threatSeverity': 1, 
                    'threat_score': 1, 
                    'Link': 1, 
                    'ProfileName': 1, 
                    'td_status': 1, 
                    'Snapshot' : 1, 
                    'visible': 1
                }).sort('td_req_dt',-1).to_list(1000)
        
        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(data)

        print(df)

        # # Generate a unique '.xlsx' file name to store the data.
        f_name = uuid.uuid1().hex + '.xlsx'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}',index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get brandmonitoring data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get brandmonitoring data"
        }


# NOT IN USE
@app.post("/bm_change_visible", response_description="Change Brand Mon Card Visibilty")
async def bm_visible(brand_monitoring_visible: BrandMonitoringVisible, request: fastapi.Request):
    """
    Changes the visibility of brand monitoring card.

    :param brandmonchangevisibility: Gives the received data based on BrandMonitoringVisible model.
    :ptype: BrandMonitoringVisible model

    :return: Status code and message for successful change.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        
        # Update the `visible` to True or False.
        brandmonitoring_collection_handle.update_one({
            '_id': bson.objectid.ObjectId(brand_monitoring_visible.cellid)
            }, {
                '$set': {
                    'visible': brand_monitoring_visible.show
                }
            })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Returns the data to be displayed.
        return {
            "status":200,
            "msg":"Changed Visibilty"
        }

    except:
        # Log error message in the log file.
        logger.error(f"Failed to change visibility status:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to change visibility status"
        }


# NOT IN USE
@app.post("/bm_change_status", response_description="Change Brand Mon Card Status")
async def bm_change_status(brand_monitoring_status: BrandMonitoringStatus, request: fastapi.Request):
    """
    Changes the status of brand monitoring card.

    :param brandmonchangestatus: Gives the received data based on BrandMonitoringStatus model.
    :ptype: BrandMonitoringStatus model

    :return: Status code and message for successful change.
    :rtype: dict
    """

    """
    <int: 1> : Request Pending
    <int: 2> : Initiate Takedown
    <int: 3> : Takedown Initiated
    <int: 4> : Takedown Completed
    <int: 5> : Takedown Rejected
    """

    logger = BrandMonitoringLogger()

    try:
        
        # Update the `td_status` to requested status(int) and `ts_req_dt` to current time.
        brandmonitoring_collection_handle.update_one({
            '_id': bson.objectid.ObjectId(brand_monitoring_status.cellid)
            }, {
                '$set': {
                    'td_status': brand_monitoring_status.status, 
                    'td_req_dt': datetime.datetime.now()
                }
            })
        
        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Returns the data to be displayed.
        return {
            "status":200,
            "msg":"Changed Status"
        }

    except:
        # Log error message in the log file.
        logger.error(f"Failed to change status :{request.url}")

        return{
            "status": 500,
            "msg": "Failed to change status"
        }


# NOT IN USE
@app.post("/bm_takedown_list", response_description="Displays takedown list in a table")
async def bm_takedown_list(brand_monitoring_take_down : BrandMonitoringTakeDown, request: fastapi.Request):
    """
    Displays list of takedowns along with the page count.

    :param brandmontakedownmodal: Gives the received data based on BrandTakeDownModal model.
    :ptype: BrandTakeDownModal model

    :return: Data to be displayed count of pages.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:
        
        # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.
        if len(brand_monitoring_take_down.search) > 2:
            # Check if `visible` is True --> check if `td_status` greater than 0 --> find on (keyword search) --> check if `created_dt` in range between `starting_date` and `ending_date` --> sort by `td_req_dt` in descending order --> skip to results on `page_number` --> convert to list.
            data = await brandmonitoring_collection_handle.find({
                '$and': [
                    {
                        'visible': True
                    }, {
                        'td_status': {
                            '$gt': 0
                        }
                    }, {
                        '$text': {
                            '$search': brand_monitoring_take_down.search
                        }
                    }, {
                        '$and': [
                            { 
                                'created_dt': {
                                    '$gte': brand_monitoring_take_down.starting_date
                                }
                            }, {
                                'created_dt': {
                                    '$lte': brand_monitoring_take_down.ending_date
                                }
                            }
                        ]
                    }
                ]
                }, {
                    '_id': 1, 
                    'threatSource': 1, 
                    'category': 1,
                    'td_req_dt': 1, 
                    'created_dt': 1, 
                    'threatSeverity': 1, 
                    'Link': 1, 
                    'ProfileName': 1, 
                    'td_status': 1
                }).sort('td_req_dt', -1).skip((brand_monitoring_take_down.page_number - 1) * 10).to_list(10)
            
        # Filter if the length of the text(data) to be searched is less than '2'.
        else: 
            
            # Check if `visible` is True --> check if `td_status` greater than 0  --> check if `created_dt` in range between `starting_date` and `ending_date` --> sort by `td_req_dt` in descending order --> skip to results on `page_number` --> convert to list.
            data = await brandmonitoring_collection_handle.find({
                '$and': [
                    {
                        'visible': True
                    }, {
                        'td_status': {
                            '$gt': 0
                        }
                    }, {
                        '$and': [
                            {
                                'created_dt': {
                                    '$gte': brand_monitoring_take_down.starting_date
                                }
                            }, {
                                'created_dt': {
                                    '$lte': brand_monitoring_take_down.ending_date
                                }
                            }
                        ]
                    }
                ]
                }, {
                    '_id': 1, 
                    'threatSource': 1, 
                    'category': 1, 
                    'created_dt': 1, 
                    'threatSeverity': 1,
                    'td_req_dt': 1, 
                    'Link': 1, 
                    'ProfileName': 1, 
                    'td_status': 1
                }).sort('td_req_dt',-1).skip((brand_monitoring_take_down.page_number-1)*10).to_list(10)

        # List to store data in the form of json string.
        filtered_records_json = []

        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in data:
            # Convert each record into json string.
            record_json = json.dumps(record, default=json_util.default)

            # Store json string record in the list.
            filtered_records_json.insert(0, record_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Returns the data to be displayed.
        return {
            'data_list': filtered_records_json , 
            'page_count': 117
        }

    except:
        # Log error message in the log file.
        logger.error(f"Failed to get brandmonitoring takedown list data :{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get brandmonitoring takedown list data :{request.url}"
        }


# NOT IN USE
@app.post("/bm_new_req", response_description="Takes the new request raised from dashboard")
async def bm_new_req(request: fastapi.Request):
    data = await request.json()
    brandmonitoring_collection_handle.insertOne(
        {
            'ProfileName' : data['ProfileName'],
            'Link' : data['Source'],
            'visible' : True,
            
            'created_dt' : datetime.datetime.now()
        }
    )


@app.post('/upload-sus-mobile', response_description="Fetch the data from the uploaded file")
async def sus_mobile_upload(file: fastapi.UploadFile,request: fastapi.Request, response: fastapi.Response) -> dict:
    """
    Analyse the uploaded file.

    :param file: Stores the uploaded file.
    :ptype: fastapi.UploadFile.

    :returns: Filename and its saved location.
    :rtype: dict
    """
    logger = BrandMonitoringLogger()

    data = str(request.url)
    username = data.split("?")[1].split("=")[1]
    

    try:

        file_location = f"files/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        df = pandas.read_excel(file_location)

        # Checking for valid headers in the file
        if df.columns.values.tolist().sort() != ['MOBILE_NUMBER','STATUS','SOURCE','MONTH'].sort():
            response.status_code = 406 
            return {'detail': f'Headers format incorrect in file !'}
        
        # rename the columns according to the database fields
        df.rename(columns={'MOBILE_NUMBER': 'mobile_no', 'SOURCE': 'source', 'STATUS' : 'status', 'MONTH' : 'month'}, inplace=True)

        # File month fetched
        month = df['month'].values[0]

        # datetime for the current month
        df['month_str'] = [pandas.to_datetime(str(month)).strftime('%B %Y')]*len(df)

        # iterate over dataframe and update the records if exists else insert new one
        for index, row in df.iterrows():
            sus_mobile_num.update_one({
                'mobile_no':row['mobile_no']
                },{
                '$addToSet' : {
                    'upload_history':{
                        "LoggedIn_username": username,
                        "LoggedIn_date": datetime.datetime.now()
                    }
                },
                '$set' : {'latest_username': username,'source':row['source'],'status': row['status'], 'month_str' : row['month_str'], 'month' : row['month']}},upsert=True)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the dictionary containing file name and the location where it is saved.
        return {
            "detail": "File Uploaded Successfully"
        }

    except Exception as e:
        print(e)
        # Log error message in the log file.
        logger.error("File analysis failed':{request.url}")

        return {
            "status": 500,
            "detail": "File analysis failed"
        }

@app.post("/sus-mobile-list",response_description = "List suspicious mobile numbers")
async def sus_mobile_list(sus_mobile : SuspiciousMobile, request : fastapi.Request):
    """
    Lists all Suspicious Mobile Numbers.
    Fetch the data to be displayed in the table.

    :param infra: Gives the received data based on SuspiciousMobile model.
    :ptype: SuspiciousMobile model.

    :return: Data to be displayed and count of pages.
    :rtype: dict

    """
    logger = BrandMonitoringLogger()

    try:

        # Search data based on the given month filter
        if sus_mobile.month != "":

            # fetch month for the given input
            month = sus_mobile.month.split(" ")[0]

            # Find records for the received year
            if month == "All":

                year = sus_mobile.month.split(" ")[1]
                
                # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                data = await sus_mobile_num.find({"month_str" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0,'month' : 0}).sort('month',-1).skip((sus_mobile.page_id - 1) * 20).to_list(20)
            
                # Count total number of documents in the results of the filtered data.
                document_count = await sus_mobile_num.count_documents({"month_str" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}})

            else:
                # Find on 'month' --> skip to results on `page_id` --> convert to list.
                data = await sus_mobile_num.find({"month_str" : sus_mobile.month}, {'_id' : 0,'month' : 0}).sort('month',-1).skip((sus_mobile.page_id - 1) * 20).to_list(20)

                # Count total number of documents in the results of the filtered data.
                document_count = await sus_mobile_num.count_documents({"month_str" : sus_mobile.month})

        # Fetch the whole data if month is not present
        else:

            data = await sus_mobile_num.find({},{'_id' : 0,'month' : 0}).sort('month',-1).skip((sus_mobile.page_id - 1) * 20).to_list(20)

            # Count total number of documents in the results of the search filter.
            document_count = await sus_mobile_num.count_documents({})
        
        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for record in data:

            # Convert each record into JSON string.
            record_json = json.dumps(record, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        page_count = math.ceil(document_count/20)

        # Return the dictionary containing filtered records and total page count of filtered records.
        return {
            'data_list': filtered_records_json[::-1], 
            'total_pages' : page_count,
            'total_rows': document_count
        }

    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to get data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get table data"
        }


@app.post("/file_download")
async def log_download(sus_mobile : SuspiciousMobile,request: fastapi.Request):
    """
    Download the suspicous numbers file.

    :param request: Gets the request coming to the route.
    :ptype: fastapi.Request.

    :return: Return the file if found otherwise  a message that the file is not found.
    :rtype: dict
    """

    logger = BrandMonitoringLogger()

    try:

        # Search data based on the given month filter  
        if sus_mobile.month != "":

            # fetch month for the given input
            month = sus_mobile.month.split(" ")[0]

            # Find records for the received year
            if month == "All":

                year = sus_mobile.month.split(" ")[1]
                
                # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                data = await sus_mobile_num.find({"month_str" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0, 'month':0,'upload_history' : 0}).sort('month',-1).to_list(10000)
            
            else:
                # Find on 'month' --> skip to results on `page_id` --> convert to list.
                data = await sus_mobile_num.find({"month_str" : sus_mobile.month}, {'_id' : 0,'month':0,'upload_history' : 0}).sort('month',-1).to_list(10000)
            
        # Fetch the whole data if month is not present
        else:

            data = await sus_mobile_num.find({}, {'_id' : 0, 'month':0,'upload_history':0}).sort('month',-1).to_list(10000)
        
        # Converts the 'fetched data' into pandas dataframe.     
        df = pandas.DataFrame(data)

        # # Generate a unique '.xlsx' file name to store the data.
        f_name = uuid.uuid1().hex + '.xlsx'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}',index=False)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to get data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get table data"
        }
    

# TOUT SECTION
@app.post('/upload_tout_data', response_description="Fetch the data from the uploaded file")
async def tout_data_upload(file: fastapi.UploadFile, response: fastapi.Response) -> dict:
    """
    Analyse the uploaded file.

    :param file: Stores the uploaded file.
    :ptype: fastapi.UploadFile.

    :returns: Filename and its saved location.
    :rtype: dict
    """

    try:
        file_location = f"files/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        workbook = openpyxl.load_workbook(file_location)
        cell_values = list()

        sheet = workbook.worksheets[0]
        image_loader = openpyxl_image_loader.SheetImageLoader(sheet)

        FILE_HEADERS = list()
        for i in list(sheet.values)[0]:
            if i is not None: FILE_HEADERS.append(str(i).strip())
        
        FILE_HEADERS_TEMP = FILE_HEADERS[:]
        CHECK_HEADER = ['Name', 'Contact', 'Email', 'Website', 'Youtube', 'Telegram', 'Whatsapp', 'Image', 'Others'].sort()

        # Checking for valid headers in the file
        if FILE_HEADERS_TEMP.sort() != CHECK_HEADER:
            response.status_code = 406 
            return {'detail': f'Headers format incorrect in file !'}
        
        count = 1
        
        for row in sheet.values:
            value = [str(i).strip() if i is not None else "" for i in list(row) ]
            if value != FILE_HEADERS:
                data = dict(zip(FILE_HEADERS, value))
                data.update({
                    'Name' : format_string(data.get('Name', '')),
                    'Contact' : format_string(str(data.get('Contact', ''))),
                    'Email' : format_string(data.get('Email', '')),
                    'Website' : format_string(data.get('Website', '')),
                    'Telegram' : format_string(data.get('Telegram', '')),
                    'Whatsapp' : format_string(data.get('Whatsapp', '')),
                    'Youtube' : format_string(data.get('Youtube', '')),
                    'Others' : format_string(data.get('Others', ''))
                })

                try:
                    image = image_loader.get('H'+str(count))
                    image = image.convert('RGB')
                    image.save(f'img_folder/tout{count}.jpg')
                    im = PIL.Image.open(f"img_folder/tout{count}.jpg")

                    image_bytes = io.BytesIO()
                    im.save(image_bytes, format='JPEG')

                    image = image_bytes.getvalue()

                    data.update({
                        'Image' : image
                    })
                except Exception as e: 
                    # print(e.msg())
                    pass

                if count < 5: print(list(data.values()))
                
                if list(data.values()).count(list(data.values())[0]) != len(list(data.values())) - 1:
                    cell_values.append(data)
            count += 1
        
        cell_values.pop(0)

        col_tout_handle.insert_many(cell_values)

        return {
            "detail": "File Uploaded Successfully"
        }

    except Exception as e:
        print(e.msg())
        return{
            "status": 500,
            "msg": "Failed to upload File"
        }

@app.post("/tout_card_list", response_description="Displays takedown list in a table")
async def tout_list(card_data : ToutCardData, request: fastapi.Request):
    try:

        if card_data.search != '':
            if ',' in card_data.search:
                search_keywords = card_data.search.split(',')

            else:
                search_keywords = card_data.search.split()

            or_conditions = [
                {"Name": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Contact": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Email": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Website": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Youtube": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Telegram": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Whatsapp": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Others": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ]

            tout_data = await col_tout_handle.find({
                '$or' : or_conditions
            },{
                '_id' : 0
            }).sort('Image',-1).skip((card_data.page_id - 1) * 9).to_list(9)

            # Count total number of documents in the results of the search filter.
            document_count = await col_tout_handle.count_documents({
                '$or' : or_conditions
            })
            
        else:
            tout_data = await col_tout_handle.find({},{
                '_id' : 0
            }).sort('Image',-1).skip((card_data.page_id - 1) * 9).to_list(9)

            # Count total number of documents in the results of the search filter.
            document_count = await col_tout_handle.count_documents({})

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for record in tout_data:

            # Convert each record into JSON string.
            record_json = json.dumps(record, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)

        page_count = math.ceil(document_count/9)

        # Return the dictionary containing filtered records and total page count of filtered records.
        return {
            'data_list': filtered_records_json[::-1], 
            'total_pages' : page_count,
            'total_rows': document_count
        }
    
    except Exception as e:
        print(e.msg())


@app.post("/tout_data_export", response_description="Export takedown list in a table")
async def tout_list(card_data : ToutCardData, request: fastapi.Request):
    try:
        print(card_data.search)

        if card_data.search != '':
            if ',' in card_data.search:
                search_keywords = card_data.search.split(',')

            else:
                search_keywords = card_data.search.split()

            or_conditions = [
                {"Name": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Contact": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Email": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Website": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Youtube": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Telegram": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Whatsapp": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ] + [
                {"Others": {"$elemMatch": {"$regex": re.compile(term, re.IGNORECASE)}}} for term in search_keywords
            ]

            tout_data = await col_tout_handle.find({
                '$or' : or_conditions
            },{
                '_id' : 0,
                'Image' :0
            }).to_list(100000)
            
        else:
            tout_data = await col_tout_handle.find({},{
                '_id' : 0,
                'Image' :0
            }).to_list(100000)

        
        for data in tout_data:
            data.update({
                'Name': ','.join(data.get('Name', '')),
                'Email': ','.join(data.get('Email', '')),
                'Website': ','.join(data.get('Website', '')),
                'Youtube': ','.join(data.get('Youtube', '')),
                'Telegram': ','.join(data.get('Telegram', '')),
                'Whatsapp': ','.join(data.get('Whatsapp', '')),
                'Others': ','.join(data.get('Others', '')),
            })
            contacts = data.get('Contact', '')
            contacts = [str(contact).split('.')[0] for contact in contacts]
            data.update({
                'Contact': ','.join(contacts),
            })

        df = pandas.DataFrame(tout_data)

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.xlsx'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}',index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    except Exception as e:
        print(e.msg())


@app.post("/web_status_overview", response_description="Displays top 5 domains and mobile app")
async def tout_list(request: fastapi.Request):

    try:

        web_data = await brandmonitoring_collection_handle.find({
            'takedownAction' : "Takedown Completed",
            'threatSource' : "Website"
        }, {
            '_id' : 0
        }).to_list(5)

        domain_data = await brandmonitoring_collection_handle.find({
            'takedownAction' : "Takedown Completed",
            'threatSource' : "Mobile Application"
        }, {
            '_id' : 0
        }).to_list(5)

        web_domain_data = web_data + domain_data

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for record in web_domain_data:

            record['Link'] = record['Link'].replace('http://', "").replace("https://","").strip()

            record['presentStatus'] = 'Completed'

            # Convert each record into JSON string.
            record_json = json.dumps(record, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)


        # Return the dictionary containing filtered records and total page count of filtered records.
        return {
            'data_list': filtered_records_json[::-1], 
        }
    
    except Exception as e:
        print(e.msg())

async def startup_event():
    setup_mount_folder('files')
    setup_mount_folder('download_reports')
    setup_mount_folder('img_folder')

async def shutdown_event():
    app.state.executor.shutdown()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


if __name__ == "__main__":
    uvicorn.run(
        'app:app', 
        host='0.0.0.0', 
        port=55556, 
        reload=True
    )