# Import libraries

import json
import fastapi
import typing
import motor.motor_asyncio
from bson import json_util
import datetime
import uvicorn
import dateutil.parser
import pydantic_settings
import pydantic
import logging


# Logger function.
def UserIDLogger():

    # Create a logger.
    logger = logging.getLogger("UserRegistration")

    # The level of the logger is set to 'INFO'.
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(threadName)s:%(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('UserId.log')

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


class UserRange(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to define model for the base data to be shown on Trends section.
    """

    # Starting date with default value 1st January 1970.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Ending date with default value current date.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)


# Collection for user registeration logs.
user_collection_handle = db.irctc_user_dash_test_1

# Global variable specifying minimum date.
min_date = datetime.datetime(1970, 1, 1)



@app.post('/userreg_dash_range')
async def user_reg_dash(userrange: UserRange, request: fastapi.Request):
    """
    Displays average users registered through VPS and NON-VPS, average users registered through vendors, top VPS ISPs registered users.

    :param userrange: Gives the received data based on UserRange model. 
    :ptype: UserRange model

    :return: Data for registered users through VPS, Non-VPS, vendor and  data for top VPS ISPs.
    :rtype: dict
    """

    # Dictionary for VPS users.
    VPS_USERS = {}

    # Dictionary for Non-VPS users.
    NON_VPS_USERS = {}

    # Dictionary for Vendor users.
    VENDORS_USERS = {}

    # Dictionary for top VPS ISPs.
    TOP_VPS_ISP = {}

    # Dictionary for top Non-VPS ISPs.
    TOP_NON_VPS_ISP = {}

    
    logger = UserIDLogger()

    try:
        
        # Find on (LOGS_DATE) between 'starting_date' and 'ending_date'  
        async for record in user_collection_handle.find({
            '$and':
            [
                {
                    'LOGS_DATE': {
                        '$gte': userrange.starting_date
                    }
                },
                {
                    'LOGS_DATE': {
                        '$lte': userrange.ending_date
                    }
                }
            ]},
            {
                '_id': 0
            }):

            # Store total number of users who registered through VPS in dictionaries `VPS_USERS` between specified dates.
            VPS_USERS[record['LOGS_DATE'].strftime("%d-%m-%y")] = record['TOTAL_VPS_USERS_REG']

            # Store total number of users who registered through Non-VPS in dictionaries `NON_VPS_USERS` between specified dates.
            NON_VPS_USERS[record['LOGS_DATE'].strftime("%d-%m-%y")] = record['TOTAL_USERS_REG'] - record['TOTAL_VPS_USERS_REG']

            # Store total number of users who registered through vendors in dictionaries `VENDORS_USERS` between specified dates.
            VENDORS_USERS[record['LOGS_DATE'].strftime("%d-%m-%y")] = record['VENDOR_USERS_COUNT']


            for i in range(20):
                # For `TOP_VPS_ISP`.
                try:
                    # If key 'ISP' for each 'VPS_ASN' does not exists in dictionary `TOP_VPS_ISP`.
                    # Then add key as 'ISP' and value as dictionary containing 'ASN', 'ISP' and 'TK_COUNT' for each 'VPS_ASN'.
                    if record['VPS_ASN'][i]['ISP'] not in TOP_VPS_ISP:
                        TOP_VPS_ISP[record['VPS_ASN'][i]['ISP']] = {
                                    'ASN' : record['VPS_ASN'][i]['ASN'],
                                    'ISP' : record['VPS_ASN'][i]['ISP'] ,
                                    'TK_COUNT': record['VPS_ASN'][i]['TK_COUNT']
                            }
                    
                    # Update the value of 'TK_COUNT' for each VPS_ASN.
                    else:
                        TOP_VPS_ISP[record['VPS_ASN'][i]['ISP']]['TK_COUNT'] += record['VPS_ASN'][i]['TK_COUNT']
                except:
                    pass
                
                # Previously used in code, now deprecated.
                # # For `TOP_NON_VPS_ISP`.
                # try:
                #     # If key 'ISP' of each 'VPS_ASN' is not in dictionary `TOP_VPS_ISP`.
                #     # Then add key as 'ISP' and value as dictionary containing 'ASN', 'ISP' and 'TK_COUNT'.
                #     if record['NON_VPS_ASN'][i]['ISP'] not in TOP_NON_VPS_ISP:
                #         TOP_NON_VPS_ISP[record['NON_VPS_ASN'][i]['ISP']] = {'ASN' : record['NON_VPS_ASN'][i]['ASN'],'ISP' : record['NON_VPS_ASN'][i]['ISP'], 'TK_COUNT': record['NON_VPS_ASN'][i]['TK_COUNT']}

                #     # Increment the value of 'TK_COUNT'.
                #     else:
                #         TOP_NON_VPS_ISP[record['NON_VPS_ASN'][i]['ISP']]['TK_COUNT'] += record['NON_VPS_ASN'][i]['TK_COUNT']
                # except:
                #     pass

        # Sort by 'TK_COUNT' in descending order.
        sorted_VPS_ISP_List = sorted(TOP_VPS_ISP.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        # Return dictionaries VPS_USERS, NON_VPS_USERS, VENDORS_USERS, TOP_VPS_ISP.
        return {
            'VPS_USERS': VPS_USERS,  
            'NON_VPS_USERS': NON_VPS_USERS, 
            'VENDORS_USERS': VENDORS_USERS, 
            'TOP_VPS_ISP': [i[1] for i in sorted_VPS_ISP_List]
        }

    except:
        
        # Log error message in the log file.
        logger.error(f"Failed to get user registration details on {request.url}")

        return{
            "status": 500,
            "msg": "Failed to get user registeration details"
        }


@app.get('/userreg_dash_uniq/{item_date}')
async def user_reg_dash(item_date, request: fastapi.Request):
    """
    Displays chart for users registered via VPS ISP and NON-VPS ISP for a specific date.
    Displays number of users registered through vendors and count of IPs found in VPS Pool.

    :param item_date: Date for which the data is to be displayed.
    :ptype: date

    :return: Data to be displayed for specific date.
    :rtype: dict
    """

    logger = UserIDLogger()
    
    try:
        # Parse `item_date` in suitable format.
        date_curr = dateutil.parser.parse(item_date)

        # Find on (date_curr) --> convert to list. 
        data = await user_collection_handle.find(
            {
                'LOGS_DATE': date_curr
            }, 
            {
                '_id': 0
            }).to_list(100)

        # List to store data in the form of json string.
        filtered_records_json = []
        
        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in data:
            # Convert each record into json string.
            record_json = json.dumps(record, default = json_util.default)

            # Store json string record in the list.
            filtered_records_json.insert(0, record_json)


        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")
        
        return {
            'data': filtered_records_json
        }

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get trend chart data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get trend chart data"
        }

if __name__ == "__main__":
    uvicorn.run(
        'app:app', 
        host='0.0.0.0', 
        port=55557, 
        reload=True)