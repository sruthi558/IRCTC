import re
import os
import json
import math
import uuid
import redis
import pandas
import typing
import fastapi
import uvicorn
import logging
import pydantic
import datetime
import icecream
import pydantic_settings
from bson import json_util
import motor.motor_asyncio
from fastapi_cache import FastAPICache
from concurrent.futures import ProcessPoolExecutor
from fastapi_cache.backends.inmemory import InMemoryBackend
from status_codes import suspected_rfi, mappingDictionary

# Logger function.
def SuspiciousLogger():

    # Create a logger.
    logger = logging.getLogger("SuspiciousMonitoring")

    # The level of the logger is set to 'INFO'.
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(threadName)s:%(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('suspicious.log')

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

# Create a handle to the collection for the suspicious PNR's.
col_pnr = db.irctc_pnr_test_1

# Create a handle to the collection for the user registered data.
col_user = db.irctc_userid_data

# Create a handle to the collection for the suspicious IP's.
col_sus_ips = db.irctc_sus_ips_test_1

# Create a handle to the collection for the suspicious Users.
col_sus_users = db.irctc_userid_data_test_1

min_date = datetime.datetime(1970, 1, 1)

today_date = datetime.datetime.combine(datetime.datetime.utcnow(), datetime.time.min)


class UserID(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it
    """
    userid: typing.Optional[list] = []

    status: typing.Optional[int] = 0

    block_date: typing.Optional[datetime.datetime] = datetime.datetime(1970,1,1)


class PnrList(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model for the suspicious PNR's.
    """

    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Set the 'trainno' for which the ticked is booked.
    trainno: typing.Optional[list] = []

    # Set the station list for which the ticket is booked
    station_list: list | str

    # Set the starting date for which the suspicious PNR's is to be searched.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Set the ending date for which the suspicious PNR's is to be searched.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

    # Set search string as empty string as default.
    search_pnr: typing.Optional[str] = ''

    filter_date: typing.Optional[str] = 'Journey Date'


class PnrId(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model to add comments to the suspicious PNR's .
    """

    # Set the the value for the PNR number.
    pnr_no: typing.Optional[str] = ''

    # Put comment for the particular suspected PNR.
    comment: typing.Optional[str] = ''

    # Set the id for the comment made.
    cid: typing.Optional[str] = ''

    rate: typing.Optional[int] = 1

class IPHistoryList(pydantic.BaseModel):

    # Set the initial page number to '1' to display the first page of the results.
    page_id : typing.Optional[int] = 1

    # Set search string as empty string as default.
    search: typing.Optional[str] = ''

    # Set starting date in the search filter for which suspicious IP's records are to be filtered.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

class IPModalHistory(pydantic.BaseModel):

    # Set the initial page number to '1' to display the first page of the results.
    page_id : typing.Optional[int] = 1

    # Set ip string as empty string as default.
    ip_addr : typing.Optional[str] = ''

    source : typing.Optional[str] = 'USER'

class IPlist(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.
    
    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model for the suspicious IP's through which the ticket is booked.
    """
    
    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Set the boolean value which defines if the ticket is booked using VPS IP addresses or NON VPS IP addresses.
    type_vps: typing.Optional[bool] = True

    # Set starting date in the search filter for which suspicious IP's records are to be filtered.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)


class SuspiciousIPHistory(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.
    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model which will show the history details of all the suspeected IP's.
    """

    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Set IP address for the model.
    ip_addr: typing.Optional[str] = ''


class UserList(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.
    
    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic to define model for the tickets booked by the suspicious Useres.
    """

    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Starting date with default value as current date.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Ending date with default value as current date.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

    # Set the current status for the user whether some action is taken against him or not.
    status: typing.Optional[list] = [0]

    # Set search string as empty string as default.
    search_user: typing.Optional[str] = ''

    source: typing.Optional[str] = 'ALL'

def setup_mount_folder(f_file):
    """Summary

    Returns:
        TYPE: Description
    """
    path = os.getcwd()
    # file Upload
    DOWNLOAD_FOLDER = os.path.join(path, f_file)
    # Make directory if "download" folder not exists
    if not os.path.isdir(DOWNLOAD_FOLDER):
        os.mkdir(DOWNLOAD_FOLDER)
    return DOWNLOAD_FOLDER


def replace_arr_vals(arr, dic):
    new_arr = []
    for i in arr:
        new_arr.append(dic[i])
    return new_arr

def convert_list_to_string(lst):
    return str(lst).replace("[", "").replace("]", "").replace("'","")

async def on_startup():
    setup_mount_folder('download_folder')
    app.state.executor = ProcessPoolExecutor()
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

app.add_event_handler('startup', on_startup)

redis_client = redis.Redis(host='localhost', port=6379, db=0)
CACHE_EXP = 60*120

########################
# Suspected IP Address #
########################


@app.post('/ip_history_list')
async def ip_history_list(ip_hist : IPHistoryList, request: fastapi.Request):
    logger = SuspiciousLogger()
    
    cache_key = f'ip-history-list-key-{ip_hist.page_id}-{ip_hist.starting_date.date()}-{ip_hist.ending_date.date()}-{ip_hist.search}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /ip_history_list')
        cached_data = redis_client.get(cache_key)

        if cached_data:
            icecream.ic('Cache hit .. ip_history_list')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            
            return eval(cached_data)
        
        else:
            icecream.ic('Cache Miss .. ip_history_list')

            try:
                icecream.ic('Getting Cache .. /ip_history_list')
                cached_data = redis_client.get(cache_key)

                ip_hist.starting_date = datetime.datetime.combine(ip_hist.starting_date.date(), datetime.time.min)

                ip_hist.ending_date = datetime.datetime.combine((ip_hist.ending_date.date() + datetime.timedelta(days=1)), datetime.time.min)

                if ip_hist.search == '':

                    if ip_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                        ip_list = await col_sus_ips.find({},{
                            '_id' : 0,
                            'TK_COUNT' : 0,
                            'USER_COUNT' : 0
                        }).sort('DATE', -1).skip((ip_hist.page_id - 1)*20).to_list(20)

                        total_count = await col_sus_ips.count_documents({})
                        print(ip_list)
                    
                    else:

                        ip_list = await col_sus_ips.find({
                            "DATE" : {
                                "$gte" : ip_hist.starting_date,
                                "$lt" : ip_hist.ending_date
                            }
                        },{
                            "_id": 0,
                            'TK_COUNT' : 0,
                            'USER_COUNT' : 0
                        }).sort('DATE', -1).skip((ip_hist.page_id - 1)*20).to_list(20)

                        total_count = await col_sus_ips.count_documents({
                                "DATE" : {
                                    "$gte" : ip_hist.starting_date,
                                    "$lt" : ip_hist.ending_date}
                            })
                        print(ip_list)

                else:
                    if ip_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                        ip_list = await col_sus_ips.find({
                            "IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)}
                        },{
                            "_id": 0,
                            'TK_COUNT' : 0,
                            'USER_COUNT' : 0
                        }).sort('DATE', -1).skip((ip_hist.page_id - 1)*20).to_list(20)

                        total_count = await col_sus_ips.count_documents({"IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)}})
                    
                    else:

                        ip_list = await col_sus_ips.find({
                            "IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)},
                            "DATE" : {
                                "$gte" : ip_hist.starting_date,
                                "$lt" : ip_hist.ending_date
                            }
                        },{
                            "_id": 0,
                            'TK_COUNT' : 0,
                            'USER_COUNT' : 0
                        }).sort('DATE', -1).skip((ip_hist.page_id - 1)*20).to_list(20)

                        total_count = await col_sus_ips.count_documents({
                            "IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)},
                            "DATE" : {
                                "$gte" : ip_hist.starting_date,
                                "$lt" : ip_hist.ending_date}
                        })

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for ip_addr in ip_list:

                    # Convert each record into JSON string.
                    record_json = json.dumps(ip_addr, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, record_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                # Return the dictionary containing filtered records and total page count of filtered records.
                page_count = math.ceil(total_count/20)
                
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': total_count
                }

                icecream.ic('Setting Cache .. /ip_history_list')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')
                
                return response_data
                
            except:
                # Log error message in the log file.
                logger.error(f"Failed to get IP History data:{request.url}")

                return{
                    "status": 500,
                    "msg": "Failed to get IP History data"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }

@app.post('/fetch_ip_modal')
async def ip_modal_list(ip_modal_hist: IPModalHistory, request: fastapi.Request):
    """
    List all the history details of the IP's.

    :param ip_mod: Gives the received data based on IPModal model.
    :ptype: IPList model.

    :return: List of data containing history details of the IP's and the  total count of the filtered data pages.
    :rtype: dict
    """

    logger = SuspiciousLogger()

    cache_key = f'/fetch_ip_modal-{ip_modal_hist.page_id}-{ip_modal_hist.ip_addr}-{ip_modal_hist.source}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /fecth_ip_modal')
        cached_data = redis_client.get(cache_key)

        if cached_data: 
            icecream.ic('Getting hit .. /fecth_ip_modal')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)

        else:
            icecream.ic('Cache Miss .. /fetch_ip_modal')
            try:

                if ip_modal_hist.source == 'USER':

                    ip_modal_list = await col_user.find(
                        {
                            'IP_ADDRESS' : ip_modal_hist.ip_addr
                        }
                    ).sort('REGISTRATION_DATETIME',-1).skip((ip_modal_hist.page_id - 1)*10).to_list(10)

                    total_count = await col_user.count_documents({'IP_ADDRESS' : ip_modal_hist.ip_addr})

                elif ip_modal_hist.source == 'PNR':

                    ip_modal_list = await col_pnr.find(
                        {
                            'IP_ADDRESS' : ip_modal_hist.ip_addr
                        }
                    ).sort('BOOKING_DATE',-1).skip((ip_modal_hist.page_id - 1)*10).to_list(10)

                    total_count = await col_pnr.count_documents({'IP_ADDRESS' : ip_modal_hist.ip_addr})

                if ip_modal_list == []:

                    return{
                        "status" : 200,
                        "msg" : f"No History details found for the source {ip_modal_hist.source}"
                    }
                
                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in ip_modal_list:

                    record = {}
                    
                    if ip_modal_hist.source == "PNR":
                        record["LOG_DATE"] = rec['BOOKING_DATE']
                        record["SOURCE"] = "PNR"
                        record["SOURCE_DATA"] = rec["PNR_NUMBER"]
                    else:
                        record["LOG_DATE"] = rec['REGISTRATION_DATETIME']
                        record["SOURCE"] = "USER"
                        record["SOURCE_DATA"] = rec["USERNAME"]

                    record["IP_ADDRESS"] = rec["IP_ADDRESS"]
                    record["ISP"] = rec["ISP"]
                    record["ASN"] = rec["ASN"]
                    record["VPS"] = rec["VPS"]

                    # Convert each record into JSON string.
                    response_json = json.dumps(record, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                # Return the dictionary containing filtered records and total page count of filtered records.
                page_count = math.ceil(total_count/10)
                
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': total_count
                }

                icecream.ic('Setting Cache .. /fetch_ip_modal')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as e:
                print(e.msg())
                logger.error(f"Failed to load history details of the IP:{request.url}")
                return{
                    "status": 500,
                    "msg": "Failed to load the history details of the IP"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return {
            "status": 500, 
            "msg": "Error with Cache Operation"
        }
        
@app.post('/down-ip-history')
async def ip_history_export(ip_hist : IPHistoryList, request: fastapi.Request):

    logger = SuspiciousLogger()

    try:
        ip_hist.starting_date = datetime.datetime.combine(ip_hist.starting_date.date(), datetime.time.min)

        ip_hist.ending_date = datetime.datetime.combine(ip_hist.ending_date.date()+ datetime.timedelta(days=1), datetime.time.min)

        if ip_hist.search == '':

            if ip_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                ip_list = await col_sus_ips.find({},{
                    '_id' : 0,
                    'TK_COUNT' : 0,
                    'USER_COUNT' : 0,
                    'TAGS' : 0
                }).sort('DATE', -1).to_list(100000)
            
            else:

                ip_list = await col_sus_ips.find({
                    "DATE" : {
                        "$gte" : ip_hist.starting_date,
                        "$lt" : ip_hist.ending_date
                    }
                },{
                    "_id": 0,
                    'TK_COUNT' : 0,
                    'USER_COUNT' : 0,
                    'TAGS' : 0
                }).sort('DATE', -1).to_list(100000)


        else:
            if ip_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                ip_list = await col_sus_ips.find({
                    "IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)}
                },{
                    "_id": 0,
                    'TK_COUNT' : 0,
                    'USER_COUNT' : 0,
                    'TAGS' : 0
                }).sort('DATE', -1).to_list(100000)
            
            else:

                ip_list = await col_sus_ips.find({
                    "IP_ADDRESS" : {"$regex" : re.compile(f'.*{ip_hist.search}.*', re.IGNORECASE)},
                    "DATE" : {
                        "$gte" : ip_hist.starting_date,
                        "$lt" : ip_hist.ending_date
                    }
                },{
                    "_id": 0,
                    'TK_COUNT' : 0,
                    'USER_COUNT' : 0,
                    'TAGS' : 0
                }).sort('DATE', -1).to_list(100000)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(ip_list)
        df['DATE'] = df['DATE'].dt.strftime('%a %d %B %Y')

        df.rename(columns={'ISP': 'ISP (LATEST)', 'ASN': 'ASN (LATEST)', 'DATE' : 'DATE (LATEST)'}, inplace=True)

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}',index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
        
    except Exception as e:
        # print(e.msg())

        # Log error message in the log file.
        logger.error(f"Failed to get IP History data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get IP History data"
        }

@app.post('/down-ip-modal')
async def ip_modal_list(ip_modal_hist: IPModalHistory, request: fastapi.Request):
    """
    List all the history details of the IP's.

    :param ip_mod: Gives the received data based on IPModal model.
    :ptype: IPList model.

    :return: List of data containing history details of the IP's and the  total count of the filtered data pages.
    :rtype: dict
    """

    logger = SuspiciousLogger()
    
    try:

        if ip_modal_hist.source == 'USER':

            ip_modal_list = await col_user.find(
                {
                    'IP_ADDRESS' : ip_modal_hist.ip_addr
                }
            ).sort('REGISTRATION_DATETIME',-1).to_list(100000)

        elif ip_modal_hist.source == 'PNR':

            ip_modal_list = await col_pnr.find(
                {
                    'IP_ADDRESS' : ip_modal_hist.ip_addr
                }
            ).sort('BOOKING_DATE',-1).to_list(100000)

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for rec in ip_modal_list:

            record = {}

            record["IP_ADDRESS"] = rec["IP_ADDRESS"]
            record["ISP"] = rec["ISP"]
            record["ASN"] = rec["ASN"]
            record["VPS"] = rec["VPS"]
            
            if ip_modal_hist.source == "PNR":
                record["LOG_DATE"] = rec['BOOKING_DATE']
                record["SOURCE"] = "PNR"
                record["PNR_DATA"] = rec["PNR_NUMBER"]
            else:
                record["LOG_DATE"] = rec['REGISTRATION_DATETIME']
                record["SOURCE"] = "USER"
                record["USER_DATA"] = rec["USERNAME"]

            # # Add the JSON to the tracking list.
            filtered_records_json.append(record)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        
        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(filtered_records_json)
        df['LOG_DATE'] = df['LOG_DATE'].dt.strftime('%a %d %B %Y')

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}',index=False)

        # # Asynchronously streams a file as the response.
        # # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    except Exception as e:

        # print(e.msg())

        logger.error(f"Failed to load history details of the IP:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to load the history details of the IP"
        }
        

@app.post('/sus_pnr_list')
async def sus_log_dash(pnr: PnrList, request: fastapi.Request):
    """
    List all the booking deatils for the suspected PNR.

    :param pnr: Gives the received data based on PnrList model.
    :ptype: PnrList model.
    
    :return: List of data containing booking details of the suspected PNR and the  total count of the filtered data pages.
    :rtype: dict
    """

    """
    pnr.starting_date.date(): From the frontend the search filter is sending suspicious date(starting_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """
    
    # print(f'Request Micro => ', pnr)

    logger = SuspiciousLogger()

    cache_key = f'/sus_pnr_list-{pnr.page_id}-{pnr.starting_date.date()}-{pnr.ending_date.date()}-{pnr.search_pnr}--{pnr.station_list}--{pnr.filter_date}'
    icecream.ic(cache_key)

    search_only_pnr = False

    try:
        icecream.ic('Getting Cache .. /sus_pnr_list')
        cached_data = redis_client.get(cache_key)

        if cached_data:
            icecream.ic('Cache hit .. /sus_pnr_list')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)

        else:
            icecream.ic('Cache Miss .. /sus_pnr_list')
            try:

                station_list = list()

                pattern = r'\((.*?)\)'

                if pnr.station_list == "" or pnr.station_list == []: station_list = []

                elif isinstance(pnr.station_list, str):

                    match = re.search(pattern, pnr.station_list)

                    station_list.append(match.group(1))

                # Get only date from the starting date value and combine it with the 'min' time.
                pnr.starting_date = datetime.datetime.combine(pnr.starting_date.date(), datetime.time.min)

                pnr.ending_date = datetime.datetime.combine(pnr.ending_date.date(), datetime.time.min)

                if pnr.filter_date == "" or pnr.filter_date == 'Journey Date':
                    if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date() and pnr.search_pnr == '':
                        date_query = [
                            {
                                'JOURNEY_DATE' : {
                                    '$gte' : datetime.datetime.now() - datetime.timedelta(days=1)
                                }
                            }, {
                                'JOURNEY_DATE' : {
                                    '$lt' : datetime.datetime.now() + datetime.timedelta(days=1)
                                }
                            }
                        ]
                    
                    else:
                        date_query = [
                            {
                                'JOURNEY_DATE' : {
                                    '$gte' : pnr.starting_date
                                }
                            }, {
                                'JOURNEY_DATE' : {
                                    '$lt' : pnr.ending_date + datetime.timedelta(days=1)
                                }
                            }
                        ]

                else:
                    if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date() and pnr.search_pnr == '':
                        date_query = [
                            {
                                'BOOKING_DATE' : {
                                    '$gte' : datetime.datetime.now() - datetime.timedelta(days=1)
                                }
                            }, {
                                'BOOKING_DATE' : {
                                    '$lt' : datetime.datetime.now() + datetime.timedelta(days=1)
                                }
                            }
                        ]
                    
                    else:
                        date_query = [
                            {
                                'BOOKING_DATE' : {
                                    '$gte' : pnr.starting_date
                                }
                            }, {
                                'BOOKING_DATE' : {
                                    '$lt' : pnr.ending_date + datetime.timedelta(days=1)
                                }
                            }
                        ]

                # Display unfiltered list of suspected PNRs.
                if pnr.search_pnr == '':
                
                    # When only station name is provided to get data for the suspected PNR's.
                    if len(station_list) > 0:

                        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                        if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                            # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'FROM': {
                                    '$in': station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists': True
                                },
                                '$and': date_query
                            }, {
                                'USERNAME' : 1,
                                'PNR_NUMBER' : 1,
                                'JOURNEY_DATE' : 1,
                                'BOOKING_DATE' : 1,
                                'BOOKING_MOBILE' : 1,
                                'TRAIN_NUMBER' : 1,
                                'FROM' : 1,
                                'TO' : 1,
                                'TK_TYPE' : 1,
                                'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                        
                        
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'FROM' : {
                                    '$in' : station_list
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and': date_query
                            })
                            
                        # To Filter all the suspected users when suspected date(starting_date) is provided.
                        else:

                            # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'FROM' : {
                                    '$in' : station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and' : date_query
                            }, {
                            'USERNAME' : 1,
                            'PNR_NUMBER' : 1,
                            'JOURNEY_DATE' : 1,
                            'BOOKING_DATE' : 1,
                            'BOOKING_MOBILE' : 1,
                            'TRAIN_NUMBER' : 1,
                            'FROM' : 1,
                            'TO' : 1,
                            'TK_TYPE' : 1,
                            'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'FROM' : {
                                    '$in' : station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })

                    # When only train number is provided to get data for the suspected PNR's.
                    else:

                        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                        if pnr.starting_date.date() == datetime.datetime(1970,1,1).date():

                            # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and' : date_query
                            }, {
                                'USERNAME' : 1,
                                'PNR_NUMBER' : 1,
                                'JOURNEY_DATE' : 1,
                                'BOOKING_DATE' : 1,
                                'BOOKING_MOBILE' : 1,
                                'TRAIN_NUMBER' : 1,
                                'FROM' : 1,
                                'TO' : 1,
                                'TK_TYPE' : 1,
                                'TAGS' :1,
                            }).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })
                        
                        else:

                            # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and' : date_query
                            }, {
                                'USERNAME' : 1,
                                'PNR_NUMBER' : 1,
                                'JOURNEY_DATE' : 1,
                                'BOOKING_DATE' : 1,
                                'BOOKING_MOBILE' : 1,
                                'TRAIN_NUMBER' : 1,
                                'FROM' : 1,
                                'TO' : 1,
                                'TK_TYPE' : 1,
                                'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({ 
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })

                elif pnr.search_pnr != '' and len(station_list) == 0 and pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                    pnr_sus_list = await col_pnr.find({
                        '$or' :[
                            {
                                'PNR_NUMBER' : pnr.search_pnr,
                            },{
                                'PNR_NUMBER': int(pnr.search_pnr),
                            }
                        ],                        
                        'TAGS.0' : {
                            '$exists': True
                        }
                    }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1}).sort('BOOKING_DATE', 1).to_list(1)
                    
                    search_only_pnr = True
                
                # Filter the suspected user data on the basis of PNR number.
                else:

                    # When only station name is provided to get data for the suspected PNR's.
                    if len(station_list) > 0:

                        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                        if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                            # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'FROM': {
                                    '$in': station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists': True
                                },
                                '$and' : date_query
                            }, {
                                'USERNAME' : 1,
                                'PNR_NUMBER' : 1,
                                'JOURNEY_DATE' : 1,
                                'BOOKING_DATE' : 1,
                                'BOOKING_MOBILE' : 1,
                                'TRAIN_NUMBER' : 1,
                                'FROM' : 1,
                                'TO' : 1,
                                'TK_TYPE' : 1,
                                'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                        
                        
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'FROM' : {
                                    '$in' : station_list
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })
                            
                        # To Filter all the suspected users when suspected date(starting_date) is provided.
                        else:

                            # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'FROM' : {
                                    '$in' : station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and' : date_query
                            }, {
                            'USERNAME' : 1,
                            'PNR_NUMBER' : 1,
                            'JOURNEY_DATE' : 1,
                            'BOOKING_DATE' : 1,
                            'BOOKING_MOBILE' : 1,
                            'TRAIN_NUMBER' : 1,
                            'FROM' : 1,
                            'TO' : 1,
                            'TK_TYPE' : 1,
                            'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'FROM' : {
                                    '$in' : station_list
                                }, 
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })

                    # When only train number is provided to get data for the suspected PNR's.
                    else:

                        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                        if pnr.starting_date.date() == datetime.datetime(1970,1,1).date():

                            # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': date_query
                            }, {
                            'USERNAME' : 1,
                            'PNR_NUMBER' : 1,
                            'JOURNEY_DATE' : 1,
                            'BOOKING_DATE' : 1,
                            'BOOKING_MOBILE' : 1,
                            'TRAIN_NUMBER' : 1,
                            'FROM' : 1,
                            'TO' : 1,
                            'TK_TYPE' : 1,
                            'TAGS' :1,
                            }).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': date_query
                            })

                        # To Filter all the suspected users when suspected date(starting_date) is provided.
                        else:

                            # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (JOURNEY_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                            pnr_sus_list = await col_pnr.find({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                } ,
                                '$and' : date_query
                            },{
                                'USERNAME' : 1,
                                'PNR_NUMBER' : 1,
                                'JOURNEY_DATE' : 1,
                                'BOOKING_DATE' : 1,
                                'BOOKING_MOBILE' : 1,
                                'TRAIN_NUMBER' : 1,
                                'FROM' : 1,
                                'TO' : 1,
                                'TK_TYPE' : 1,
                                'TAGS' :1}).sort('BOOKING_DATE', 1).skip((pnr.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_pnr.count_documents({
                                'PNR_NUMBER': {
                                    '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and' : date_query
                            })
                                
                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for suspicious_pnrs in pnr_sus_list:

                    tags = await col_sus_users.find_one({'USERNAME': suspicious_pnrs['USERNAME']}, {'TAGS':1, '_id':0})

                    if tags != None and 'TAGS' in tags.keys():

                        suspicious_pnrs['TAGS'] = suspicious_pnrs['TAGS'] + tags['TAGS']
                        suspicious_pnrs['TAGS'] =list(set(suspicious_pnrs['TAGS']))

                    rfi = []
                    try:
                        for tag in suspicious_pnrs['TAGS']:
                            try:
                                rfi.append(suspected_rfi[tag])
                            except:
                                pass
                    except:
                        pass

                    suspicious_pnrs['RFI_RULE'] = rfi
                    
                    # Convert each record into JSON string.
                    record_json = json.dumps(suspicious_pnrs, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, record_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                if not search_only_pnr:
                    # Return the dictionary containing filtered records and total page count of filtered records.
                    page_count = math.ceil(document_count/10)
                
                else:
                    page_count = 1
                    document_count = 1
                    
                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': document_count
                }

                icecream.ic('Setting Cache .. /sus_pnr_list')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data
            
            except Exception as e:
                print(e.msg())

                # Log error message in the log file.
                logger.error(f"Failed to get suspicious PNR data:{request.url}")

                return{
                    "status": 500,
                    "msg": "Failed to get suspicious PNR data"
                }
            
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }

@app.post('/sus_down_pnr')
async def sus_pnr_down(pnr: PnrList, request: fastapi.Request):
    """
    List all the booking deatils for the suspected PNR.

    :param pnr: Gives the received data based on PnrList model.
    :ptype: PnrList model.
    
    :return: List of data containing booking details of the suspected PNR and the  total count of the filtered data pages.
    :rtype: dict
    """

    """
    pnr.starting_date.date(): From the frontend the search filter is sending suspicious date(starting_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """

    logger = SuspiciousLogger()

    try:

        station_list = list()
        pattern = r'\((.*?)\)'

        if pnr.station_list == "" or pnr.station_list == []: station_list = []

        elif isinstance(pnr.station_list, str):

            match = re.search(pattern, pnr.station_list)

            station_list.append(match.group(1))

        # Get only date from the starting date value and combine it with the 'min' time.
        pnr.starting_date = datetime.datetime.combine(pnr.starting_date.date(), datetime.time.min)

        pnr.ending_date = datetime.datetime.combine(pnr.ending_date.date(), datetime.time.min)

        if pnr.filter_date == "" or pnr.filter_date == 'Journey Date':
            if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date() and pnr.search_pnr == '':
                date_query = [
                    {
                        'JOURNEY_DATE' : {
                            '$gte' : datetime.datetime.now() - datetime.timedelta(days=1)
                        }
                    }, {
                        'JOURNEY_DATE' : {
                            '$lt' : datetime.datetime.now() + datetime.timedelta(days=1)
                        }
                    }
                ]
            
            else:
                date_query = [
                    {
                        'JOURNEY_DATE' : {
                            '$gte' : pnr.starting_date
                        }
                    }, {
                        'JOURNEY_DATE' : {
                            '$lt' : pnr.ending_date + datetime.timedelta(days=1)
                        }
                    }
                ]

        else:
            if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date() and pnr.search_pnr == '':
                date_query = [
                    {
                        'BOOKING_DATE' : {
                            '$gte' : datetime.datetime.now() - datetime.timedelta(days=1)
                        }
                    }, {
                        'BOOKING_DATE' : {
                            '$lt' : datetime.datetime.now() + datetime.timedelta(days=1)
                        }
                    }
                ]
            
            else:
                date_query = [
                    {
                        'BOOKING_DATE' : {
                            '$gte' : pnr.starting_date
                        }
                    }, {
                        'BOOKING_DATE' : {
                            '$lt' : pnr.ending_date + datetime.timedelta(days=1)
                        }
                    }
                ]

        # Display unfiltered list of suspected PNRs.
        if pnr.search_pnr == '':
        
            # When only station name is provided to get data for the suspected PNR's.
            if len(station_list) > 0:

                # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                    # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'FROM': {
                            '$in': station_list
                        }, 
                        'TAGS.0' : {
                            '$exists': True
                        },
                        '$and': date_query
                    }, {
                    'USERNAME' : 1,
                    'PNR_NUMBER' : 1,
                    'JOURNEY_DATE' : 1,
                    'BOOKING_DATE' : 1,
                    'BOOKING_MOBILE' : 1,
                    'TRAIN_NUMBER' : 1,
                    'FROM' : 1,
                    'TO' : 1,
                    'TK_TYPE' : 1,
                    'TAGS' :1}).to_list(100000)
                
                    
                # To Filter all the suspected users when suspected date(starting_date) is provided.
                else:

                    # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'FROM' : {
                            '$in' : station_list
                        }, 
                        'TAGS.0' : {
                            '$exists' : True
                        },
                        '$and' : date_query
                    }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1}).to_list(100000)

            # When only train number is provided to get data for the suspected PNR's.
            else:

                # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                if pnr.starting_date.date() == datetime.datetime(1970,1,1).date():

                    # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'TAGS.0' : {
                            '$exists' : True
                        },
                        '$and' : date_query
                    }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1
                    }).to_list(100000)
                
                else:

                    # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'TAGS.0' : {
                            '$exists' : True
                        },
                        '$and' : date_query
                        }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1}).to_list(100000)
                    
        elif pnr.search_pnr != '' and len(station_list) == 0 and pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
            pnr_sus_list = await col_pnr.find({
                '$or' :[
                    {
                        'PNR_NUMBER' : pnr.search_pnr,
                    },{
                        'PNR_NUMBER': int(pnr.search_pnr),
                    }
                ],                        
                'TAGS.0' : {
                    '$exists': True
                }
            }, {
                'USERNAME' : 1,
                'PNR_NUMBER' : 1,
                'JOURNEY_DATE' : 1,
                'BOOKING_DATE' : 1,
                'BOOKING_MOBILE' : 1,
                'TRAIN_NUMBER' : 1,
                'FROM' : 1,
                'TO' : 1,
                'TK_TYPE' : 1,
                'TAGS' :1}).to_list(1)
            
        # Filter the suspected user data on the basis of PNR number.
        else:

            # When only station name is provided to get data for the suspected PNR's.
            if len(station_list) > 0:

                # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                if pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                    # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'PNR_NUMBER': {
                            '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                        },
                        'FROM': {
                            '$in': station_list
                        }, 
                        'TAGS.0' : {
                            '$exists': True
                        },
                        '$and' : date_query
                    }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1
                    }).to_list(100000)
                    
                # To Filter all the suspected users when suspected date(starting_date) is provided.
                else:

                    # Find on keyword (TRAIN_NUMBER), (FROM), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by 'BOOKING_DATE' --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'PNR_NUMBER': {
                            '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                        },
                        'FROM' : {
                            '$in' : station_list
                        }, 
                        'TAGS.0' : {
                            '$exists' : True
                        },
                        '$and' : date_query
                        }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1}).to_list(100000)

            # When only train number is provided to get data for the suspected PNR's.
            else:

                # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                if pnr.starting_date.date() == datetime.datetime(1970,1,1).date():

                    # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (BOOKING_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'PNR_NUMBER': {
                            '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                        },
                        'TAGS.0' : {
                            '$exists' : True
                        },
                        '$and': date_query
                        }, {
                        'USERNAME' : 1,
                        'PNR_NUMBER' : 1,
                        'JOURNEY_DATE' : 1,
                        'BOOKING_DATE' : 1,
                        'BOOKING_MOBILE' : 1,
                        'TRAIN_NUMBER' : 1,
                        'FROM' : 1,
                        'TO' : 1,
                        'TK_TYPE' : 1,
                        'TAGS' :1
                        }).to_list(100000)

                # To Filter all the suspected users when suspected date(starting_date) is provided.
                else:

                    # Find on keyword (TRAIN_NUMBER), ((TAGS.0) if exists) and (JOURNEY_DATE) --> remove `_id` and `ANALYZED_FILE_REFERENCE` from the filtered document --> sort by `BOOKING_DATE` --> skip to results on `page_id` --> convert to list.
                    pnr_sus_list = await col_pnr.find({
                        'PNR_NUMBER': {
                            '$regex': re.compile(f'.*{pnr.search_pnr}.*', re.IGNORECASE)
                        },
                        'TAGS.0' : {
                            '$exists' : True
                        } ,
                        '$and' : date_query
                        }, 
                        {
                            'USERNAME' : 1,
                            'PNR_NUMBER' : 1,
                            'JOURNEY_DATE' : 1,
                            'BOOKING_DATE' : 1,
                            'BOOKING_MOBILE' : 1,
                            'TRAIN_NUMBER' : 1,
                            'FROM' : 1,
                            'TO' : 1,
                            'TK_TYPE' : 1,
                            'TAGS' :1
                        }).to_list(100000)
                        
        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for suspicious_pnrs in pnr_sus_list:

            tags = await col_sus_users.find_one({'USERNAME': suspicious_pnrs['USERNAME']}, {'TAGS':1, '_id':0})

            if tags != None and 'TAGS' in tags.keys():

                suspicious_pnrs['TAGS'] = suspicious_pnrs['TAGS'] + tags['TAGS']
                suspicious_pnrs['TAGS'] =list(set(suspicious_pnrs['TAGS']))
            
            # Convert each record into JSON string.
            record_json = json.dumps(suspicious_pnrs, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")   
    
        # Converts the 'pnr_sus_list' into pandas dataframe.     
        df = pandas.DataFrame(pnr_sus_list)

        try:
            df['BOOKING_DATE'] = df['BOOKING_DATE'].dt.strftime('%a %d %B %Y')
            df['JOURNEY_DATE'] = df['JOURNEY_DATE'].dt.strftime('%a %d %B %Y')
            df['TAGS'] = df['TAGS'].apply(lambda x: replace_arr_vals(x, mappingDictionary))
            df['TAGS'] = df["TAGS"].apply(convert_list_to_string)
        
        except: pass
        
        # Replace the boolean value with the string.
        booleanDictionary = {
            True: 'TRUE', 
            False: 'FALSE'
        }

        # Replaces the dataframe keys with the values specified in `booleanDictionary`.
        df = df.replace(booleanDictionary)

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}',index=False)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    
    except Exception as e:

        print(e.msg())

        # Log error message in the log file.
        logger.error(f"Failed to download suspicious PNR file")

        return{
            "status": 500,
            "msg": f"Failed to download suspicious PNR file"
        }


