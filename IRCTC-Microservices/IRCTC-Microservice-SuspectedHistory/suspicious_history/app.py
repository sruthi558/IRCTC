# Import libraries

import json
import math
import os
import re
import uuid
import fastapi
import typing
import motor.motor_asyncio
from bson import json_util
import datetime
import pandas
import uvicorn
import dateutil.parser
import pydantic
import logging
import dateutil.relativedelta as relativedelta
from status_codes import rfi_risk_pnr,  rfi_risk, ip_rfi_risk,  overview_case_rfi
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from concurrent.futures import ProcessPoolExecutor
import redis
import requests
from icecream import ic
import maxminddb
import Levenshtein


class Settings(pydantic.BaseSettings):
    """
    Set the configurations for the microservice's functionality through the env file.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to setup the basic configuration from the env file.
    """
    # Default configuration values to be used if these parameters are not defined in the env file.
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "irctc_backend_test_6"

    # Read the env file to construct a configuration for the microservice.
    class Config:
        env_file = "../.env"


# Global variables to be used by the endpoints.
settings = Settings()

# Instance of class FastAPI that acts as a main point of interaction to create all API.
app = fastapi.FastAPI()

# Connect to MongoDB.
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)

# Get reference to the database `MONGO_DB`.
db = client[settings.MONGO_DB]


class UserHistoryList(pydantic.BaseModel):

    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Set search string as empty string as default.
    search: typing.Optional[str] = ''

    # Set starting date in the search filter for which suspicious IP's records are to be filtered.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(
        1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(
        default_factory=datetime.datetime.now)


class UserModalHistory(pydantic.BaseModel):

    # Set the initial page number to '1' to display the first page of the results.
    page_id: typing.Optional[int] = 1

    # Set user id string as empty string as default.
    userid: typing.Optional[str] = ""

    # Set user name string as empty string as default.
    username: typing.Optional[str] = ""


class CaseManagement(pydantic.BaseModel):

    page_id: typing.Optional[int] = 1

    risk: typing.Optional[list] = []

    username: typing.Optional[str] = ""

    ip_address: typing.Optional[str] = ""

    # Set starting date in the search filter for which suspicious IP's records are to be filtered.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(
        1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(
        default_factory=datetime.datetime.now)


class CaseManagementPnr(pydantic.BaseModel):

    page_id: typing.Optional[int] = 1

    risk: typing.Optional[list] = []

    # Set starting date in the search filter for which suspicious IP's records are to be filtered.
    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(
        default_factory=datetime.datetime.now)

    filter_date: typing.Optional[str] = 'Booking Date'

    search_pnr: typing.Optional[str] = ""


class CaseManagementPNR(pydantic.BaseModel):

    pnr_number: str | int | float


class CaseManagementUser(pydantic.BaseModel):

    username: typing.Optional[str] = ''


class Overview(pydantic.BaseModel):

    starting_date: typing.Optional[datetime.datetime] = datetime.datetime(
        1970, 1, 1)

    # Set ending date in the search filter for which suspicious IP's records are to be filtered.
    ending_date: typing.Optional[datetime.datetime] = pydantic.Field(
        default_factory=datetime.datetime.now)

    page_id: typing.Optional[int] = 1


class OverviewPie(pydantic.BaseModel):

    filter_date: typing.Optional[str] = ""

    page_id: typing.Optional[int] = 1


class CaseManagementOverviewDetail(pydantic.BaseModel):

    page_id: typing.Optional[int] = 1

    username: typing.Optional[str] = ""

    email: typing.Optional[str] = ""

    ip_address: typing.Optional[str] = ""

    status: typing.Optional[int] = 0


col_sus_user = db.irctc_userid_data_test_1

col_user_data = db.irctc_userid_data

col_pnr = db.irctc_pnr_test_1

col_sus_history = db.irctc_user_history_main

col_case_mgmt = db.irctc_case_management_test_1

col_sus_ip = db.irctc_sus_ips_test_1

col_case_overview = db.irctc_case_overview_trend

geoip = maxminddb.open_database(os.path.expanduser('~') + "/Databases/GeoLite2-City.mmdb")

# Global variable specifying minimum date.
min_date = datetime.datetime(1970, 1, 1)

# Redis Client
redis_client = redis.Redis(host='localhost', port=6379, db=0)
CACHE_EXP = 60*120  # two hours


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


def calculate_similarity_ratio(input_string, matching_string, similarity_threshold):
    len_diff = abs(len(input_string) - len(matching_string))
    if len_diff <= 2 * similarity_threshold:
        distance = Levenshtein.distance(input_string, matching_string)
        max_length = max(len(input_string), len(matching_string))
        similarity_ratio = 1 - (distance / max_length)
        if similarity_ratio >= similarity_threshold:
            return matching_string

    return None

###################
# Case Management #
###################

# OVERVIEW CASE MANAGEMENT


@app.post("/overview-severity-total")
async def overview_total(overview: OverviewPie):

    cache_key = f'overview-severity-total-{overview.filter_date}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. overview-severity-total')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            return eval(cached_data)

        else:
            ic('Cache miss .. overview-severity-total')

            try:
                if overview.filter_date == "last_week":
                    starting_date = datetime.datetime.now() - datetime.timedelta(days=7)
                    ending_date = datetime.datetime.now()

                elif overview.filter_date == "last_15_days":
                    starting_date = datetime.datetime.now() - datetime.timedelta(days=15)
                    ending_date = datetime.datetime.now()

                elif overview.filter_date == "last_month":
                    starting_date = datetime.datetime.now() - datetime.timedelta(days=30)
                    ending_date = datetime.datetime.now()

                elif overview.filter_date == "last_three_month":
                    starting_date = datetime.datetime.now() - relativedelta.relativedelta(months=3)
                    ending_date = datetime.datetime.now()

                severity_data = await col_case_overview.find({
                    'DATE': {
                        '$gte': starting_date,
                        '$lte': ending_date
                    }}, {
                        '_id': 0,
                }).to_list(10)

                response_data = dict()
                total_high, high_ip, high_user, high_pnr = 0, 0, 0, 0
                total_med, med_ip, med_user, med_pnr = 0, 0, 0, 0
                total_low, low_ip, low_user, low_pnr = 0, 0, 0, 0

                for trend_data in severity_data:
                    data = trend_data.get('SEVERITY_TREND')

                    total_high += data.get('HIGH').get('TOTAL')
                    high_ip += data.get('HIGH').get('IP')
                    high_user += data.get('HIGH').get('USER')
                    try:
                        high_pnr += data.get('HIGH').get('PNR')
                    except:
                        high_pnr += 0

                    total_med += data.get('MEDIUM').get('TOTAL')
                    med_ip += data.get('MEDIUM').get('IP')
                    med_user += data.get('MEDIUM').get('USER')
                    try:
                        med_pnr += data.get('MEDIUM').get('PNR')
                    except:
                        med_pnr += 0

                    total_low += data.get('LOW').get('TOTAL')
                    low_ip += data.get('LOW').get('IP')
                    low_user += data.get('LOW').get('USER')
                    try:
                        low_pnr += data.get('LOW').get('PNR')
                    except:
                        low_pnr += 0

                overall = high_ip + high_user + high_pnr + med_ip + \
                    med_user + med_pnr + low_ip + low_user + low_pnr

                response_data = {
                    'data_list': [
                        {"HIGH": {"TOTAL": total_high, "PERCENTAGE": (
                            total_high/overall)*100 if overall != 0 else 0, "IP": high_ip, "USER": high_user, "PNR": high_pnr}},
                        {"MEDIUM": {"TOTAL": total_med, "PERCENTAGE": (
                            total_med/overall)*100 if overall != 0 else 0, "IP": med_ip, "USER": med_user, "PNR": med_pnr}},
                        {"LOW": {"TOTAL": total_low, "PERCENTAGE": (total_low/overall)*100 if overall != 0 else 0, "IP": low_ip, "USER": low_user, "PNR": low_pnr}}]
                }

                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Overview Pie Chart Stats"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/overview-weekly-stats")
