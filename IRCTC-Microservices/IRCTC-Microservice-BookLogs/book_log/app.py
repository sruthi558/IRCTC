# Import Libraries

import json
import redis
import typing
import fastapi
import uvicorn
import logging
import icecream
import pydantic
import datetime
import dateutil.parser
import pydantic_settings
import motor.motor_asyncio
from bson import json_util
from typing import Optional
from datetime import time, timedelta

# Logger function.
def BookingLogLogger():

    # Create a logger.
    logger = logging.getLogger("BookingLogs")

    # The level of the logger is set to 'INFO'.
    logger.setLevel(logging.INFO)

    # Format for the logged data.
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(threadName)s:%(message)s')

    # Create a handle for the file generated.
    file_handler = logging.FileHandler('booklog.log')

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
    MONGO_DB: str = "irctc_analyser_test"
    IP_ANALYZER_IPINFO_TOKENS: list = ["9856331fcaa070", "a5dd07db73b440","a9e668faf838b3", "96269c96436649"]
    IP_ANALYZER_IPREGISTRY_TOKENS: list = ["tlz6eacbhflzphhi", "glaf6rgqc8kfvdf5"]
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

# Setting up redis client for caching.
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Setting expiration date for the cached data.
CACHE_EXP = 60*120

class BookRange(pydantic.BaseModel):
    """
    Base user model class for intercepting process request and reading variables from it.

    :param pydantic.BaseModel: Inherits from BaseModel class of pydantic which defines the model for staring and the ending date of booking.
    """

    # Set the starting date for which the booking logs data is to be fetched.
    std: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Set the ending date for which the booking logs data is to be fetched.
    etd: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=datetime.datetime.now)

class DataSearchDate(pydantic.BaseModel):

    # Set the date for which the registeration stats data has to be fetced for daily status section.
    searchDate : Optional[str] = ""

# Create a handle to the collection for daily booking log analysis.
col_pnr_dash = db.irctc_dash_test_1
col_userid = db.irctc_userid_data
col_pnr_data = db.irctc_pnr_test_1

min_date = datetime.datetime(1970, 1, 1)