@app.post('/fetch-comment-pnr')
async def fetch_pnr_comment(pnr_id: PnrId, request: fastapi.Request):
    """
    List all the comment deatils for the suspected PNR.

    :param pnr: Gives the received data based on PnrId model.
    :ptype: PnrId model.
    
    :return: List of data that contains comments on the suspected PNR.
    :rtype: dict
    """

    logger = SuspiciousLogger()

    try:

        # Find the comments for the `PNR NUMBER`. 
        pnr_comment_list = await col_pnr.find_one({
            'PNR_NUMBER' : pnr_id.pnr_no
            }, {
            '_id' : 0
        })

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # When comments are present for the suspected PNR.
        if 'COMMENTS' in pnr_comment_list.keys():

            # Iterate over the fetched data.
            for comments in pnr_comment_list['COMMENTS']:

                # Convert each record into JSON string.
                response_json = json.dumps(comments, default = json_util.default)

                # Add the JSON to the tracking list.
                filtered_records_json.insert(0, response_json)

            # Get the user email, cookie and remember token from the request header.
            header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

            # Log the data into the log file.
            logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

            # Retun the list containing comments for the suspectd PNR.
            return {
                'data_list': filtered_records_json
            }
        
        # When no comments are present for the suspected PNR.
        else:

            # Get the user email, cookie and remember token from the request header.
            header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

            # Log the data into the log file.
            logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

            # Return empty list if nop comment is present.
            return {
                'data_list':[]
            }
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to fetch comments for the suaspected PNR:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to fetch comments for the suspected PNR"
        }


