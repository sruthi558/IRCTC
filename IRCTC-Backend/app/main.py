"""Summary

Attributes:
    ALLOWED_EXTENSIONS_LOGS (TYPE): Description
    ALLOWED_EXTENSIONS_REPORT (TYPE): Description
    main (TYPE): Description
    url_ana (str): Description
    url_bm (str): Description
    url_booklog (str): Description
    url_dash (str): Description
    url_infra (str): Description
    url_isp (str): Description
    url_uid (str): Description
"""
import re
import time
from flask import Blueprint, request, render_template, send_from_directory
from flask_login import login_required, current_user
import pandas
from werkzeug.utils import secure_filename
from .models import User, Report
from . import db
from flask_login import current_user, login_required
from flask import jsonify, current_app
import pathlib
import os
import requests
import dateutil
import json
import hashlib
import dateutil.parser
import datetime
import json
from sqlalchemy import desc

import pydantic
import pydantic_settings

main = Blueprint('main', __name__)
log = current_app

# Refrencing current app handler to initiate logging
log = current_app


class Settings(pydantic_settings.BaseSettings):
    """
    Set the configurations for the microservice's functionality through the env file.

    :param pydantic.BaseSettings: Inherit from the BaseSettings class of pydantic to setup the basic configuration from the env file.
    """

    # Default configuration values to be used if these parameters are not defined in the env file.
    url_bm: str = 'http://127.0.0.1:55556'
    url_uid: str = 'http://127.0.0.1:55557'
    url_ana: str = 'http://127.0.0.1:55562'
    url_isp: str = 'http://127.0.0.1:55558'
    url_dash: str = 'http://127.0.0.1:55559'
    url_infra: str = 'http://127.0.0.1:55560'
    url_booklog: str = 'http://127.0.0.1:55561'
    url_sus: str = 'http://127.0.0.1:55570'
    url_report: str = 'http://127.0.0.1:55571'
    url_sus_history: str = 'http://127.0.0.1:55563'

    # Read the env file to construct a configuration for the microservice.
    model_config = pydantic_settings.SettingsConfigDict(env_file="../.env")

settings = Settings()
print(f'Reading env: {settings}')

# Define the allowed extensions for log files.
ALLOWED_EXTENSIONS_LOGS = set(['xlsx', 'xlsb', 'csv', 'txt', 'xls'])


def allowed_file_logs(filename):
    """
    Check for the valid extensions for log file.
    
    :param: filename
    :ptype: string
    
    :return: Valid expression or not.
    :rtype: boolean
    """

    # Extracting the extension from file name and checking if present in `ALLOWED_EXTENSION_LOGS`.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_LOGS

# Define the allowed extensions for report files.
ALLOWED_EXTENSIONS_REPORT = set(['pdf'])


def allowed_file_report(filename):
    """
    Check for the valid extensions for report file.
    
    :param: filename
    :ptype: string
    
    :return: Valid expression or not.
    :rtype: boolean
    """

    # Extracting the extension from file name and checking if present in `ALLOWED_EXTENSION_REPORT`.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_REPORT


def get_file_size_in_MB(filepath):
    """
    File size in megabytes.
    
    :param filepath: Path of the file
    :ptype: string
    
    :return file_in_MB: Size of the file
    :rtype: float
    """
    # Get size of the file.
    filesize = os.path.getsize(filepath)

    # Converting into megabytes.
    filesize_in_MB = filesize / 1024 / 1024

    # Rounding off to 2 decimals.
    filesize_in_MB = round(filesize_in_MB, 2)

    return filesize_in_MB


##########################
#### Admin Panel Page ####
##########################

# Default: Home Route 
@main.route('/', methods=['GET'])
@login_required
def home():
    return jsonify(message='Server is running..'), 200 

@main.route('/admin_panel', methods=['POST'])
@login_required
def panel():
    """
    Admin Panel (only admin) will retrieve all the users-list as a json format.

    :return: List of users in DB.
    :rtype: JSON
    """

    # Check if current user role is not `admin`.
    if current_user.role != 'admin':

        # Return status code and response message.
        return jsonify({'detail': 'INVALID_PERMISSIONS'}), 403
    
    log.logger.info('%s %s %s %s %s',
        current_user.email,
        request.method,
        request.full_path,
        request.headers['Cookie'].split(";")[0],
        request.headers['Cookie'].split(";")[1]
    )

    # Fetch all users.
    users = User.query.all()

    # Tracking list to store the filtered records.
    admin_users_list = []
    
    # Iterate over the fetched data.
    for user in users:
        # Convert each record into dictionary.
        dictionary_record = user.to_dict()

        # Delete password key value pairs from dictionary.
        del dictionary_record['password']

        # Add the JSON to the tracking list.
        admin_users_list.append(dictionary_record)

    # Return the data in JSON format.
    return jsonify(admin_users_list), 200


########################
#### Dashboard Page ####
########################

@main.route('/fetch-over-data', methods=['GET'])
@login_required
def fetch_overdata():
    """
    Overview page will retrieve all the data(PNRs Analyzed, PNRs Flagged, User Registrations Analyzed, User IDs Flagged, IP Addresses Blacklisted, Vulnerabilities Reported) as a json format.
    
    :return: Response data
    :rtype: JSON
    """
    try:
        if True:
            print(f'Making req to analyser')
            # Request data from analyzer microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_ana}/over-data', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })
            # print(f'Response received from the analyser: {r}')

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/overview_data', methods=['POST'])
@login_required
def overviewdata():
    """Summary
    
    Returns:
        TYPE: Description
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `filteroption` in request.
            if 'filteroption' in request.json:

                # Request data from microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_dash}/dash_first', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/overview_count', methods=['POST'])
@login_required
def overviewcount():
    """Summary
    
    Returns:
        TYPE: Description
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_dash}/dash_board_const', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


########################
#### Book Log Page ####
########################


