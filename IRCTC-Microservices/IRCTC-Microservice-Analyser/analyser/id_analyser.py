# Import required modules.

import os
import re
import time
import json
import string
import random
import polars
import pandas
import openpyxl
import requests
import datetime
import icecream
import itertools
import xlsxwriter
import Levenshtein
import concurrent.futures
from dateutil import parser
from mongo_connection import *
from ip_analyser import IPAnalyser
from collections import defaultdict
from gchat_notification import notify_gchat
from mapping_data import map_userid_tags, map_rfi_tags, map_vps_tags

class IDAnalyser:

    def __init__(self, file_location, analysed_file_reference=''.join(random.choices(string.ascii_lowercase + string.digits, k = 32))) -> None:
        
        self.base_dir = os.path.expanduser('~')

        # List to store the vendors ip address.
        self.vendors_list = polars.read_csv(self.base_dir + "/Databases/VENDOR_IP_LIST.csv")["IP_ADDRESS"].to_list()

        # List to store the whitelisted subnets.
        self.whitelisted_subnets_file = self.base_dir + "/Databases/WHITELISTED_SUBNETS.csv"

        self.vendors_file = self.base_dir + "/Databases/vendors.xlsx"

        # List to store the government asn.
        self.govt_asn = polars.read_csv(self.base_dir + "/Databases/GOVT_ASNS.csv")["ASN"].to_list()

        # initialise starting time to calculate overall operating time
        self.time_calc = time.time()

        # Path of the file to analyse.
        self.file_path = file_location

        self.low_severity_users = 0

        self.medium_severity_users = 0

        self.high_severity_users = 0

        self.low_severity_sus_ips = 0

        self.medium_severity_sus_ips = 0
        
        self.high_severity_sus_ips = 0

        # Initialize the initial value of the 'file_date' as None.
        self.file_date = None
        
        '''
            Default dictionary to store all the details related to the particular ip address.

            dtype: dict
            key: ip address
            value: dict
                : Key: USER_COUNT : value: int
                : key: EMAIL : value: str
                : key: USERNAME : value: str
                : key: FULLNAME : value: str
                : key: ADDRESS : value: str
                : key: REGISTRATION_DATETIME : value: datetime
        '''
        self.ip_data = defaultdict(dict)

        '''
            Default dictionary to store all the suspected ip addresses and their corresponding suspected tags.

            dtype: dict
            key: ip address
            value: list of tags.
        '''
        self.sus_ips = defaultdict(list)
        '''
            Default dictionary to store all the suspected users and their corresponding suspected tags.

            dtype: dict
            key: username
            value: {list of tags, user id, ip address and email}
        '''
        self.sus_users = defaultdict(dict)

        # Count of tickets booked using vendor ip addresses.
        self.vendor_ticket_count = 0

        # Count of tickets booked using vps.
        self.vps_ticket_count = 0

        # Dictionary to store the VPS ASN related details.
        self.vps_asn = dict()

        # Dictionary to store the NON VPS ASN related details.
        self.non_vps_asn = dict()

        # Dictionary to store the NON VPS IP related details.
        self.non_vps_ip = dict()

        # Dictionary to store the VPS IP related details.
        self.vps_ip = dict()

        # Dictionary to store the vendor records related details.
        self.vendor_users = dict()

        # Dictionary to store the ASN related details.
        self.asn_data = dict()

        # Stores unique ip addresses that uses VPS.
        self.vps_ip_pool = set()

        self.sus_mobile_set = set()

        # Dictionary to store the details of the daily log analysis for the dashboard.
        self.user_trend_data = dict()

        # List of the all the unique ip addresses from the sheet.
        # Used in IP Analyser to fetch ip address details.
        self.ip_all_list = list()

        # Initialize the initial value of the sheet dataframe with None
        self.data_df = None

        # list of dictionary to store vendor details from the vendor details file to analyse the user id file
        self.vendor_data = self.vendors()

        # Variable to store the JSON data of the uploaded file.
        self.file_raw_json_data = self.convert_to_json()

        # Unique hash value generated for the particular file.
        self.analysed_file_reference = analysed_file_reference

        # data to store disposable email domains from API
        self.disposable_email_data_from_api = None

        '''
            Default dictionary to store all the emails along with their username.

            dtype: dict
            key: emails
            value: list of usernames
        '''
        self.email_username_data = defaultdict(list)

        '''
            Default dictionary to store all the fullnames along with their username.

            dtype: dict
            key: conactenated fullname
            value: list of usernames
        '''
        self.fullname_username_data = defaultdict(list)
        
        '''
            Default dictionary to store all the address along with their username.

            dtype: dict
            key: concatenated address
            value: list of usernames
        '''
        self.address_username_data = defaultdict(list)

        self.office_phone_username = defaultdict(list)

        # list to store username of unverified users
        self.unverified_users = list()

        # Create instance for IP Analyser.
        self.ip_analyzer = IPAnalyser()

        '''
           Get all the hosting details of the ip address from the IP Analyser.

           dtype: dict
           value: dict
                : key: COUNTRY : value: str
                : key: ISP : value: str
                : key: ASN : value: str
                : key: VPS : value: boolean
        '''
        self.ip_overall_info = self.ip_analyzer.maxmind(self.ip_all_list)

        # Parse the uploaded file for further analysis.
        self.parse_file()

        # Data of USERS along with their IP and further details
        self.users_data = self.user_data()

        # Data of users along with their username, email and suspected tags for analyzed sheet.
        self.sus_users_data = self.sus_user_data()

        # Generate the final sheet data to be exported as result
        self.generate_sheet_data()

    def generate_sheet_data(self) -> None:
        '''
           Generate excel sheet of the analyzed USER data.
        '''
        msg_str = f"GENERATING DATAFRAME SHEET: {self.file_date} : USER"
        icecream.ic(msg_str)

        # Convert the fetched data into dataframes
        self.users_data = polars.DataFrame(self.users_data)
        self.sus_users_data = polars.DataFrame(self.sus_users_data)

        msg_str = f"DATAFRAMES GENERATED: {self.file_date} : USER"
        icecream.ic(msg_str)

        # Convert dataframes into separate sheets in excel file
        with xlsxwriter.Workbook("download_reports/" + self.analysed_file_reference+".xlsx") as writer:
            self.users_data.write_excel(workbook=writer,worksheet="IP WITH USERID")   
            self.sus_users_data.write_excel(workbook=writer,worksheet="SUSPICIOUS USERIDS")       
        
        col_file_handle.update_one({'hash':self.analysed_file_reference},  { "$set": { 'status': 'Processed' } },upsert=True)
        notify_gchat(f"USER File analysed : {self.file_date}")
        print("USER ID: ",self.file_date,": ", (time.time() - self.time_calc)/60)


    def convert_to_json(self) -> dict:
        '''
           Check the extension of the uploaded file and convert its data into JSON.

           :return: list of dictionaries
           :rtype: list
        '''
        msg_str = f"CONVERTING FILE TO JSON DATA: {self.file_date} : USER"
        icecream.ic(msg_str)

        # Read the file based on extension : Excel or CSV
        if self.file_path.endswith('.xlsx') or self.file_path.endswith('.xls'):

            # Load the workbook.
            workbook = openpyxl.load_workbook(self.file_path)

            # Trcker to store each row in dictionary format.
            sheet_data = list()
            
            # Get the first sheet from the workbook.
            worksheet = workbook.worksheets[0]

            # Get the headers of the columns.
            keys = [i for i in list(worksheet.values)[0] if i is not None]

            # Iterate over each row.
            for row in worksheet.values:

                # Get the row values.
                values = [i for i in list(row)]

                # Check if values are not equal to the heders.
                if values != keys:

                    # Map value with its corresponding header value.
                    data = dict(zip(keys,values))

                    # Add the record in the tracker list.
                    sheet_data.append(data)

                    # Populate all the ip addresses in a list.
                    self.ip_all_list.append(data['IP_ADDRESS'])
            
            # Return the list of dictionary containing the sheet data.
            return sheet_data
        
    def vendors(self):
        """
           Parse vendors details file and store it to access locally
        
           return: list of dictionarie
           rtype: list
        """
        
        # Convert the vendors data file in to pandas dataframe.
        self.vendor_df = pandas.read_excel(self.vendors_file)
        
        # Convert the dataframe into json records and return it.
        return eval(self.vendor_df.to_json(orient='records'))
    
    def fetch_vendor_data(self, ip_address):

        """
           Fetch and return vendor details based

           :param ip_address: IP_ADDRESS along which vendor data is to fetched.
           :ptype: str

           :return: dictionary conatining vendors data.
           :rtype: dict
        """
        
        # Iterate over the vendors data records.
        for data in self.vendor_data:

            # Check if the `ip_address` exists in the records
            if ip_address in data['IP_ADDRESSES']:

                # Return the vendor data along the `ip_address` found.
                return data
            
        # Return empty dictionary if no data is found.
        return {}
        
    def populate_data(self, row):
        '''
           Update row wise sheet data, ip overall data for parameter analysis and ASN data.

           :param row: contains single row data of the sheet.
           :ptype: dict

           :return :Message that the data is updated successfully or error message if any.
           :rtype: str
        '''

        try:
            # Get the 'REGISTRATION_DATE' from the row.
            reg_date = row["REGISTRATION_DATE"]
            
            # Check if the REGISTRATION_DATE is in 'int' format --> convert it into datetime format.
            if isinstance(reg_date, int):
                reg_date = datetime.datetime.fromtimestamp(reg_date/1e3)

            # Check if the REGISTRATION_DATE is in 'str' format --> convert it into datetime format.
            if isinstance(reg_date, str):

                # define multiple format conversions to handle different encountered cases
                try:
                    try:
                        reg_date = datetime.datetime.strptime(reg_date, "%d-%b-%y %H:%M:%S.%f %p")
                    except:
                        try:
                            reg_date = datetime.datetime.strptime(reg_date, "%d/%m/%Y %H:%M:%S")
                        except:
                            reg_date = datetime.datetime.strptime(reg_date, "%d\\/%m\\/%Y %H:%M:%S")
                except:
                    reg_date = datetime.datetime.strptime(reg_date, "%d-%m-%Y %H:%M:%S")
            
            # Check for misinterpretation between 'day' and 'month' when date is less than `12` in REGISTRATION_DATE.
            if reg_date.day <= 12:

                # Store the `date` from the current 'REGISTRATION_DATE'  from the row in th temp variable.
                temp_date = datetime.datetime.combine(reg_date.date(), datetime.time.min)

                # Check if data corresponding to the 'REGISTRATION_DATE' already exists or if the 'REGISTRATION_DATE' read is greater than the current date.
                if (col_userid_handle.count_documents({
                    "REGISTRATION_DATETIME" : {
                        '$gte' : temp_date, 
                        '$lt' : temp_date + datetime.timedelta(days=1)
                    }}) > 0) or (reg_date.date() > datetime.datetime.now().date()):
                    
                    # Stores the current 'REGISTRATION_DATE' into a variable.
                    curr_reg_date = reg_date
                    
                    # Convert the current 'REGISTRATION_DATE' into datetime string format.
                    curr_reg_date = curr_reg_date.strftime("%d%m%Y %I:%M:%S")

                    # Defines the format for the new format.
                    time_format = "%m%d%Y %I:%M:%S"

                    # Interchange the 'month' with the 'day' and 'day' with the 'month'.
                    reg_date = datetime.datetime.strptime(curr_reg_date,time_format)
            
            # Replace the 'REGISTRATION_DATETIME' value in the row with the updated 'REGISTRATION_DATE' value.
            row["REGISTRATION_DATETIME"] = reg_date

            # delete the original key 'REGISTRATION_DATE' to manage consistency with existing database
            del row["REGISTRATION_DATE"]
            
            # Update the 'file_date' value.
            if self.file_date == None:
                self.file_date = datetime.datetime.combine(reg_date.date(), datetime.time.min)

            # Update the 'IP_ADDRESS' of the row into the 'str' data type.
            row["IP_ADDRESS"] = str(row["IP_ADDRESS"])
            # row["USERNAME"] = str(row["USERNAME"])

            # Update the 'USERNAME' of the row into the 'str' data type.
            try:
                if ((isinstance(row["USERNAME"], str)==False) and (isinstance(row["USERNAME"], int))): 
                    # read the datetime format and convert to equivalent string value
                    try:
                        row["USERNAME"] = datetime.datetime.fromtimestamp(row["USERNAME"]/1e3)
                        row["USERNAME"] = row["USERNAME"].strftime("%b-%y")
                    except:
                        row["USERNAME"] = datetime.datetime.fromtimestamp(row["USERNAME"]/1e3)
                        row["USERNAME"] = row["USERNAME"].strftime("%b/%y")

                elif (isinstance(row["USERNAME"], datetime.datetime)):
                    try:
                        row["USERNAME"] = row["USERNAME"].strftime("%b-%y")
                    except:
                        row["USERNAME"] = row["USERNAME"].strftime("%b/%y")

                elif ("/" in row['USERNAME'] or "-" in row['USERNAME']) and row['USERNAME'].isalpha() != True:
                    try:
                        date_str = parser.parse(row["USERNAME"])
                        row["USERNAME"] = date_str.strftime("%b-%y")
                    except:
                        date_str = parser.parse(row["USERNAME"])
                        row["USERNAME"] = date_str.strftime("%b/%y")

                else:
                    row["USERNAME"] = str(row["USERNAME"])

            except Exception as e:
                row["USERNAME"] = str(row["USERNAME"])
            

            # get the corresponding vendor details for the IP Address if exists
            vendor_data = self.fetch_vendor_data(row['IP_ADDRESS'])
            
            # Update the row with the 'IP_ADDRESS' details from the IP Analyser and Vendor details.
            row.update({
                "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
                "ISP" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("ISP"),
                "ASN" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("ASN"),
                "VPS" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("VPS"),
                "COUNTRY" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("COUNTRY"),
                "VENDOR_REGISTRATION": True if row['IP_ADDRESS'] in self.vendors_list else False,
                'VENDOR_ID': vendor_data['MASTER_USER_ID'] if vendor_data != {} else "N.A",
                'VENDOR_NAME': vendor_data['COMPANY_NAME'] if vendor_data != {} else "N.A",
                'VENDOR_CODE': vendor_data['USER_LOGINID'] if vendor_data != {} else "N.A",
                'ADDRESS' : str(row['ADDRESS']),
                'STREET' : str(row['STREET']),
                'COLONY' : str(row['COLONY']),
                'DISTRICT': str(row['DISTRICT']),
                'POSTOFFICE' : str(row['POSTOFFICE']),
                'STATE': str(row['STATE']),
                'PIN_CODE': str(row['PIN_CODE']),
                'FIRST_NAME': str(row["FIRST_NAME"]),
                'MIDDLE_NAME': str(row["MIDDLE_NAME"]),
                'LAST_NAME': str(row['LAST_NAME'])
            })

            row['REGISTERED_MOBILE'] = str(row['REGISTERED_MOBILE']).split(".")[0]

            row['OFFICE_PHONE'] = str(row['OFFICE_PHONE']).split(".")[0]

            # Check if the 'IP_ADDRESS' does not existes in vendor list, government asn list.
            if (row['IP_ADDRESS'] not in self.vendors_list) and (row["ASN"] not in self.govt_asn):

                # concatenate fullname and address into one string from multiple distributed parts
                full_name = (str(row["FIRST_NAME"]) if row['FIRST_NAME'] != "" else "") + " " + (str(row["MIDDLE_NAME"]) if row['MIDDLE_NAME'] != "" else "") + " " + (str(row["LAST_NAME"]) if row['LAST_NAME'] != "" else "")

                address = (str(row["ADDRESS"]) if row["ADDRESS"] != "" else "") + " " + (str(row["STREET"]) if row["STREET"] != "" else "") + " " + (str(row["COLONY"]) if row["COLONY"] != "" else "") + " " +  (str(row["DISTRICT"]) if row["DISTRICT"] != "" else "") + " " + (str(row["POSTOFFICE"]) if row["POSTOFFICE"] != "" else "") + " " + (str(row["STATE"]) if row["STATE"] != "" else "") + " " + (str(row["PIN_CODE"]) if row["PIN_CODE"] != "" else "")
                
                # Update the variable 'self.ip_data' for the the parameter analysis.
                # Update the record if it already exists.
                if row["IP_ADDRESS"] in  self.ip_data.keys():
                    self.ip_data[row["IP_ADDRESS"]]['USER_COUNT'] += 1
                    self.ip_data[row["IP_ADDRESS"]]['REGISTRATION_DATETIME'].append(row["REGISTRATION_DATETIME"])
                    self.ip_data[row["IP_ADDRESS"]]['USERNAME'].append(row["USERNAME"])
                    self.ip_data[row["IP_ADDRESS"]]['EMAIL'].append(row["EMAIL"])
                    self.ip_data[row["IP_ADDRESS"]]['FULL_NAME'].append(full_name)
                    self.ip_data[row["IP_ADDRESS"]]['ADDRESS'].append(address)
                
                # Insert the record if it does not exists.
                else:
                    self.ip_data[row["IP_ADDRESS"]] = {
                        'USER_COUNT' : 1,
                        'REGISTRATION_DATETIME' : [row["REGISTRATION_DATETIME"]],
                        'USERNAME' : [row["USERNAME"]],
                        'EMAIL' : [row["EMAIL"]],
                        'FULL_NAME' : [full_name],
                        'ADDRESS' : [address],
                        'VPS' : self.ip_overall_info[row["IP_ADDRESS"]]["VPS"]
                    }

                # POPULATE ASN DATA.
                # Insert the record if it does not exists.
                if row['ASN'] not in self.asn_data:
                    self.asn_data[row['ASN']] = {
                        'ASN': row['ASN'], 
                        'USER_COUNT': 1, 
                        'ISP': row['ISP'], 
                        'VPS': row.get('VPS', False), 
                        'COUNTRY': row['COUNTRY']
                    }
                
                # Update the record if it already exists.
                else:
                    self.asn_data[row['ASN']]['USER_COUNT'] += 1

                '''
                    Update dictionary to store all the users and their userid with empty tags list (to be updated during parameter analysis).

                    dtype: dict
                    key: username
                    value: {empty list of tags, ip address, email and userid}
                '''
                self.sus_users[row["USERNAME"]] = {
                    "USER_ID" : row["USER_ID"],
                    'IP_ADDRESS' : row['IP_ADDRESS'],
                    'EMAIL' : row['EMAIL'],
                    "TAGS" : set()
                }

                # store the username in unverified list if it is unverified.
                if row['VERIFIED'] == 0:
                    self.unverified_users.append(row['USERNAME'])

                # update vps related data if IP Address is using VPS
                if row['VPS'] == True: 

                    # update VPS count
                    self.vps_ticket_count += 1

                    # add the IP Address into VPS pool
                    self.vps_ip_pool.add(row['IP_ADDRESS'])

                    # update VPS ASN details.
                    # Insert the record if it does not exists.
                    if row['ASN'] not in self.vps_asn:
                        self.vps_asn[row['ASN']] = {
                            'ASN': row['ASN'], 
                            'ISP': row['ISP'], 
                            'VPS': row['VPS'], 
                            'COUNTRY': row['COUNTRY'], 
                            'TK_COUNT': 1
                        }

                    else:
                        # Update the record if it already exists.
                        self.vps_asn[row['ASN']]['TK_COUNT'] += 1

                    # update VPS IP details.
                    # Insert the record if it does not exists.
                    if row['IP_ADDRESS'] not in self.vps_ip:
                        self.vps_ip[row['IP_ADDRESS']] = {
                            'IP': row['IP_ADDRESS'], 
                            'ISP': row['ISP'],
                            'ASN': row['ASN'], 
                            'VPS': row['VPS'], 
                            'COUNTRY': row['COUNTRY'], 
                            'TK_COUNT': 1
                        }

                    else:
                        # Update the record if it already exists.
                        self.vps_ip[row['IP_ADDRESS']]['TK_COUNT'] += 1
                
                # update non vps related data if IP Address is using VPS
                else:

                    # update NON VPS ASN details
                    if row['ASN'] not in self.non_vps_asn:
                        self.non_vps_asn[row['ASN']] = {
                            'ASN': row['ASN'], 
                            'ISP': row['ISP'], 
                            'VPS': row['VPS'], 
                            'COUNTRY': row['COUNTRY'], 
                            'TK_COUNT': 1
                        }

                    else:
                        self.non_vps_asn[row['ASN']]['TK_COUNT'] += 1

                    # update NON VPS IP details
                    if row['IP_ADDRESS'] not in self.non_vps_ip:
                        self.non_vps_ip[row['IP_ADDRESS']] = {
                            'IP': row['IP_ADDRESS'], 
                            'ISP': row['ISP'],
                            'ASN': row['ASN'], 
                            'VPS': row['VPS'], 
                            'COUNTRY': row['COUNTRY'], 
                            'TK_COUNT': 1
                        }

                    else:
                        self.non_vps_ip[row['IP_ADDRESS']]['TK_COUNT'] += 1

                # store username corresponding to address, fullname and email as keys for further analysis
                self.email_username_data[row["EMAIL"]].append(row["USERNAME"])
                self.fullname_username_data[full_name].append(row["USERNAME"])
                self.address_username_data[address].append(row["USERNAME"])
                self.office_phone_username[row['OFFICE_PHONE']].append(row['USERNAME'])

            # Check if the 'IP_ADDRESS' exists in vendor list
            elif row['IP_ADDRESS'] in self.vendors_list:
                # increment the count of tickets booked through VENDORS
                self.vendor_ticket_count += 1
                
                # updta ethe vendor data if user is registered through vendor
                if vendor_data != {}:
                    if vendor_data['MASTER_USER_ID'] not in self.vendor_users:
                        self.vendor_users[vendor_data['MASTER_USER_ID']] = {
                            'VENDOR_ID': vendor_data['MASTER_USER_ID'], 
                            'VENDOR_NAME': vendor_data['COMPANY_NAME'], 
                            'TK_COUNT': 1
                        }
                    else:
                        self.vendor_users[vendor_data['MASTER_USER_ID']]['TK_COUNT'] += 1
              
            # Update the IP Address collection to store the details of all the IP Address
            col_ip_handle.update_one({
                'IP_ADDRESS':row['IP_ADDRESS']
            }, {
                '$set': {
                    'VPS': row['VPS'],
                    'ISP': row['ISP'],
                    'ASN': row['ASN'],
                    'COUNTRY': row['COUNTRY'],
                    'VENDOR_IP': row['VENDOR_REGISTRATION']
                }
            }, upsert=True)

            return f"{row['IP_ADDRESS']} updated"
        
        except Exception as e:
            # return exception if any occurs
            notify_gchat(f"USER : {self.file_date} : {repr(e)}")
            return e.msg()


    def parse_file(self):
        '''
            Central function to call all the other functions and populate data into database.
                1) Populate data for daily log analysis.
                2) Insert USER data into database.
                3) Do parameter analysis.
                4) Updated suspected tags into the database
        '''

        ## Parse the JSON records and populate temporary data for further analysis.
        msg_str = f"PARSING AND POPULATING THE DATA: {self.file_date} : USER"
        icecream.ic(msg_str)

        # ThreadPool to populate IP Address Data for each row of the records
        with concurrent.futures.ThreadPoolExecutor() as executor:

            # Submit task to the executor for each records in JSON data.
            future_data = {executor.submit(self.populate_data, json_data): json_data for json_data in self.file_raw_json_data}

            # Iterate over the futures to get the results.
            for future in concurrent.futures.as_completed(future_data):
                
                # Get future object from all the future objects.
                url = future_data[future]

                try:
                    # Get result from the future object.
                    data = future.result()

                # Raise exception message if occured.
                except Exception as exc:
                    notify_gchat(f"USER : {self.file_date} : {repr(exc)}")
                    print(exc.msg())

        msg_str = f"IP DATA POPULATED: {self.file_date} : USER"
        icecream.ic(msg_str)
        
        # INSERT raw JSON data into Database before analysis
        self.insert_into_database()
        msg_str = f"USER DATA INSERTED INTO DATABASE:: {self.file_date} : USER"
        icecream.ic(msg_str)

        msg_str = f"ANALYZING SUSPECTED : {self.file_date} : USER"
        icecream.ic(msg_str)

        # Analysing the data based on multiple parameters
        self.all_parameter_analysis()
        msg_str = f"PARAMETER ANALYSIS COMPLETED: {self.file_date} : USER"
        icecream.ic(msg_str)

        # calculate the trend data wrequired for overview on the dashboard
        self.user_trend_data_update()

        # update analysed records and suspected tags into the db 
        self.update_into_database()

    def insert_into_database(self):
        '''
           Function to populate data into database.
        '''
        
        try:
            # Insert all the USER raw records into the database before analysis.
            col_userid_handle.insert_many(self.file_raw_json_data, ordered=False)
        
        except pymongo.errors.BulkWriteError as e:
            for error in e.details.get('writeErrors', []):
                if error.get('code') == 11000:
                    pass

    def all_parameter_analysis(self):
        '''
           Analyze all the RFI(RED FLAG INDICATORS) parameters and update the suspected users and ip address.
        '''
        # for each IP Address in the data file
        for ip_address in self.ip_data.keys():
            
            # User count for the IP Address based on which parameters are applied
            user_count = self.ip_data.get(ip_address).get('USER_COUNT')
        
            # below parameters are checked if IP Address is used more than 4 times.
            if user_count >= 4:

                # PARAM 1 - Check for Similarity in emails or Gibberish email.
                self.check_gibberish_email(ip_address)
                
                # PARAM 2 - Check for Similarity in usernames or Gibberish username.
                self.check_gibberish_username(ip_address)
                
                # PARAM 3 - Check for registration time difference if less than 60 seconds.
                self.check_sus_reg_date(ip_address)
                         
            # below parameters are checked if IP Address is used more than 5 times.
            if user_count >= 5:

                # PARAM 4 - Check for Similarity in fullnames or Gibberish fullname.
                self.check_suspicious_fullname(ip_address)
                
                # PARAM 5 - Check for Similarity in address or Gibberish address.
                self.check_suspicious_address(ip_address)
            
                # PARAM 6 - Check for same fullname for multiple users.
                self.check_same_fullname(ip_address)
                
                # PARAM 7 - Check for same address for multiple users.
                self.check_same_address(ip_address)
        
        # PARAM 8 - Check for Unverified users.
        self.unverified_user()

        # PARAM 9 - Check for Disposable email IDs
        self.disposable_domain()

        self.check_suspicious_mobile()

        self.check_same_ip_pool()

        

    def calculate_similarity_ratio(self, pair : tuple, threshold : float):
        '''
            Check similarity ratio between two pairs based on the threshold value.

           :param pair: pair between which similarity ratio is to be checked.
           :ptype: tuple

           :param threshold: comparison threshold value between two pairs.
           :ptype: float

           :return: pairs which meet the threshold value None otherwise
           :rtype: tuple
           :rtypr: None
        '''
        
        # Calculate the Levenshtein distance for the pairs of usernames
        len_diff = abs(len(pair[0]) - len(pair[1]))
        if len_diff <= 2 * threshold:
            distance = Levenshtein.distance(pair[0], pair[1])
            max_length = max(len(pair[0]), len(pair[1]))
            similarity_ratio = 1 - (distance / max_length)

            # similarity ratio >= threshold (85% similar) -> return the usernames
            if similarity_ratio >= threshold:
                return (pair[0], pair[1])
        return None
    
    def check_gibberish_email(self, ip_address : str):
        '''
           Check for similarity between the emails along the ip_address and flag those whose similarity ratio is greater than or equal to the threashold value.

           :param ip_address: ip_address details that meet the 
        '''

        # initialise chunk size and minimum threshold for similarity
        chunk_size = 500
        threshold = 0.85

        # email list corresponding to the IP Address
        email_list = self.ip_data.get(ip_address).get("EMAIL")

        for index in range(0, len(email_list), chunk_size):

            # create username chunks
            chunk = email_list[index:index+chunk_size]
            pairs = list(itertools.combinations(chunk,2))

            # for each pair calculate similarity ratio
            result = [pair for pair in pairs if self.calculate_similarity_ratio(pair, threshold) is not None]

            # for emails returned (passed threshold check) 
            # add each username to dictionary of suspicious ones with the corresponding tag for the parameter.
            for res in result:
                if res != None:

                    for username in self.email_username_data[res[0]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_EMAIL")
                    for username in self.email_username_data[res[1]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_EMAIL")

    def check_gibberish_username(self, ip_address):

        # initialise chunk size and minimum threshold for similarity
        chunk_size = 500
        threshold = 0.85

        # username list corresponding to the IP Address
        username_list = self.ip_data.get(ip_address).get("USERNAME")

        for index in range(0, len(username_list), chunk_size):

            # create username chunks
            chunk = username_list[index:index+chunk_size]
            pairs = list(itertools.combinations(chunk,2))

            # for each pair calculate similarity ratio
            result = [pair for pair in pairs if self.calculate_similarity_ratio(pair, threshold) is not None]

            # for usernames returned (passed threshold check) 
            # add each username to dictionary of suspicious ones with the corresponding tag for the parameter.
            for res in result:
                if res != None:

                    self.sus_users[res[0]]["TAGS"].add("GIBBERISH_USERNAME")
                    self.sus_users[res[1]]["TAGS"].add("GIBBERISH_USERNAME")

    def check_suspicious_fullname(self, ip_address):
        # initialise chunk size and minimum threshold for similarity
        chunk_size = 500
        threshold = 0.85

        # fullname list corresponding to the IP Address
        fullname_list = self.ip_data.get(ip_address).get("FULL_NAME")

        for index in range(0, len(fullname_list), chunk_size):

            # create username chunks
            chunk = fullname_list[index:index+chunk_size]
            pairs = list(itertools.combinations(chunk,2))

            # for each pair calculate similarity ratio
            result = [pair for pair in pairs if self.calculate_similarity_ratio(pair, threshold) is not None]

            # for fullnames returned (passed threshold check) 
            # add each username to dictionary of suspicious ones with the corresponding tag for the parameter.
            for res in result:
                if res != None:
                    for username in self.fullname_username_data[res[0]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_FULLNAME")
                    for username in self.fullname_username_data[res[1]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_FULLNAME")

    def check_suspicious_address(self, ip_address):
        # initialise chunk size and minimum threshold for similarity
        chunk_size = 500
        threshold = 0.85

        # address list corresponding to the IP Address
        address_list = self.ip_data.get(ip_address).get("ADDRESS")

        for index in range(0, len(address_list), chunk_size):

            # create username chunks
            chunk = address_list[index:index+chunk_size]
            pairs = list(itertools.combinations(chunk,2))

            # for each pair calculate similarity ratio
            result = [pair for pair in pairs if self.calculate_similarity_ratio(pair, threshold) is not None]

            # for address returned (passed threshold check) 
            # add each username to dictionary of suspicious ones with the corresponding tag for the parameter.
            for res in result:
                if res != None:
                    for username in self.address_username_data[res[0]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_ADDRESS")
                    for username in self.fullname_username_data[res[1]]:
                        self.sus_users[username]["TAGS"].add("GIBBERISH_ADDRESS")

    def check_same_fullname(self, ip_address):
        
        # fetch fullname corresponding to the IP address
        fullname_list = self.ip_data[ip_address]["FULL_NAME"]

        # check if any fullname exists more than 4 times
        for name in fullname_list:
            if fullname_list.count(name) > 4:

                # update the corresponding usernames with suspected tags
                for username in self.ip_data[ip_address]["USERNAME"]:
                    self.sus_users[username]["TAGS"].add("SUSPICIOUS_FULLNAME")

                break

    def check_same_address(self, ip_address):

        # fetch address corresponding to the IP address
        address_list = self.ip_data[ip_address]["ADDRESS"]

        # check if any address exists more than 4 times
        for address in address_list:
            if address_list.count(address) > 4:

                # update the corresponding usernames with suspected tags
                for username in self.ip_data[ip_address]["USERNAME"]:
                    self.sus_users[username]["TAGS"].add("SUSPICIOUS_ADDRESS")
                break

    def check_sus_reg_date(self, ip_address):
        '''
           Parameter to check if the same IP address is used to register users at least 3 times within 60 secs.

           :param ip_address: ip address with corresponding details.
           :ptype: dict

        '''

        # initialise pointer variables
        count = 0
        pointer_one = 0
        ip_corr_registered_date_list = self.ip_data.get(ip_address).get('REGISTRATION_DATETIME')

        # Reverse sort the list of registration dates corresponding to the IP Address.
        ip_corr_registered_date_list.sort(reverse=True)
        maximum_allowed_time_difference = datetime.timedelta(seconds=60)
        for pointer_two in range(1, len(ip_corr_registered_date_list)):

            # if difference between two consecutive time is less than 60 seconds and more than 2 cases for this exists.
            time_difference = ip_corr_registered_date_list[pointer_one] - ip_corr_registered_date_list[pointer_two]

            if time_difference < maximum_allowed_time_difference: count += 1
            
            if count >= 2: 

                # Add the corresponding Usernames into the dictionary of suspicious ones with the corresponding tag for the parameter.
                for username in self.ip_data.get(ip_address).get('USERNAME'):
                    self.sus_users[username]["TAGS"].add('SUS_REG_TIME_60')
                    
                # Add the IP Address into dictionary of suspicious ones with the corresponding tag for the parameter.
                self.sus_ips[ip_address].append('SUS_REG_TIME_60')

                break

            pointer_one += 1


    def unverified_user(self):
        
        # add all the unverified users in suspected list
        for username in self.unverified_users:
            self.sus_users[username]["TAGS"].add("UNVERIFIED_USER")

    def check_same_ip_pool(self):

        sus_ip_list = set()
        iplist = list(self.ip_data.keys())
        iplist.sort()

        for ip in range(len(iplist)):
            if self.ip_data.get(iplist[ip]).get('VPS') == True:
                try:
                    split_ip = [str(iplist[ip]).split('.'), str(iplist[ip+1]).split('.'), str(iplist[ip+2]).split('.'), str(iplist[ip+3]).split('.')]
                    if split_ip[0][:3] == split_ip[1][:3] == split_ip[2][:3] == split_ip[3][:3]:
                        sus_ip_list.add('.'.join(split_ip[0]))
                        sus_ip_list.add('.'.join(split_ip[1]))
                        sus_ip_list.add('.'.join(split_ip[2]))
                        sus_ip_list.add('.'.join(split_ip[3]))
                except:pass
        
        for ip_address in sus_ip_list:
            for username in self.ip_data.get(ip_address).get("USERNAME"):
                self.sus_users[username]['TAGS'].add("4_USER_REGISTERED_USING_VPS_AND_SAME_IP_POOL")

            self.sus_ips[ip_address].append("4_USER_REGISTERED_USING_VPS_AND_SAME_IP_POOL")

    def check_suspicious_mobile(self):

        pointer = 0
        mobile_list = list(self.office_phone_username.keys())
        mobile_list.sort()
        
        for mobile in self.office_phone_username:

            try:
                num1_start, num2_start, num3_start = mobile_list[pointer][:8], mobile_list[pointer+1][:8], mobile_list[pointer+2][:8]

                num1_end, num2_end, num3_end = mobile_list[pointer][-8:], mobile_list[pointer+1][-8:], mobile_list[pointer+2][-8:]

                if (num1_start == num2_start and num2_start == num3_start and num1_start == num3_start) or (num1_end == num2_end and num2_end== num3_end and num1_end == num3_end):
                    self.sus_mobile_set.add(mobile_list[pointer])
                    self.sus_mobile_set.add(mobile_list[pointer+1])
                    self.sus_mobile_set.add(mobile_list[pointer+2])
            except:
                pass
            
            # check for mobile numbers if they already exist as a TOUT's mobile number in the existing database.
            if (col_sus_mobile_handle.count_documents({'mobile_no' : mobile}) > 0) or (len(self.office_phone_username[mobile]) >= 4):
                self.sus_mobile_set.add(mobile)

            pointer += 1
        
        for number in self.sus_mobile_set:
            # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
            for username in self.office_phone_username.get(number):
                self.sus_users[username]["TAGS"].add("TEMPORARY_NUMBER")

    def disposable_domain(self):
        '''
            Parameter to check if the registered email address is temperory or not by matching its domain along the list of disposable domains. 

        '''
        # Get the list of disposable domains from the open source.
        disposable_email_list = requests.get("https://raw.githack.com/disposable/disposable-email-domains/master/domains.json")

        # Check if the response status is 200.
        if disposable_email_list.status_code == 200:

            # Convert the data into json format.
            self.disposable_email_data_from_api = disposable_email_list.json()
        
        # Store the disposable email if found otherwise None.
        results = list()
        
        # Concurrent threadpool operation to match each domain of the email along the disposable domain list.
        with concurrent.futures.ThreadPoolExecutor() as executor:

            futures = [executor.submit(self.check_for_disposable_email, email) for email in self.email_username_data.keys()]
            
            # Iterate over the futures to get the results.
            for future in concurrent.futures.as_completed(futures):
                try:
                    # Get the result from each future. 
                    result = future.result()

                    # Append the result in the list of results.
                    results.append(result)
                
                # Raise exceptin if occured.
                except Exception as e:
                    pass
        
        # Iterate of the list of results. 
        for res in results:

            # Check if the result does not contains any `None` value.
            if res != None:

                # Iterate over of the dictionary to get the `USERNAME` along the 'EMAIL` 
                for username in self.email_username_data[res]:

                    # Add the suspected tag of disposable email along that `USERNAME`.
                    self.sus_users[username]["TAGS"].add("DISPOSABLE_EMAIL")

    def check_for_disposable_email(self, email):
        '''
           Check if the email address has domain that is in the list of disposable domains.

           :param: email
           :ptype: str

           :return: email
           :return: None

           :rtype: str
           :rtype: None
        '''
        try:
            
            # Extract the domain out of the email address.
            domain = email.split("@")[1]

            # Check if domain is in the list of disposable domains.
            if domain in self.disposable_email_data_from_api:

                # Return the email if found in disposable domain list.
                return email
    
        except Exception as e:

            # Return None if email is not found in the list.
            return None

    def user_trend_data_update(self):

        # reverse sort VPS ASN and IP, NON VPS ASN and IP, and Vendor Data based on User count
        reverse_vps_asn = sorted(self.vps_asn.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)
        reverse_nonvps_asn = sorted(self.non_vps_asn.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)
        reverse_vps_ip = sorted(self.vps_ip.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)
        reverse_nonvps_ip = sorted(self.non_vps_ip.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)
        reverse_vendor_users = sorted(self.vendor_users.items(), key=lambda x:x[1]['TK_COUNT'], reverse=True)

        # update the user trend count data dictionary for dashboard
        self.user_trend_data = {
            'LOGS_DATE': self.file_date,
            'TOTAL_USERS_REG': len(self.file_raw_json_data), 
            'TOTAL_VPS_USERS_REG': self.vps_ticket_count, 
            'VENDOR_USERS_COUNT':  self.vendor_ticket_count, 
            'VPS_IP_POOL': len(self.vps_ip_pool), 
            'VPS_ASN': [i[1] for i in reverse_vps_asn[:20]],
            'NON_VPS_ASN': [i[1] for i in reverse_nonvps_asn[:20]], 
            'VPS_IP_USERS': [i[1] for i in reverse_vps_ip[:20]], 
            'NON_VPS_IP_USERS': [i[1] for i in reverse_nonvps_ip[:20]], 
            'VENDOR_USERS': [i[1] for i in reverse_vendor_users[:20]]
        }

    def update_sus_users(self, username):
        
        try:
            # initialise severity as -1
            severity = -1

            # fetch user tags for the suspected users
            user_tags = list(self.sus_users[username]["TAGS"])

            # check if user exist for the same username
            suspected_username_tags = col_sus_userid_handle.find_one({
                'USER_ID' : self.sus_users[username]['USER_ID'],
                'USERNAME' : username
            }, {
                '_id' : 0,
                'TAGS' : 1,
                'SOURCE' : 1
            })

            source = 'USER'

            # update the user tags list with the overall tags, including existing ones. to calculate severity
            if (suspected_username_tags) and ("TAGS" in suspected_username_tags): 

                if 'SOURCE' in suspected_username_tags and suspected_username_tags['SOURCE'] != source:
                    source = 'USER/PNR'
                user_tags += suspected_username_tags['TAGS']

            # update user rfi based on tags
            user_rfi = []
            for tag in user_tags:
                try:
                    user_rfi.append(map_rfi_tags[tag])
                except:
                    continue

            # calculate the severity based on the rfi's generated [LOW : 3, MEDIUM : 2,HIGH : 1]
            if len(list(filter(lambda tags: re.match('^UA', tags), user_rfi))) >= 2: 
                severity = 1
                self.high_severity_users += 1

            elif len(list(filter(lambda tags: re.match('^UB', tags), user_rfi))) >= 2: 
                severity = 2
                self.medium_severity_users += 1

            elif len(list(filter(lambda tags: re.match('^UA', tags), user_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UB', tags), user_rfi))) == 1: 
                severity = 2
                self.medium_severity_users += 1

            elif len(list(filter(lambda tags: re.match('^UA', tags), user_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UC', tags), user_rfi))) == 1: 
                severity = 2
                self.medium_severity_users += 1

            else: 
                severity = 3
                self.low_severity_users += 1

            # update the suspected user along with user details, TAGS and SEVERITY
            col_sus_userid_handle.update_one({
                'USER_ID' : self.sus_users[username]['USER_ID'],
                'USERNAME' : username,
                'SOURCE' : source
            },{
                '$set' : {
                    'SUS_DATE' : self.file_date,
                    'IP_ADDRESS' : self.sus_users[username]['IP_ADDRESS'],
                    'Severity' : severity,    
                    'EMAIL' : self.sus_users[username]['EMAIL'],
                    'status' : 0                             
                },
                '$addToSet' : {
                    'ANALYZED_FILE_REFERENCE' : self.analysed_file_reference,
                    "TAGS" : {
                        '$each' : list(user_tags)
                    }
                }
            }, upsert=True)
        
        except Exception as e:
            notify_gchat(f"USER : {self.file_date} : {repr(e)}")

    def update_overview_trend(self):

        try:

            case_trend_data = col_case_overview.find_one({
                'DATE' : self.file_date
            },{
                '_id':0,
            })
            
            try:
                total_high = self.high_severity_sus_ips + self.high_severity_users + case_trend_data['SEVERITY_TREND']['HIGH']['TOTAL'] 
            except: total_high = self.high_severity_sus_ips + self.high_severity_users
            
            try:
                total_medium = self.medium_severity_sus_ips + self.medium_severity_users + case_trend_data['SEVERITY_TREND']['MEDIUM']['TOTAL']
            except: total_medium = self.medium_severity_sus_ips + self.medium_severity_users
            
            try:
                total_low = self.low_severity_sus_ips + self.low_severity_users + case_trend_data['SEVERITY_TREND']['LOW']['TOTAL']
            except: total_low = self.low_severity_sus_ips + self.low_severity_users

            overall = total_high + total_medium + total_low
            
            try:
                col_case_overview.update_one({
                    'DATE' : self.file_date
                },{
                    '$set' : {
                        'SEVERITY_TREND.HIGH.TOTAL' : total_high,
                        'SEVERITY_TREND.HIGH.PERCENTAGE' : (total_high / overall) * 100 if overall != 0 else 0,
                        'SEVERITY_TREND.HIGH.IP' : self.high_severity_sus_ips,
                        'SEVERITY_TREND.HIGH.USER': self.high_severity_users,
                        
                        'SEVERITY_TREND.MEDIUM.TOTAL' : total_medium,
                        'SEVERITY_TREND.MEDIUM.PERCENTAGE': (total_medium / overall) * 100 if overall != 0 else 0,
                        'SEVERITY_TREND.MEDIUM.IP' : self.medium_severity_sus_ips,
                        'SEVERITY_TREND.MEDIUM.USER': self.medium_severity_users,

                        'SEVERITY_TREND.LOW.TOTAL' : total_low,
                        'SEVERITY_TREND.LOW.PERCENTAGE' : (total_low / overall) * 100 if overall != 0 else 0,
                        'SEVERITY_TREND.LOW.IP' : self.low_severity_sus_ips,
                        'SEVERITY_TREND.LOW.USER' : self.low_severity_users,                 
                    }
                }, upsert=True)

            except Exception as e:
                notify_gchat(f"USER : {self.file_date} : {repr(e)}")

        except Exception as e:
            notify_gchat(f"USER : {self.file_date} : {repr(e)}")

    def update_into_database(self):

        try:

            severity = -1

            # Update the suspicious IP Address along with their details and TAGS
            for sus_ip in self.sus_ips:

                ips_tags = list(self.sus_ips[sus_ip])

                # check if user exist for the same username
                suspected_ips_tags = col_sus_ips_handle.find_one({
                    'IP_ADDRESS' : self.sus_ips[sus_ip]
                }, {
                    '_id' : 0,
                    'TAGS' : 1
                })

                if suspected_ips_tags and len(suspected_ips_tags['TAGS']) > 0:

                    ips_tags += suspected_ips_tags['TAGS']

                # update user rfi based on tags
                # sus_ips_rfi = list(map_rfi_tags[tag] for tag in ips_tags)
                sus_ips_rfi = []
                for tag in ips_tags:
                    try:
                        sus_ips_rfi.append(map_rfi_tags[tag])
                    except:
                        continue

                # calculate the severity based on the rfi's generated [LOW : 3, MEDIUM : 2,HIGH : 1]
                if len(list(filter(lambda tags: re.match('^UA', tags), sus_ips_rfi))) >= 2: 
                    severity = 1
                    self.high_severity_sus_ips += 1

                elif len(list(filter(lambda tags: re.match('^UB', tags), sus_ips_rfi))) >= 2: 
                    severity = 2
                    self.medium_severity_sus_ips += 1

                elif len(list(filter(lambda tags: re.match('^UA', tags), sus_ips_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UB', tags), sus_ips_rfi))) == 1: 
                    severity = 2
                    self.medium_severity_sus_ips += 1

                elif len(list(filter(lambda tags: re.match('^UA', tags), sus_ips_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UC', tags), sus_ips_rfi))) == 1: 
                    severity = 2
                    self.medium_severity_sus_ips += 1

                else: 
                    severity = 3
                    self.low_severity_sus_ips += 1

                col_sus_ips_handle.update_one({
                    'IP_ADDRESS': sus_ip,
                    'DATE':self.file_date,
                    'ISP': self.ip_overall_info[sus_ip]["ISP"], 
                    'VPS': self.ip_overall_info[sus_ip]['VPS'], 
                    'ASN':self.ip_overall_info[sus_ip]['ASN']},
                    {
                        '$inc' : {
                            'TK_COUNT': self.ip_data[sus_ip]['USER_COUNT']
                        }, 
                        '$addToSet' : {
                            'TAGS': { 
                                '$each' : list(self.sus_ips[sus_ip])
                            }
                        },
                        '$set' : {
                            'Severity' : severity
                        }
                        
                    },upsert=True)
            
            print(f"sus ips tags updated: {self.file_date} : USER")

            # ThreadPool to update suspicious users along with their tags in the suspected collection
            with concurrent.futures.ThreadPoolExecutor() as executor:

                # Submit task to the executor for each records in suspicious users data.
                future_data = {executor.submit(self.update_sus_users, username): username for username in self.sus_users if self.sus_users != {} and "TAGS" in self.sus_users[username] and list(self.sus_users[username]["TAGS"]) != []}

                # Iterate over the futures to get the results.
                for future in concurrent.futures.as_completed(future_data):
                    
                    # Get future object from all the future objects.
                    url = future_data[future]

                    try:
                        # Get result from the future object.
                        data = future.result()

                    # Raise exception message if occured.
                    except Exception as exc:
                        notify_gchat(f"USER : {self.file_date} : {repr(exc)}")
                        print(exc.msg())

            print(f"sus user tags updated: {self.file_date} : USER")

            self.update_overview_trend()
                
            # update user trend data into the database
            col_user_trend_handle.insert_one(self.user_trend_data)

            col_overdash_data = col_overdash_handle.find_one({'NAME':'OVER_DATA'},{'USER_TOTAL_TREND': 1})

            user_total = json.loads(col_overdash_data['USER_TOTAL_TREND'].replace("\'", "\""))

            user_total[self.file_date.strftime('%B %Y')] = user_total.get(self.file_date.strftime('%B %Y'),0) + len(self.file_raw_json_data)

            col_overdash_handle.update_one({'NAME':'OVER_DATA'},{'$inc':{'USER_COUNT':len(self.file_raw_json_data),'SUS_USER_COUNT':len(self.sus_users)},'$set':{'USER_TOTAL_TREND':str(user_total)}})

        except Exception as e:

            notify_gchat(f"USER : {self.file_date} : {repr(e)}")
        
    def replace_arr_vals(self, arr, dic):
        new_arr = []

        # Return the corresponding explanation for the requested TAGS
        for i in arr:
            try:
                new_arr.append(dic[i])
            except:
                continue
        return new_arr

    def user_data(self):

        # fetch the complete USER DATA to be exported 
        user_id_list = polars.DataFrame(list(col_userid_handle.find({
            "ANALYZED_FILE_REFERENCE":self.analysed_file_reference
        },{
            "_id":0,
            'USER_ID': 1, 
            'USERNAME': 1, 
            'EMAIL': 1,
            'IP_ADDRESS' :1,
            'ASN': 1,
            'ISP': 1,
            'VPS': 1,
            'FIRST_NAME':1,
            'MIDDLE_NAME': 1,
            'LAST_NAME': 1,
            'ENABLE': 1,
            'VERIFIED':1,
            'REGISTERED_MOBILE' :1, 
            'OFFICE_PHONE' :1,
            'ADDRESS': 1,
            'COLONY': 1,
            'POSTOFFICE' :1,
            'DISTRICT': 1,
            'STATE': 1,
            'PIN_CODE': 1,
            'REGISTRATION_DATETIME': 1,
            'VENDOR_CODE': 1,
            'VENDOR_ID': 1,
            'VENDOR_NAME': 1
        })))

        # Replace the TAGS for suspicious USER records with the corresponding explanation of the TAGS.
        user_id_list = user_id_list.with_columns(polars.col('VPS').replace(map_vps_tags))
        
        return user_id_list
        
    
    def sus_user_data(self):

        # fetch the suspected users data along with TAGS to be exported
        user_id_list = polars.DataFrame(list(col_sus_userid_handle.find({
            "ANALYZED_FILE_REFERENCE":self.analysed_file_reference
        },{
            "_id":0,
            'USER_ID': 1, 
            'USERNAME': 1, 
            'EMAIL': 1, 
            'TAGS':1 
        })))

        # Replace the TAGS for suspicious USER records with the corresponding explanation of the TAGS.
        user_id_list = user_id_list.with_columns(polars.col('TAGS').map_elements(lambda x: self.replace_arr_vals(x,map_userid_tags)))

        # Convert List elements into a single String by joining them.
        user_id_list = user_id_list.with_columns(polars.col('TAGS').cast(polars.List(polars.Utf8)).list.join(", "))

        return user_id_list

            