@app.post('/submit-comment-pnr')
async def submitpnrcomment(pnr_id: PnrId, request: fastapi.Request):
    """
    Add the comment for the suspected PNR.

    :param pnr: Gives the received data based on PnrId model.
    :ptype: PnrId model.
    
    :return: Response that the comment is added for the suspected PNR.
    :rtype: dict
    """

    logger = SuspiciousLogger()

    try:

        # Update the collection by appending the comment for thr specific suspected PNR.
        col_pnr.update_one({
            'PNR_NUMBER' : pnr_id.pnr_no
            }, {
            '$push' : {
                'COMMENTS' : {
                    'DATE': datetime.datetime.now(), 
                    'COMMENT': pnr_id.comment,
                    'EMAIL': 'irctc@pinacalabs.com',
                    'CID':uuid.uuid4().hex,
                    'RATE': pnr_id.rate
                }
            }
        })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the success message for the added comment.
        return {
            'detail': f'{pnr_id.pnr_no} Comment Added'
        }
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to add comment for the PNR")

        return{
            "status": 500,
            "msg": "Failed to add comment for the PNR"
        }


@app.post('/sus_user_list')
async def sus_list_user(user_list: UserList, request: fastapi.Request):
    """
    List all the booking deatils for the suspected Users.

    :param user: Gives the received data based on UserList model.
    :ptype: UserList model.

    :return: List of data containing booking details of the suspected User and the  total count of the filtered data pages.
    :rtype: dict
    """

    """
    user.suspected_date.date(): From the frontend the search filter is sending suspicious date(suspected_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """

    logger = SuspiciousLogger()

    cache_key = f'/sus_user_list-{user_list.page_id}-{user_list.starting_date.date()}-{user_list.ending_date.date()}-{user_list.search_user}-{user_list.source}'
    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /sus_user_list')
        cached_data = redis_client.get(cache_key)

        if cached_data:
            icecream.ic('Cache hit .. /sus_user_list')
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)

        else:
            icecream.ic('Cache Miss .. /sus_user_list')
            try:

                user_list.starting_date = datetime.datetime.combine(user_list.starting_date.date(), datetime.time.min)

                user_list.ending_date = datetime.datetime.combine(user_list.ending_date.date(), datetime.time.min)
            
                # Display unfiltered list of suspected users.
                if user_list.search_user == '':

                    # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                    if user_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                        if user_list.source == 'ALL':

                            # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                }
                            }, {
                                '_id' : 0}).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                }
                            })
                        
                        else:

                            # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                },
                                'SOURCE' : user_list.source
                            }, {
                                '_id' : 0}).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                },
                                'SOURCE' : user_list.source
                            })
                    
                    # To Filter all the suspected users when suspected date(suspected_date) is provided.
                    else:

                        if user_list.source == 'ALL':
                            # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                }}, {
                                '_id' : 0
                                }).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                }
                            })
                        
                        else:
                            # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                },'SOURCE' : user_list.source
                                }, {
                                '_id' : 0
                                }).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                },'SOURCE' : user_list.source
                            })
                
                # Filter the suspected user data based on username.
                else:

                    # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
                    if user_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                        if user_list.source == 'ALL':

                            # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                'status' : {
                                    '$in' : user_list.status
                                }
                            }, {
                                '_id' : 0}).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                }
                            })
                        
                        else:
                            # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                'status' : {
                                    '$in' : user_list.status
                                }, 'SOURCE' : user_list.source
                            }, {
                                '_id' : 0}).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            

                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                'status' : {
                                    '$in' : user_list.status
                                }, 'SOURCE' : user_list.source
                            })
                        
                    # To Filter all the suspected users when suspected date(suspected_date) is provided.
                    else:
                        if user_list.source == 'ALL':

                            # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                }}, {
                                '_id' : 0
                                }).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                }
                            })

                        else:
                            # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                            user_sus_list = await col_sus_users.find({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                },
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                }, 'SOURCE' : user_list.source
                                }, {
                                '_id' : 0
                                }).sort('SUS_DATE', -1).skip((user_list.page_id - 1) * 10).to_list(10)
                            
                            # Count total number of documents in the results of the filtered records.
                            document_count = await col_sus_users.count_documents({
                                'USERNAME': {
                                    '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                                },
                                'TAGS.0' : {
                                    '$exists' : True
                                }, 
                                '$and': [{
                                            'SUS_DATE' : {
                                                '$gte' : user_list.starting_date
                                            }
                                        }, {
                                            'SUS_DATE': {
                                                '$lte' : user_list.ending_date
                                            }
                                        }
                                    ],
                                'status' : {
                                    '$in' : user_list.status
                                },'SOURCE' : user_list.source
                            })

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for userid in user_sus_list:
                    
                    if 'SOURCE' not in userid.keys():
                        userid['SOURCE'] = "N.A."
                    rfi = []
                    try:
                        for tag in userid['TAGS']:
                            try:
                                rfi.append(suspected_rfi[tag])
                            except:
                                pass
                    except:
                        pass

                    userid['RFI_RULE'] = rfi

                    # Convert each record into JSON string.
                    response_json = json.dumps(userid, default = json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                # Return the dictionary containing filtered records and total page count of filtered records.
                page_count = math.ceil(document_count/10)

                response_data = {
                    'data_list': filtered_records_json[::-1], 
                    'total_pages' : page_count,
                    'total_rows': document_count
                }
            
                icecream.ic('Setting cache .. /sus_user_list')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')
                return response_data
            
            except:

                # Log error message in the log file.
                logger.error(f"Failed to get suspicious user list")

                return{
                    "status": 500,
                    "msg": "Failed to get suspicious user list"
                }
    
    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500, 
            "msg": "Error with Cache Operation"
        }


@app.post('/sus-down-user')
async def sus_user_down(user_list: UserList, request: fastapi.Request):
    """
    Download the file for the suspected User.

    :param user: Gives the received data based on UserList model.
    :ptype: UserList model.

    :return: Return the file path directly from the path operation function.
    :rtype: file
    """

    logger = SuspiciousLogger()

    user_list.starting_date = datetime.datetime.combine(user_list.starting_date.date(), datetime.time.min)

    user_list.ending_date = datetime.datetime.combine(user_list.ending_date.date(), datetime.time.min)
       
    # Display unfiltered list of suspected users.
    if user_list.search_user == '':

        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
        if user_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            if user_list.source == 'ALL':

                # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                user_sus_list = await col_sus_users.find({
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    'status' : {
                        '$in' : user_list.status
                    }
                }, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1}).to_list(100000)
            else:
                user_sus_list = await col_sus_users.find({
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    'status' : {
                        '$in' : user_list.status
                    }, 'SOURCE' : user_list.source
                }, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1}).to_list(100000)
        
        # To Filter all the suspected users when suspected date(suspected_date) is provided.
        else:

            if user_list.source == 'ALL':

                # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                user_sus_list = await col_sus_users.find({
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    '$and': [{
                                'SUS_DATE' : {
                                    '$gte' : user_list.starting_date
                                }
                            }, {
                                'SUS_DATE': {
                                    '$lte' : user_list.ending_date
                                }
                            }
                        ],
                    'status' : {
                        '$in' : user_list.status
                    }}, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1
                    }).to_list(100000)
            else:
                user_sus_list = await col_sus_users.find({
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    '$and': [{
                                'SUS_DATE' : {
                                    '$gte' : user_list.starting_date
                                }
                            }, {
                                'SUS_DATE': {
                                    '$lte' : user_list.ending_date
                                }
                            }
                        ],
                    'status' : {
                        '$in' : user_list.status
                    }, 'SOURCE' : user_list.source}, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1
                    }).to_list(100000)
    
    # Filter the suspected user data based on username.
    else:

        # To Filter all the suspected users when the page is loaded and no value is provided in the search box.
        if user_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            if user_list.source == 'ALL':

                # Filter records on the basis of the keyword ((TAGS.0) if exists) --> `_id` not equals to '0' --> sort by `SUS_DATE` in descending order --> skip to results on `page_id` --> convert to list.
                user_sus_list = await col_sus_users.find({
                    'USERNAME': {
                        '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                    },
                    'TAGS.0' : {
                        '$exists' : True
                    }, 
                    'status' : {
                        '$in' : user_list.status
                    }
                }, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1}).to_list(100000)
            else:
                user_sus_list = await col_sus_users.find({
                    'USERNAME': {
                        '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                    },
                    'TAGS.0' : {
                        '$exists' : True
                    }, 
                    'status' : {
                        '$in' : user_list.status
                    },'SOURCE' : user_list.source
                }, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1}).to_list(100000)
        
        # To Filter all the suspected users when suspected date(suspected_date) is provided.
        else:
            if user_list.source == 'ALL':

                # Filter records on the basis of the keyword ((TAGS.0) if exists) and (SUS_DATE) --> `_id` not equals to '0' --> sort by (SUS_DATE) in descending order --> skip to results on `page_id` --> convert to list.
                user_sus_list = await col_sus_users.find({
                    'USERNAME': {
                        '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                    },
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    '$and': [{
                                'SUS_DATE' : {
                                    '$gte' : user_list.starting_date
                                }
                            }, {
                                'SUS_DATE': {
                                    '$lte' : user_list.ending_date
                                }
                            }
                        ],
                    'status' : {
                        '$in' : user_list.status
                    }}, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1
                    }).to_list(100000)
            else:
                user_sus_list = await col_sus_users.find({
                    'USERNAME': {
                        '$regex': re.compile(f'.*{user_list.search_user}.*', re.IGNORECASE)
                    },
                    'TAGS.0' : {
                        '$exists' : True
                    },
                    '$and': [{
                                'SUS_DATE' : {
                                    '$gte' : user_list.starting_date
                                }
                            }, {
                                'SUS_DATE': {
                                    '$lte' : user_list.ending_date
                                }
                            }
                        ],
                    'status' : {
                        '$in' : user_list.status
                    },'SOURCE' : user_list.source}, {
                    '_id' : 0,
                    'USER_ID' : 1, 
                    'USERNAME' : 1, 
                    'SUS_DATE' : 1,
                    'SOURCE' : 1,
                    'TAGS' : 1
                    }).to_list(100000)
    
    # Converts the 'pnr_sus_list' into pandas dataframe.
    df = pandas.DataFrame(user_sus_list)

    # Replace the boolean value with the string.
    booleanDictionary = {
        True: 'TRUE',
        False: 'FALSE'
    }

    # Replaces the dataframe keys with the values specified in `booleanDictionary`.
    df = df.replace(booleanDictionary)

    try:

        # Replaces the dataframe keys with the values specified in `mappingDictionary`.
        df = df.replace(mappingDictionary)

        # Replace the (TAGS) keys with the values in the 'mappingDictionary'.
        df['TAGS'] = df['TAGS'].apply(lambda x: replace_arr_vals(x, mappingDictionary))
        df['TAGS'] = df["TAGS"].apply(convert_list_to_string)

        df['SUS_DATE'] = df['SUS_DATE'].dt.strftime('%a %d %B %Y')

        # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}', index=False)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to download {f_name} suspicious user file")

        return{
            "status": 500,
            "msg": f"Failed to download {f_name} suspicious user file"
        }