@main.route('/fetch-book-data', methods=['GET'])
@login_required
def fetch_bookdata():
    """
    Charts for tickets booked using VPS, tickets booked using Non-VPS and count of IPs found in VPS pool for a particular date.
    
    :return: Response data containing the details of the booking on a particular date.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetch data corresponding to `log_date` and `f_type` from URL path parameter.
            l_date = request.args.get('log_date')
            f_type = request.args.get('f_type')

            # Request data from booklog microservice --> send cookie and current user email.
            r = requests.get(
                f'{settings.url_booklog}/booklog_dash_uniq/{l_date}/{f_type}', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

########################
#### Daily Stats ####
########################

@main.route('/fetch-user-reg-logs', methods=['GET','POST'])
@login_required
def fetch_userlogs():
    """
    Table for data related to user registration and pnr logs. 
    
    :return: Response data containing the details of the ticket count of AC, NONAC, ARP, VPS and NON VPS registrations.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            
            print("Printing req parameters..")
            req_data = request.data
            req_json_data = request.json 
            print(f"Req Data: {req_data}")
            print(f"Req JSON: {req_json_data}")

            #check for empty json or no request body
            if not request.json or 'searchDate' not in request.json:
                return jsonify({'detail': 'INVALID_REQUEST'}), 400

            # Check for `searchDate ` in request.
            elif 'searchDate' in request.json:

                # Request data from booklogs microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_booklog}/user-registration-logs', json=request.json
                    , cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email}
                )                 

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
                
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except:
        return jsonify({'detail': 'BAD_REQUEST'}), 500
    

@main.route('/fetch-book-trend', methods=['GET', 'POST'])
@login_required
def fetch_booktrend():
    """
    Trends for total tickets booked, total tickets booked through VPS, top 10 ISP booked tickets.
    
    :return: Booking log data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `std` in request.
            if 'std' in request.json:

                # Request data from booklog microservice --> send cookie and current user email.
                r = requests.post(
                    f'{settings.url_booklog}/booklog_dash_range', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



######################
#### User ID Page ####
######################

@main.route('/case-mgmt', methods=['GET', 'POST'])
@login_required
def case_management():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/case-mgmt', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/export-case-mgmt', methods=['GET', 'POST'])
@login_required
def export_case_management():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            r = requests.post(f'{settings.url_sus_history}/export-case-mgmt', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logging
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/ip-case-mgmt', methods=['GET', 'POST'])
@login_required
def ip_case_management():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/ip-case-mgmt', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/export-ip-case', methods=['GET', 'POST'])
@login_required
def export_ip_caset():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            r = requests.post(f'{settings.url_sus_history}/export-ip-case-mgmt', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logging
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/pnr_case_export', methods=['GET', 'POST'])
@login_required
def case_pnr_export():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            r = requests.post(f'{settings.url_sus_history}/pnr_case_data_export', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logging
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/case-mgmt-user', methods=['GET', 'POST'])
@login_required
def case_management_user():
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

                # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/case-user-details', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logging
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/fetch-user-history', methods=['GET', 'POST'])
@login_required
def fetch_user_history():
    """
    List all the booking details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    
    print(f'API hit for sus hist data ')

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/user_history_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })
                
                print(f'Sus usr response: {r.json()}')

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as err:
        print(f'Error getting sus usr history: {err}')
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/view-user-history', methods=['GET', 'POST'])
@login_required
def fetch_user_history_modal():
    """
    List all the booking details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/fetch_user_modal', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/download-user-history', methods=['POST'])
@login_required
def download_user_history():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/export-user-history', json=request.json,cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email}
            )

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    
@main.route('/download-user-modal', methods=['POST'])
@login_required
def download_user_modal():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/down-user-modal', json=request.json,cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email}
            )

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    
@main.route('/fetch-userid-data', methods=['GET'])
@login_required
def fetch_userreg():
    """
    Charts for users registered using VPS ISP, users registered using Non-VPS ISP, users registered through vendors and count of IPs found in VPS pool.
    
    :return: Data to be displayed for specific date.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `log_date` and `f_type` from URL path parameter.
            l_date = request.args.get('log_date')

            # Request data from user_id microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_uid}/userreg_dash_uniq/{l_date}', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/fetch-userid-trend', methods=['GET', 'POST'])
@login_required
def fetch_trend():
    """
    Trends for average users registered, average users registered through vendors, top ISP registered users.

    :return: Response data containing data for registered users through VPS, Non-VPS, vendor and  data for top VPS ISPs.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `starting_date` in request.
            if 'starting_date' in request.json:

                # Request data from user_id microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_uid}/userreg_dash_range', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )
                
                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
        


@main.route('/userid_list_all', methods=['POST'])
@login_required
def user_id():
    """
    List of all the users registered.

    :return: Response data containing data for registered users.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from user_id microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_uid}/userid_all', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )
                
                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503  


@main.route('/userid_pagecount_all', methods=['POST'])
@login_required
def user_id_all_count():
    """
    Count of all the users registered.
    
    :return: Response data containing page count.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_uid}/userid_all_count', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return page count in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/userid_list_find', methods=['POST'])
@login_required
def user_id_find():
    """
    Find the details of the specific user registered.

    :return: Response data containing data for specific user.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:
                
                # Request data from user_id microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_uid}/userid_find', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/userid_pagecount_find', methods=['POST'])
@login_required
def user_id_find_count():
    """
    Find the page details of the specific user registered.

    :return: Response data containing data for specific user.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_uid}/userid_find_count', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return page count in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/uid_count', methods=['GET'])
@login_required
def uid_count():
    """
    Find the count for users registered through vps, vendor and blocked users.

    :return: Response data containing data for vps users, vendor users and blocked users.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r1 = requests.get(f'{settings.url_uid}/vpscount/1', timeout=2, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        r1.content = 0

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r2 = requests.get(f'{settings.url_uid}/vencount', timeout=2, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger 
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        r2.content = 0

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r3 = requests.get(f'{settings.url_uid}/blockcount', timeout=2, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        r3.content = 0

    # Return all the data in JSON format.
    return jsonify({
        'detail': {
            'vpscount': int(r1.content), 
            'vendcount': int(r2.content), 
            'block_acc': int(r3.content)
        }
    }), 200


@main.route('/uid_vps/<int:num>', methods=['POST'])
@login_required
def uid_vps_count(num: int):
    """
    Responds vpscount true with 1 false 0
    
    :param: <int: num> 1 if want VPS 0 if VPS False
    :return: (int) 
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            if (num == 0 or num or 1):

                # Request data from user_id microservice --> send cookie and current user email.
                r = requests.get(f'{settings.url_uid}/vpscount/{num}', cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the content.
                return r.content
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/vend_acc', methods=['GET'])
@login_required
def vend_acc():
    """
    Responds with count of accounts created by vendors
    
    :return: (int) for vendor ip true 
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_uid}/vencount', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/block_acc', methods=['GET'])
@login_required
def block_acc():
    """
    Responds with count of accounts created by vendors
    
    :return: (int) for vendor ip true 
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from user_id microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_uid}/blockcount', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger 
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


###############################
#### Brand Monitoring Page ####
###############################

@main.route('/brandmon-upload-file', methods=['POST'])
@login_required
def bd_up_file():
    """
    Upload file feature in user registration logs and daily logs analysis page.
    
    :return: Response data 
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]

            # Check for allowed file extension.
            if file and allowed_file_logs(file.filename):

                # Secure version of file name.
                orig_filname = secure_filename(file.filename)

                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filname).name
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(filepath)

                # Open the file in read mode.
                files = {'file': open(filepath, 'rb')}

                try:
                    # Request data from analyzer microservice --> send cookie and current user email.
                    r = requests.post(f'{settings.url_bm}/upload_brand_data', files=files, cookies={
                        "cookie" : request.headers['Cookie'], 
                        "email": current_user.email
                    })

                    # Logger
                    log.logger.info('%s %s %s %s %s %s',
                        current_user.email,
                        request.method,
                        request.full_path,
                        request.data,
                        request.headers['Cookie'].split(";")[0],
                        request.headers['Cookie'].split(";")[1]
                    )
                    
                    # Return all the data in JSON format.
                    return jsonify(r.json()), 200
                
                except Exception as e:
                    # Return status code and response message.
                    return jsonify({'detail': 'FILEUPLOAD_ERROR'}), 400
                
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