async def overview_stats(overview: Overview):

    cache_key = f'overview-weekly-stats-{overview.starting_date.date()}-{overview.ending_date.date()}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. overview-weekly-stats')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')
            return eval(cached_data)

        else:
            try:
                ic('Cache miss .. overview-weekly-stats')

                overview.starting_date = datetime.datetime.combine(
                    overview.starting_date.date(), datetime.time.min)
                overview.ending_date = datetime.datetime.combine(
                    overview.ending_date.date(), datetime.time.min)

                if overview.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                    overview.starting_date = datetime.datetime.combine(
                        overview.ending_date.date() - datetime.timedelta(days=28), datetime.time.min)
                    overview.ending_date = datetime.datetime.combine(
                        overview.ending_date.date(), datetime.time.min)

                dates = []
                curr_date = overview.starting_date
                dates.append(curr_date)
                while (curr_date <= overview.ending_date):
                    next_date = datetime.datetime.combine(
                        curr_date.date() + datetime.timedelta(days=7), datetime.time.min)
                    if next_date >= overview.ending_date:
                        dates.append(overview.ending_date)
                        break
                    dates.append(next_date)
                    curr_date = next_date

                filtered_data = list()

                for i in range(len(dates)):
                    date_stats = {}
                    if i == 0:
                        start = dates[i] - datetime.timedelta(days=8)
                        end = dates[i] + datetime.timedelta(days=1)
                    else:
                        start = dates[i-1]
                        end = dates[i] + datetime.timedelta(days=1)

                    weekly_data = await col_case_overview.find({
                        'DATE': {
                            '$gte': start,
                            '$lt': end
                        }
                    }, {
                        '_id': 0,
                    }).to_list(None)

                    sus_ips_high_total, sus_user_high_total, sus_pnr_high_total = 0, 0, 0
                    sus_ips_low_total, sus_user_low_total, sus_pnr_low_total = 0, 0, 0
                    sus_ips_med_total, sus_user_med_total, sus_pnr_med_total = 0, 0, 0

                    for weekly_data in weekly_data:
                        data = weekly_data.get('SEVERITY_TREND')

                        sus_ips_high_total += data.get('HIGH').get('IP')
                        sus_user_high_total += data.get('HIGH').get('USER')
                        try:
                            sus_pnr_high_total += data.get('HIGH').get('PNR')
                        except:
                            sus_pnr_high_total += 0

                        sus_ips_med_total += data.get('MEDIUM').get('IP')
                        sus_user_med_total += data.get('MEDIUM').get('USER')
                        try:
                            sus_pnr_med_total += data.get('MEDIUM').get('PNR')
                        except:
                            sus_pnr_med_total += 0

                        sus_ips_low_total += data.get('LOW').get('IP')
                        sus_user_low_total += data.get('LOW').get('USER')
                        try:
                            sus_pnr_low_total += data.get('LOW').get('PNR')
                        except:
                            sus_pnr_low_total += 0

                    date_stats[end - datetime.timedelta(days=1)] = {
                        'HIGH': {
                            "IP": sus_ips_high_total,
                            "USER": sus_user_high_total,
                            "PNR": sus_pnr_high_total,
                            "TOTAL": sus_ips_high_total + sus_user_high_total + sus_pnr_high_total
                        },
                        "MEDIUM": {
                            "IP": sus_ips_med_total,
                            "USER": sus_user_med_total,
                            "PNR": sus_pnr_med_total,
                            "TOTAL": sus_ips_med_total + sus_user_med_total + sus_pnr_med_total
                        },
                        "LOW": {
                            "IP": sus_ips_low_total,
                            "USER": sus_user_low_total,
                            "PNR": sus_pnr_low_total,
                            "TOTAL": sus_ips_low_total + sus_pnr_low_total + sus_user_low_total
                        }
                    }

                    filtered_data.append(date_stats)

                response_data = {
                    "data_list": filtered_data
                }
                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Overview Weekly Stats"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/overview-main")
async def overview_case(overview: Overview, request: fastapi.Request):

    cache_key = f'overview-main-{overview.page_id}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. case-mgmt')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            return eval(cached_data)

        else:
            ic('Cache miss .. case-mgmt')

            try:

                data = await col_sus_user.aggregate([
                    {
                        '$match': {
                            '$and': [{
                                'SEVERITY': {
                                    '$exists': True
                                }
                            }, {
                                'TAGS.0': {
                                    '$exists': True
                                }
                            }]
                        }
                    },
                    {"$group": {
                        "_id": "$IP_ADDRESS",
                        "doc": {"$first": "$$ROOT"}
                    }},
                    {"$replaceRoot": {
                        "newRoot": "$doc"
                    }},
                    {
                        '$sort': {"SEVERITY": 1, "SUS_DATE": -1}
                    },
                    {
                        '$skip': (overview.page_id - 1) * 10
                    },
                    {
                        '$limit': 10
                    }
                ]).to_list(length=None)

                total_count = await col_sus_user.aggregate([
                    {
                        '$match': {
                            '$and': [{
                                'SEVERITY': {
                                    '$exists': True
                                }
                            }, {
                                'TAGS.0': {
                                    '$exists': True
                                }
                            }]
                        }
                    },
                    {"$group": {
                        "_id": "$IP_ADDRESS",
                        "doc": {"$first": "$$ROOT"},
                        "count": {"$sum": 1}
                    }},
                    {"$replaceRoot": {
                        "newRoot": "$doc"
                    }},
                    {"$count": "totalDocuments"}
                ]).to_list(length=None)

                total_count = total_count[0]['totalDocuments']

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in data:

                    if rec["SEVERITY"] == 1:
                        rec["SEVERITY"] = "HIGH"
                    elif rec["SEVERITY"] == 2:
                        rec["SEVERITY"] = "MEDIUM"
                    else:
                        rec["SEVERITY"] = "LOW"

                    pnr_data = await col_pnr.find({"USERNAME": rec["USERNAME"]}, {"PNR_NUMBER": 1}).sort("BOOKING_DATE", -1).to_list(1)
                    # usr_data = await col_user_data.find({"USERNAME" : rec["USERNAME"]},{"IP_ADDRESS" : 1}).to_list(1)

                    rec["PNR_NUMBER"] = pnr_data[0]["PNR_NUMBER"] if pnr_data != [
                    ] else "N.A."
                    # rec["IP_ADDRESS"] = usr_data[0]["IP_ADDRESS"] if usr_data != [] else (pnr_data[0]["IP_ADDRESS"] if pnr_data != [] else "N.A.")

                    rfi = []
                    try:
                        for tag in rec['TAGS']:
                            try:
                                rfi.append(overview_case_rfi[tag])
                            except:
                                pass
                    except:
                        pass

                    rec['RFI_RULE'] = rfi

                    del rec['TAGS']
                    del rec['_id']

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.

                response_data = {
                    'data_list': filtered_records_json[::-1],
                    'total_pages': math.ceil(total_count/10),
                    'total_rows': total_count
                }

                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')
                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Overview Case Management data"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/overview-status-update")