@app.post('/change-status-user')
async def user_status_change(user_id: UserID, request: fastapi.Request):
    """
    Block or Ignore the selected suspicious useres.

    :param user: Gives the received data based on UserID model.
    :ptype: UserList model.

    :return: Response with the message that the user status is changed.
    :rtype: dict
    """

    logger = SuspiciousLogger()
    
    try:

        # Find on keyword (USERNAME) --> set the status for the user.
        col_sus_users.update_many({
            'USERNAME' : {
                '$in' : user_id.userid
            }
        }, {
            '$set' : {
                'status' : user_id.status
            }
        })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        logger.info(f"User status changed successfully:{request.url}")

        return {
            'detail' : f'{user_id.userid} USER STATUS CHANGED'
        }
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to change the user status:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to change user status"
        }


@app.post('/block-user-date')
async def block_usersuspected_date(user: UserID, request: fastapi.Request):
    """
    Block all suspicious useres for the particular date.

    :param user: Gives the received data based on UserID model.
    :ptype: UserID model.

    :return: Response with the message that the user status is changed.
    :rtype: dict
    """

    logger = SuspiciousLogger()

    try:

        # Find on keyword (SUS_DATE) --> set the status for the user.
        col_sus_users.update_many({
            'SUS_DATE' : datetime.datetime.combine(user.block_date.date(), datetime.time.min)
            }, {
            '$set' : {
                'status' : 1
            }
        })

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        return {
            'detail': 'MULTIPLE USERS BLOCKED'
        }
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to block multiple users:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to block multiple users"
        }