@main.route('/brandmon_list_all', methods=['POST'])
@login_required
def bm_panel():
    """
    Generates data from bm panel from microservice request
    
    :param: <int: num> to get pagination
 
    :return: Returns json data with pagination.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_id' in request.json:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_all', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
                    
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/bm_card_list', methods=['POST'])
@login_required
def bm_card_modal():
    """
    Displays the data on card model for brand monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_id' in request.json:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_card_modal', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500
    


# NOT IN USE
@main.route('/brandmon_pagecount_all', methods=['POST'])
@login_required
def bm_all_count():
    """
    Displays count of total number of documents in data collection.
    
    :return: Response data containing page count.
    :rtype: JSON
    """
    visi_dict = {}

    # Check if current user is `admin`.
    if current_user.role == 'admin':
        visi_dict['visibility'] = True

    try:
        # Request data from brandmonitoring microservice --> send cookie and current user email.
        r = requests.post(f'{settings.url_bm}/bm_all_count', json=visi_dict, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })
        
        # Logger
        log.logger.info('%s %s %s %s %s',
            current_user.email,
            request.method,
            request.full_path,
            request.headers['Cookie'].split(";")[0],
            request.headers['Cookie'].split(";")[1]
        )
        
        # Return page count data in JSON format.
        return jsonify({'page_count': r.json()['page_count']}), 200
    
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


# NOT IN USE
@main.route('/brandmon_list_find', methods=['POST'])
@login_required
def bm_find():
    """
    Find the details of the specific brandmonitoring data.

    :return: Response data containing specific brandmonitoring data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_find', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

# NOT IN USE

@main.route('/brandmon_pagecount_find', methods=['POST'])
@login_required
def bm_find_count():
    """
    Find the page details of the specific brandmonitoring data.

    :return: Response data containing specific brandmonitoring data.
    :rtype: JSON
    """
    try: 
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from brandmonitoring microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_bm}/bm_find_count', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return page count data in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({'detail':'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

# NOT IN USE

@main.route('/pend-bm/<int:action>', methods=['POST'])
@login_required
def pend_bm(action: int):
    """
    Responds with total pending requests
    
    Total 3 calls from frontend
    
    Request TakeDown Action : <int: 1> = 'Request TakeDown'
    Pending Action : <int: 2> = 'Pending Requests'
    Took Down : <int: 3> = 'Took Down'
    Rejected : <int: 4> = 'Rejected'
    
    :return: (int) responds with the count of pending requests 
    
    Args:
        action (int): Description
    
    Returns:
        TYPE: Description
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            if action < 5 and action > 0:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.get(f'{settings.url_bm}/td_status/{action}', cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the content.
                return r.content
            
            else:
                # Return status code and response message.
                return jsonify({'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

# NOT IN USE

@main.route('/brandmon_change_visible', methods=['POST'])
@login_required
def changevisi():
    """
    Changes the visibility of brand monitoring card.

    :return: Response data containing status code and message for successful change.
    :rtype: JSON
    """
    if request.json['show'] == True:

        # Check if current user is not `admin`.
        if current_user.role != 'admin':

            # Return status code and response message.
            return jsonify({'detail': 'INVALID_PERMISSIONS'}), 403

    # Check for `cellid` in request.
    if 'cellid' in request.json:

        # Request data from brandmonitoring microservice --> send cookie and current user email.
        r = requests.post(f'{settings.url_bm}/bm_change_visible', json=request.json, cookies={
            "cookie" : request.headers['Cookie'], 
            "email": current_user.email
        })

        # Logger
        log.logger.info('%s %s %s %s %s %s',
            current_user.email,
            request.method,
            request.full_path,
            request.data,
            request.headers['Cookie'].split(";")[0],
            request.headers['Cookie'].split(";")[1]
        )
        
        # Return all the data in JSON format.
        return jsonify(r.json()), 200
    
    else:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400

# NOT IN USE
@main.route('/brandmon_delete_visible', methods=['POST'])
@login_required
def delvisi():
    """
    Changes the visibility of brand monitoring card.

    :return: Response data containing status code and message for successful change.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            request.json['show'] = False

            # Check for `cellid` in request.
            if 'cellid' in request.json:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_change_visible', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
             # Return status code and response message.
             return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


# NOT IN USE

@main.route('/brandmon_change_status', methods=['POST'])
@login_required
def changestatus():
    """
    Changes the status of brand monitoring card.
    
    :return: Response data containing status code and message for successful change.
    :rtype: JSON
    """
    
    # Check if current user is not `admin` and `status` is invalid integer.
    if current_user.role != 'admin' and request.json['status'] > 1:

        # Return status code and response message.
        return jsonify({'detail': 'INVALID_PERMISSIONS'}), 400

    request.json['username'] = current_user.username

    # Check for `cellid` in request.
    if 'cellid' in request.json:

        # Request data from brandmonitoring microservice --> send cookie and current user email.
        r = requests.post(f'{settings.url_bm}/bm_change_status', json=request.json, cookies={
            "cookie" : request.headers['Cookie'], 
            "email": current_user.email
        })

        # Logger
        log.logger.info('%s %s %s %s %s %s',
            current_user.email,
            request.method,
            request.full_path,
            request.data,
            request.headers['Cookie'].split(";")[0],
            request.headers['Cookie'].split(";")[1]
        )

        # Return all the data in JSON format.
        return jsonify(r.json()), 200
    
    else:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


# NOT IN USE
@main.route('/brandmon_new_request', methods=['POST'])
@login_required
def sendcomment():
    """
    Generating new request for brand monitoring page.
    
    :return: Response data containing new request details.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            user_name = current_user.username

            # Check for `comment` in request.
            if 'comment' in request.json:

                # Set the username to current user's username.
                request.json['username'] = user_name 

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_new_req', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
              
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


# NOT IN USE
@main.route('/bm_td_list', methods=['POST'])
@login_required
def bm_takedown_modal():
    """
    Displays list of takedowns along with the page count.

    :return: Response data with pagination
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from brandmonitoring microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/bm_takedown_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


# NOT IN USE
@main.route('/bm_card_list_download', methods=['POST'])
@login_required
def bm_card_list_download():
    """
    Displays the data on card model for brand monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from brandmonitoring microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_bm}/brand_card_download', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


# NOT IN USE
@main.route('/bm_count_card', methods=['GET'])
@login_required
def bm_card_count():
    """
    Displays count of takedown requested, takedown initiated, takedown completed.
    
    :return: Response data 
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from brandmonitoring microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_bm}/bm_card_count', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


#####################
### Analyse Page ####
#####################

@main.route('/upload-file', methods=['POST'])
@login_required
def up_file():
    """
    Upload file feature in user registration logs and daily logs analysis page.
    
    :return: Response data 
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]
            
            if request.form.get('0') != "undefined":
                print(request.form.get('0'))

            # Check for allowed file extension.
            if file and allowed_file_logs(file.filename):

                # Secure version of file name.
                orig_filname = secure_filename(file.filename)

                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filname).name
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(filepath)

                # Open the file in read mode.
                files = {'file': open(filepath, 'rb')}

                try:

                    df = pandas.read_excel(filepath)

                    # common checks for data files
                    if 'USER_ID' in df.columns and df['USER_ID'].hasnans:
                        return jsonify({'detail' : 'Field USER_ID contains empty values'}), 403
                    if 'USERNAME' in df.columns and df['USERNAME'].hasnans:
                        return jsonify({'detail' : 'Field USERNAME contains empty values'}), 403
                    if 'IP_ADDRESS' in df.columns and df['IP_ADDRESS'].hasnans:
                        return jsonify({'detail' : 'Field IP_ADDRESS contains empty values'}), 403

                    # separate checks for user id file 
                    
                    if 'EMAIL' in df.columns and df['EMAIL'].hasnans:
                        return jsonify({'detail' : 'Field EMAIL contains empty values'}), 403
                    if 'REGISTRATION_DATE' in df.columns and df['REGISTRATION_DATE'].hasnans:
                        return jsonify({'detail' : 'Field REGISTRATION_DATE contains empty values'}), 403
                    
                    
                    # separate checks for PNR files
                    if 'BOOKING_DATE' in df.columns and df['BOOKING_DATE'].hasnans:
                        return jsonify({'detail' : 'Field BOOKING_DATE contains empty values'}), 403
                    if 'JOURNEY_DATE' in df.columns and df['JOURNEY_DATE'].hasnans:
                        return jsonify({'detail' : 'Field JOURNEY_DATE contains empty values'}), 403
                    if 'PNR_NUMBER' in df.columns and df['PNR_NUMBER'].hasnans:
                        return jsonify({'detail' : 'Field PNR_NUMBER contains empty values'}), 403

                    
                    # record = 0
                    # for user in df['USERNAME']:
                    #     record += 1
                    #     if isinstance(user,str) != True or re.match(r"^\d*/\d*",user):
                    #         return jsonify({'detail' : f'Invalid format for USERNAME at record {record}'}), 403
                        
                    # Request data from analyzer microservice --> send cookie and current user email.
                    r = requests.post(f'{settings.url_ana}/file_ana', files=files, cookies={
                        "cookie" : request.headers['Cookie'], 
                        "email": current_user.email
                    })

                    # Logger
                    log.logger.info('%s %s %s %s %s %s',
                        current_user.email,
                        request.method,
                        request.full_path,
                        request.data,
                        request.headers['Cookie'].split(";")[0],
                        request.headers['Cookie'].split(";")[1]
                    )
                    
                    # Return all the data in JSON format.
                    return jsonify(r.json()), 200
                
                except Exception as e:
                    print(repr(e))
                    # Return status code and response message.
                    return jsonify({'detail': 'FILEUPLOAD_ERROR'}), 400
                
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        print(e.msg())
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500




