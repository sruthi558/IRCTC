# Library Imports

import os
import re
import json
import math
import uuid
import redis
import pandas
import typing
import fastapi
import logging
import uvicorn
import pydantic
import icecream
import datetime
import bson.objectid
import pydantic_settings
from bson import json_util
import motor.motor_asyncio
from fastapi import UploadFile
from fastapi_cache import FastAPICache
from concurrent.futures import ProcessPoolExecutor
from fastapi_cache.backends.inmemory import InMemoryBackend




# Logger function.
def InfrastructureMonitoringLogger():

    # Create a logger.
    logger = logging.getLogger("InfrastructureMonitoring")

    # The level of the logger is set to 'INFO'.
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(threadName)s : %(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('inframon.log')

    # Set the format for the logged data.
    file_handler.setFormatter(formatter)

    # Add the handler to the logger.
    logger.addHandler(file_handler)

    # Return the logger.
    return logger


############################## MICROSERVICE SETUP ##############################


class Settings(pydantic_settings.BaseSettings):
    """
    Set the configurations for the microservice's functionality through the env file.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to setup the basic configuration from the env file.
    """

    # Default configuration values to be used if these parameters are not defined in the env file.
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "irctc_backend_test_6"
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



############################## BASE DATA MODEL ##############################



class InfrastructureMonitoringBaseData(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model for the base data to be shown on the cyber threat monitoring page.
    """

    # Set the initial page number to '1' to display the first page of the results.
    page_number: typing.Optional[int] = 1

    vulnerability_status: typing.Optional[int] = [True, False]

    # Set the initial months for which discovered vulnerability count is to be displayed.
    vulnerability_discovered_month: typing.Optional[str] = ['December', 'January','May']

    # Set the default search parameter as empty.
    search: typing.Optional[str] = ''

    # Specification of severity of vulnerabilities.
    risk_severity_of_vulnerabilities: typing.Optional[list] = ['Low', 'Medium', 'High', 'Critical','Informative']

    # Set the default month parameter as empty.
    month: typing.Optional[str] = ''

    # Set the default month parameter as empty.
    vulnerability_type: typing.Optional[str] = ''


######################### VULNERABILITY STATUS MODEL #########################

class VulnerabilityStatus(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define vulnerability status model to show if vulnerability is resolved or unresolved.
    """

    status: typing.Optional[int] = 0

    cellid: typing.Optional[str] = ''



######################### VULNERABILITY BREAKDOWN MODEL ######################### 



class InfrastructureMonitoringStatus(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define vulneralibity severity model.
    """
    status: typing.Optional[list] = [True]

    # Set the initial page number to '1' to display the first page of the results.
    page_number: typing.Optional[int] = 1

    # Specification of severity of vulnerabilities.
    severe: typing.Optional[list] = ['Low', 'Medium', 'High', 'Critical','Informative']

class InfrastuctureMonitoringStatistics(pydantic.BaseModel):

    # Set the default month parameter as empty.
    month: typing.Optional[str] = ""

    # Set the default year parameter as empty.
    year: typing.Optional[str] = ""

    # Set the initial page number to '1' to display the first page of the results.
    page_number: typing.Optional[int] = 1

    # Set the default severity parameter as empty.
    severity : typing.Optional[list] = []

# Redis Client 
redis_client = redis.Redis(host='localhost', port=6379, db=0)
CACHE_EXP = 60*120 # two hours 

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

async def on_startup():
    setup_mount_folder('files')
    setup_mount_folder('download_folder')
    app.state.executor = ProcessPoolExecutor()
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

app.add_event_handler('startup', on_startup)

# Create a handle to the collection for trend charts data.
trend_chart_collection_handle = db.irctc_infra_mon_test_1_new_new

# Create a handle to the collection for vulnerabilities chart data.
vulnerability_chart_collection_handle = db.irctc_infra_mon_const_test_1_new_new

overdash_col = db.irctc_over_dash_const_1

min_date = datetime.datetime(1970, 1, 1)



@app.post('/infra_data_request', response_description = "List default data for infrastructure monitoring page")
async def list_default_data(infrastructure_monitoring_base_data: InfrastructureMonitoringBaseData, request: fastapi.Request) -> dict:
    """
    Fetch the data to be displayed in the table.

    :param infra: Gives the received data based on InfrastructureMonitoringBaseData model.
    :ptype: InfrastructureMonitoringBaseData model.

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """
    logger = InfrastructureMonitoringLogger()

    cache_key = f'/infra_data_request-{infrastructure_monitoring_base_data.page_number}-{infrastructure_monitoring_base_data.vulnerability_status}-{infrastructure_monitoring_base_data.vulnerability_discovered_month}-{infrastructure_monitoring_base_data.search}-{infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities}-{infrastructure_monitoring_base_data.month}-{infrastructure_monitoring_base_data.vulnerability_type}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /infra_data_request')
        cached_data = redis_client.get(cache_key)

        if(cached_data):
            icecream.ic('Cache hit .. /infra_data_request')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)
        
        else:
            icecream.ic('Cache Miss .. /infra_data_request')
            try:
                # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.  
                if infrastructure_monitoring_base_data.search != "":

                    # Log the data into the log file.
                    logger.info(f"Search text is greater than 2:{request.url}")

                    # initilize keywords list to store the list of keywords provided in search
                    keywords = []

                    # split based on the separator
                    if ',' in infrastructure_monitoring_base_data.search:
                        keywords = infrastructure_monitoring_base_data.search.split(',') 

                    else:
                        keywords = infrastructure_monitoring_base_data.search.split()

                    # create regex patters for each keyword
                    regex_patterns = [re.compile(keyword, re.IGNORECASE) for keyword in keywords]

                    # or conditions for each keyword and column
                    or_conditions = []

                    for pattern in regex_patterns:
                        #list of column conditions for each regex pattern
                        column_condition = []
                        # for each regex pattern create an or condition for each column
                        for column in ['Subdomain', 'Service', 'Type','Severity','Month']:
                            column_condition.append({column:pattern})

                        # append each or condition for each regex pattern on every column
                        or_conditions.append({"$or": column_condition})

                    # query initialization with and and or conditions
                    query = {
                        "$and": or_conditions
                    }

                    data = await trend_chart_collection_handle.find(query).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the search filter.
                    document_count = await trend_chart_collection_handle.count_documents(query)


                # Filter on the basis of severity if the length of the text(data) to be searched is less than '2'.
                else:

                    # Log the data into the log file.
                    logger.info(f"Search text is less than 2:{request.url}")

                    # Find on (keyword severity) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
                    data = await trend_chart_collection_handle.find({'Severity': {
                                    '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                                }
                        }, {}).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the filtered data.
                    document_count = await trend_chart_collection_handle.count_documents({'Severity': {
                                    '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                                }
                        }
                    )

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

                page_count = math.ceil(document_count/10)

                # Return the dictionary containing filtered records and total page count of filtered records.
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': document_count
                }

                icecream.ic('Setting cache .. /infra_data_request')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as e:
                print(e.msg())

                # Log error message in the log file.
                logger.error(f"Failed to get data:{request.url}")

                err_data = {
                    "status": 500,
                    "msg": "Failed to get table data"
                }

                return err_data
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }


@app.post('/export_infra_mon', response_description = "Export list of data of infrastructure montioring page")
async def export_infra_mon(infrastructure_monitoring_base_data: InfrastructureMonitoringBaseData, request: fastapi.Request) -> dict:
    """
    Export the data displayed in the table.

    :param infra: Gives the received data based on InfrastructureMonitoringBaseData model.
    :ptype: InfrastructureMonitoringBaseData model.

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """
    logger = InfrastructureMonitoringLogger()

    try:

        # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.  
        if infrastructure_monitoring_base_data.search != "":

            # Log the data into the log file.
            logger.info(f"Search text is greater than 2:{request.url}")
            
            # initilize keywords list to store the list of keywords provided in search
            keywords = []

            # split based on the separator
            if ',' in infrastructure_monitoring_base_data.search:
                keywords = infrastructure_monitoring_base_data.search.split(',') 

            else:
                keywords = infrastructure_monitoring_base_data.search.split()

            # create regex patters for each keyword
            regex_patterns = [re.compile(keyword, re.IGNORECASE) for keyword in keywords]

            # or conditions for each keyword and column
            or_conditions = []

            for pattern in regex_patterns:
                #list of column conditions for each regex pattern
                column_condition = []
                # for each regex pattern create an or condition for each column
                for column in ['Subdomain', 'Service', 'Type','Severity','Month']:
                    column_condition.append({column:pattern})

                # append each or condition for each regex pattern on every column
                or_conditions.append({"$or": column_condition})

            # query initialization with and and or conditions
            query = {
                "$and": or_conditions
            }

            data = await trend_chart_collection_handle.find(query, {'_id' : 0}).sort('Status', -1).to_list(10000)

            
        # Filter on the basis of sevirity if the length of the text(data) to be searched is less than '2'.
        else:
        # print("filtered : ",filtered_records_json)

            # Log the data into the log file.
            logger.info(f"Search text is less than 2:{request.url}")

            # Find on (keyword severity) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
            data = await trend_chart_collection_handle.find({'Severity': {
                            '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                        }
                }, {'_id' : 0}).sort('Status', -1).to_list(10000)
        

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")   
    
        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(data)
        
        # Replace the boolean value with the string.
        booleanDictionary = {
            True: 'TRUE',
            1 : 'TRUE', 
            False: 'FALSE',
            0 : 'FALSE'
        }

        # Replaces the dataframe keys with the values specified in `booleanDictionary`.
        df = df.replace(booleanDictionary)

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

@app.post('/infra_month_data_request', response_description = "List data for infrastructure monitoring page according to the month")
async def month_default_data(infrastructure_monitoring_base_data: InfrastructureMonitoringBaseData, request: fastapi.Request) -> dict:
    """
    Fetch the data to be displayed in the table according to the month.

    :param infra: Gives the received data based on InfrastructureMonitoringBaseData model.
    :ptype: InfrastructureMonitoringBaseData model.

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    cache_key = f'/infra_month_data_request-{infrastructure_monitoring_base_data.page_number}-{infrastructure_monitoring_base_data.vulnerability_status}-{infrastructure_monitoring_base_data.vulnerability_discovered_month}-{infrastructure_monitoring_base_data.search}-{infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities}-{infrastructure_monitoring_base_data.month}-{infrastructure_monitoring_base_data.vulnerability_type}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /infra_month_data_request')
        cached_data = redis_client.get(cache_key)
        
        if(cached_data):
            icecream.ic('Cache hit .. /infra_month_data_request')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)
        
        else:
            icecream.ic('Cache miss .. /infra_month_data_request')
            try:

                # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.  
                if len(infrastructure_monitoring_base_data.search) > 2:

                    # Log the data into the log file.
                    logger.info(f"Search text is greater than 2:{request.url}")

                    # Find on ((keyword search) and (severity)) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
                    data = await trend_chart_collection_handle.find({
                        '$and': [
                            {
                                '$text': {
                                    '$search': infrastructure_monitoring_base_data.search
                                }
                            }, {
                                'Severity': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                            }, {
                                'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_base_data.month}.*', re.IGNORECASE)}
                            }
                        ]
                    }, {}).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the search filter.
                    document_count = await trend_chart_collection_handle.count_documents({
                        '$and' : [
                            {
                                '$text' : { 
                                    '$search': infrastructure_monitoring_base_data.search
                                }
                            }, {
                                'Severity': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                            }, {
                                'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_base_data.month}.*', re.IGNORECASE)}
                            }
                        ]
                    })
                    
                # Filter on the basis of sevirity if the length of the text(data) to be searched is less than '2'.
                else:

                    # Log the data into the log file.
                    logger.info(f"Search text is less than 2:{request.url}")

                    # Find on (keyword severity) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
                    data = await trend_chart_collection_handle.find({
                        '$and' : [
                            {
                                'Severity': {
                                    '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                                }
                            }, {
                                'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_base_data.month}.*', re.IGNORECASE)}
                            }
                        ]
                        }, {}).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

                    # Count total number of documents in the results of the filtered data.
                    document_count = await trend_chart_collection_handle.count_documents({
                            '$and' : [
                                {
                                    'Severity': {
                                        '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                                    }
                                }, {
                                'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_base_data.month}.*', re.IGNORECASE)}
                            }
                            ]
                        }
                    )
                
                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for record in data:
                    
                    record['Month'] = infrastructure_monitoring_base_data.month

                    # Convert each record into JSON string.
                    record_json = json.dumps(record, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, record_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                page_count = math.ceil(document_count/10)

                # Return the dictionary containing filtered records and total page count of filtered records.
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': document_count
                }

                icecream.ic('Setting Cache .. /infra_month_data_request')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as exception_error:

                # Log error message in the log file.
                logger.error(f"Failed to get data:{request.url}")

                return{
                    "status": 500,
                    "msg": "Failed to get table data"
                }
    
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }


@app.post('/infra_vulnerability_type_data_request', response_description = "List data for infrastructure monitoring page according to the vulnerability type")
async def vulnerability_default_data(infrastructure_monitoring_base_data: InfrastructureMonitoringBaseData, request: fastapi.Request) -> dict:
    """
    Fetch the data to be displayed in the table according to the month.

    :param infra: Gives the received data based on InfrastructureMonitoringBaseData model.
    :ptype: InfrastructureMonitoringBaseData model.

    :return: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:

        # Search data if the length of the text(data) to be searched is greater than '2' to reduce the search load from the database.  
        if len(infrastructure_monitoring_base_data.search) > 2:

            # Log the data into the log file.
            logger.info(f"Search text is greater than 2:{request.url}")

            # Find on ((keyword search) and (severity)) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
            data = await trend_chart_collection_handle.find({
                '$and': [
                    {
                        '$text': {
                            '$search': infrastructure_monitoring_base_data.search
                        }
                    }, {
                        'Severity': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                    }, {
                        'Type': infrastructure_monitoring_base_data.vulnerability_type
                    }
                ]
            }, {}).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

            # Count total number of documents in the results of the search filter.
            document_count = await trend_chart_collection_handle.count_documents({
                '$and' : [
                    {
                        '$text' : { 
                            '$search': infrastructure_monitoring_base_data.search
                        }
                    }, {
                        'Severity': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                    }, {
                        'Type': infrastructure_monitoring_base_data.vulnerability_type
                    }
                ]
            })
            
        # Filter on the basis of sevirity if the length of the text(data) to be searched is less than '2'.
        else:

            # Log the data into the log file.
            logger.info(f"Search text is less than 2:{request.url}")

            # Find on (keyword severity) --> sort by status, open vulnerabilities first --> skip to results on `page_number` --> convert to list.
            data = await trend_chart_collection_handle.find({
                '$and' : [
                    {
                        'Severity': {
                            '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                        }
                    }, {
                        'Type': infrastructure_monitoring_base_data.vulnerability_type
                    }
                ]
                }, {}).sort('Status', -1).skip((infrastructure_monitoring_base_data.page_number - 1) * 10).to_list(10)

            # Count total number of documents in the results of the filtered data.
            document_count = await trend_chart_collection_handle.count_documents({
                    '$and' : [
                        {
                            'Severity': {
                                '$in': infrastructure_monitoring_base_data.risk_severity_of_vulnerabilities
                            }
                        }, {
                        'Type': infrastructure_monitoring_base_data.vulnerability_type
                    }
                    ]
                }
            )

        
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

        page_count = math.ceil(document_count/10)

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



@app.post('/infra_vulnerability_change_status', response_description = "Change the status if it is resolved or unresolved")
async def vulnerability_status(vulnerability_status: VulnerabilityStatus, request: fastapi.Request) -> dict:
    """
    Change the status of the vulnerability(resolved/unresolved).

    :param inst: Gives the received data based on VulnerabilityStatus model.
    :ptype: VulnerabilityStatus model.

    :return: Status and the message.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()
    
    try:

        # Log the data into the log file.
        logger.info(f"Vulnerability status changed:{request.url}")

        # Update the status of the vulnerabilty in the trend chart collection.
        trend_chart_collection_handle.update_one({
            '_id': bson.objectid.ObjectId(vulnerability_status.cellid)
            }, {
            '$set': {
                'Status': vulnerability_status.status, 
                'stc_req_dt': datetime.datetime.now()
            }
        })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the dictionary containing status and the message.
        return {
            "status": 200,
            "msg": "Changed Status"
        }
    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to update the status of the vulnerability:{request.url}")

        return {
            "status": 500,
            "msg": "Failed to change Status"
        }