@app.post('/sus_ip_list')
async def sus_list_ip(ip_list: IPlist, request: fastapi.Request):
    """
    List all the booking deatils for the suspected IP's.

    :param user: Gives the received data based on IPList model.
    :ptype: IPList model.

    :return: List of data containing booking details of the suspected IP's and the  total count of the filtered data pages.
    :rtype: dict
    """
    
    """
    ip.suspected_ip_date.date(): From the frontend the search filter is sending suspicious IP date(suspected_ip_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """

    logger = SuspiciousLogger()
    
    try:

        # To Filter all the suspected IP's when the page is loaded and no value is provided in the search box.
        if ip_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            # Filter records on the basis of the keyword ((VPS) if IP uses VPS) --> remove `_id` from the filtered document --> sort by (DATE), (TK_COUNT) and (USER_COUNT) in descending order --> skip to results on `page_id` --> convert to list.
            pnr_sus_list = await col_sus_ips.find({
                'VPS' : ip_list.type_vps
            }, {
                '_id' : 0}).sort(
                    [('DATE',-1),
                    ('TK_COUNT',-1),
                    ('USER_COUNT', -1) 
                    ]).skip((ip_list.page_id - 1) * 10).to_list(10)
            
            # Count total number of documents in the results of the filtered records.
            document_count = await col_sus_ips.count_documents({
                'VPS' : ip_list.type_vps
            })
        
        # To Filter all the suspected IP's when suspected IP date(suspected_ip_date) is provided.
        else:

            # Getting the required format of the datetime to filter the records.
            new_starting_date = datetime.datetime.combine(ip_list.starting_date.date(), datetime.time.min)

            # Get only date from the ending date value and combine it with the 'min' time.
            new_ending_date = datetime.datetime.combine(ip_list.ending_date.date(), datetime.time.min)

            # Filter records on the basis of the keyword ((VPS) if IP uses VPS) --> remove `_id` from the filtered document --> sort by (DATE), (TK_COUNT) and (USER_COUNT) in descending order --> skip to results on `page_id` --> convert to list.
            pnr_sus_list = await col_sus_ips.find({
                'VPS' : ip_list.type_vps,
                '$and': [{
                    'DATE' : {
                        '$gte' : new_starting_date
                        }
                    }, {
                    'DATE': {
                        '$lte' : new_ending_date
                        }
                    }   
                ]
            }, {
                '_id' : 0
            }).sort([
                ('DATE',-1),
                ('TK_COUNT', -1),
                ('USER_COUNT', -1)
            ]).skip((ip_list.page_id - 1) * 10).to_list(10)

            # Count total number of documents in the results of the filtered records.
            document_count = await col_sus_ips.count_documents({
                'VPS' : ip_list.type_vps, 
                '$and': [{
                    'DATE' : {
                        '$gte' : new_starting_date
                        }
                    }, {
                    'DATE': {
                        '$lte' : new_ending_date
                        }
                    }   
                ]
            })

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for userid in pnr_sus_list: 

            # Convert each record into JSON string.
            response_json = json.dumps(userid, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, response_json)


        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the dictionary containing filtered records and total page count of filtered records.
        return {
            'data_list': filtered_records_json[::-1], 
            'page_count': document_count
        }
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to get suspicious IP list data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get suspicious IP list data"
        }