@main.route('/analysis_list_all', methods=['POST'])
@login_required
def ana_panel():
    """
    List of all files for user registration page and daily log analysis page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from analyzer microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_ana}/files_all', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500
    

@main.route('/analysis_list_find', methods=['POST'])
@login_required
def ana_find():
    """
    Search all files for user registration page and daily log analysis page for specified date.

    :return: Response data for the specified date.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `searchDate ` in request.
            if 'searchDate' in request.json:

                # Request data from analyzer microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_ana}/files_find', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'BAD_REQUEST'}), 500


@main.route('/analysis_pagecount_all', methods=['POST'])
@login_required
def anas_all_count():
    """
    Displays count of total number of pages.
    
    :return: Response data containing page count.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from analyzer microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_ana}/files_all_count', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


###################
#### INFRA MON ####
###################

@main.route('/infra_mon_find', methods=['POST'])
@login_required
def infra_mon_panel():
    """
    Fetch the default data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:
                # return jsonify({}), 200

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/infra_data_request', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/export_infra', methods=['POST'])
@login_required
def download_infra():
    """
    Download the details of software report.
    
    :return: Response content containing details of the softwares along with total count of data.
    :rtype: JSON
    """
    try:
        if True:
            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_infra}/export_infra_mon', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        print(e.msg())
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    
@main.route('/infra_stats', methods=['GET','POST'])
@login_required
def infra_stats():
    """
    Fetch the default data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
        
            # Request data from inframon microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_infra}/infra_stats_count', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/export_infra_stats', methods=['GET','POST'])
@login_required
def export_infra_stats():
    """
    Fetch the default data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
        
            # Request data from inframon microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_infra}/export_infra_stats_count', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/infra_history', methods=['POST'])
@login_required
def infra_history():
    """
    Fetch the monthly wise data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/infra_history', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/export_infra_history', methods=['POST'])
@login_required
def export_infra_history():
    """
    Fetch the monthly wise data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/export_infra_history', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return r.content, 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
    
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/infra_month_data', methods=['POST'])
@login_required
def infra_month_panel():
    """
    Fetch the monthly wise data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/infra_month_data_request', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/infra_vulnerability_type_data', methods=['POST'])
@login_required
def infra_vulnerability_data_panel():
    """
    Fetch the monthly wise data to be displayed on the page on page load on cyber threat monitoring page.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/infra_vulnerability_type_data_request', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/infra_status_find', methods=['POST'])
