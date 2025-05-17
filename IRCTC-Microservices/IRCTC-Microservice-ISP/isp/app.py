# Import libraries
import os
import re
import http
import json
import uuid
import math
import typing
import fastapi
import uvicorn
import logging
import datetime
import pydantic
import calendar
import ipaddress
import numpy as np
import pandas as pd
from utils import *
import create_blacklist
import pydantic_settings
import motor.motor_asyncio
from bson import json_util



# Logger function.
def BlackListLogger():

    # Create a logger.
    logger = logging.getLogger("Blacklist")

    # The level of the logger is set to 'INFO'.
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(threadName)s:%(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('blacklist.log')

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

# Connect to MongoDB.
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)

# Get reference to the database `MONGO_DB`.
db = client[settings.MONGO_DB]


class IspBlacklist(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data to be shown on Blacklisted ISP page.
    """

    # Page ID with initial value '1'.
    page_id: typing.Optional[int] = 1

    # Default value as empty string.
    search: typing.Optional[str] = ''

    # Length of the table to be displayed on page.
    # Default value as 10 rows.
    month: typing.Optional[str] = ''

class IspSubnetDownload(pydantic.BaseModel):

    isp : typing.Optional[str] = ''

    month : typing.Optional[str] = ''

class IspDownload(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data for download functionality.
    """

    # Default value as empty string.
    isp_name: typing.Optional[str] = ''

    # Default value as current date.
    isp_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

class CreateBlacklist(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it
    """
    # Set the starting date for which the suspicious PNR's is to be searched.
    filter_date: typing.Optional[str] = ""


def setup_mount_folder(fname):
    """
    Function for returning the downloaded file which contains excel sheet containing blacklisted subnets.

    :param fname: Folder

    :return UPLOAD_FOLDER: Folder with blacklisted subnets excel sheet. 
    """

    # Path contains current working directory.
    path = os.getcwd()
    
    # Create folder with path name joining the current path with folder name as `f_file`.
    UPLOAD_FOLDER = os.path.join(path, fname)
    
    # Make directory if `UPLOAD_FOLDER` folder does not exist.
    if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    return UPLOAD_FOLDER


# Create a collection for blacklisted ISPs.
isp_collection_handle = db.irctc_isp_test_1_new

# Create a handle to the collection for trend charts data.
trend_chart_collection_handle = db.irctc_infra_mon_test_1

# Collection instance to update overall blacklisted count
overdash_collection = db.irctc_over_dash_const_1

# Create a handle to the collection for vulnerabilities chart data.
vulnerability_chart_collection_handle = db.irctc_infra_mon_const_test_1


@app.post('/isp_all', response_description="List of ISPs with pagination")
async def list_isp(isp_black_list: IspBlacklist, request: fastapi.Request) -> dict:
    """
    Displays list of Blacklisted ISPs with pagination.

    :param zIsp : Gives the received data based on IspBlacklist model.
    :ptype :IspBlacklist model

    :return : Data to be displayed and count of pages.
    :rtype :dict
    """

    logger = BlackListLogger()

    try:

        # Display unfiltered list of blacklisted ISPs.
        if isp_black_list.search == '':
        
            if isp_black_list.month != "":

                # fetch month for the given input
                month = isp_black_list.month.split(" ")[0]

                # Find records for the received year
                if month == "All":

                    year = isp_black_list.month.split(" ")[1]
                    
                    # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({"REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)
                
                    # Count total number of documents in the results of the filtered data.
                    document_count = await isp_collection_handle.count_documents({"REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}})

                else:
                    # Find on 'month' --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({"REPORT_MONTH" : isp_black_list.month}, {'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the filtered data.
                    document_count = await isp_collection_handle.count_documents({"REPORT_MONTH" : isp_black_list.month})

            # Fetch the whole data if month is not present
            else:

                data = await isp_collection_handle.find({},{'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)

                # Count total number of documents in the results of the search filter.
                document_count = await isp_collection_handle.count_documents({})

        else:

            if isp_black_list.month != "":

                # fetch month for the given input
                month = isp_black_list.month.split(" ")[0]

                # Find records for the received year
                if month == "All":

                    year = isp_black_list.month.split(" ")[1]
                    
                    # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({
                        'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},
                        "REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)
                
                    # Count total number of documents in the results of the filtered data.
                    document_count = await isp_collection_handle.count_documents({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},"REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}})

                else:
                    # Find on 'month' --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},"REPORT_MONTH" : isp_black_list.month}, {'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the filtered data.
                    document_count = await isp_collection_handle.count_documents({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},"REPORT_MONTH" : isp_black_list.month})

            # Fetch the whole data if month is not present
            else:

                data = await isp_collection_handle.find({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},},{'_id' : 0}).sort('FLAGGED_DATE',-1).skip((isp_black_list.page_id - 1) * 10).to_list(10)

                # Count total number of documents in the results of the search filter.
                document_count = await isp_collection_handle.count_documents({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},})

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
    
        # Return data to be displayed and count of pages.
        return {
            'data_list': filtered_records_json[::-1], 
            'total_rows': document_count,
            'total_pages' : math.ceil(document_count/10)
        }

    except:
        
        # Log error message in the log file.
        logger.error(f"Failed to get blacklisted isp data:{request.url}")

        return{
            "status": 500,
            "detail": "Failed to get blacklisted isp data"
        }

@app.post('/blacklist_status')
async def check_status():
    status = await isp_collection_handle.find_one({
        'name' : 'Blacklist_Status'
    },{
        'status' : 1,
        '_id' : 0
    })

    if status == [] or status == None:
        await isp_collection_handle.update_one({
            'name' : 'Blacklist_Status'
        },{
            '$set' : {
                'status' : 1
            }
        }, upsert=True)

        status = await isp_collection_handle.find_one({
            'name' : 'Blacklist_Status'
        },{
            'status' : 1,
            '_id' : 0
        })
        
    status = status['status']
        
    return {
        'status' : status
    }

@app.post('/create_new_blacklist', status_code=http.HTTPStatus.ACCEPTED)
async def create_new_blacklist(blacklist: CreateBlacklist, background_tasks: fastapi.BackgroundTasks):

    ending_date = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time.min)
    
    if blacklist.filter_date == "last_week": starting_date = ending_date - datetime.timedelta(days=7)

    if blacklist.filter_date == "last_15_days": starting_date = ending_date - datetime.timedelta(days=15)

    if blacklist.filter_date == "last_month": starting_date = ending_date - datetime.timedelta(days=30)

    await isp_collection_handle.update_one({
        'name' : 'Blacklist_Status'
    },{
        '$set' : {
            'status' : 0
        }
    })
    
    # Call IDAnalyser for file analysis --> add task as the background process.
    background_tasks.add_task(create_blacklist.IPBlacklist , starting_date, ending_date)

    # After file analysis return the message containing the detail fo the analyzed file location.
    return {
        'status' : 200,
        'msg' : f'Creating Blacklist file for {blacklist.filter_date}'
    }

@app.post('/isp_view_modal', response_description="List of ISPs for specific date without pagination")
async def modal_isp(isp_blacklist: IspBlacklist, request: fastapi.Request) -> dict:
    """
    Displays blacklisted ISPs without pagination corresponding to the specific date respectively.

    :param zIsp : Gives the received data based on IspBlacklist model. 
    :ptype :IspBlacklist model

    :return : Data to be displayed and count of pages.
    :rtype :dict
    """

    logger = BlackListLogger()

    try:
        
        # Find on (search)  --> convert to list.
        data = await isp_collection_handle.find(
            {
                'ISP': isp_blacklist.search
            }, 
            {
                'BLACK_DATES': 1
            }).to_list(10)    

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
            'data_list': filtered_records_json[::-1]
        }
        
    except:
        # Log error message in the log file.
        logger.error(f"Failed to get blacklisted isp data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get balcklisted isp data"
        }


@app.post('/download-isp', response_description="Download blacklisted subnet excel sheet", response_class=fastapi.responses.FileResponse)
async def download_isp(isp_black_list: IspBlacklist,  request: fastapi.Request):
    """
    Downloads excel file displaying blacklisted ISPs.

    :param dIsp : Gives the received data based on IspDownload model. 
    :ptype :IspDownload model

    :return : Excel sheet containing blacklisted subnets.
    :rtype :File
    """

    logger = BlackListLogger()

    try:
        
        
        # Display unfiltered list of blacklisted ISPs.
        if isp_black_list.search == '':
        
            if isp_black_list.month != "":

                # fetch month for the given input
                month = isp_black_list.month.split(" ")[0]

                # Find records for the received year
                if month == "All":

                    year = isp_black_list.month.split(" ")[1]
                    
                    # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({"REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

                else:
                    # Find on 'month' --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({"REPORT_MONTH" : isp_black_list.month}, {'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

            # Fetch the whole data if month is not present
            else:

                data = await isp_collection_handle.find({},{'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

        else:

            if isp_black_list.month != "":

                # fetch month for the given input
                month = isp_black_list.month.split(" ")[0]

                # Find records for the received year
                if month == "All":

                    year = isp_black_list.month.split(" ")[1]
                    
                    # Find on 'month' for the provided year --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({
                        'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},
                        "REPORT_MONTH" : {'$regex' : re.compile(f'.*{year}.*', re.IGNORECASE)}}, {'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

                else:
                    # Find on 'month' --> skip to results on `page_id` --> convert to list.
                    data = await isp_collection_handle.find({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},"REPORT_MONTH" : isp_black_list.month}, {'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

            # Fetch the whole data if month is not present
            else:

                data = await isp_collection_handle.find({'ISP': {'$regex': re.compile(f'.*{isp_black_list.search}.*', re.IGNORECASE)},},{'_id' : 0, 'BLACKLIST_DETAILS' : 0, 'UPLOAD_HISTORY' : 0}).sort('FLAGGED_DATE',-1).to_list(10000)

        # Converts the 'fetched data' into pandas dataframe.     
        df = pd.DataFrame(data)
        df['FLAGGED_DATE'] = df['FLAGGED_DATE'].dt.strftime('%a %d %B %Y')
        df['BLACKLIST_DATE'] = df['BLACKLIST_DATE'].dt.strftime('%a %d %B %Y')

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
    

    except Exception as e:


        # Log error message in the log file.
        logger.error(f"Failed to download blacklisted isp excel file :{request.url}")

        return{
            "status": 500,
            "detail": "Failed to download blacklisted isp data"
        }


@app.post('/date-isp', response_description="Download blacklisted subnets excel sheet for specific date", response_class=fastapi.responses.FileResponse)
async def date_isp(isp_download: IspDownload, request: fastapi.Request):
    """
    Downloads excel file displaying blacklisted ISPs for specisic date.

    :param dIsp : Gives the received data based on IspDownload model. 
    :ptype :IspDownload model
    
    :return : Excel sheet containing blacklisted subnets.
    :rtype :File
    """

    logger = BlackListLogger()

    try:
        
        # Find on (isp_name) --> deconstruct by `SUBNETS` --> find on (isp_date) --> returns a single document --> project only `subnets` --> convert to list.
        data = await isp_collection_handle.aggregate(
            [
                {
                    '$match': {
                        'ISP': isp_download.isp_name
                    }
                },
                {
                    '$unwind': '$SUBNETS'
                },
                {
                    '$match': {
                        'SUBNETS.DATE': isp_download.isp_date
                    }
                },
                    {
                    '$group': {
                        '_id': None,
                            'subnets': {
                            '$push': "$SUBNETS.SUBNET"
                        }
                    }
                },
                {
                '$project': {
                    'subnets': True,
                    '_id': False
                    }
                }
            ]).to_list(1)
        
        # Fetching subnets from list.
        subnets = data[0]['subnets']

        # Calling DataFrame constructor.
        df = pd.DataFrame({'Subnets': subnets})

        # Converting to excel.
        df.to_excel('download_isp_black/output.xlsx',index=False)
        
        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        return 'download_isp_black/output.xlsx'

    except:
        # Log error message in the log file.
        logger.error(f"Failed to download blacklisted isp data :{request.url}")

        return{
            "status": 500,
            "msg": "Failed to download blacklisted isp data"
        }


@app.post('/isp_overview', response_description="List of monthly blacklisted isp stats")
async def over_isp(request: fastapi.Request) -> dict:

    logger = BlackListLogger()

    try:

        curr_year = str(datetime.datetime.now().year)

        month_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        stats_data = []

        for month in month_list:

            report_month = month + " " + curr_year

            data = await isp_collection_handle.aggregate(
                [
                    {'$match' : {"REPORT_MONTH" : report_month}},
                    {'$group' : {'_id' : '$REPORT_MONTH', "ISP_Count" : {'$sum' : 1}, 'Subnet_Count' : {'$sum' : '$TOTAL_BLACKLIST_SUBNET'}, 'IP_Count' : {'$sum' : '$TOTAL_BLACKLIST_IPS'}}}
                ]
            ).to_list(1)

            if data:

                stats_data.append(data[0])

        filtered_records_json = []
            
        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in stats_data:
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
            'data_list': filtered_records_json[::-1]
        }
    
    except:
        # Log error message in the log file.
        logger.error(f"Failed to get stats data :{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get stats data"
        }

@app.post('/isp_subnet_export', response_description="export List of ISPs subnets")
async def export_subnets(isp_subnet: IspSubnetDownload, request: fastapi.Request, response: fastapi.Response) -> dict:
    """
    Export list of Blacklisted ISPs subnets.

    :param zIsp : Gives the received data based on IspSubnetDownload model.
    :ptype :IspSubnetDownload model

    :return : Data to be displayed.
    :rtype :dict
    """
    try:

        # Display unfiltered list of blacklisted ISPs.
        if isp_subnet.isp == '' or isp_subnet.month == '':

            response.status_code = 406
            return {
                'detail': 'Invalid input'
            } 
        
        else:

            subnets = await isp_collection_handle.find_one(
                {
                    "REPORT_MONTH" : isp_subnet.month, 
                    "ISP" : isp_subnet.isp
                }, 
                {
                    '_id' : 0,
                    'BLACKLIST_FILE_REF' : 1
                })
            
            filename = subnets['BLACKLIST_FILE_REF']
        
        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'Final_Blacklist/{filename}')

    except Exception as e:
        
        # Log error message in the log file.
        # logger.error(f"Failed to get isp subnets data:{request.url}")

        return{
            "status": 500,
            "detail": "Failed to get isp subnets data"
        }

if __name__ == "__main__":
    setup_mount_folder('download_folder')
    setup_mount_folder('download_isp_black')
    setup_mount_folder('Blacklistfiles')
    setup_mount_folder('Blacklist_Subnets')
    setup_mount_folder('Final_Blacklist')

    uvicorn.run(
        'app:app', 
        host='0.0.0.0', 
        port=55558, 
        reload=True)