@app.post('/sus-down-ip')
async def sus_ip_down(ip_list: IPlist, request: fastapi.Request):
    """
    Download the file for the suspected IP's.

    :param ip: Gives the received data based on IPList model.
    :ptype: IPList model.

    :return: Return the file path directly from the path operation function.
    :rtype: file
    """

    """
    ip.suspected_ip_date.date(): From the frontend the search filter is sending suspicious IP date(suspected_ip_date) which contains time along with the date by default, but analysis is only based on date so only date is being used for the check.
    
    datetime.datetime(1970, 1, 1).date(): Pydantic does not allow datetime comparison with 'None' so deault value is provided for the comparison when all the suspected user has to be displayed.
    """

    logger = SuspiciousLogger()

    try:

        # To Filter all the suspected IP's when the page is loaded and no value is provided in the search box.
        if ip_list.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            # Filter records on the basis of the keyword ((VPS) if IP uses VPS) --> `_id` not equals to '0' --> sort by 'DATE', 'TK_COUNT' and 'USER_cOUNT' in descending order --> skip to results on `page_id` --> convert to list.
            pnr_sus_list = await col_sus_ips.find({
                'VPS' : ip_list.type_vps
            }, {
                '_id' : 0
            }).to_list(100000)

        # To Filter all the suspected IP's when suspected IP date(suspected_ip_date) is provided.
        else:

            # Getting the required format of the datetime to filter the records.
            new_starting_date = datetime.datetime.combine(ip_list.starting_date.date(), datetime.time.min)

            # Get only date from the ending date value and combine it with the 'min' time.
            new_ending_date = datetime.datetime.combine(ip_list.ending_date.date(), datetime.time.min)

            # Filter all the suspected IP's when suspected IP date(suspected_ip_date) is provided.
            pnr_sus_list = await col_sus_ips.find({
                'VPS' : ip_list.type_vps,
                '$and': [{
                    'DATE' : {
                        '$gte' : new_starting_date
                        }
                    }, {
                    'DATE': {
                        '$lte' : new_ending_date
                        }
                    }   
                ]
            }, {
                '_id' : 0
            }).to_list(100000)

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(pnr_sus_list)

        # Replace the boolean value with the string.
        booleanDictionary = {
            True : 'TRUE', 
            False : 'FALSE'
        }
        
        # Replaces the dataframe keys with the values specified in `booleanDictionary`.
        df = df.replace(booleanDictionary)
        # mappingDictionary = {'USER_BOOK_MULTIPLE_IP': 'Multi-IP Bookings', 'USER_BOOK_SUSPICIOUS_MOBILE': 'Suspicious Booking Mobile Number','USER_BOOK_VPS': 'VPS Booking','USER_REG_IP_ADDR_SAME_MORE_4': 'Duplicate Address','USER_SERIES_BOOK_NONVPS':'User Series Booking','USER_SERIES_BOOK_VPS':'User Series Booking'}
        # df['TAGS'] = df['TAGS'].apply(lambda x: replace_arr_vals(x,mappingDictionary))

        df['DATE'] = df['DATE'].dt.strftime('%a %d %B %Y')
        # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}',index=False)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')
    
    except:

        # Log error message in the log file.
        logger.error(f"Failed to download suspicious IP list:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to download suspicious IP list"
        }