@login_required
def infra_status_find():
    """
    Tracks status of vulnerabilities whether it is open or resolved.

    :return: Response data with pagination
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_number' in request.json:
                # return jsonify({}), 200

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_infra}/infra_status_find', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/infra_mon_trend', methods=['GET'])
@login_required
def infra_mon_tr():
    """
    Tracks count of vulnerabilities discovered in the past months.

    :return: Response data containing vulnerability count per month, total count and not_info.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # return jsonify({}), 200
            # Request data from inframon microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_infra}/infra_trend_chart_data', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400

@main.route('/infra_chart_vuln', methods=['GET'])
@login_required
def infra_chart_mon():
    """
    Tracks the type of vulnerability.
    
    :return: Response data vulnerability type.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # return jsonify({}), 200
            # Request data from inframon microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_infra}/infra_vulnerability_chart_data', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/upload-infra', methods=['POST'])
@login_required
def up_infra_file():
    """
    Analyse the uploaded file.
    
    :return: Response data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]

            if request.form.get('0') != "undefined":
                print(request.form.get('0'))

            # Check for allowed file extension.
            if file and allowed_file_logs(file.filename):

                # Secure version of file name.
                orig_filname = secure_filename(file.filename)


                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filname).name
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(filepath)

                # Open the file in read mode.
                files = {'file': open(filepath, 'rb')}

                try:
                    # Request data from inframon microservice --> send cookie and current user email.
                    r = requests.post(f"{settings.url_infra}/infra_file_analysis", files=files, cookies={
                        "cookie" : request.headers['Cookie'], 
                        "email": current_user.email
                    })

                    # Logger
                    log.logger.info('%s %s %s %s %s %s',
                        current_user.email,
                        request.method,
                        request.full_path,
                        request.data,
                        request.headers['Cookie'].split(";")[0],
                        request.headers['Cookie'].split(";")[1]
                    )

                    # Return all the data in JSON format.
                    return jsonify(r.json()), 200
                
                except:
                    # Return status code and response message.
                    return jsonify({'detail': 'FILEUPLOAD_ERROR'}), 400
                
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/infra_open_count', methods=['GET'])
@login_required
def open_infra_count():
    """
    Tracks count of vulnerabilities that are still open.
    
    :return: Response data containing count of open vulnerabilities.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # return jsonify({}), 200
            # Request data from inframon microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_infra}/infra_count_open_vulnerabilities', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/infra_change_vuln_status', methods=['POST'])
@login_required
def infra_chnge_status():
    """
    Change the status of the vulnerability(resolved/unresolved).

    :return: Response data containing status and the message.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `cellid` in request.
            if 'cellid' in request.json and len(request.json['cellid']) >= 12:

            # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(
                    f'{settings.url_infra}/infra_vulnerability_change_status', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


########################
#### BLACKLIST PAGE ####
########################

@main.route('/upload_blacklist', methods=['POST'])
@login_required
def up_black_file():
    """
    Analyse the uploaded file.
    
    :return: Response data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            
            # Fetching the file.
            file = request.files["file"]

            # Secure version of file name.
            orig_filename = secure_filename(file.filename)

            # Check for allowed file extension.
            if file and allowed_file_logs(file.filename):

                # Fetching hash for file.
                hash = hashlib.md5(file.read()).hexdigest()
                
                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filename).name
                pure_filename = pure_filename.replace(' ', '_')
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(filepath)
                filesize = get_file_size_in_MB(filepath)

                # # Fetch `Date of report` argument.
                # if request.form.get('0') != "undefined":
                #     filedate = dateutil.parser.parse(request.form.get('0'))
                # else:
                #     filedate = datetime.datetime.now()

                # # Fetch `Report category` argument.
                # if request.form.get('1') != "undefined":
                #     service_provider = request.form.get('1')
                # else:
                #     service_provider = "Others"

                files = {'file': open(filepath, 'rb')}

                # Request data from inframon microservice --> send cookie and current user email.
                r = requests.post(f"{settings.url_isp}/blacklist_file_upload",
                    files=files,
                    cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email}
                )

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
                
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/isp_list_all', methods=['POST'])
@login_required
def isp_panel():
    """
    Displays list of Blacklisted ISPs with pagination.
    
    :return: Response data to be displayed and count of pages.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_id' in request.json:

                # Request data from black/isp microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_isp}/isp_all', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/isp_overview', methods=['GET','POST'])
@login_required
def isp_overview():
    """
    Displays list of monthly stats for blacklisted isp and subnets.
    
    :return: Response data to be displayed and count of pages.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/isp_overview', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

                # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/isp_subnet_export', methods=['GET','POST'])
@login_required
def isp_subnet_export():
    """
    Displays list of monthly stats for blacklisted isp and subnets.
    
    :return: Response data to be displayed and count of pages.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/isp_subnet_export', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
        
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/download-black-isp', methods=['POST'])
@login_required
def isp_download():
    """
    Downloads excel file displaying blacklisted ISPs.
    
    :return: Response content
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/download-isp', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400

@main.route('/download-date-isp', methods=['POST'])
@login_required
def isp_date():
    """
    Downloads excel file displaying blacklisted ISPs for specisic date
    
    :return: Response content
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/date-isp', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )
            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/isp_date_view', methods=['POST'])
@login_required
def isp_modal_view():
    """
    Displays blacklisted ISPs without pagination corresponding to the specific date respectively.
    
    :return: Response data containing list of blacklisted ISP subnets for the specified date.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `search` in request.
            if 'search' in request.json:

                # Request data from black/isp microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_isp}/isp_view_modal', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/isp_pagecount_all', methods=['POST'])
@login_required
def isp_all_count():
    """
    Displays count of total number of pages for blacklisted ISPs.
    
    :return: Response data containing page count.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/isp_all_count', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/isp_pagecount_find', methods=['POST'])