@app.get('/booklog_dash_uniq/{booking_date}/{travel_class_type}', response_description = "Booking details data on particular date")
async def book_log_dash(booking_date, travel_class_type, request: fastapi.Request) -> dict:
    """
    Shows all the booking details of a particular date.

    :param booking_date: date of ticket booking.
    :param travel_class_type: Equivalent class (AC / ARP / NON-AC) for the booking.

    :return: All the details of the booking on a particular date.
    :rtype: dict
    """

    # Instance to the logger function.
    logger = BookingLogLogger()

    try:

        # Parse datetime string in suitable format.
        date_curr = dateutil.parser.parse(booking_date)

        # Filter entries based on the keyword (LOG_DATE) --> `_id` not equal to '0' --> convert to list.
        book_log_dash = await col_pnr_dash.find({
            'LOGS_DATE': date_curr
            }, {
            '_id': 0
            }).to_list(100)

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for userid in book_log_dash:

            # Convert each record into JSON string.
            record_json = json.dumps(userid, default = json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Return all the booking details on a particular date.
        return {
            'data': filtered_records_json[0]
        }

    except:
        # Log error message in the log file.
        logger.error(f"Failed to get booking details on {booking_date}:{request.url}")

        # Return all the booking details on a particular date.
        return {
            "status": 500,
            "msg": f"Failed to get booking details on {booking_date}"
        }

@app.post('/booklog_dash_range', response_description = "Data for booking logs trend chart")
async def booklog_trend_chart(book_range: BookRange, request: fastapi.Request) -> dict:
    """
    Data for booking logs trend chart.

    :param book_range: Gives the received data based on BookRange model.
    :ptype: BookRange model

    :return: Booking log data between specified dates (startdate to enddate).
    :rtype: dict
    """

    # Instance to the logger function.
    logger = BookingLogLogger()

    try:

        # Tracking dictionary to store the total 'ARP' tickets booked between specified dates.
        ARP_TICKETS = {}

        # Tracking dictionary to store the total 'ARP' tickets booked using VPS between specified dates.
        ARP_VPS_TICKETS = {}

        # Tracking dictionary to store the total 'AC' tickets booked between specified dates.
        AC_TICKETS = {}

        # Tracking dictionary to store the total 'AC' tickets booked using VPS between specified dates.
        AC_VPS_TICKETS = {}

        # Tracking dictionary to store the total 'NON_AC' tickets booked between specified dates.
        NON_AC_TICKETS = {}

        # Tracking dictionary to store the total 'NON_AC' tickets booked using VPS between specified dates.
        NON_AC_VPS_TICKETS = {}

        # Tracking dictionary to store top ISP used to book tickets using VPS between specified dates.
        TOP_ISP_VPS_TICKETS = {}

        # Filter entries based on the keyword ((LOG_DATE > starting date) and (LOG_DATE < ending date)) --> fetch all fields except `_id`.
        async for db_entries in col_pnr_dash.find({
                '$and' : [
                    {
                        'LOGS_DATE' : {
                            '$gte' : book_range.std
                        }
                    }, {
                        'LOGS_DATE' : {
                            '$lte' : book_range.etd
                        }
                    }
                ]
            }, {
                '_id': 0
            }):

            # Convert the booking date into string format --> assign it total number of ARP tickets booked on that day --> Update the 'ARP_TICKETS' tracking dictionarty.
            ARP_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('ARP',{}).get('TOT_TK',0)

            # Convert the booking date into string format --> assign it total number of ARP tickets booked using VPS on that day --> Update the 'ARP_VPS_TICKETS' tracking dictionarty.
            ARP_VPS_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('ARP',{}).get('VPS_TK',0)

            # Convert the booking date into string format --> assign it total number of AC tickets booked on that day --> Update the 'AC_TICKETS' tracking dictionarty.
            AC_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('AC',{}).get('TOT_TK',0)

            # Convert the booking date into string format --> assign it total number of AC tickets booked using VPS on that day --> Update the 'AC_VPS_TICKETS' tracking dictionarty.
            AC_VPS_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('AC',{}).get('VPS_TK',0)

            # Convert the booking date into string format --> assign it total number of NON_AC tickets booked on that day --> Update the 'NON_AC_TICKETS' tracking dictionarty.
            NON_AC_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('NON_AC',{}).get('TOT_TK',0)

            # Convert the booking date into string format --> assign it total number of NON_AC tIckets booked using VPS on that day --> Update the 'NON_AC_VPS_TICKETS' tracking dictionarty.
            NON_AC_VPS_TICKETS[db_entries['LOGS_DATE'].strftime("%d-%m-%y")] = db_entries.get('NON_AC',{}).get('VPS_TK',0)

            # Iterate over 'db_entries' to find 'TOP_ISP_VPS_TICKETS' for different 'ticket_class'.
            for ticket_class in ['AC', 'NON_AC','ARP']:

                # Check if the 'ticket_class' is present in the database on that date.
                if ticket_class in db_entries:

                    # Maximum '20' ISP can be shown.
                    for i in range(20):
                        try:

                            # Check if VPS 'ISP' is not present in the 'TOP_ISP_VPS_TICKETS' tracking dictionary.
                            if db_entries[ticket_class]['VPS_ISP'][i]['ISP'] not in TOP_ISP_VPS_TICKETS:

                                # Update the 'TOP_ISP_VPS_TICKETS' dictionary with 'ISP' as the key and corresponding 'ASN number', 'ISP' and 'ticket count' as value in the form of dictionary.
                                TOP_ISP_VPS_TICKETS[db_entries[ticket_class]['VPS_ISP'][i]['ISP']] = {'ASN': db_entries[ticket_class]['VPS_ISP'][i]['ASN'], 'ISP': db_entries[ticket_class]['VPS_ISP'][i]['ISP'], 'TK_COUNT': db_entries[ticket_class]['VPS_ISP'][i]['TK_COUNT']}
                            else:

                                # Increament the ticket count booked by the ISP which uses VPS in the 'TOP_ISP_VPS_TICKETS' dictionary.
                                TOP_ISP_VPS_TICKETS[db_entries[ticket_class]['VPS_ISP'][i]['ISP']]['TK_COUNT'] += db_entries[ticket_class]['VPS_ISP'][i]['TK_COUNT']
                        except:
                            continue

        # Sort the 'TOP_ISP_VPS_TICKETS' dictionary based on the ticket count in reverse order.
        top_ISP = sorted(TOP_ISP_VPS_TICKETS.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)

        # Get the user email, cookie and remember token from the request header.
        header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

        # Log the data into the log file.
        logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

        # Returns the booking log data.
        return {
            'ARP_TOT': ARP_TICKETS,
            'AC_TOT': AC_TICKETS,
            'NON_AC_TOT': NON_AC_TICKETS,
            'NON_AC_VPS': NON_AC_VPS_TICKETS,
            'AC_VPS': AC_VPS_TICKETS,
            'ARP_VPS': ARP_VPS_TICKETS,
            'TOP_ISP': [i[1] for i in top_ISP]
        }

    except:

        # Log error message in the log file.
        logger.error(f"Failed to get trend chart data:{request.url}")

        return{
            "status": 500,
            "msg": "Failed to get trend chart data"
        }

@app.post('/user-registration-logs', response_description = "Data for booking logs trend chart")
async def user_registration_logs(search_date: DataSearchDate, request: fastapi.Request):

    """
    Data for user registration and ticket booking logs.

    :param search_date: Gives the received data based on DataSearchDate model.
    :ptype: DataSearchDate model

    :return: search date for the logs.
    :rtype: dict
    """

    logger = BookingLogLogger()

    # Define cache key for the requested data.
    cache_key = f'/user-registration-logs-{search_date.searchDate}'

    icecream.ic(cache_key)

    try:
        icecream.ic('Getting Cache .. /user-registration-logs')

        # Get the cached data from the redis.
        cached_data = redis_client.get(cache_key)

        # Check if cached data is preset.
        if cached_data:
            icecream.ic('CACHED DATA: /user-registration-logs :', cache_key)
            print(f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            # Returns the cached data.
            return eval(cached_data)

        else:

            icecream.ic('Cache Miss .. /user-registration-logs')

            # check if searchDate provided is empty or not
            if (search_date.searchDate == ""):
                return {'detail': 'Invalid request body'}

            # check is the provided date is a valid datetime object or not
            try:
                date = dateutil.parser.isoparse(search_date.searchDate)
            except:
                return {'detail': 'Invalid request body'}

            try:

                # Initialize variables to 0 for VPS and NON VPS data of AC, NON AC and ARP
                # arp_vps_total,ac_vps_total, non_ac_vps_total = 0,0,0
                # arp_non_vps_total, ac_non_vps_total, non_ac_non_vps_total = 0,0,0
                temp_arp_vps_time, temp_arp_nvps_time = {"1 min" : 0, "3 min" : 0, "5 min" : 0},{"1 min" : 0, "3 min" : 0, "5 min" : 0}
                temp_ac_vps_time, temp_ac_nvps_time = {"1 min" : 0, "3 min" : 0, "5 min" : 0},{"1 min" : 0, "3 min" : 0, "5 min" : 0}
                temp_nac_vps_time, temp_nac_nvps_time = {"1 min" : 0, "3 min" : 0, "5 min" : 0}, {"1 min" : 0, "3 min" : 0, "5 min" : 0}
                arp_vps_time, arp_nvps_time = {"min_1" : 0, "min_3" : 0, "min_5" : 0},{"min_1" : 0, "min_3" : 0, "min_5" : 0}
                ac_vps_time, ac_nvps_time = {"min_1" : 0, "min_3" : 0, "min_5" : 0},{"min_1" : 0, "min_3" : 0, "min_5" : 0}
                nac_vps_time, nac_nvps_time = {"min_1" : 0, "min_3" : 0, "min_5" : 0}, {"min_1" : 0, "min_3" : 0, "min_5" : 0}
                user_reg = {"VPS" : 0, "NON_VPS" : 0}
                user_total,pnr_total = 0,0

                #set pnr date to the given date
                pnr_date = datetime.datetime.combine(date.date(), time.min)

                #set user date as 1 day before the given
                user_date = pnr_date - timedelta(days=1)

                # query to get total user and pnr ip, total pnr and user count
                user_total = await col_userid.count_documents({'REGISTRATION_DATETIME': {'$gte': user_date,'$lt': user_date+timedelta(days=1)}})
                print("User total :",user_total)

                # query to find the pnr booking logs
                pnr_total = await col_pnr_data.count_documents(
                    {
                        'BOOKING_DATE': {'$gte': pnr_date, '$lt': pnr_date + timedelta(days=1)},
                    })

                total_ip = user_total + pnr_total

                # query to find the user registration logs
                user_reg_count = col_userid.aggregate([
                    {
                        '$match': {
                            'REGISTRATION_DATETIME': {
                                '$gte': user_date,
                                '$lt': user_date + timedelta(days=1)}
                        }
                    },
                    {
                        '$group': {
                            '_id': {
                                'VPS': '$VPS'
                            },
                            'count': {'$sum': 1}
                        }
                    }
                ])

                # AC booking start time 10 AM
                ac_start_time = datetime.datetime.combine(pnr_date.date(), time(10, 0))

                # NON_AC booking start time 11 AM
                nac_start_time = datetime.datetime.combine(pnr_date.date(), time(11, 0))

                # ARP booking start time 8 AM
                arp_start_time = datetime.datetime.combine(pnr_date.date(), time(8, 0))

                # fetch data from AC pnr logs with booking time under 1 min, 3 min and 5 min
                for i in range(1,6,2):
                    ac_stats = col_pnr_data.aggregate(
                        [
                            {
                                '$match' : {
                                    'BOOKING_DATE' : {
                                        '$gte': ac_start_time,
                                        '$lt': (ac_start_time + timedelta(minutes=i))
                                    },
                                    'TK_TYPE' : 'AC'
                                }
                            },
                            {
                                '$group' : {
                                    '_id' : {
                                        'VPS' : '$VPS'
                                    },
                                    'count' : {
                                        '$sum' : 1
                                    }
                                }
                            }
                        ]
                    )
                    ac_stats = await ac_stats.to_list(length=None)

                    # if data exists for that time
                    if ac_stats != {}:

                        # list traversal to get distrubuted count for vps and non vps
                        for rec in ac_stats:
                            if rec["_id"]["VPS"] == True:
                                temp_ac_vps_time[str(i) + ' min'] = rec['count']
                            else:
                                temp_ac_nvps_time[str(i) + ' min'] = rec['count']

                ac_vps_time['min_1'],ac_vps_time['min_3'],ac_vps_time['min_5'] = temp_ac_vps_time['1 min'], temp_ac_vps_time['3 min'], temp_ac_vps_time['5 min']
                ac_nvps_time['min_1'],ac_nvps_time['min_3'],ac_nvps_time['min_5'] = temp_ac_nvps_time['1 min'], temp_ac_nvps_time['3 min'], temp_ac_nvps_time['5 min']

                # to fetch data from NON_AC pnr logs with booking time under 1 min, 3 min and 5 min
                for i in range(1,6,2):
                    nac_stats = col_pnr_data.aggregate(
                        [
                            {
                                '$match' : {
                                    'BOOKING_DATE' : {'$gte': nac_start_time, '$lt': (nac_start_time+timedelta(minutes=i))},
                                    'TK_TYPE' : 'NON_AC'
                                }
                            },
                            {
                                '$group' : {
                                    '_id' : {'VPS' : '$VPS'},
                                    'count' : {'$sum' : 1}
                                }
                            }
                        ]
                    )
                    nac_stats = await nac_stats.to_list(length=None)

                    # if data exists for that time
                    if nac_stats != {}:

                        # list traversal to get distrubuted count for vps and non vps
                        for rec in nac_stats:
                            if rec["_id"]["VPS"] == True:
                                temp_nac_vps_time[str(i) + ' min'] = rec['count']
                            else:
                                temp_nac_nvps_time[str(i) + ' min'] = rec['count']

                nac_vps_time['min_1'],nac_vps_time['min_3'],nac_vps_time['min_5'] = temp_nac_vps_time['1 min'], temp_nac_vps_time['3 min'], temp_nac_vps_time['5 min']
                nac_nvps_time['min_1'],nac_nvps_time['min_3'],nac_nvps_time['min_5'] = temp_nac_nvps_time['1 min'], temp_nac_nvps_time['3 min'], temp_nac_nvps_time['5 min']


                # # to fetch data from ARP pnr logs with booking time under 1 min, 3 min and 5 min
                for i in range(1,6,2):
                    arp_stats = col_pnr_data.aggregate(
                        [
                            {
                                '$match' : {
                                    'BOOKING_DATE' : {'$gte': arp_start_time, '$lt': (arp_start_time+timedelta(minutes=i))},
                                    'TK_TYPE' : 'ARP'
                                }
                            },
                            {
                                '$group' : {
                                    '_id' : {'VPS' : '$VPS'},
                                    'count' : {'$sum' : 1}
                                }
                            }
                        ]
                    )
                    arp_stats = await arp_stats.to_list(length=None)

                    # if data exists for that time
                    if arp_stats != {}:

                        # list traversal to get distrubuted count for vps and non vps
                        for rec in arp_stats:
                            if rec["_id"]["VPS"] == True:
                                temp_arp_vps_time[str(i) + ' min'] = rec['count']
                            else:
                                temp_arp_nvps_time[str(i) + ' min'] = rec['count']
                arp_vps_time['min_1'],arp_vps_time['min_3'],arp_vps_time['min_5'] = temp_arp_vps_time['1 min'], temp_arp_vps_time['3 min'], temp_arp_vps_time['5 min']
                arp_nvps_time['min_1'],arp_nvps_time['min_3'],arp_nvps_time['min_5'] = temp_arp_nvps_time['1 min'], temp_arp_nvps_time['3 min'], temp_arp_nvps_time['5 min']

                # traverse the list to calculate individual count for user reg logs
                async for user in user_reg_count:
                    if user["_id"]["VPS"] == True:
                        user_reg["VPS"] = user['count']
                    else:
                        user_reg["NON_VPS"] = user['count']

                # Get the user email, cookie and remember token from the request header.
                header_content = request.headers['Cookie'].replace("cookie=", "").split(";")

                # Log the data into the log file.
                logger.info(f"SUCCESS:{request.method}:{header_content[2]}:{request.url}:{header_content[0]}:{header_content[1]}")

                # returns the user and pnr booking logs data
                # return user_reg_count
                response_data = {
                    "TOTAL_IP" : total_ip,
                    "TOTAL_USER" : {
                        "TOTAL" : user_total,
                        "USER_REG" : user_reg
                    },
                    "TOTAL_PNR" : {
                        "TOTAL" : pnr_total,
                        "PNR_BOOKING" : {
                            "ARP_VPS" : {"BREAKDOWN" : [arp_vps_time]},
                            "AC_VPS" : {"BREAKDOWN" : [ac_vps_time]},
                            "NON_AC_VPS" : {"BREAKDOWN" : [nac_vps_time]},
                            "ARP_NON_VPS" : {"BREAKDOWN" : [arp_nvps_time]},
                            "AC_NON_VPS" : {"BREAKDOWN" : [ac_nvps_time]},
                            "NON_AC_NON_VPS" : {"BREAKDOWN" : [nac_nvps_time]}
                        }
                    }
                }

                icecream.ic('Setting Cache .. /user-registration-logs')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:

                # Log error message in the log file.
                print(e.msg())
                logger.error(f"Failed to get logs data:{request.url}")

                return{
                    "msg": "Failed to get logs chart data"
                }, 500

    except Exception as e:
        icecream.ic('Error with Cache Operation ..')
        print(e.msg())
        return{
            "status": 500,
            "msg": "Error with Cache Operation"
        }


if __name__ == "__main__":
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=55561,
        reload=True
    )