@app.post('/infra_file_analysis', response_description="Analyse the uploaded file")
async def infra_analyser(file: UploadFile, request: fastapi.Request) -> dict:
    """
    Analyse the uploaded file.

    :param file: Stores the uploaded file.
    :ptype: fastapi.UploadFile.

    :returns: Filename and its saved location.
    :rtype: dict
    """
    logger = InfrastructureMonitoringLogger()

    # Construct the file location.
    file_location = f"files/{file.filename}"

    try:
        # Opens a file handle to the constructed file location in binary format.
        with open(file_location, "wb+") as file_object:

            # Reads from the uploaded file and writes to a local copy of the file.
            file_object.write(file.file.read())

        # Reads the data from excel and stores it into a pandas DataFrame.
        df = pandas.read_excel(file_location)
        df['Status'] = df['Status'].replace(to_replace=["Open","Close"], value=[True,False], regex=True)
        df['Type'] = df['Type'].replace(to_replace=["\n"," "], value=['',''], regex=True)
        df["Subdomain"] = df['Subdomain'].replace(to_replace =['^www.','^http://',"^https://","https://www.","http://www."," "], value = ['','','','','',''], regex = True)
        month = df.iloc[1]['Month']
        month = month.strftime('%B %Y')

        df = df.drop(columns=['Month'])
        df['Month'] = [month]*len(df)

        df["identifier"] = df["Type"]+"-"+df["Subdomain"]
        df['Severity'] = df['Severity'].str.capitalize()
        df.drop_duplicates(inplace=True)

        # Declare dictionary with initial value '0' that stores the statistics of the uploaded file.
        store_dict = {
            'Month': '',
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Informative': 0,
            'VULN_COUNT': 0
        }

        unique_iden = set(await trend_chart_collection_handle.distinct('identifier'))

        current_iden = set(df["identifier"].tolist()) - unique_iden

        total_unique_vuln = len(unique_iden) + len(current_iden)

        current_iden_severity = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Informative': 0
        }

        # Export the dataframe in a dictionary format of type `records`.
        # Iterate over the dictionary and calculate the statistics.

        if await vulnerability_chart_collection_handle.count_documents({'chartconst':True}) == 0:
            await vulnerability_chart_collection_handle.insert_one({'chartconst': True})

        vulnerability_type = await vulnerability_chart_collection_handle.find_one({
                'chartconst' : True
            },{
                '_id' : 0
            })

        for record in df.to_dict('records'):
            if store_dict['Month'] == '':
                # Update the `Month` key with the value from the the uploaded file.
                store_dict['Month'] = record['Month']
            
            if record['Severity'] != 'Informative':
                record["Type"] = record['Type'].replace(".","-")
                if record["Type"] in vulnerability_type.keys():
                    vulnerability_type[record['Type']] += 1
                else:
                    vulnerability_type[record['Type']] = 1

            if record["identifier"] in current_iden:
                current_iden.remove(record["identifier"])
                current_iden_severity[record['Severity']] += 1

            # Get the severity of the entry, and increment the total count of that severity level.
            try:
                store_dict[record['Severity']] += 1
            except:
                pass

            trend_chart_collection_handle.update_one(
                {
                    "identifier" : record["identifier"]
                },{
                    '$set' : {
                        'Status' : True,
                        'Type' : record['Type'],
                        'Subdomain' : record['Subdomain'],
                        'Severity' : record['Severity'],
                        'Service' : record['Service']
                    },
                    '$addToSet' : {
                        'Month' : record['Month']
                    }
            },upsert = True)

        vulnerability_chart_collection_handle.replace_one({'chartconst':True}, vulnerability_type)

        # Update the overall vulnerability count as the sum of all the severity levels.
        store_dict['VULN_COUNT'] = store_dict['Critical'] + store_dict['High'] + store_dict['Medium'] + store_dict['Low'] + store_dict['Informative']
        
        # Insert the dictionary data into the vulnerability chart collection.
        vulnerability_chart_collection_handle.insert_one(store_dict)

        vuln_type = json.loads((await overdash_col.find_one({'NAME' : 'OVER_DATA'}))['VULN_TYPE'].replace("\'", "\""))
        vuln_type['Critical'] += current_iden_severity['Critical']
        vuln_type['High'] += current_iden_severity['High']
        vuln_type['Medium'] += current_iden_severity['Medium']
        vuln_type['Low'] += current_iden_severity['Low']
        vuln_type['Informative'] += current_iden_severity['Informative']

        overdash_col.update_one({
            'NAME' : 'OVER_DATA'
        },{
            '$set' : {
                'VULN_REPORTED' : total_unique_vuln,
                'VULN_TYPE' : str(vuln_type)
            }
        }, upsert=True)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the dictionary containing file name and the location where it is saved.
        return {
            "detail": f"file '{file.filename}' saved at '{file_location}'"
        }
    
    except Exception as exception_error:
        print(exception_error.msg())
        
        # Log error message in the log file.
        # logger.error(f"File '{upload_file.filename}' analysis failed '{file_location}':{request.url}")

        return {
            "status": 500,
            "detail": f"file '{file.filename}' analysis failed '{file_location}'"
        }