@login_required
def isp_find_count():
    """
    Find the page details of the specific blacklisted ISP.

    :return: Response data containing data for specific blacklisted ISP.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from black/isp microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_isp}/isp_find_count', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify({'page_count': r.json()['page_count']}), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

########################
#### DOT ####
########################

@main.route('/sus-mobile-upload', methods=['POST'])
@login_required
def sus_mobile_upload():
    """
    Upload suspicious mobile numbers files
    
    :return: Response message and status code.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]

            # Check for allowed file extension.
            if file and allowed_file_logs(file.filename):

                # Secure version of file name.
                orig_filname = secure_filename(file.filename)

                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filname).name
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(filepath)

                user_data = {"username" : current_user.username}

                files = {'file': open(filepath, 'rb')}

                try:
                    # Request data from analyzer microservice --> send cookie and current user email.
                    r = requests.post(f'{settings.url_bm}/upload-sus-mobile', files=files, params=user_data, cookies={
                        "cookie" : request.headers['Cookie'], 
                        "email": current_user.email
                    })

                    # Logger
                    log.logger.info('%s %s %s %s %s %s',
                        current_user.email,
                        request.method,
                        request.full_path,
                        request.data,
                        request.headers['Cookie'].split(";")[0],
                        request.headers['Cookie'].split(";")[1]
                    )

                    # Return all the data in JSON format.
                    return jsonify(r.json()), 200
                
                except Exception as err:
                    print(f'Error in sus-mobile-upload: {err}')
                    # Return status code and response message.
                    return jsonify({'detail': 'FILEUPLOAD_ERROR'}), 400
                    
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        print(e)
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/sus-mobile', methods=['POST'])
@login_required
def sus_mobile():
    """
    Fetch the data to be displayed on the page Suspicious Mobiles.

    :return: Response data with pagination
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_number` in request.
            if 'page_id' in request.json:

                # Request data from brandmon microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/sus-mobile-list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/sus-mobile-export', methods=['POST'])
@login_required
def sus_mobile_download():
    """
    Download Suspicious Mobile Numbers files
    
    :return: Downloaded file.
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            r = requests.post(f'{settings.url_bm}/file_download', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
    
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

########################
#### Report Archive ####
########################

@main.route('/archive-upload', methods=['POST'])
@login_required
def upload_archive():
    """
    Upload archive files
    
    :return: Response message and status code.
    :rtype: JSON
    """

    try: 
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]

            # Secure version of file name.
            orig_filename = secure_filename(file.filename)

            # Check for allowed file extension.
            if file and allowed_file_report(file.filename):

                # Fetching hash for file.
                hash = hashlib.md5(file.read()).hexdigest()
                
                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filename).name
                pure_filename = pure_filename.replace(' ', '_')
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                print("file: ", file)
                file.save(filepath)
                print("file after saving: ", file)
                filesize = get_file_size_in_MB(filepath)

                # Fetch `Date of report` argument.
                if request.form.get('0') != "undefined":
                    filedate = dateutil.parser.parse(request.form.get('0'))
                else:
                    filedate = datetime.datetime.now()

                # Fetch `Report category` argument.
                if request.form.get('1') != "undefined":
                    ftype = request.form.get('1')
                else:
                    ftype = "Others"

                # Request data from analyzer microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_report}/upload_report',
                    json={
                        'hash':hash,
                        'orig_filename': orig_filename,
                        'pure_filename': pure_filename,
                        'filesize': filesize,
                        'filedate': request.form.get('0'),
                        'ftype': ftype
                    }
                )
                
                # Logger
                log.logger.info('%s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return status code and response message.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400

        else:
            # Return status code and response message.
            return jsonify({"'detail": 'INVALID_PERMISSIONS'}), 403
            
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/upload_software_procurement', methods=['POST'])
@login_required
def upload_procurement():
    """
    Upload software procurement files
    
    :return: Response message and status code.
    :rtype: JSON
    """
    
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            file = request.files["file"]

            # Secure version of file name.
            orig_filename = secure_filename(file.filename)

            # Check for allowed file extension.
            if file and allowed_file_report(file.filename):

                # Fetching hash for file.
                hash = hashlib.md5(file.read()).hexdigest()
                
                # Cleaning file name and path.
                pure_filename = pathlib.Path(orig_filename).name
                pure_filename = pure_filename.replace(' ', '_')
                filename = pure_filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                print("file: ", file)
                file.save(filepath)
                print("file after saving: ", file)
                filesize = get_file_size_in_MB(filepath)

                #Fetch data from the request body
                data = json.loads(request.form.get('1'))

                # Request data from analyzer microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_report}/upload_software_procurement_report',
                    json={
                        'hash':hash,
                        'orig_filename': orig_filename,
                        'pure_filename': pure_filename,
                        'filesize': filesize,
                        "software_name": data['software_name'],
                        'purpose' : data['purpose'],
                        'software_price' : data['software_price'],
                        'approval_date' : data['approval_date'],
                        'purchase_date' : data['purchase_date'],
                        'current_status' : data['current_status'],
                        'remarks' : data['remarks']
                    }
                )
                
                # Logger
                log.logger.info('%s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return status code and response message.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail": 'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/software-procurement-list', methods=['POST'])
@login_required
def software_procurement_list():
    """
    List all software procurement files
    
    :return: Response data list along with pagination.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                if 'search' in  request.json:
                    search = request.json['search']
                else: search = ""

                r = requests.post(f'{settings.url_report}/software_procurement_list', 
                                  json = {
                                      'search': search,
                                      'page_id': request.json['page_id'],
                                      'starting_date' : request.json['starting_date'],
                                      'ending_date': request.json['ending_date']                             
                                }) 

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
                # return jsonify({'data_list': corpus_json, 'page_count': corpus_count}), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/archive-list', methods=['POST'])
@login_required
def archive_list():
    """
    List all archive files
    
    :return: Response data list along with pagination.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                if 'search' in  request.json:
                    search = request.json['search']
                else: search = ""

                r = requests.post(f'{settings.url_report}/report_list', 
                    json = {
                        'search': search,
                        'page_id': request.json['page_id'],
                        'starting_date' : request.json['starting_date'],
                        'ending_date': request.json['ending_date'],
                }) 

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
                # return jsonify({'data_list': corpus_json, 'page_count': corpus_count}), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/archive-download', methods=['GET'])
@login_required
def archive_download():
    """
    Download archive files
    
    :return: Downloaded file.
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_hash` from URL path parameter.
            f_hash = request.args.get('f_hash')
            
            uploads = os.path.join(current_app.root_path,current_app.config['UPLOAD_FOLDER'])

            r = requests.get(f'{settings.url_report}/report_download', json={'f_hash':f_hash})

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

            file_info = r.json()
            file_info = file_info['file']
            filename = file_info['filename']

            return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/software-report-download', methods=['GET'])
@login_required
def software_report_download():
    """
    Download software procurement files
    
    :return: Downloaded file.
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_hash` from URL path parameter.
            f_hash = request.args.get('f_hash')
            
            uploads = os.path.join(current_app.root_path,current_app.config['UPLOAD_FOLDER'])

            r = requests.get(f'{settings.url_report}/software_procurement_download', json={'f_hash':f_hash})

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

            file_info = r.json()
            file_info = file_info['file']
            filename = file_info['filename']

            return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/log-download', methods=['GET'])
@login_required
def log_download():
    """
    Download log files
    
    :return: Downloaded file.
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_hash` from URL path parameter.
            f_hash = request.args.get('fileHash')
            if f_hash == None:
                f_hash = request.args.get('f_hash')
            
            r = requests.get(f'{settings.url_ana}/log_download', json={'f_hash':f_hash})

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/log-delete', methods=['GET'])
@login_required
def log_delete():
    """
    Delete log files
    
    :return: Response data
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_hash` and `f_type` from URL path parameter.
            f_hash = request.args.get('f_hash')
            f_type = request.args.get('f_type')

            if f_type and f_hash:
                # Request data from analyzer microservice.
                r = requests.get(f'{settings.url_ana}/delete-log/{f_type}/{f_hash}', cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'ERR':'INVALID_REQUEST'}), 402
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/software-procurement-delete', methods=['GET'])
@login_required
def software_report_delete():
    """
    Delete record files
    
    :return: Response data
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_type` from URL path parameter.
            f_hash = request.args.get('f_hash')

            r = requests.get(f'{settings.url_report}/delete_software_procurement', json={'f_hash':f_hash})

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return status code and response message.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/archive-delete', methods=['GET'])
@login_required
def archive_delete():
    """
    Delete record files
    
    :return: Response data
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching data corresponding to `f_type` from URL path parameter.
            f_hash = request.args.get('f_hash')

            r = requests.get(f'{settings.url_report}/report_delete', json={'f_hash':f_hash})

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return status code and response message.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/export-software-report', methods=['POST'])
@login_required
def download_software_report():
    """
    Download the details of software report.
    
    :return: Response content containing details of the softwares along with total count of data.
    :rtype: JSON
    """
    try:
        if True:
            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_report}/download_software_report', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        print(e.msg())
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    

#########################
#### Suspicious Page ####
#########################

@main.route('/fetch-sus-data', methods=['GET'])
@login_required
def fetch_susdata():
    """Summary
    
    Returns:
        TYPE: Description
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            # Fetch data corresponding to `log_date` and `f_type` from URL path parameter.
            l_date = request.args.get('log_date')
            f_type = request.args.get('f_type')

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.get(f'{settings.url_ana}/sus_dash_uniq/{l_date}', cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400

@main.route('/fetch-ip-all', methods=['POST'])
@login_required
def fetch_ipall():
    """
    List all the history details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/sus_ip_modal', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

# Moved this API to the TOP 

# @main.route('/fetch-over-data', methods=['GET'])
# @login_required
# def fetch_overdata():
#     """
#     Overview page will retrieve all the data(PNRs Analyzed, PNRs Flagged, User Registrations Analyzed, User IDs Flagged, IP Addresses Blacklisted, Vulnerabilities Reported) as a json format.
    
#     :return: Response data
#     :rtype: JSON
#     """
#     try:
#         if True:
#             # Request data from analyzer microservice --> send cookie and current user email.
#             r = requests.get(f'{settings.url_ana}/over-data', cookies={
#                 "cookie" : request.headers['Cookie'], 
#                 "email": current_user.email
#             })

#             # Logger
#             log.logger.info('%s %s %s %s %s',
#                 current_user.email,
#                 request.method,
#                 request.full_path,
#                 request.headers['Cookie'].split(";")[0],
#                 request.headers['Cookie'].split(";")[1]
#             )

#             # Return all the data in JSON format.
#             return jsonify(r.json()), 200
        
#         else:
#             # Return status code and response message.
#             return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
#     except Exception as e:
#         # Return status code and response message.
#         return jsonify({'detail': 'INVALID_REQUEST'}), 400

@main.route('/fetch-sus-trend', methods=['GET', 'POST'])
@login_required
def fetch_sustrend():
    """Summary
    
    Returns:
        TYPE: Description
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for starting date in request.
            if 'std' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(
                    f'{settings.url_ana}/sus_dash_range', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/fetch-sus-pnrs', methods=['GET', 'POST'])
@login_required
def fetch_susonrs():
    """
    List all the booking details of suspected PNR.
    
    :return: Response data containing booking details of the suspected PNR along with total count of data.
    :rtype: JSON
    """

    try:
        if True:
            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/sus_pnr_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/download-sus-pnrs', methods=['POST'])
@login_required
def download_pnr():
    """
    Download the booking details of suspected PNR.
    
    :return: Response content containing booking details of the suspected PNR along with total count of data.
    :rtype: JSON
    """
    try:
        if True:
            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus}/sus_down_pnr', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        print(e.msg())
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/download-sus-ips', methods=['POST'])
@login_required
def download_ip():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus}/sus-down-ip', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    


@main.route('/download-ip-history', methods=['POST'])
@login_required
def download_ip_history():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus}/down-ip-history', json=request.json,cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email}
            )

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400

@main.route('/download-ip-modal', methods=['POST'])
@login_required
def download_ip_modal():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus}/down-ip-modal', json=request.json,cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email}
            )

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400



@main.route('/download-sus-users', methods=['POST'])
@login_required
def download_users():
    """
    Download the file for suspected users.
    
    :return: Response content containing booking details of the suspected users along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus}/sus-down-user', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400



@main.route('/fetch-sus-ips', methods=['GET', 'POST'])
@login_required
def fetch_susips():
    """
    List all the booking details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/sus_ip_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/fetch_ip_history', methods=['GET', 'POST'])
@login_required
def fetch_ip_history():
    """
    List all the booking details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/ip_history_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503



@main.route('/fetch-ip-history-modal', methods=['GET', 'POST'])
@login_required
def fetch_sus_ip_history_modal():
    """
    List all the booking details of suspected IPs.
    
    :return: Response data containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/fetch_ip_modal', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logging
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    


# @main.route('/delete-sus-ips', methods=['GET', 'POST'])
# def delete_susips():
#     """Summary
    
#     Returns:
#         TYPE: Description
#     """
#     if in request.json:
#         r = requests.post(f'{settings.url_sus}/sus_ip_list', json=request.json)
#         return jsonify(r.json()), 200
#     else:
#         return jsonify({'detail': 'INVALID_REQUEST'}), 400


@main.route('/fetch-sus-user', methods=['GET', 'POST'])
@login_required
def fetch_sususer():
    """
    List all the booking details of suspected user.
    
    :return: Response content containing booking details of the suspected users along with total count of data.
    :rtype: JSON
    """

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `page_id` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/sus_user_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/change-user-status', methods=['GET', 'POST'])
@login_required
def change_user_status():
    """
    Block or ignore the selected suspicious user.
    
    :return: Response with the message that user status is changed.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `userid` in request.
            if 'userid' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/change-status-user', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/block-users-date', methods=['GET', 'POST'])
@login_required
def date_block_user():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'block_date' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/block-user-date', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/fetch-pnr-comments', methods=['POST'])
@login_required
def fetch_pnr_comment():
    """
    List all the comment details for the suspected PNR.
    
    :return: Response data containing list of comments.
    :rtype: JSON
    """

    try:
        if True:
            # Check for `pnr_no` in request.
            if 'pnr_no' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/fetch-comment-pnr', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/submit-pnr-comment', methods=['POST'])
@login_required
def submit_pnr_comment():
    """
    Add the comment for the suspected PNR.
    
    :return: Response data for submitted comment.
    :rtype: JSON
    """

    try:
        if True:
            # Check for `pnr_no` and `comment` in request.
            if 'pnr_no' in request.json and 'comment' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/submit-comment-pnr', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/delete-pnr-comment', methods=['POST'])
@login_required
def delete_pnr_comment():
    """
    Delete the comment for the suspected PNR.
    
    :return: Response data for deleted comment.
    :rtype: JSON
    """

    try:
        if True:
            # Check for `block_date` in request.
            if 'block_date' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus}/block-user-date', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
        
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


# CASE MANAGEMENT

@main.route('/case_pnr_data', methods=['POST'])
@login_required
def case_pnr_history():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/pnr_case_data', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
    
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/overview-severity', methods=['POST'])
@login_required
def overview_severity():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/overview-severity-total', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    
@main.route('/overview-weekly', methods=['POST'])
@login_required
def overview_weekly():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/overview-weekly-stats', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/overview-main', methods=['POST'])
@login_required
def overview_main():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            if 'page_id' in request.json:
                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/overview-main', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/case_pnr_data_detail', methods=['POST'])
@login_required
def case_pnr_history_detail():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'pnr_number' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/pnr_case_data_detail', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/overview-status-update', methods=['POST'])
@login_required
def overview_status():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'username' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/overview-status-update', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200
            
            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503

@main.route('/case_overview_detail', methods=['POST'])
@login_required
def case_overview_detail():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'username' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_sus_history}/overview_case_detail', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200

            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/overview_case_detail_export', methods=['POST'])
@login_required
def case_overview_detail_export():
    """
    Download the file for suspected IPs.
    
    :return: Response content containing booking details of the suspected IPs along with total count of data.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_sus_history}/case_detail_export', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email}
            )

            # # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the content.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
            
    except Exception as e:
        # Return status code and response message.
        return jsonify({'detail': 'INVALID_REQUEST'}), 400
    
# TOUT SECTION
@main.route('/tout_data_upload', methods=['POST'])
@login_required
def upload_tout_data():
    """
    Upload archive files
    
    :return: Response message and status code.
    :rtype: JSON
    """

    try: 
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Fetching the file.
            try:
                file = request.files["file"]

                # Secure version of file name.
                orig_filename = secure_filename(file.filename)

                # Check for allowed file extension.
                if file and allowed_file_logs(file.filename):

                    # Fetching hash for file.
                    hash = hashlib.md5(file.read()).hexdigest()
                    
                    # Cleaning file name and path.
                    pure_filename = pathlib.Path(orig_filename).name
                    pure_filename = pure_filename.replace(' ', '_')
                    filename = pure_filename
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.seek(0)
                    file.save(filepath)
                    files = {'file': open(filepath, 'rb')}

                    # Request data from analyzer microservice --> send cookie and current user email.
                    r = requests.post(f'{settings.url_bm}/upload_tout_data', files=files)
                    
                    # Logger
                    log.logger.info('%s %s %s %s %s',
                        current_user.email,
                        request.method,
                        request.full_path,
                        request.headers['Cookie'].split(";")[0],
                        request.headers['Cookie'].split(";")[1]
                    )

                    # Return status code and response message.
                    return jsonify(r.json()), 200
                
                else:
                    # Return status code and response message.
                    return jsonify({'detail': 'FILEUPLOAD_EXTENSION_NOT_ALLOWED'}), 400
            except Exception as e:
                print(e.msg())

        else:
            # Return status code and response message.
            return jsonify({"'detail": 'INVALID_PERMISSIONS'}), 403
            
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/tout_card_detail', methods=['POST'])
@login_required
def tout_detail():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Check for `block_date` in request.
            if 'page_id' in request.json:

                # Request data from sus microservice --> send cookie and current user email.
                r = requests.post(f'{settings.url_bm}/tout_card_list', json=request.json, cookies={
                    "cookie" : request.headers['Cookie'], 
                    "email": current_user.email
                })

                # Logger
                log.logger.info('%s %s %s %s %s %s',
                    current_user.email,
                    request.method,
                    request.full_path,
                    request.data,
                    request.headers['Cookie'].split(";")[0],
                    request.headers['Cookie'].split(";")[1]
                )

                # Return all the data in JSON format.
                return jsonify(r.json()), 200

            else:
                # Return status code and response message.
                return jsonify({'detail': 'INVALID_REQUEST'}), 400

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/export_tout_details', methods=['GET', 'POST'])
@login_required
def export_tout_data():

    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            r = requests.post(f'{settings.url_bm}/tout_data_export', json=request.json
                              , cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            }
            )

            # Logging
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return r.content, 200
            
        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403
        
    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503


@main.route('/overview_top_web', methods=['POST'])
@login_required
def top_web():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():
            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_bm}/web_status_overview', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except:
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503
    

@main.route('/overview_top_software', methods=['POST'])
@login_required
def top_software():
    """
    Block all the suspicious users for the given date.
    
    :return: Response data with the message.
    :rtype: JSON
    """
    try:
        # Check if current user belongs to board, irctc or pinaca department.
        if 'board' in current_user.department.lower() or 'irctc' in current_user.department.lower() or 'pinaca' in current_user.department.lower() or 'it' in current_user.department.lower():

            # Request data from sus microservice --> send cookie and current user email.
            r = requests.post(f'{settings.url_report}/overview_software_list', json=request.json, cookies={
                "cookie" : request.headers['Cookie'], 
                "email": current_user.email
            })

            # Logger
            log.logger.info('%s %s %s %s %s %s',
                current_user.email,
                request.method,
                request.full_path,
                request.data,
                request.headers['Cookie'].split(";")[0],
                request.headers['Cookie'].split(";")[1]
            )

            # Return all the data in JSON format.
            return jsonify(r.json()), 200

        else:
            # Return status code and response message.
            return jsonify({"'detail":'INVALID_PERMISSIONS'}), 403

    except Exception as e:
        print(e.msg())
        # Return status code and response message.
        return jsonify({'detail': 'INTERNAL_SERVER_ERROR'}), 503