async def overview_status_update(user_status: CaseManagementOverviewDetail, request: fastapi.Request):

    try:

        col_sus_user.update_many({
            "USERNAME": user_status.username
        }, {
            '$set': {
                'ACCEPT_STATUS': user_status.status
            }
        })
        pattern = 'overview-main*'
        keys = redis_client.scan_iter(pattern)
        for key in keys:
            print(f'{key} deleted')
            redis_client.delete(key)

        print(f"{user_status.username} cache clear")
        status = "Accepted" if user_status.status == 1 else "Rejected"

        return {
            "msg": f"{user_status.username} Status updated to {status}",
            "status": 200
        }

    except Exception as e:
        print(e.msg())
        err_msg = {
            "status": 500,
            "msg": "Failed to update status"
        }
        return err_msg

# User Case Management APIs


@app.post("/case-mgmt")
async def case_management(case: CaseManagement, request: fastapi.Request):

    cache_key = f'user-cm-key-{case.page_id}-{case.starting_date}-{case.ending_date}-{case.risk}-{case.username}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. case-mgmt')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            return eval(cached_data)

        else:
            ic('Cache miss .. case-mgmt')

            try:
                case.starting_date = datetime.datetime.combine(
                    case.starting_date.date(), datetime.time.min)
                case.ending_date = datetime.datetime.combine(
                    case.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

                if case.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                    if case.risk == [] or 'ALL' in case.risk:

                        if case.username != "":

                            data = await col_sus_user.find({
                                'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                            },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                            }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}})

                        else:

                            data = await col_sus_user.find({},
                                                           {
                                'USERNAME': 1,
                                'EMAIL': 1,
                                'SUS_DATE': 1,
                                'TAGS': 1,
                                'Severity': 1,
                                '_id': 0
                            }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({})

                    else:

                        if case.username != "":

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_user.find(
                                {
                                    'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)},
                                    'Severity': severity
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({
                                'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)},
                                'Severity': severity
                            })

                        else:

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_user.find(
                                {
                                    'Severity': severity
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({'Severity': severity})

                else:

                    if case.risk == [] or 'ALL' in case.risk:

                        if case.username != "":

                            data = await col_sus_user.find(
                                {
                                    'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                    'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({
                                'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                            })

                        else:

                            data = await col_sus_user.find(
                                {
                                    'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}})

                    else:

                        if case.username != "":

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_user.find(
                                {
                                    'Severity': severity,
                                    'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                    'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({
                                'Severity': severity,
                                'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                            })

                        else:

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_user.find(
                                {
                                    'Severity': severity,
                                    'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                                },
                                {
                                    'USERNAME': 1,
                                    'EMAIL': 1,
                                    'SUS_DATE': 1,
                                    'TAGS': 1,
                                    'Severity': 1,
                                    '_id': 0
                                }
                            ).sort([('Severity', 1), ('SUS_DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({'Severity': severity, 'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}})

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in data:
                    try:
                        rfi = []
                        for tag in rec['TAGS']:
                            rfi.append(overview_case_rfi[tag])

                        rec['RFI_RULE'] = rfi

                        if 'Severity' in rec:
                            if rec['Severity'] == 1:
                                rec['USR_RISK'] = 'HIGH'
                            elif rec['Severity'] == 2:
                                rec['USR_RISK'] = 'MEDIUM'
                            else:
                                rec['USR_RISK'] = 'LOW'
                            del rec['Severity']

                        del rec['TAGS']
                    except:
                        rec['RFI_RULE'] = 'N.A.'
                        rec['USR_RISK'] = 'N.A.'

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.

                response_data = {
                    'data_list': filtered_records_json[::-1],
                    'total_pages': math.ceil(total_count/20),
                    'total_rows': total_count
                }

                # print(response_data)
                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Case Management details"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/export-case-mgmt")
async def export_case_management(case: CaseManagement, request: fastapi.Request):

    try:
        case.starting_date = datetime.datetime.combine(
            case.starting_date.date(), datetime.time.min)
        case.ending_date = datetime.datetime.combine(
            case.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

        if case.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            if case.risk == [] or 'ALL' in case.risk:

                if case.username != "":

                    data = await col_sus_user.find({
                        'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                    },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                    }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

                else:

                    data = await col_sus_user.find({},
                                                   {
                        'USERNAME': 1,
                        'EMAIL': 1,
                        'SUS_DATE': 1,
                        'TAGS': 1,
                        'Severity': 1,
                        '_id': 0
                    }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

            else:

                if case.username != "":

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_user.find(
                        {
                            'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)},
                            'Severity': severity
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

                else:

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_user.find(
                        {
                            'Severity': severity
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

        else:

            if case.risk == [] or 'ALL' in case.risk:

                if case.username != "":

                    data = await col_sus_user.find(
                        {
                            'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                            'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

                else:

                    data = await col_sus_user.find(
                        {
                            'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

            else:

                if case.username != "":

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_user.find(
                        {
                            'Severity': severity,
                            'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                            'USERNAME': {"$regex": re.compile(f'.*{case.username}.*', re.IGNORECASE)}
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

                else:

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_user.find(
                        {
                            'Severity': severity,
                            'SUS_DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                        },
                        {
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'SUS_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1,
                            '_id': 0
                        }
                    ).sort([('Severity', 1), ('SUS_DATE', -1)]).to_list(50000)

        # Iterate over the fetched data.
        for rec in data:

            try:
                rfi = []
                for tag in rec['TAGS']:
                    rfi.append(overview_case_rfi[tag])

                rec['RFI_RULE'] = rfi
                if 'Severity' in rec:
                    if rec['Severity'] == 1:
                        rec['USR_RISK'] = 'HIGH'
                    elif rec['Severity'] == 2:
                        rec['USR_RISK'] = 'MEDIUM'
                    else:
                        rec['USR_RISK'] = 'LOW'
                    del rec['Severity']
                else:
                    rec['USR_RISK'] = 'N.A.'

                del rec['TAGS']
            except:
                rec['RFI_RULE'] = 'N.A.'

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(data)
        df['SUS_DATE'] = df['SUS_DATE'].dt.strftime('%a %d %B %Y')

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}', index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except Exception as e:
        print(e.msg())
        err_msg = {
            "status": 500,
            "msg": "Failed to get Case Management details"
        }
        return err_msg


@app.post("/case-user-details")
async def case_management_user(user: CaseManagementUser, request: fastapi.Request):

    cache_key = f'username-{user.username}'
    ic(cache_key)

    try:
        ic('Getting Cache .. case-user-details')
        cache_data = redis_client.get(cache_key)

        if (cache_data):
            ic('Cache hit ..')
            print(
                f'Raw type: {type(cache_data)} | Eval type: {type(eval(cache_data))}')

            return eval(cache_data)

        else:
            ic("Cache Miss .. case-user-details")

            try:

                if user.username != '':

                    data = await col_user_data.find(
                        {
                            'USERNAME': user.username
                        }, {
                            '_id': 0,
                            'ANALYZED_FILE_REFERENCE': 0
                        }
                    ).to_list(None)

                    total_count = await col_user_data.count_documents(
                        {
                            'USERNAME': user.username
                        })

                    if data == []:

                        return {
                            "status": 200,
                            "msg": "No User Registration details found for the username"
                        }

                    else:

                        ticket_count = await col_pnr.count_documents({'USERNAME': user.username})

                        filtered_records_json = []

                        for rec in data:

                            rec["TOTAL_BOOKED_TICKETS"] = ticket_count

                            rec["SOURCE"] = "REG_USR"

                            # Convert each record into JSON string.
                            response_json = json.dumps(
                                rec, default=json_util.default)

                            # Add the JSON to the tracking list.
                            filtered_records_json.insert(0, response_json)

                        res_data = {
                            'data_list': filtered_records_json[::-1],
                            'total_pages': math.ceil(total_count/20),
                            'total_rows': total_count
                        }

                        ic('Setting Cache ..')
                        redis_client.setex(cache_key, CACHE_EXP, f'{res_data}')

                        return res_data

                else:
                    return {
                        "status": 406,
                        "msg": "username not provided"
                    }

            except Exception as e:
                # print(e.msg())
                return {
                    "status": 500,
                    "msg": "Failed to get User details"
                }

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err)
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


# PNR Case Management APIs

@app.post("/pnr_case_data")
async def case_management_pnr(case_pnr: CaseManagementPnr, request: fastapi.Request):

    cache_key = f'pnr-cm-key-{case_pnr.page_id}-{case_pnr.risk}-{case_pnr.starting_date}-{case_pnr.ending_date}--{case_pnr.filter_date}--{case_pnr.search_pnr}'
    ic(cache_key)

    try:
        ic('Getting Cache .. pnr_case_data')
        cache_data = redis_client.get(cache_key)

        if (cache_data):
            ic('Cache hit .. pnr_case_data')
            print(
                f'Raw type: {type(cache_data)} | Eval type: {type(eval(cache_data))}')

            return eval(cache_data)

        else:
            ic('Cache Miss ..')

            try:
                case_pnr.starting_date = datetime.datetime.combine(
                    case_pnr.starting_date.date(), datetime.time.min)
                case_pnr.ending_date = datetime.datetime.combine(
                    case_pnr.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

                if case_pnr.filter_date == "" or case_pnr.filter_date == 'Journey Date':
                    date_query = [
                        {
                            'JOURNEY_DATE': {
                                '$gte': case_pnr.starting_date
                            }
                        }, {
                            'JOURNEY_DATE': {
                                '$lt': case_pnr.ending_date
                            }
                        }
                    ]

                else:
                    date_query = [
                        {
                            'BOOKING_DATE': {
                                '$gte': case_pnr.starting_date
                            }
                        }, {
                            'BOOKING_DATE': {
                                '$lt': case_pnr.ending_date
                            }
                        }
                    ]

                if case_pnr.risk == [] or 'ALL' in case_pnr.risk:
                    if case_pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                        data = await col_pnr.find({
                            'TAGS.0': {
                                '$exists': True
                            },
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        }, {
                            '_id': 0,
                            'USERNAME': 1,
                            'PNR_NUMBER': 1,
                            'BOOKING_DATE': 1,
                            'JOURNEY_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1
                        }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).skip((case_pnr.page_id - 1)*20).to_list(20)

                        total_count = await col_pnr.count_documents({
                            'TAGS.0': {
                                '$exists': True
                            },
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        })

                    else:
                        data = await col_pnr.find({
                            'TAGS.0': {
                                '$exists': True
                            },
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        }, {
                            '_id': 0,
                            'USERNAME': 1,
                            'PNR_NUMBER': 1,
                            'BOOKING_DATE': 1,
                            'JOURNEY_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1
                        }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).skip((case_pnr.page_id - 1)*20).to_list(20)

                        total_count = await col_pnr.count_documents({
                            'TAGS.0': {
                                '$exists': True
                            },
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        })

                else:
                    severity = 0
                    if 'LOW' in case_pnr.risk:
                        severity = 3
                    if 'MEDIUM' in case_pnr.risk:
                        severity = 2
                    if 'HIGH' in case_pnr.risk:
                        severity = 1

                    if case_pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                        data = await col_pnr.find({
                            'Severity': severity,
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        }, {
                            '_id': 0,
                            'USERNAME': 1,
                            'PNR_NUMBER': 1,
                            'BOOKING_DATE': 1,
                            'JOURNEY_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1
                        }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).skip((case_pnr.page_id - 1)*20).to_list(20)

                        total_count = await col_pnr.count_documents({
                            'Severity': severity,
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        })

                    else:
                        data = await col_pnr.find({
                            'Severity': severity,
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        }, {
                            '_id': 0,
                            'USERNAME': 1,
                            'PNR_NUMBER': 1,
                            'BOOKING_DATE': 1,
                            'JOURNEY_DATE': 1,
                            'TAGS': 1,
                            'Severity': 1
                        }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).skip((case_pnr.page_id - 1)*20).to_list(20)

                        total_count = await col_pnr.count_documents({
                            'Severity': severity,
                            '$and': date_query,
                            'PNR_NUMBER': {
                                '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                            }
                        })

                # Tracking list to store the filtered records.
                filtered_records_json = []

                for parse in data:

                    try:
                        tags = parse.get('TAGS')
                        codes = list()
                        for tag in tags:
                            codes.append(overview_case_rfi.get(tag))
                        parse['TAGS'] = codes

                        if 'Severity' in parse:
                            if parse['Severity'] == 1:
                                parse['Severity'] = 'HIGH'
                            elif parse['Severity'] == 2:
                                parse['Severity'] = 'MEDIUM'
                            else:
                                parse['Severity'] = 'LOW'
                        else:
                            parse['Severity'] = 'N.A.'
                    except:
                        parse['TAGS'] = 'N.A.'

                    # Convert each record into JSON string.
                    response_json = json.dumps(
                        parse, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.
                page_count = math.ceil(total_count/20)

                response_data = {
                    'data_list': filtered_records_json[::-1],
                    'total_pages': page_count,
                    'total_rows': total_count
                }

                ic('Setting cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:
                print(e.msg())
                return {
                    "status": 500,
                    "msg": "Failed to get Case Management data"
                }

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err)
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/pnr_case_data_export")
async def case_management_pnr_export(case_pnr: CaseManagementPnr, request: fastapi.Request):
    try:
        case_pnr.starting_date = datetime.datetime.combine(
            case_pnr.starting_date.date(), datetime.time.min)
        case_pnr.ending_date = datetime.datetime.combine(
            case_pnr.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

        if case_pnr.filter_date == "" or case_pnr.filter_date == 'Journey Date':
            date_query = [
                {
                    'JOURNEY_DATE': {
                        '$gte': case_pnr.starting_date
                    }
                }, {
                    'JOURNEY_DATE': {
                        '$lt': case_pnr.ending_date
                    }
                }
            ]

        else:
            date_query = [
                {
                    'BOOKING_DATE': {
                        '$gte': case_pnr.starting_date
                    }
                }, {
                    'BOOKING_DATE': {
                        '$lt': case_pnr.ending_date
                    }
                }
            ]

        if case_pnr.risk == [] or 'ALL' in case_pnr.risk:
            if case_pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                data = await col_pnr.find({
                    'TAGS.0': {
                        '$exists': True
                    },
                    '$and': date_query,
                    'PNR_NUMBER': {
                        '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                    }
                }, {
                    '_id': 0,
                    'USERNAME': 1,
                    'PNR_NUMBER': 1,
                    'BOOKING_DATE': 1,
                    'JOURNEY_DATE': 1,
                    'TAGS': 1,
                    'Severity': 1
                }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).to_list(50000)

            else:
                data = await col_pnr.find({
                    'TAGS.0': {
                        '$exists': True
                    },
                    '$and': date_query,
                    'PNR_NUMBER': {
                        '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                    }
                }, {
                    '_id': 0,
                    'USERNAME': 1,
                    'PNR_NUMBER': 1,
                    'BOOKING_DATE': 1,
                    'JOURNEY_DATE': 1,
                    'TAGS': 1,
                    'Severity': 1
                }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).to_list(50000)

        else:
            severity = 0
            if 'LOW' in case_pnr.risk:
                severity = 3
            if 'MEDIUM' in case_pnr.risk:
                severity = 2
            if 'HIGH' in case_pnr.risk:
                severity = 1

            if case_pnr.starting_date.date() == datetime.datetime(1970, 1, 1).date():
                data = await col_pnr.find({
                    'Severity': severity,
                    '$and': date_query,
                    'PNR_NUMBER': {
                        '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                    }
                }, {
                    '_id': 0,
                    'USERNAME': 1,
                    'PNR_NUMBER': 1,
                    'BOOKING_DATE': 1,
                    'JOURNEY_DATE': 1,
                    'TAGS': 1,
                    'Severity': 1
                }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).to_list(50000)

            else:
                data = await col_pnr.find({
                    'Severity': severity,
                    '$and': date_query,
                    'PNR_NUMBER': {
                        '$regex': re.compile(f'.*{case_pnr.search_pnr}.*', re.IGNORECASE)
                    }
                }, {
                    '_id': 0,
                    'USERNAME': 1,
                    'PNR_NUMBER': 1,
                    'BOOKING_DATE': 1,
                    'JOURNEY_DATE': 1,
                    'TAGS': 1,
                    'Severity': 1
                }).sort([('Severity', 1), ("BOOKING_DATE", -1)]).to_list(50000)

        for parse in data:

            try:
                tags = parse.get('TAGS')
                codes = list()
                for tag in tags:
                    codes.append(overview_case_rfi.get(tag))
                parse['TAGS'] = codes

                if 'Severity' in parse:
                    if parse['Severity'] == 1:
                        parse['Severity'] = 'HIGH'
                    elif parse['Severity'] == 2:
                        parse['Severity'] = 'MEDIUM'
                    else:
                        parse['Severity'] = 'LOW'
                else:
                    parse['Severity'] = 'N.A.'
            except:
                parse['TAGS'] = 'N.A.'

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(data)
        df['BOOKING_DATE'] = df['BOOKING_DATE'].dt.strftime('%a %d %B %Y')
        df['JOURNEY_DATE'] = df['JOURNEY_DATE'].dt.strftime('%a %d %B %Y')

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}', index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except Exception as e:
        print(e.msg())
        return {
            "status": 500,
            "msg": "Failed to export Case Management data."
        }


@app.post("/pnr_case_data_detail")
async def case_management_pnr_detail(case_pnr: CaseManagementPNR, request: fastapi.Request):

    cache_key = f'pnr-{case_pnr.pnr_number}'
    ic(cache_key)

    try:
        ic('Getting Cache ..')
        cache_data = redis_client.get(cache_key)

        if (cache_data):
            ic('Cache hit .. pnr_case_data_detail')
            print(
                f'Raw type: {type(cache_data)} | Eval type: {type(eval(cache_data))}')

            return eval(cache_data)

        else:
            ic('Cache Miss .. pnr_case_data_detail')

            try:
                data = await col_pnr.find({
                    'PNR_NUMBER': case_pnr.pnr_number
                }, {
                    '_id': 0,
                    'ANALYZED_FILE_REFERENCE': 0,
                    'BOOKING DATE': 0,
                    'JOURNEY DATE': 0,
                }
                ).to_list(1)

                if data == []:
                    data = await col_pnr.find({
                        'PNR_NUMBER': int(case_pnr.pnr_number)
                    }, {
                        '_id': 0,
                        'ANALYZED_FILE_REFERENCE': 0,
                        'BOOKING DATE': 0,
                        'JOURNEY DATE': 0,
                    }
                    ).to_list(1)

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in data:

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.

                res_data = {
                    'data_list': filtered_records_json[::-1],
                }

                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{res_data}')

                return res_data

            except Exception as e:
                print(e.msg())
                return {
                    "status": 500,
                    "msg": "Failed to get Case Management details"
                }

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err)
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }

##########################
# IP CASE MANAGEMENT     #
##########################


@app.post("/ip-case-mgmt")
async def ip_case_management(case: CaseManagement, request: fastapi.Request):

    cache_key = f'ip-cm-key-{case.page_id}-{case.starting_date}-{case.ending_date}-{case.risk}-{case.ip_address}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. ip-case-mgmt')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            return eval(cached_data)

        else:
            ic('Cache miss .. ip-case-mgmt')

            try:
                case.starting_date = datetime.datetime.combine(
                    case.starting_date.date(), datetime.time.min)
                case.ending_date = datetime.datetime.combine(
                    case.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

                if case.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                    if case.risk == [] or 'ALL' in case.risk:

                        if case.ip_address != "":

                            data = await col_sus_ip.find({
                                'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                            }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_user.count_documents({'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}})

                        else:

                            data = await col_sus_ip.find({}, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({})

                    else:

                        if case.ip_address != "":

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_ip.find(
                                {
                                    'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)},
                                    'Severity': severity
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({
                                'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)},
                                'Severity': severity
                            })

                        else:

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_ip.find(
                                {
                                    'Severity': severity
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({'Severity': severity})

                else:

                    if case.risk == [] or 'ALL' in case.risk:

                        if case.ip_address != "":

                            data = await col_sus_ip.find(
                                {
                                    'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                    'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({
                                'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                            })

                        else:

                            data = await col_sus_ip.find(
                                {
                                    'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}})

                    else:

                        if case.ip_address != "":

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_ip.find(
                                {
                                    'Severity': severity,
                                    'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                    'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({
                                'Severity': severity,
                                'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                                'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                            })

                        else:

                            severity = 0
                            if 'LOW' in case.risk:
                                severity = 3
                            if 'MEDIUM' in case.risk:
                                severity = 2
                            if 'HIGH' in case.risk:
                                severity = 1

                            data = await col_sus_ip.find(
                                {
                                    'Severity': severity,
                                    'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                                }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).skip((case.page_id - 1)*20).to_list(20)

                            total_count = await col_sus_ip.count_documents({'Severity': severity, 'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}})

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in data:

                    try:
                        rfi = []
                        for tag in rec['TAGS']:
                            rfi.append(overview_case_rfi[tag])

                        rec['RFI_RULE'] = rfi

                        if 'Severity' in rec:
                            if rec['Severity'] == 1:
                                rec['RISK'] = 'HIGH'
                            elif rec['Severity'] == 2:
                                rec['RISK'] = 'MEDIUM'
                            else:
                                rec['RISK'] = 'LOW'
                            del rec['Severity']
                        else:
                            rec['RISK'] = 'N.A.'
                        del rec['TAGS']

                    except:
                        rec['TAGS'] = 'N.A.'

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.

                response_data = {
                    'data_list': filtered_records_json[::-1],
                    'total_pages': math.ceil(total_count/20),
                    'total_rows': total_count
                }

                # print(response_data)
                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP, f'{response_data}')

                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get IP Case Management details"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post("/export-ip-case-mgmt")
async def export_ip_case_management(case: CaseManagement, request: fastapi.Request):

    try:
        case.starting_date = datetime.datetime.combine(
            case.starting_date.date(), datetime.time.min)
        case.ending_date = datetime.datetime.combine(
            case.ending_date.date() + datetime.timedelta(days=1), datetime.time.min)

        if case.starting_date.date() == datetime.datetime(1970, 1, 1).date():

            if case.risk == [] or 'ALL' in case.risk:

                if case.ip_address != "":

                    data = await col_sus_ip.find({
                        'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                    }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

                else:

                    data = await col_sus_ip.find({}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

            else:

                if case.ip_address != "":

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_ip.find(
                        {
                            'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)},
                            'Severity': severity
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

                else:

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_ip.find(
                        {
                            'Severity': severity
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

        else:

            if case.risk == [] or 'ALL' in case.risk:

                if case.ip_address != "":

                    data = await col_sus_ip.find(
                        {
                            'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                            'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

                else:

                    data = await col_sus_ip.find(
                        {
                            'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

            else:

                if case.ip_address != "":

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_ip.find(
                        {
                            'Severity': severity,
                            'DATE': {'$lt': case.ending_date, '$gte': case.starting_date},
                            'IP_ADDRESS': {"$regex": re.compile(f'.*{case.ip_address}.*', re.IGNORECASE)}
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

                else:

                    severity = 0
                    if 'LOW' in case.risk:
                        severity = 3
                    if 'MEDIUM' in case.risk:
                        severity = 2
                    if 'HIGH' in case.risk:
                        severity = 1

                    data = await col_sus_ip.find(
                        {
                            'Severity': severity,
                            'DATE': {'$lt': case.ending_date, '$gte': case.starting_date}
                        }, {'_id': 0}).sort([('Severity', 1), ('DATE', -1)]).to_list(50000)

        # Iterate over the fetched data.
        for rec in data:
            try:
                rfi = []
                for tag in rec['TAGS']:
                    rfi.append(overview_case_rfi[tag])

                rec['RFI_RULE'] = rfi
                if 'Severity' in rec:
                    if rec['Severity'] == 1:
                        rec['USR_RISK'] = 'HIGH'
                    elif rec['Severity'] == 2:
                        rec['USR_RISK'] = 'MEDIUM'
                    else:
                        rec['USR_RISK'] = 'LOW'
                    del rec['Severity']
                else:
                    rec['USR_RISK'] = 'N.A.'
                del rec['TAGS']

            except:
                rec['TAGS'] = 'N.A.'

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(data)
        df['DATE'] = df['DATE'].dt.strftime('%a %d %B %Y')

        if 'TK_COUNT' in df.columns:
            df[['TK_COUNT']] = df[['TK_COUNT']].fillna(value=0)
        if 'USER_COUNT' in df.columns:
            df[['USER_COUNT']] = df[['USER_COUNT']].fillna(value=0)

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_csv(f'download_folder/{f_name}', index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except Exception as e:
        print(e.msg())
        err_msg = {
            "status": 500,
            "msg": "Failed to get IP Case Management details"
        }
        return err_msg

##########################
# Suspected User History #
##########################


@app.post('/user_history_list')
async def user_history_list_temp(user_hist: UserHistoryList, request: fastapi.Request):
    """
    List all the history of all the users.

    :param ip_mod: Gives the received data based on UserHistory model.
    :ptype: UserHistoryList model.

    :return: List of data containing history of all the users and the  total count of the filtered data pages.
    :rtype: dict
    """

    print(f'Request received in micro.. for sus usr data.')

    try:
        user_hist.starting_date = datetime.datetime.combine(
            user_hist.starting_date.date(), datetime.time.min)

        if user_hist.search == '':

            if user_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$sort": {"TOTAL_BOOKED_TICKETS": -1}
                    }, {
                        "$skip": (user_hist.page_id - 1) * 20
                    }, {
                        "$limit": 20
                    }
                ], allowDiskUse=True).to_list(None)

                total_count = await col_sus_history.count_documents({})

            else:
                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "$and": [
                                {
                                    "SUSPECTED_DATE": {
                                        "$gte": user_hist.starting_date
                                    }
                                }, {
                                    "SUSPECTED_DATE": {
                                        "$lte": user_hist.ending_date
                                    }
                                }
                            ]
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }, {
                        "$skip": (user_hist.page_id - 1) * 20
                    }, {
                        "$limit": 20
                    }
                ], allowDiskUse=True).to_list(None)

                total_count = await col_sus_history.count_documents({
                    "$and": [{
                        "SUSPECTED_DATE": {
                            "$gte": user_hist.starting_date
                        },
                    }, {
                        "SUSPECTED_DATE": {
                            "$lte": user_hist.ending_date
                        }
                    }
                    ]})

        else:
            if user_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "REG_USERNAME": {
                                "$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)
                            }
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }, {
                        "$skip": (user_hist.page_id - 1) * 20
                    }, {
                        "$limit": 20
                    }
                ], allowDiskUse=True).to_list(None)

                total_count = await col_sus_history.count_documents({
                    "REG_USERNAME": {
                        "$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)
                    }
                })

            else:
                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "REG_USERNAME": {
                                "$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)
                            },
                            "$and": [
                                {
                                    "SUSPECTED_DATE": {
                                        "$gte": user_hist.starting_date
                                    }
                                }, {
                                    "SUSPECTED_DATE": {
                                        "$lte": user_hist.ending_date
                                    }
                                }
                            ]
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }, {
                        "$skip": (user_hist.page_id - 1) * 20
                    }, {
                        "$limit": 20
                    }
                ], allowDiskUse=True).to_list(None)

                total_count = await col_sus_history.count_documents({
                    "REG_USERNAME": {"$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)},
                    "$and": [{
                        "SUSPECTED_DATE": {
                             "$gte": user_hist.starting_date
                             },
                    }, {
                        "SUSPECTED_DATE": {
                            "$lte": user_hist.ending_date
                        }
                    }
                    ]})

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the data and insert into `filtered_records_json` in json string format.
        for record in sus_user_data:

            del record['_id']

            # Convert each record into json string.
            record_json = json.dumps(record, default=json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, record_json)

        # Return the dictionary containing filtered records and total page count of filtered records.
        page_count = math.ceil(total_count/20)

        print(f'Data Records: {filtered_records_json}')

        return {
            'data_list': filtered_records_json[::-1],
            'total_pages': page_count,
            'total_rows': total_count
        }

    except Exception as err:
        print(f'Error occured in: user_history_list; {err}')

        return {
            "status": 500,
            "msg": "Failed to get User History data"
        }


@app.post('/fetch_user_modal')
async def user_modal_list(user_modal_hist: UserModalHistory, request: fastapi.Request):
    """
    List all the history details of a particular user.

    :param ip_mod: Gives the received data based on UserModal model.
    :ptype: UserModal model.

    :return: List of data containing history details of the user and the  total count of the filtered data pages.
    :rtype: dict
    """

    try:
        user_modal_list = await col_pnr.find({
            "$and": [
                {
                    'USER_ID': float(user_modal_hist.userid)
                }, {
                    'USERNAME': user_modal_hist.username}
            ]}, {
            '_id': 0,
            'USER_ID': 1,
            'FROM': 1,
            'TO': 1,
            'BOOKING_DATE': 1,
            'JOURNEY_DATE': 1,
            'BOOKING_MOBILE': 1,
            'IP_ADDRESS': 1,
            'PNR_NUMBER': 1,
            'USERNAME': 1,
            'TAGS': 1,
            'TK_TYPE': 1
        }).sort("JOURNEY_DATE", -1).skip((user_modal_hist.page_id - 1)*10).to_list(10)

        total_count = await col_pnr.count_documents(
            {
                "$and": [
                    {
                        'USER_ID': float(user_modal_hist.userid)
                    }, {
                        'USERNAME': user_modal_hist.username}
                ]})

        if user_modal_list != []:
            for pnr_detail in user_modal_list:
                suspected_codes = list()
                pnr_suspected_status_dict = {
                    'IP_ADDRESS': False,
                    'USERNAME': False,
                    'USER_ID': False,
                    "BOOKING_MOBILE": False,
                    "PNR_NUMBER": False,
                    "BOOKING_DATE": False
                }

                if 'TAGS' in pnr_detail:
                    PNR_tags = pnr_detail['TAGS']
                    for tag in PNR_tags:
                        if 'IP' in tag:
                            pnr_suspected_status_dict['IP_ADDRESS'] = True
                            suspected_codes.append('UB1')
                        if 'USER' in tag:
                            pnr_suspected_status_dict['USERNAME'] = True
                            suspected_codes.append('UA6')

                    pnr_detail.update(
                        {"PNR_SUSPECTED_STATUS": pnr_suspected_status_dict})
                    pnr_detail.update({"SUSPECTED_CODES": suspected_codes})

        # Tracking list to store the filtered records.
        filtered_records_json = []

        # Iterate over the fetched data.
        for rec in user_modal_list:

            # Convert each record into JSON string.
            response_json = json.dumps(rec, default=json_util.default)

            # Add the JSON to the tracking list.
            filtered_records_json.insert(0, response_json)

        # Return the dictionary containing filtered records and total page count of filtered records.
        page_count = math.ceil(total_count/10)
        return {
            'data_list': filtered_records_json[::-1],
            'total_pages': page_count,
            'total_rows': total_count
        }

    except Exception as e:

        print(e.msg())

        return {
            "status": 500,
            "msg": "Failed to load the history details of user"
        }


@app.post('/export-user-history')
async def user_history_export(user_hist: UserHistoryList, request: fastapi.Request):
    """
    Export all the history of all the users.

    :param ip_mod: Gives the received data based on UserHistory model.
    :ptype: UserHistory model.

    :return: List of data containing history of all the users and the  total count of the filtered data pages.
    :rtype: dict
    """

    try:
        user_hist.starting_date = datetime.datetime.combine(
            user_hist.starting_date.date(), datetime.time.min)

        if user_hist.search == '':

            if user_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$sort": {"TOTAL_BOOKED_TICKETS": -1}
                    }
                ], allowDiskUse=True).to_list(None)

            else:

                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "$and": [
                                {
                                    "SUSPECTED_DATE": {
                                        "$gte": user_hist.starting_date
                                    }
                                }, {
                                    "SUSPECTED_DATE": {
                                        "$lte": user_hist.ending_date
                                    }
                                }
                            ]
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }
                ], allowDiskUse=True).to_list(None)

        else:
            if user_hist.starting_date.date() == datetime.datetime(1970, 1, 1).date():

                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "REG_USERNAME": {
                                "$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)
                            }
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }
                ], allowDiskUse=True).to_list(None)

            else:
                sus_user_data = await col_sus_history.aggregate([
                    {
                        "$match": {
                            "REG_USERNAME": {
                                "$regex": re.compile(f'.*{user_hist.search}.*', re.IGNORECASE)
                            },
                            "$and": [
                                {
                                    "SUSPECTED_DATE": {
                                        "$gte": user_hist.starting_date
                                    }
                                }, {
                                    "SUSPECTED_DATE": {
                                        "$lte": user_hist.ending_date
                                    }
                                }
                            ]
                        }
                    }, {
                        "$sort": {
                            "TOTAL_BOOKED_TICKETS": -1
                        }
                    }
                ], allowDiskUse=True).to_list(None)

        modifiledSusUserData = list()

        for user in sus_user_data:
            regAddress = user.get("REG_ADDRESS")
            del user["REG_ADDRESS"]
            del user["SUSPECTED_STATUS"]
            user.update({
                "ADDRESS": regAddress.get("ADDRESS"),
                "COLONY": regAddress.get("COLONY"),
                "STREET": regAddress.get("STREET"),
                "POSTOFFICE": regAddress.get("POSTOFFICE"),
                "DISTRICT": regAddress.get("DISTRICT"),
                "STATE": regAddress.get("STATE"),
                "PIN_CODE": regAddress.get("PIN_CODE"),

            })
            modifiledSusUserData.append(user)

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(modifiledSusUserData)
        df['SUSPECTED_DATE'] = df['SUSPECTED_DATE'].dt.strftime('%a %d %B %Y')

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}', index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except Exception as e:
        print(e.msg())

        return {
            "status": 500,
            "msg": "Failed to get User History data"
        }


@app.post('/down-user-modal')
async def user_modal_export(user_modal_hist: UserModalHistory, request: fastapi.Request):
    """
    Export all the history details of the user.

    :param ip_mod: Gives the received data based on UserModal model.
    :ptype: UserModal model.

    :return: List of data containing history details of the user and the  total count of the filtered data pages.
    :rtype: dict
    """

    try:
        user_modal_list = await col_pnr.find({
            "$and": [
                {
                    'USER_ID': float(user_modal_hist.userid)
                }, {
                    'USERNAME': user_modal_hist.username}
            ]}, {
            '_id': 0,
            'USER_ID': 1,
            'FROM': 1,
            'TO': 1,
            'BOOKING_DATE': 1,
            'JOURNEY_DATE': 1,
            'BOOKING_MOBILE': 1,
            'IP_ADDRESS': 1,
            'PNR_NUMBER': 1,
            'USERNAME': 1,
            'TAGS': 1,
            'TK_TYPE': 1
        }).to_list(10000)

        if user_modal_list != []:
            for pnr_detail in user_modal_list:
                suspected_codes = list()
                if 'TAGS' in pnr_detail:
                    PNR_tags = pnr_detail['TAGS']
                    for tag in PNR_tags:
                        if 'IP' in tag:
                            suspected_codes.append('UB1')
                        if 'USER' in tag:
                            suspected_codes.append('UA6')

                    pnr_detail.update({"SUSPECTED_CODES": suspected_codes})

        # Converts the 'pnr_sus_list' into pandas dataframe.
        df = pandas.DataFrame(user_modal_list)
        df['BOOKING_DATE'] = df['BOOKING_DATE'].dt.strftime('%a %d %B %Y')
        df['JOURNEY_DATE'] = df['JOURNEY_DATE'].dt.strftime('%a %d %B %Y')

        # # Generate a unique '.csv' file name to store the data.
        f_name = uuid.uuid1().hex + '.csv'

        # Converts the pandas dataframe into a excel sheet.
        df.to_excel(f'download_folder/{f_name}', index=False)

        # Asynchronously streams a file as the response.
        # Return the file path directly from the path operation function.
        return fastapi.responses.FileResponse(f'download_folder/{f_name}')

    except:

        return {
            "status": 500,
            "msg": "Failed to load the history details of the User"
        }


@app.post('/overview_case_detail')
async def overview_case_data(overview_detail: CaseManagementOverviewDetail):
    cache_key = f'overview_case_detail-{overview_detail.username}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. overview_case_detail')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            filter_data = eval(cached_data)

            cache_response = list()

            for data_record in filter_data:

                data = json.loads(data_record)
                cache_response.append(data)

            pnr_data = cache_response[(
                overview_detail.page_id - 1) * 10: overview_detail.page_id * 10]

            json_records = list()

            filter_total_count = len(filter_data)

            page_count = math.ceil(filter_total_count/10)

            for data in pnr_data:
                # Convert each record into JSON string.
                response_json = json.dumps(data, default=json_util.default)

                # Add the JSON to the tracking list.
                json_records.insert(0, response_json)

            response_data = {
                'data_list': json_records,
                'total_pages': page_count,
                'total_rows': filter_total_count
            }
            return response_data

        else:
            ic('Cache miss .. overview_case_detail')

            try:
                overview_detail.username = overview_detail.username[:math.ceil(
                    len(overview_detail.username) * 0.70)]
                data = await col_sus_user.find({
                    'USERNAME': {"$regex": re.compile(f'^{overview_detail.username}.*')}
                }, {'_id': 0, 'USERNAME': 1}).to_list(None)

                sus_user_data = list()
                check_data = set()
                for similar_username in data:
                    user_data = await col_user_data.find({
                        'USERNAME': similar_username['USERNAME']
                    }, {
                        '_id': 0,
                        'USERNAME': 1,
                        'EMAIL': 1,
                        'REGISTRATION_DATETIME': 1,
                        'REGISTERED_MOBILE': 1,
                        'FIRST_NAME': 1,
                        'MIDDLE_NAME': 1,
                        'LAST_NAME': 1,
                        'IP_ADDRESS': 1
                    }).sort('REGISTRATION_DATETIME', -1).to_list(None)

                    if user_data != []:
                        # print(list(user_data[0].values()))
                        sus_user_data.extend(user_data)

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in sus_user_data:

                    if 'IP_ADDRESS' in rec:
                        rec.update({"Geolocation": [], "Location": "N.A"})
                        try:
                            data = geoip.get(rec["IP_ADDRESS"])
                            loc = data["city"]["names"]["en"]
                            rec.update({"Location": loc})

                            lat = data["location"]["latitude"]
                            lon = data["location"]["longitude"]

                            rec.update({"Geolocation": [lat, lon]})
                        except:
                            pass

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.
                filtered_records_json = filtered_records_json[::-1]

                # # print(response_data)
                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP,
                                   f'{filtered_records_json}')

                total_count = len(filtered_records_json)

                json_records = list()

                if overview_detail.page_id == 1:

                    # data = [d for json.loads(filtered_records_json)]

                    pnr_data = sus_user_data[(
                        overview_detail.page_id - 1) * 10: overview_detail.page_id * 10]

                    for data in pnr_data:
                        # Convert each record into JSON string.
                        response_json = json.dumps(
                            data, default=json_util.default)

                        # Add the JSON to the tracking list.
                        json_records.insert(0, response_json)

                page_count = math.ceil(total_count/10)

                response_data = {
                    'data_list': json_records,
                    'total_pages': page_count,
                    'total_rows': total_count
                }

                return response_data

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Overview Case Management details"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


@app.post('/case_detail_export')
async def overview_case_data_export(overview_detail: CaseManagementOverviewDetail):
    cache_key = f'overview_case_detail-{overview_detail.username}'
    ic(cache_key)

    try:
        ic('Getting Cache')
        cached_data = redis_client.get(cache_key)

        if (cached_data):
            ic('Cache hit .. overview_case_detail')
            print(
                f'Raw type: {type(cached_data)} | Eval Type: {type(eval(cached_data))}')

            filter_data = eval(cached_data)

            cache_response = list()

            for data_record in filter_data:

                data = json.loads(data_record)
                data['REGISTRATION_DATETIME'] = data['REGISTRATION_DATETIME']['$date']
                data['REGISTRATION_DATETIME'] = dateutil.parser.parse(
                    data['REGISTRATION_DATETIME'])
                cache_response.append(data)

            # Converts the 'pnr_sus_list' into pandas dataframe.
            df = pandas.DataFrame(cache_response)
            df['REGISTRATION_DATETIME'] = df['REGISTRATION_DATETIME'].dt.strftime(
                '%a %d %B %Y')

            # # Generate a unique '.csv' file name to store the data.
            f_name = uuid.uuid1().hex + '.csv'

            # Converts the pandas dataframe into a excel sheet.
            df.to_csv(f'download_folder/{f_name}', index=False)

            # Asynchronously streams a file as the response.
            # Return the file path directly from the path operation function.
            return fastapi.responses.FileResponse(f'download_folder/{f_name}')

        else:
            ic('Cache miss .. overview_case_detail')

            try:
                user_data = list()
                documents = await col_sus_user.find({}, {'_id': 0, 'USERNAME': 1}).to_list(None)
                for document in documents:
                    username = document.get('USERNAME', '')
                    username = str(username)
                    similar_username = calculate_similarity_ratio(
                        overview_detail.username, username, 0.80)
                    if similar_username != None:
                        sus_user_data = await col_user_data.find({
                            'USERNAME': similar_username
                        }, {
                            '_id': 0,
                            'USERNAME': 1,
                            'EMAIL': 1,
                            'REGISTRATION_DATETIME': 1,
                            'REGISTERED_MOBILE': 1,
                            'BOOKING_MOBILE': 1,
                            'FIRST_NAME': 1,
                            'MIDDLE_NAME': 1,
                            'LAST_NAME': 1,
                            'IP_ADDRESS': 1
                        }).sort('REGISTRATION_DATETIME', -1).to_list(None)

                        if sus_user_data != []:
                            user_data.extend(sus_user_data)

                # Tracking list to store the filtered records.
                filtered_records_json = []

                # Iterate over the fetched data.
                for rec in user_data:

                    if 'IP_ADDRESS' in rec:
                        rec.update({"Geolocation": [], "Location": "N.A"})
                        try:
                            data = geoip.get(rec["IP_ADDRESS"])
                            loc = data["city"]["names"]["en"]
                            rec.update({"Location": loc})

                            lat = data["location"]["latitude"]
                            lon = data["location"]["longitude"]

                            rec.update({"Geolocation": [lat, lon]})
                        except:
                            pass

                    # Convert each record into JSON string.
                    response_json = json.dumps(rec, default=json_util.default)

                    # Add the JSON to the tracking list.
                    filtered_records_json.insert(0, response_json)

                # Return the dictionary containing filtered records and total page count of filtered records.
                filtered_records_json = filtered_records_json[::-1]

                # print(response_data)
                ic('Setting Cache ..')
                redis_client.setex(cache_key, CACHE_EXP,
                                   f'{filtered_records_json}')

                # Converts the 'pnr_sus_list' into pandas dataframe.
                df = pandas.DataFrame(data)

                # # Generate a unique '.csv' file name to store the data.
                f_name = uuid.uuid1().hex + '.csv'

                # Converts the pandas dataframe into a excel sheet.
                df.to_csv(f'download_folder/{f_name}', index=False)

                # Asynchronously streams a file as the response.
                # Return the file path directly from the path operation function.
                return fastapi.responses.FileResponse(f'download_folder/{f_name}')

            except Exception as e:
                print(e.msg())
                err_msg = {
                    "status": 500,
                    "msg": "Failed to get Overview Case Management details"
                }
                return err_msg

    except Exception as err:
        ic('Error with Cache Operation ..')
        print(err.msg())
        return {
            "status": 500,
            "msg": "Error with Cache Operation"
        }


async def startup_event():
    setup_mount_folder('files')
    setup_mount_folder('download_reports')
    app.state.executor = ProcessPoolExecutor()
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


async def shutdown_event():
    app.state.executor.shutdown()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=55563,
        reload=True)