@app.post('/infra_status_find' , response_description = "Open vulnerabilities and their number")
async def infra_status_chart(infrastructure_monitoring_status: InfrastructureMonitoringStatus, request: fastapi.Request) -> dict:

    """
    Tracks status of vulnerabilities whether it is open or resolved.

    :param infra: Gets the received data based on InfraStat model.
    :ptype: InfrastructureMonitoringStatus model.

    :returns: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    cache_key = f'/infra_status_find-{infrastructure_monitoring_status.severe}-{infrastructure_monitoring_status.page_number}-{infrastructure_monitoring_status.status}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /infra_status_find')
        cached_data = redis_client.get(cache_key)
        
        if(cached_data):
            icecream.ic('Cache hit .. /infra_status_find')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)
        
        else:
            icecream.ic('Cache miss .. /infra_status_find')
            try:

                # Find on ((keyword severity) and (status)) --> skip to results on `page_number` --> convert to list.
                data = await trend_chart_collection_handle.find({
                    '$and' : [
                                {
                                    'Severity' : {
                                        '$in': infrastructure_monitoring_status.severe
                                    }
                                }, {
                                
                                    'Status' : {
                                        '$in': infrastructure_monitoring_status.status
                                    }
                                }
                            ]
                    }, {
                        'Type' : 1,
                        'Subdomain' : 1,
                        'Severity' : 1,
                        'Service' : 1,
                        'Status' : 1
                    }).skip((infrastructure_monitoring_status.page_number-1) * 10).to_list(10)

                # Count total number of documents in the results of the search filter.
                document_count = await trend_chart_collection_handle.count_documents({
                    '$and' : [
                                {
                                    'Severity' : {
                                        '$in': infrastructure_monitoring_status.severe
                                    }
                                }, {
                                    'Status' : {
                                        '$in':infrastructure_monitoring_status.status
                                    }
                                }
                            ]
                    })

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

                page_count = math.ceil(document_count/10)

                # Return the dictionary containing filtered records and total page count of filtered records.
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': document_count
                }
            
                icecream.ic('Setting Cache .. /infra_status_find')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as exception_error:

                # Log error message in the log file.
                logger.error(f"Failed to track status of vulnerabilities{request.url}")

                return {
                    "status": 500,
                    "msg": "Failed to track status of vulnerabilities"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }

@app.post('/export_infra_status_find' , response_description = "Open vulnerabilities and their number")
async def export_infra_status_chart(infrastructure_monitoring_status: InfrastructureMonitoringStatus, request: fastapi.Request) -> dict:

    """
    Tracks status of vulnerabilities whether it is open or resolved.

    :param infra: Gets the received data based on InfraStat model.
    :ptype: InfrastructureMonitoringStatus model.

    :returns: Data to be displayed and count of pages.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()


    try:

        # Find on ((keyword severity) and (status)) --> skip to results on `page_number` --> convert to list.
        data = await trend_chart_collection_handle.find({
            '$and' : [
                        {
                            'Severity' : {
                                '$in': infrastructure_monitoring_status.severe
                            }
                        }, {
                        
                            'Status' : {
                                '$in': infrastructure_monitoring_status.status
                            }
                        }
                    ]
            }, {
                '_id' : 0,
                'Month' : 0,
                'identifier' : 0
            }).to_list(10000)

        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(data)
        df.fillna("NA", inplace=True)

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
        logger.error(f"Failed to track status of vulnerabilities{request.url}")

        return {
            "status": 500,
            "msg": "Failed to track status of vulnerabilities"
        }