@app.post('/sus_ip_modal')
async def sus_list_ip(suspicious_ip_history: SuspiciousIPHistory, request: fastapi.Request):
    """
    List all the history details of the suspected IP's.

    :param ip_mod: Gives the received data based on IPModal model.
    :ptype: IPList model.

    :return: List of data containing booking details of the suspected IP's and the  total count of the filtered data pages.
    :rtype: dict
    """

    logger = SuspiciousLogger()
    
    try:

        # Filter records for the keyword (IP_ADDRESS) --> `_id` not equal to '0' --> sort by 'DATE', 'TK_COUNT' AND 'USER_COUNT' in descending order --> convert to list.
        pnr_sus_list = await col_sus_ips.find({
            'IP_ADDRESS' : suspicious_ip_history.ip_addr
        }, {
            '_id' : 0
        }).sort([
            ('DATE', -1),
            ('TK_COUNT', -1),
            ('USER_COUNT', -1)]).to_list(1000)
        
        # Count total number of documents in the results of the filtered records.
        document_count = await col_sus_ips.count_documents({
            'IP_ADDRESS' : suspicious_ip_history.ip_addr
        })

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for userid in pnr_sus_list:

            # Convert each record into JSON string.
            response_json = json.dumps(userid, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, response_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return the dictionary containing filtered records and total page count of filtered records.
        return {
            'data_list' : filtered_records_json[::-1], 
            'page_count': document_count
        }
    
    except:

        logger.error(f"Failed to load history details of the suspected IP's:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to load the history details of the suspected IP's"
        }


if __name__ == "__main__":
    uvicorn.run(
        'app:app', 
        host='0.0.0.0', 
        port=55570, 
        reload=True
    )