@app.get('/infra_trend_chart_data', response_description = "Data for trend chart")
async def infra_trend(request: fastapi.Request) -> dict:
    """
    Tracks count of vulnerabilities discovered in the past months.

    :returns: Dictionary containing vulnerability count per month, total count and not_info.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:

        # Tracking dictionary to store the count of vulnerabilities per month.
        vulnerability_count_per_month = {}

        # Tracking dictionary to store the count of severity level.
        vulnerability_count = json.loads((await overdash_col.find_one({'NAME' : 'OVER_DATA'}))['VULN_TYPE'].replace("\'", "\""))
        
        # Tracks total count of the vulnerability.
        total_vulnerability_count = (await overdash_col.find_one({'NAME' : 'OVER_DATA'}))['VULN_REPORTED']

        # Tracks total count of vulnerabilities that are resolved.
        not_info = 0

        # Filter the records based on the boolean keyword (chartconst) --> remove `_id` from the filtered documents --> iterate over it.
        # `chartconst` is a switch for the type of data. If 'True', the corresponding data will be shownin Vulnerability Chart, otherwise in Trend Charts.
        async for db_entries in vulnerability_chart_collection_handle.find(
                {
                    'chartconst': {
                        '$ne': True
                    }
                }, {
                    '_id': 0
                }
            ):
            # Update the count of vulnerabilities of the given month.
            vulnerability_count_per_month[db_entries['Month']] = db_entries['VULN_COUNT']

            # Update count of vulnerabilities that are resolved.
            not_info += db_entries['VULN_COUNT']
            
        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Returns the dictionary containing vulnerability count per month, total vulnerability count and count of vulnerabilities that are resolved(not_info).
        return {
            'MONTH_COUNT': vulnerability_count_per_month, 
            'VULN_COUNT': vulnerability_count, 
            'TOTAL': total_vulnerability_count, 
            'NOT_INFO': not_info
        }
    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to track count of vulnerability per month:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to track count of vulnerability per month"
        }


@app.get('/infra_vulnerability_chart_data', response_description = "Data for vulnerability chart")
async def infra_vuln_chart(request: fastapi.Request) -> dict:
    """
    Tracks the type of vulnerability.

    :returns: Vulnerability type.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:

        # Tracking dictionary to store the type of vulnerability.
        vulnerability_type = {}

        # Filter the records based on the boolean keyword (chartconst) --> remove `_id` from the filtered documents --> iterate over it.
        # `chartconst` is a switch for the type of data. If 'True', the corresponding data will be shownin Vulnerability Chart, otherwise in Trend Charts.
        async for db_entries in vulnerability_chart_collection_handle.find({
                'chartconst' : True
            }, {
                '_id': 0
            }):

            # Iterate over the keys of the filtered records.
            for key_list in db_entries.keys():

                # Key not in tracking dictionary and is not equal to the boolean keyword 'charconst'.
                if key_list not in vulnerability_type and key_list != 'chartconst':

                    # Update the dictionary.
                    vulnerability_type[key_list] = db_entries[key_list]

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Return dictionary containing list of type of vulnerabilities.
        return {
            'data_list': vulnerability_type
        }
    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to get vulnerability chart data:{request.url}")

        return {
            "status": 500,
            "msg": "Failed to get vulnerability chart data"
        }


@app.get('/infra_count_open_vulnerabilities', response_description = "Count of open Vulnerabilities")
async def infra_open(request: fastapi.Request) -> dict:

    """
    Tracks count of vulnerabilities that are still open.

    :returns: Count of open vulnerabilities.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:
        vul = ['Low', 'Medium', 'High', 'Critical','Informative']
        # Count the records whose vulnerability status is still open.
        count_open = await overdash_col.find_one({
            'NAME' : 'OVER_DATA'
        })
        count_open = count_open['VULN_REPORTED']
        # count_open = await trend_chart_collection_handle.count_documents({
        #     'Status': True,
        #     'Severity': {
        #         '$in': vul
        #         }
        #     })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Return the dictionary containing count of open vulnerabilities.
        return {
            'open_count': count_open
        }
    
    except Exception as exception_error:

        # Log error message in the log file.
        logger.error(f"Failed to get the count of vulnerability that are still open:{request.url}")

        return {
            "status": 500,
            "msg": "Failed to get the count of vulnerability that are still open"
        }

@app.post('/infra_history', response_description = "History of month data")
async def infra_history(infrastructure_monitoring_statistics: InfrastuctureMonitoringStatistics, request: fastapi.Request) -> dict:
    """
    Fetch the month history to be displayed in the table.

    :param infra: Gives the received data based on InfrastuctureMonitoringStatistics model.
    :ptype: InfrastuctureMonitoringStatistics model.

    :return: Data to be displayed and count of pages and rows.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    cache_key = f'/infra_history-{infrastructure_monitoring_statistics.page_number}-{infrastructure_monitoring_statistics.month}-{infrastructure_monitoring_statistics.year}-{infrastructure_monitoring_statistics.severity}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /infra_history')
        cached_data = redis_client.get(cache_key)
        
        if(cached_data):
            icecream.ic('Cache hit .. /infra_history')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            
            return eval(cached_data)
        
        else:
            try:
                icecream.ic('Cache miss .. /infra_history')
                # check for both and year to be present -> else invalid input for data filtering
                if infrastructure_monitoring_statistics.month == "" or infrastructure_monitoring_statistics.year == "":

                    return {
                        "status" : 406,
                        "msg" : "Invalid input"
                    }

                # concatenate month and year as a single string
                month = infrastructure_monitoring_statistics.month + " " + infrastructure_monitoring_statistics.year

                # filter based on the multiple severities
                if infrastructure_monitoring_statistics.severity != []:

                    data = await trend_chart_collection_handle.find(
                        {
                            'Month' : {'$in' : [month]},
                            'Severity' : {'$in' : infrastructure_monitoring_statistics.severity}
                        },{'_id' : 0}
                    ).skip((infrastructure_monitoring_statistics.page_number-1) * 10).to_list(10)

                    document_count = await trend_chart_collection_handle.count_documents(
                        {
                            'Month' : {'$in' : [month]},
                            'Severity' : {'$in' : infrastructure_monitoring_statistics.severity}
                        }
                    )
                
                # fetch data for the requested month 
                else:

                    data = await trend_chart_collection_handle.find(
                        {
                            'Month' : {'$in' : [month]}
                        },{'_id' : 0}
                    ).skip((infrastructure_monitoring_statistics.page_number-1) * 10).to_list(10)

                    document_count = await trend_chart_collection_handle.count_documents(
                        {
                            'Month' : {'$in' : [month]}
                        }
                    )

                filtered_records_json = []
                
                # Iterate over the fetched data.
                for record in data:
                    
                    record['Month'] = month

                    # Convert each record into JSON string.
                    record_json = json.dumps(record, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, record_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                response_data = {
                    "data" : filtered_records_json,
                    "total_rows" : document_count,
                    "total_pages" : math.ceil(document_count/10)
                }

                icecream.ic('Setting Cache .. /infra_history')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as e:
                print(e.msg())
                # Log error message in the log file.
                logger.error(f"Failed to get the vulnerabilities:{request.url}")

                return {
                    "status": 500,
                    "msg": "Failed to get the vulnerabilities"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }
    
@app.post('/export_infra_history', response_description = "export the history of month data")
async def export_infra_history(infrastructure_monitoring_statistics: InfrastuctureMonitoringStatistics, request: fastapi.Request) -> dict:

    """
    Export the data displayed in the table.

    :param infra: Gives the received data based on InfrastuctureMonitoringStatistics model.
    :ptype: InfrastuctureMonitoringStatistics model.

    :return: Data to be displayed and count of pages and rows.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:
        # check for both and year to be present -> else invalid input for data filtering
        if infrastructure_monitoring_statistics.month == "" or infrastructure_monitoring_statistics.year == "":

            return {
                "status" : 406,
                "msg" : "Invalid input"
            }

        # concatenate month and year as a single string
        month = infrastructure_monitoring_statistics.month + " " + infrastructure_monitoring_statistics.year

        # filter based on the multiple severities
        if infrastructure_monitoring_statistics.severity != []:

            data = await trend_chart_collection_handle.find(
                {
                    'Month' : {'$in' : [month]},
                    'Severity' : {'$in' : infrastructure_monitoring_statistics.severity}
                },{'_id' : 0, 'identifier' : 0}
            ).to_list(10000)
        
        # fetch data for the requested month 
        else:

            data = await trend_chart_collection_handle.find(
                {
                    'Month' : {'$in' : [month]}
                },{'_id' : 0, 'identifier' : 0}
            ).to_list(10000)

        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(data)
        
        df['Month'] = [month]*len(df)
        df.fillna("NA", inplace=True)

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
    
    except:
        # Log error message in the log file.
        logger.error(f"Failed to get the vulnerabilities:{request.url}")

        return {
            "status": 500,
            "msg": "Failed to get the vulnerabilities"
        }


@app.post('/infra_stats_count', response_description = "Statistics of overall data")
async def infra_stats(infrastructure_monitoring_statistics: InfrastuctureMonitoringStatistics, request: fastapi.Request) -> dict:

    """
    Fetch the stats to be displayed in the table.

    :param infra: Gives the received data based on InfrastuctureMonitoringStatistics model.
    :ptype: InfrastuctureMonitoringStatistics model.

    :return: Data to be displayed and count of pages and rows.
    :rtype: dict
    """
        
    logger = InfrastructureMonitoringLogger()

    cache_key = f'/infra_stats_count-{infrastructure_monitoring_statistics.year}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /infra_stats_count')
        cached_data = redis_client.get(cache_key)

        if cached_data:
            icecream.ic('Cache hit .. /infra_stats_count')
            return eval(cached_data)
        
        else:
            icecream.ic('Cache Miss .. /infra_stats_count')
            try:
                
                # return whole data statistics if no year is provided
                if infrastructure_monitoring_statistics.year == "":

                    data = await vulnerability_chart_collection_handle.find({
                        "chartconst" : {"$ne" : True},
                    },{"_id" : 0}).sort('_id', 1).to_list(None)

                    # Count total number of documents in the results of the search filter.
                    document_count = await vulnerability_chart_collection_handle.count_documents({}) 

                # filter the data based on the provided year
                else:

                    data = await vulnerability_chart_collection_handle.find({
                            "chartconst" : {"$ne" : True},
                            'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_statistics.year}.*', re.IGNORECASE)}
                    },{"_id" : 0}).sort('_id', 1).to_list(None)

                    # Count total number of documents in the results of the search filter.
                    document_count = await vulnerability_chart_collection_handle.count_documents({
                            'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_statistics.year}.*', re.IGNORECASE)}
                    })
                    
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

                response_data = {
                    "data" : filtered_records_json,
                    "total_rows" : document_count,
                    "total_pages" : math.ceil(document_count/12)
                }

                icecream.ic('Setting Cache .. /infra_stats_count')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as e:
                # Log error message in the log file.
                logger.error(f"Failed to get the count of month wise vulnerabilities:{request.url}")

                return {
                    "status": 500,
                    "msg": "Failed to get the count of month wise vulnerabilities"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }
    
@app.post('/export_infra_stats_count', response_description = "Export the Statistics of overall data")
async def export_infra_stats(infrastructure_monitoring_statistics: InfrastuctureMonitoringStatistics, request: fastapi.Request) -> dict:
    """
    Export the data displayed in the table.

    :param infra: Gives the received data based on InfrastuctureMonitoringStatistics model.
    :ptype: InfrastuctureMonitoringStatistics model.

    :return: Data to be displayed and count of pages and rows.
    :rtype: dict
    """

    logger = InfrastructureMonitoringLogger()

    try:
        
        # return whole data statistics if no year is provided
        if infrastructure_monitoring_statistics.year == "":

            data = await vulnerability_chart_collection_handle.find({
                "chartconst" : {"$ne" : True},
            },{"_id" : 0}).sort('_id', 1).to_list(100)

        # filter the data based on the provided year
        else:

            data = await vulnerability_chart_collection_handle.find({
                    "chartconst" : {"$ne" : True},
                    'Month': {"$regex" : re.compile(f'.*{infrastructure_monitoring_statistics.year}.*', re.IGNORECASE)}
            },{"_id" : 0}).sort('_id', 1).to_list(100)

        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(data)

        # # Generate a unique '.xlsx' file name to store the data.
        f_name = uuid.uuid1().hex + '.xlsx'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}',index=False)

        # # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    except Exception as e:
        # Log error message in the log file.
        print(repr(e))
        logger.error(f"Failed to get the count of month wise vulnerabilities:{request.url}")

        return {
            "status": 500,
            "msg": "Failed to get the count of month wise vulnerabilities"
        }


if __name__ == "__main__":
    uvicorn.run(
        'app:app', 
        host='0.0.0.0', 
        port=55560, 
        reload=True
    )