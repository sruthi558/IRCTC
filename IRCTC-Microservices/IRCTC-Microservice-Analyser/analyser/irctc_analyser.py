import os
import pprint
import re
import time
import json
import string
import random
import polars
import pandas
import datetime
import openpyxl
import icecream
import itertools
import xlsxwriter
import Levenshtein
import concurrent.futures
from mongo_connection import *
from ip_analyser import IPAnalyser
from collections import defaultdict
from gchat_notification import notify_gchat
from mapping_data import map_pnr_tags, map_rfi_tags, map_vps_tags

class IRCTCAnalyser:

    def __init__(self, file_path, file_type, analysed_file_reference=''.join(random.choices(string.ascii_lowercase + string.digits, k = 32))) -> None:
        
        self.base_dir = os.path.expanduser('~')

        # List to store the vendors ip address.
        self.vendors_list = polars.read_csv(self.base_dir + "/Databases/VENDOR_IP_LIST.csv")["IP_ADDRESS"].to_list()

        # List to store the whitelisted subnets.
        self.whitelisted_subnets_file = self.base_dir + "/Databases/WHITELISTED_SUBNETS.csv"

        # List to store the government asn.
        self.govt_asn = polars.read_csv(self.base_dir + "/Databases/GOVT_ASNS.csv")["ASN"].to_list()

        # initialise starting time to calculate overall operating time
        self.time_calc = time.time()

        # Path of the file to analyse.
        self.file_path = file_path

        self.low_severity_users = 0

        self.medium_severity_users = 0

        self.high_severity_users = 0

        self.low_severity_sus_ips = 0

        self.medium_severity_sus_ips = 0
        
        self.high_severity_sus_ips = 0

        self.low_severity_pnrs = 0

        self.medium_severity_pnrs = 0
        
        self.high_severity_pnrs = 0
        
        '''
            Default dictionary to store all the details related to the particular ip address.

            dtype: dict
            key: ip address
            value: dict
                : Key: TK_COUNT : value: int
                : key: BOOKING_DATE : value: datetime
                : key: USERNAME : value: str
                : key: PNR_NUMBER : value: str
                : key: VPS : value: boolean
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
            Default dictionary to store all the suspected pnr numbers and their corresponding suspected tags.

            dtype: dict
            key: pnr number
            value: list of tags.
        '''
        self.sus_pnrs = defaultdict(list)

        '''
            Default dictionary to store all the suspected users and their corresponding suspected tags.

            dtype: dict
            key: username
            value: {list of tags and user id}
        '''
        self.sus_users = defaultdict(dict)

        '''
            Default dictionary to store the booking mobile with their corresponding pnr number.

            dtype: dict
            key: booking mobile
            value: list of pnr numbers.
        '''
        self.booking_mobile_pnr_list = defaultdict(list)

        self.username_booking_mobile = defaultdict(list)

        '''
            Dictionary to store the username with their corresponding pnr number.

            dtype: dict
            key: username
            value: pnr number.
        '''
        self.username_pnr = dict()

        # Dictionary to store the ASN related details.
        self.asn_data = dict()

        # Stores unique ip addresses that uses VPS.
        self.vps_ip_pool = set()

        # List of the all the unique ip addresses from the sheet.
        # Used in IP Analyser to fetch ip address details.
        self.ip_all_list = list()

        # List of dictionary to store the details of the top 20 ip addresses using VPS.
        self.top_20_vps_ip = list()

        # List of dictionary to store the details of the top 20 ips using VPS.
        self.top_20_vps_isp = list()

        # Dictionary to store the details of the daily log analysis for the dashboard.
        self.trend_data_dict = dict()

        # List of dictionary to store the details of the top 20 ip addresses tat are not using VPS.
        self.top_20_non_vps_ip = list()

        # List of dictionary to store the details of the top 20 isp that are not using VPS.
        self.top_20_non_vps_isp = list()

        self.sus_mobile_set = set()
        
        # Initialize the initial value of the sheet dataframe with None
        self.data_df = None

        # Initialize the initial value of the 'file_date' as None.
        self.file_date = None

        # Count of VPS tickets booked
        self.vps_ticket_count = 0

        # Type of the file being analyzed (ARP, AC, NONAC).
        self.file_type = file_type

        # Count of tickets booked using vendor ip addresses.
        self.vendor_ticket_count = 0

        # Create instance for IP Analyser.
        self.ip_analyzer = IPAnalyser()

        # Variable to store the JSON data of the uploaded file.
        self.file_raw_json_data = self.convert_to_json()
        
        msg_str = f"JSON DATA for the file CREATED: {self.file_date} : PNR"
        icecream.ic(msg_str)

        # Total number of tickets booked.
        self.total_tickets = len(self.file_raw_json_data)

        # Unique hash value generated for the particular file.
        self.analysed_file_reference = analysed_file_reference

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

        ## Exportable data

        # Data of PNR along with suspected for analysed sheet.
        self.pnr_ip_data = self.pnr_data()

        # Top ISP data in order of maximum number of booked tickets
        self.top_isp_data = self.isp_data()

        # ISP with IP Addresses using VPS 
        self.isp_vps_data = self.vps_isp_data()

        # ISP with IP Addresses not using VPS (NON-VPS) 
        self.isp_nonvps_data = self.non_vps_isp_data()

        # Foreign IP Address Data
        self.foreign_data = self.foreign_ip_data()

        # Stores the data for the PNRs that are booked within 40sec.
        self.till_40sec = self.time_bound_pnr_data40()

        ## Function call to populate ASN Data into the collection
        self.asn_process()

        # Generate the final sheet data to be exported as result
        self.generate_sheet_data()


    def generate_sheet_data(self) -> None:
        '''
           Generate excel sheet of the analyzed PNR data.
        '''
        msg_str = f"GENERATING DATAFRAME SHEET: {self.file_date} : PNR"
        icecream.ic(msg_str)

        # Convert the fetched data into dataframes
        self.pnr_ip_data = polars.DataFrame(self.pnr_ip_data)
        self.top_isp_data = polars.DataFrame(self.top_isp_data)
        self.isp_vps_data = polars.DataFrame(self.isp_vps_data)
        self.isp_nonvps_data = polars.DataFrame(self.isp_nonvps_data)
        self.foreign_data = polars.DataFrame(self.foreign_data)
        self.till_40sec = polars.DataFrame(self.till_40sec)

        msg_str = f"DATAFRAMES GENERATED: {self.file_date} : {self.file_type}"
        icecream.ic(msg_str)

        # Convert dataframes into separate sheets in excel file
        with xlsxwriter.Workbook("download_reports/" + self.analysed_file_reference+".xlsx") as writer:
            self.pnr_ip_data.write_excel(workbook=writer,worksheet="PNR_IP_DATA")   
            self.top_isp_data.write_excel(workbook=writer,worksheet="ISP_ANALYSIS")
            self.isp_vps_data.write_excel(workbook=writer,worksheet="VPS_IP_ANALYSIS")
            self.isp_nonvps_data.write_excel(workbook=writer,worksheet="NON_VPS_IP_ANALYSIS")
            self.foreign_data.write_excel(workbook=writer,worksheet="FOREIGN_IP_DATA")
            self.till_40sec.write_excel(workbook=writer,worksheet="Till_40_sec")        
        
        col_file_handle.update_one({'hash':self.analysed_file_reference},  { "$set": { 'status': 'Processed' } },upsert=True)
        notify_gchat(f"{self.file_type} : File analysed : {self.file_date}")
        print(self.file_type,": ",self.file_date, ": ", (time.time() - self.time_calc)/60)

    def convert_to_json(self) -> dict:
        '''
           Check the extension of the uploaded file and convert its data into JSON.

           :return: list of dictionaries
           :rtype: list
        '''
        msg_str = f"CONVERTING FILE TO JSON DATA: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)

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
        
    def populate_data(self, row):
        '''
           Update row wise sheet data, ip overall data for parameter analysis and ASN data.

           :param row: contains single row data of the sheet.
           :ptype: dict

           :return :Message that the data is updated successfully or error message if any.
           :rtype: str
        '''

        try:
            # Get the 'BOOKING_DATE' from the row.
            booking_date = row["BOOKING_DATE"]

            # Get the 'JOURNEY_DATE' from the row.
            journey_date = row["JOURNEY_DATE"]
            
            # Check if the booking date is in 'int' format --> convert it into datetime format.
            if isinstance(booking_date,int):
                booking_date = datetime.datetime.fromtimestamp(booking_date/1e3)
                
            # Check if the journey date is in 'int' format --> convert it into datetime format.
            if isinstance(journey_date,int):
                journey_date = datetime.datetime.fromtimestamp(journey_date/1e3)

            # Check if the booking date is in 'str' format --> convert it into datetime format.
            if isinstance(booking_date,str):
                booking_date = datetime.datetime.strptime(booking_date, "%d-%m-%Y %H:%M:%S")
            
            # Check for misinterpretation between 'day' and 'month' when date is less than `12` in 'BOOKING_DATE.
            if booking_date.day <= 12:

                # Store the `date` from the current 'BOOKING_DATE'  from the row in th temp variable.
                temp_date = datetime.datetime.combine(booking_date.date(), datetime.time.min)

                # Check if data corresponding to the 'BOOKING_DATE' and the 'file_type' already exists or if the 'BOOKING_DATE' read is creater than the current date.
                if (col_pnr_handle.count_documents({
                    "BOOKING_DATE" : {
                        '$gte' : temp_date, 
                        '$lt' : temp_date + datetime.timedelta(days=1)
                    },
                      "TK_TYPE" : self.file_type}) > 0) or (booking_date.date() > datetime.datetime.now().date()):
                    
                    # Stores the current 'BOOKING_DATE' into a variable.
                    curr_book_date = booking_date
                    
                    # Convert the current 'BOOKING_DATE' into datetime string format.
                    curr_book_date = curr_book_date.strftime("%d%m%Y %I:%M:%S")

                    # Defines the format for the new format.
                    time_format = "%m%d%Y %I:%M:%S"

                    # Interchange the 'month' with the 'day' and 'day' with the 'month'.
                    booking_date = datetime.datetime.strptime(curr_book_date,time_format)
            
            # Replace the 'BOOKING_DATE' value in the row with the updated 'BOOKING_DATE' value.
            row["BOOKING_DATE"] = booking_date

            # Check if the journey date is in 'str' format --> convert it into datetime format.
            if isinstance(journey_date,str):
                journey_date = datetime.datetime.strptime(journey_date, "%d-%m-%Y %H:%M:%S")
                
            # Check for misinterpretation between 'day' and 'month' when date is less than `12` in 'JOURNEY_DATE'.
            # Check if 'BOOKING_DATE' is greater than 'JOURNEY_DATE'.
            if booking_date > journey_date:

                # Stores the current 'JOURNEY_DATE' into a variable.
                curr_journey_date = journey_date

                # Convert the current 'JOURNEY_DATE' into datetime string format.
                curr_journey_date = curr_journey_date.strftime("%d%m%Y %I:%M:%S")

                # Defines the format for the new format.
                time_format = "%m%d%Y %I:%M:%S"

                # Interchange the 'month' with the 'day' and 'day' with the 'month'.
                journey_date = datetime.datetime.strptime(curr_journey_date,time_format)

            # Replace the 'JOURNEY_DATE' value in the row with the updated 'BOOKING_DATE' value.
            row["JOURNEY_DATE"] = journey_date
            
            # Update the 'file_date' value.
            if self.file_date == None:
                self.file_date = datetime.datetime.combine(booking_date.date(), datetime.time.min)

            # Update the 'PNR_NUMBER' of the row into the 'str' data type.
            row["PNR_NUMBER"] = str(row["PNR_NUMBER"])

            # Update the 'IP_ADDRESS' of the row into the 'str' data type.
            row["IP_ADDRESS"] = str(row["IP_ADDRESS"])

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
                else:
                    row["USERNAME"] = str(row["USERNAME"])

            except Exception as e:
                row["USERNAME"] = str(row["USERNAME"])
            
            # Update the row with the 'IP_ADDRESS' details from the IP Analyser.
            row.update({
                "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
                "TK_TYPE" : self.file_type,
                "ISP" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("ISP"),
                "ASN" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("ASN"),
                "VPS" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("VPS"),
                "COUNTRY" : self.ip_overall_info.get(row["IP_ADDRESS"]).get("COUNTRY"),
                "VENDOR_IP": True if row['IP_ADDRESS'] in self.vendors_list else False,
                "TICKET_TIME":int(str(row["BOOKING_DATE"]).split(" ")[1].split(".")[0].replace(":","")),
                "TAGS" : []
            })

            # Update the variable 'self.ip_data' for the the parameter analysis.
            row['BOOKING_MOBILE'] = str(row['BOOKING_MOBILE']).split(".")[0]

            # Check if the 'IP_ADDRESS' does not existes in vendor list, government asn list.
            if (row['IP_ADDRESS'] not in self.vendors_list) and (row["ASN"] not in self.govt_asn):
                
                # Update the row with the details of the IP_ADDRESS.
                if row["IP_ADDRESS"] in self.ip_data.keys():
                    self.ip_data[row["IP_ADDRESS"]]['TK_COUNT'] += 1
                    self.ip_data[row["IP_ADDRESS"]]['BOOKING_DATE'].append(row["BOOKING_DATE"])
                    self.ip_data[row["IP_ADDRESS"]]['USERNAME'].append(row["USERNAME"])
                    self.ip_data[row["IP_ADDRESS"]]['PNR_NUMBER'].append(row["PNR_NUMBER"])
                    
                else:
                    self.ip_data[row["IP_ADDRESS"]] = {
                        "IP_ADDRESS" : row["IP_ADDRESS"],
                        'TK_COUNT' : 1,
                        'BOOKING_DATE' : [row["BOOKING_DATE"]],
                        'USERNAME' : [row["USERNAME"]],
                        'PNR_NUMBER' : [row["PNR_NUMBER"]],
                        'VPS' : self.ip_overall_info[row["IP_ADDRESS"]]["VPS"]
                    }

                # POPULATE ASN DATA
                if row['ASN'] not in self.asn_data:
                    self.asn_data[row['ASN']] = {
                        'ASN': row['ASN'], 
                        'TK_COUNT': 1, 
                        'ISP': row['ISP'], 
                        'VPS': row.get('VPS', False), 
                        'COUNTRY': row['COUNTRY']
                    }

                else:
                    self.asn_data[row['ASN']]['TK_COUNT'] += 1

                '''
                    Update dictionary for suspicious booking mobile analysis.

                    dtype: dict
                    key: BOOKING_MOBILE
                    value: PNR_NUMBER
                '''
                
                # if row['BOOKING_MOBILE'] not in self.booking_mobile_pnr_list.keys():
                self.booking_mobile_pnr_list[row['BOOKING_MOBILE']].append(row['PNR_NUMBER'])

                self.username_booking_mobile[row['BOOKING_MOBILE']].append(row['USERNAME'])

                # Total VPS booked tickets.
                if row['VPS'] == True: 
                    self.vps_ticket_count += 1
                    self.vps_ip_pool.add(row['IP_ADDRESS'])

                '''
                    Update dictionary for username and PNR number correlation.

                    dtype: dict
                    key: USERNAME
                    value: PNR_NUMBER
                '''
                self.username_pnr[row["USERNAME"]] = row["PNR_NUMBER"]

                '''
                    Update dictionary to store all the users and their userid with empty tags list (to be updated during parameter analysis).

                    dtype: dict
                    key: username
                    value: {list of tags and userid}
                '''
                self.sus_users[row["USERNAME"]] = {
                    "USER_ID" : row["USER_ID"],
                    "IP_ADDRESS" : row["IP_ADDRESS"],
                    "TAGS" : set()
                }
                
            # Check if the 'IP_ADDRESS' exists in vendor list
            elif row['IP_ADDRESS'] in self.vendors_list:
                # increment the count of tickets booked through VENDORS
                self.vendor_ticket_count += 1
              
            # Update the IP Address collection to store the details of all the IP Address
            col_ip_handle.update_one({
                'IP_ADDRESS':row['IP_ADDRESS']
            },{
                '$set': {
                    'VPS': row['VPS'],
                    'ISP':row['ISP'],
                    'ASN':row['ASN'],
                    'COUNTRY':row['COUNTRY'],
                    'VENDOR_IP':row['VENDOR_IP']
                }
            }, upsert=True)

            return f"{row['IP_ADDRESS']} updated"
        
        except Exception as e:
            # return exception if any occurs
            notify_gchat(f'{self.file_date} : {self.file_type} : {repr(e)}')
            return e.msg()

    def parse_file(self):
        '''
            Central function to call all the other functions and populate data into database.
                1) Insert PNR data into database.
                2) Do parameter analysis.
                3) Populate data for daily log analysis.
                4) Updated suspected tags into the database
        '''

        ## Parse the JSON records and populate temporary data for further analysis.
        msg_str = f"PARSING AND POPULATING THE DATA: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)

        # ThreadPool to populate IP Address Data for each row of the records
        with concurrent.futures.ThreadPoolExecutor() as executor:

            # Submit task to the executor for each records in JSON data.
            future_data = {executor.submit(self.populate_data, json_data): json_data for json_data in self.file_raw_json_data}

            for future in concurrent.futures.as_completed(future_data):

                url = future_data[future]

                try:
                    data = future.result()

                except Exception as exc:
                    notify_gchat(f'{self.file_date} : {self.file_type} : {repr(exc)}')
                    print(exc.msg())

        msg_str = f"IP DATA POPULATED: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)
        
        # INSERT raw JSON data into Database before analysis
        self.insert_into_database()
        msg_str = f"PNR DATA INSERTED INTO DATABASE: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)
        
        msg_str = f"ANALYZING SUSPECTED PARAMETERS: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)

        # Analysing the data based on multiple parameters
        self.all_parameter_analysis()
        msg_str = f"PARAMETER ANALYSIS COMPLETED: {self.file_date} : : {self.file_type}"
        icecream.ic(msg_str)

        # calculate the trend data wrequired for overview on the dashboard
        self.pnr_trend_data_for_dashboard()
        
        self.update_into_database()

    def check_ip_vps(self, ip_address : str) -> None:
        '''
           Parameter to check if the same IP address is used to book tickets at least 4 times and is using VPS.

           :param ip_address: ip address with corresponding details
           :ptype: dict

        '''

        # Check for VPS status of the IP Address
        if self.ip_data.get(ip_address).get("VPS") == True:

            # Add the IP Address into dictionary of suspicious ones with the corresponding tag for the parameter.
            self.sus_ips[ip_address].append("SAMEIP_MORE4_VPS")

            # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
            for pnr in self.ip_data.get(ip_address).get("PNR_NUMBER"):
                self.sus_pnrs[pnr].append("SAMEIP_MORE4_VPS")
            
            for username in self.ip_data.get(ip_address).get("USERNAME"):
                self.sus_users[username]['TAGS'].add("SAMEIP_MORE4_VPS")

            
    def ip_address_more_5(self, ip_address : str) -> None:
        '''
           Parameter to check if the same IP address is used to book tickets more than 5 times.

           :param ip_address: ip address with corresponding details.
           :ptype: dict

        '''

        # Add the IP Address into dictionary of suspicious ones with the corresponding tag for the parameter.
        self.sus_ips[ip_address].append("5_PNR_BOOK_SAMEIP_SAMEDAY")
        
        # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
        for pnr in self.ip_data.get(ip_address).get("PNR_NUMBER"):
            self.sus_pnrs[pnr].append("5_PNR_BOOK_SAMEIP_SAMEDAY")

        for username in self.ip_data.get(ip_address).get("USERNAME"):
            self.sus_users[username]['TAGS'].add("5_PNR_BOOK_SAMEIP_SAMEDAY")

    def check_suspicious_booking_date(self, ip_address: str) -> None:
        '''
           Parameter to check if the same IP address is used to book tickets at least 3 times within 60 secs.

           :param ip_address: ip address with corresponding details.
           :ptype: dict

        '''

        # initialise pointer variables
        count = 0
        pointer_one = 0
        booking_dates_corr_to_ip = self.ip_data.get(ip_address).get('BOOKING_DATE')

        # Reverse sort the list of booking dates corresponding to the IP Address
        booking_dates_corr_to_ip.sort(reverse=True)

        # Set the threashold time of 1 min.
        maximum_allowed_time_difference = datetime.timedelta(seconds=60)

        # Iterate over the resverse sorted booking date list.
        for pointer_two in range(1, len(booking_dates_corr_to_ip)):

            # Check the time difference between booking dates.
            time_difference = booking_dates_corr_to_ip[pointer_one] - booking_dates_corr_to_ip[pointer_two]
            
            # update the count tracker by one if the threashold condition is satisfied.
            if time_difference < maximum_allowed_time_difference: count += 1

            if count >= 2:
                # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
                for pnr_number in self.ip_data.get(ip_address).get('PNR_NUMBER'):
                    self.sus_pnrs[pnr_number].append('5_PNR_BOOK_SAMEIP_60SEC')

                for username in self.ip_data.get(ip_address).get("USERNAME"):
                    self.sus_users[username]['TAGS'].add("5_PNR_BOOK_SAMEIP_60SEC")
                
                # Add the IP Address into dictionary of suspicious ones with the corresponding tag for the parameter.
                self.sus_ips[ip_address].append('5_PNR_BOOK_SAMEIP_60SEC')    

                break

            pointer_one += 1


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
    
    def check_similar_username(self, ip_address):

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
                    self.sus_users[res[0]]["TAGS"].add("SERIES_USERNAME")
                    self.sus_users[res[1]]["TAGS"].add("SERIES_USERNAME")

                    # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
                    if self.username_pnr[res[0]] not in self.sus_pnrs.keys() or "SERIES_USERNAME" not in self.sus_pnrs[res[0]]:
                        self.sus_pnrs[self.username_pnr[res[0]]].append("SERIES_USERNAME")

                    if self.username_pnr[res[1]] not in self.sus_pnrs.keys() or "SERIES_USERNAME" not in self.sus_pnrs[res[1]]:
                        self.sus_pnrs[self.username_pnr[res[1]]].append("SERIES_USERNAME")

    def check_suspicious_booking_mobile(self):

        pointer = 0
        mobile_list = list(self.booking_mobile_pnr_list.keys()).sort()
        
        for booking_mobile in self.booking_mobile_pnr_list:

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
            if (col_sus_mobile_handle.count_documents({'mobile_no' : booking_mobile}) > 0) or (len(self.booking_mobile_pnr_list[booking_mobile]) >= 4):
                self.sus_mobile_set.add(booking_mobile)

            pointer += 1
        
        for number in self.sus_mobile_set:
            # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
            for pnr in self.booking_mobile_pnr_list.get(number):
                self.sus_pnrs[pnr].append("TEMPORARY_NUMBER")

            # Add the corresponding PNR Numbers into the dictionary of suspicious ones with the corresponding tag for the parameter.
            for username in self.username_booking_mobile.get(number):
                self.sus_users[username]['TAGS'].add("TEMPORARY_NUMBER")
            
            # Update the suspicious mobile into sus mobile collection.
            col_sus_mobile_handle.update_many({
                'mobile_no' : number
            },{
                '$set' : {
                    'month' : datetime.datetime.combine(self.file_date.date(), datetime.time.min),
                    'month_str' : str(self.file_date.strftime('%B')) + " " + str(self.file_date.year),
                    'source' : 'Booking Logs',
                    'status' : 'High',
                    'latest_username' : 'ADMIN',
                },
                '$addToSet' : {
                    'upload_history' : self.file_date
                }
                
            }, upsert=True)

    def check_same_ip_pool(self):
        '''
           Check if the ip address is using VPS and belong to the same subnet.
        '''
        
        # Tracker to store the suspicious ip address list.
        sus_ip_list = set()

        # Get all the ip addresses from the ip data list.
        iplist = list(self.ip_data.keys())

        # Sort the list of ip addresses
        iplist.sort()

        # Iterate over the list of ip addresses.
        for ip in range(len(iplist)):

            # Check if the ip address is using VPS or not.
            if self.ip_data.get(iplist[ip]).get('VPS') == True:
                try:
                    
                    # Split the ip address.
                    split_ip = [str(iplist[ip]).split('.'), str(iplist[ip+1]).split('.'), str(iplist[ip+2]).split('.'), str(iplist[ip+3]).split('.')]
                    
                    # Match the starting three addresses of the ip address --> threashold of 4 ip addresses --> add the suspected number in suspected numbers list. 
                    if split_ip[0][:3] == split_ip[1][:3] == split_ip[2][:3] == split_ip[3][:3]:

                        sus_ip_list.add('.'.join(split_ip[0]))
                        sus_ip_list.add('.'.join(split_ip[1]))
                        sus_ip_list.add('.'.join(split_ip[2]))
                        sus_ip_list.add('.'.join(split_ip[3]))

                except:pass
        
        # Iterate over the suspected ip address data.
        for ip_address in sus_ip_list:

            # Flag all the pnr numbers along the ip address.
            for pnr_number in self.ip_data.get(ip_address).get('PNR_NUMBER'):
                self.sus_pnrs[pnr_number].append('4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL')
        
            # Flag the username along the ip address.
            for username in self.ip_data.get(ip_address).get("USERNAME"):
                self.sus_users[username]['TAGS'].add("4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL")
            
            # Flag the ip addresses in the suspected ip address dictionary with the corresponding suspected tag.
            self.sus_ips[ip_address].append("4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL")


    def all_parameter_analysis(self):
       
        # for each IP Address in the data file
        for ip_address in self.ip_data.keys():
            
            # Ticket count for the IP Address based on which parameters are applied
            ticket_count = self.ip_data.get(ip_address).get('TK_COUNT')
        
            # PARAM 1 - IP VPS ANALYSIS.
            if ticket_count >= 3:
                self.check_ip_vps(ip_address)
                         
            # PARAM 2 - SUSPICIOUS BOOKING DATE ANALYSIS.
            if ticket_count >= 3:
                self.check_suspicious_booking_date(ip_address)

            # PARAM 3 - SIMILAR USERNAME ANALYSIS.
            if ticket_count >= 3:
                self.check_similar_username(ip_address)

            # PARAM 4 - IP COUNT MORE THAN 5 ANALYSIS.
            if ticket_count > 4:
                self.ip_address_more_5(ip_address)
            
        # PARAM 5 - SUSPICIOUS BOOKING MOBILE ANALYSIS.
        self.check_suspicious_booking_mobile()

        # PARAM 6 - SUSPICIOUS IP ADDRESS POOL ANALYSIS.
        self.check_same_ip_pool() 

                
    def pnr_trend_data_for_dashboard(self):

        # reverse sort the list of IP Address based on the Ticket Count
        ip_sorted_data = sorted(self.ip_data.items(), key = lambda x : x[1]['TK_COUNT'], reverse=True)

        for ip_data in ip_sorted_data:

            # populate the top 20 VPS IP and NON VPS IP Addresses
            insert_ip_data = {
                    "IP_ADDRESS" : ip_data[1].get('IP_ADDRESS'),
                    "VPS" :  ip_data[1].get('VPS'),
                    "TK_COUNT" : ip_data[1].get('TK_COUNT')
                }
            
            # Update the corresponding dictionary based on VPS Status.
            if insert_ip_data.get('VPS') == True and len(self.top_20_vps_ip) < 21:
                self.top_20_vps_ip.append(insert_ip_data)
                
            if insert_ip_data.get('VPS') == False and len(self.top_20_non_vps_ip) < 21:
                self.top_20_non_vps_ip.append(insert_ip_data)               

            else: break

        # reverse sort the list of ASNs based on the Ticket Count
        asn_sorted_data = sorted(self.asn_data.items(), key = lambda x : x[1]['TK_COUNT'], reverse=True)

        # populate the top 20 VPS ISP and NON VPS ISP Addresses
        for asn_data in asn_sorted_data:

            # Update the corresponding dictionary based on VPS Status.
            if asn_data[1].get('VPS') == True and len(self.top_20_vps_isp) < 21:
                self.top_20_vps_isp.append(asn_data[1])

            if  asn_data[1].get('VPS') == False and len(self.top_20_non_vps_isp) < 21:
                self.top_20_non_vps_isp.append(asn_data[1])
                
            else: break

        # Update the existing dictionary with overview data along with the filetype
        self.trend_data_dict = {
            self.file_type : {
                'VPS_ISP' : self.top_20_vps_isp,
                'NON_VPS_ISP' : self.top_20_non_vps_isp,
                'VPS_IP' : self.top_20_vps_ip,
                'NON_VPS' : self.top_20_non_vps_ip,
                'TOT_TK' : self.total_tickets,
                'VPS_TK' : self.vps_ticket_count,
                'VENDOR_TK' : self.vendor_ticket_count,
                'VPS_POOL' : len(self.vps_ip_pool),
                'ANALYZED_FILE_REFERENCE': self.analysed_file_reference
            }
        }

    def insert_into_database(self):

        try:
            # Insert all the PNR raw records into the database before analysis
            col_pnr_handle.insert_many(self.file_raw_json_data, ordered=False)

        except pymongo.errors.BulkWriteError as e:
            for error in e.details.get('writeErrors', []):
                if error.get('code') == 11000:
                    pass

    def update_sus_pnrs(self, sus_pnr):

        severity = -1

        try:
            pnr_tags = list(self.sus_pnrs[sus_pnr])

            # update user rfi based on tags
            sus_pnr_rfi = list(set(map_rfi_tags[tag] for tag in pnr_tags))

            # calculate the severity based on the rfi's generated [LOW : 3, MEDIUM : 2,HIGH : 1]
            if len(list(filter(lambda tags: re.match('^UA', tags), sus_pnr_rfi))) >= 2: 
                severity = 1
                self.high_severity_pnrs += 1

            elif len(list(filter(lambda tags: re.match('^UB', tags), sus_pnr_rfi))) >= 2: 
                severity = 2
                self.medium_severity_pnrs += 1

            elif len(list(filter(lambda tags: re.match('^UA', tags), sus_pnr_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UB', tags), sus_pnr_rfi))) == 1: 
                severity = 2
                self.medium_severity_pnrs += 1

            elif len(list(filter(lambda tags: re.match('^UA', tags), sus_pnr_rfi))) == 1 and len(list(filter(lambda tags: re.match('^UC', tags), sus_pnr_rfi))) == 1: 
                severity = 2
                self.medium_severity_pnrs += 1

            else: 
                severity = 3
                self.low_severity_pnrs += 1

            col_pnr_handle.update_one({
                "PNR_NUMBER" : sus_pnr
            },{
                '$addToSet' : {
                    'TAGS': { 
                        '$each' : list(self.sus_pnrs[sus_pnr])
                    }
                },
                '$set' :{
                    'Severity' : severity
                }
                
            })
        
        except Exception as e:
            notify_gchat(f"{self.file_type} : {self.file_date} : {repr(e)}")

    def update_overview_trend(self):

        try:
            case_trend_data = col_case_overview.find_one({
                'DATE' : self.file_date
            },{
                '_id':0,
            })
            
            try:
                total_high = self.high_severity_sus_ips + self.high_severity_users + self.high_severity_pnrs + case_trend_data['SEVERITY_TREND']['HIGH']['TOTAL'] 
            except: total_high = self.high_severity_sus_ips + self.high_severity_users + self.high_severity_pnrs
            
            try:
                total_medium = self.medium_severity_sus_ips + self.medium_severity_users + self.medium_severity_pnrs + case_trend_data['SEVERITY_TREND']['MEDIUM']['TOTAL']
            except: total_medium = self.medium_severity_sus_ips + self.medium_severity_users + self.medium_severity_pnrs
            
            try:
                total_low = self.low_severity_sus_ips + self.low_severity_users + self.low_severity_pnrs + case_trend_data['SEVERITY_TREND']['LOW']['TOTAL']
            except: total_low = self.low_severity_sus_ips + self.low_severity_users + self.low_severity_pnrs

            overall = total_high + total_medium + total_low

            col_case_overview.update_one({
                'DATE' : self.file_date
            },{
                '$set' : {
                    'SEVERITY_TREND.HIGH.TOTAL' : total_high,
                    'SEVERITY_TREND.HIGH.PERCENTAGE' : (total_high / overall) * 100 if overall != 0 else 0,
                    'SEVERITY_TREND.HIGH.PNR' : self.high_severity_pnrs,
                    'SEVERITY_TREND.HIGH.IP' : self.high_severity_sus_ips,
                    'SEVERITY_TREND.HIGH.USER': self.high_severity_users,
                    
                    'SEVERITY_TREND.MEDIUM.TOTAL' : total_medium,
                    'SEVERITY_TREND.MEDIUM.PERCENTAGE': (total_medium / overall) * 100 if overall != 0 else 0,
                    'SEVERITY_TREND.MEDIUM.PNR' : self.medium_severity_pnrs,
                    'SEVERITY_TREND.MEDIUM.IP' : self.medium_severity_sus_ips,
                    'SEVERITY_TREND.MEDIUM.USER': self.medium_severity_users,

                    'SEVERITY_TREND.LOW.TOTAL' : total_low,
                    'SEVERITY_TREND.LOW.PERCENTAGE' : (total_low / overall) * 100 if overall != 0 else 0,
                    'SEVERITY_TREND.LOW.PNR' : self.low_severity_pnrs,
                    'SEVERITY_TREND.LOW.IP' : self.low_severity_sus_ips,
                    'SEVERITY_TREND.LOW.USER' : self.low_severity_users,                
                }
            }, upsert=True)

        except Exception as e:
            notify_gchat(f"{self.file_type} : {self.file_date} : {repr(e)}")
            

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
                            'TK_COUNT': self.ip_data[sus_ip]['TK_COUNT']
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
            
            print(f"sus ips tags updated: {self.file_date} : : {self.file_type}")

            with concurrent.futures.ThreadPoolExecutor() as executor:

                # Submit task to the executor for each records in suspicious pnrs  data.
                future_data = {executor.submit(self.update_sus_pnrs, sus_pnr): sus_pnr for sus_pnr in self.sus_pnrs}

                # Iterate over the futures to get the results.
                for future in concurrent.futures.as_completed(future_data):
                    
                    # Get future object from all the future objects.
                    url = future_data[future]

                    try:
                        # Get result from the future object.
                        data = future.result()

                    # Raise exception message if occured.
                    except Exception as exc:
                        notify_gchat(f'{self.file_date} : {self.file_type} : {repr(e)}')
                        print(exc.msg())
            
            print(f"pnr tags updated: {self.file_date} : : {self.file_type}")

            # UPDATE PNR TREND DATA 
            col_pnr_trend_handle.update_many({
                'LOGS_DATE' : self.file_date
                },{
                    '$set' : {
                        self.file_type : self.trend_data_dict[self.file_type]
                    }
                }, upsert=True)
            
            print(f"PNR TREND DATA UPDATED: {self.file_date} : : {self.file_type}")
            
            for username in self.sus_users:

                if self.sus_users[username] == {} or "TAGS" not in self.sus_users[username] or list(self.sus_users[username]["TAGS"]) == []:
                    continue

                # initialise severity as -1
                severity = -1

                # fetch user tags for the suspected users
                user_tags = list(set(self.sus_users[username]["TAGS"]))

                source = "PNR"

                # check if user exist for the same username
                suspected_username_tags = col_sus_userid_handle.find_one({
                    'USER_ID' : self.sus_users[username]['USER_ID'],
                    'USERNAME' : username
                }, {
                    '_id' : 0,
                    'TAGS' : 1,
                    'SOURCE' : 1
                })
                # update the user tags list with the overall tags, including existing ones. to calculate severity.

                if (suspected_username_tags) and ("TAGS" in suspected_username_tags): 
                    
                    if 'SOURCE' in suspected_username_tags and suspected_username_tags['SOURCE'] != source:
                        source = "USER/PNR"
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

                # update the suspected user along with user detaisl, TAGS and SEVERITY
                col_sus_userid_handle.update_one({
                    'USER_ID' : self.sus_users[username]['USER_ID'],
                    'USERNAME' : username,
                    'SOURCE' : source
                },{
                    '$set' : {
                        'SUS_DATE' : self.file_date,
                        'PNR_IP_ADDRESS' : self.sus_users[username]['IP_ADDRESS'],
                        'Severity' : severity,
                        'status' : 0 
                    },
                    '$addToSet' : {
                        'ANALYZED_FILE_REFERENCE' : self.analysed_file_reference,
                        "TAGS" : {
                            '$each' : list(user_tags)
                        }
                    }
                }, upsert=True) 

            print(f"SUSPECTED USERS DATA UPDATED: {self.file_date} : : {self.file_type}")

            self.update_overview_trend()

            print(f"CASE OVERVIEW DATA UPDATE: {self.file_date} : : {self.file_type}")

            col_overdash_data = col_overdash_handle.find_one({'NAME':'OVER_DATA'},{'PNR_TOTAL_TREND': 1,'PNR_VPS_TREND': 1})

            pnr_total = json.loads(col_overdash_data['PNR_TOTAL_TREND'].replace("\'", "\""))

            pnr_vps = json.loads(col_overdash_data['PNR_VPS_TREND'].replace("\'", "\""))
            
            pnr_total[self.file_date.strftime('%B %Y')] = pnr_total.get(self.file_date.strftime('%B %Y'),0) + len(self.file_raw_json_data)

            pnr_vps[self.file_date.strftime('%B %Y')] = pnr_vps.get(self.file_date.strftime('%B %Y'),0) + self.vps_ticket_count      

            col_overdash_handle.update_one({'NAME':'OVER_DATA'},{'$inc':{'PNR_COUNT':self.total_tickets,'SUS_PNR_COUNT':len(self.sus_pnrs)},'$set':{'PNR_TOTAL_TREND':str(pnr_total),'PNR_VPS_TREND':str(pnr_vps)}})
            
            #File update with total tickets
            col_file_handle.update_one({
                'hash':self.analysed_file_reference
                }, { 
                    "$set" : {
                        "ticket_count" : self.total_tickets , 
                        "ip_processing" : False,
                        "asn_processing" : False
                    } 
                }, upsert=True)
        
        except Exception as e:
            print(e.msg())
            notify_gchat(f'{self.file_date} : {self.file_type} : {repr(e)}')

    def asn_process(self):
        
        asn_data = []

        # Group ASN data reverse sorted based on the number of tickets booked
        for pnr in col_pnr_handle.aggregate([
            { 
                "$match" : { 
                    "ANALYZED_FILE_REFERENCE": self.analysed_file_reference
                }
            },{
                "$group" : { 
                    "_id": "$ASN",
                    "count" : {
                        "$sum" : 1
                    }
                }
            },{ 
                "$sort" : { 
                    "count" : -1 
                }
            }], allowDiskUse=True):
            
            temp_data  = {}
            fetched = col_pnr_handle.find_one({"ASN":pnr["_id"]})
            temp_data["asn"] = pnr["_id"]
            temp_data["isp"] = fetched["ISP"]
            temp_data["country"] = fetched["COUNTRY"]
            temp_data["vps"] = fetched["VPS"]
            temp_data["broadband"] = False
            temp_data["hosting"] = False
            temp_data["business"] = False
            temp_data["blacklisted"] = False
            asn_data.append(temp_data)

        try:
            # Update the ASN collection
            col_asn_handle.insert_many(asn_data,ordered=False)

        except pymongo.errors.BulkWriteError as e:
            for error in e.details.get('writeErrors', []):
                if error.get('code') == 11000:
                    pass

    def replace_arr_vals(self, arr, dic):
        new_arr = []

        # Return the corresponding explanation for the requested TAGS
        for i in arr:
            try:
                new_arr.append(dic[i])
            except:
                continue
        return new_arr

    def convert_list_to_string(self, lst):

        # Replace special characters from the list or text
        return str(lst).replace("[", "").replace("]", "").replace("'","")

    def pnr_data(self):

        # Fetch the PNR data to be exported
        pnr_data_list = polars.DataFrame(list(col_pnr_handle.find({
            "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference
        },{
            "_id" : 0,
            "ANALYZED_FILE_REFERENCE" : 0,
            "TK_TYPE" : 0,
            "VENDOR_IP" : 0,
            'COUNTRY' : 0,
            "TICKET_TIME" : 0,
            "BOOKING DATE" : 0,
            "JOURNEY DATE" : 0,
            "Severity": 0
        })))
        
        # Replace the TAGS for suspicious PNR records with the corresponding explanation of the TAGS.
        pnr_data_list = pnr_data_list.with_columns(polars.col('TAGS').map_elements(lambda x: self.replace_arr_vals(x,map_pnr_tags)))

        # Convert List elements into a single String by joining them.
        pnr_data_list = pnr_data_list.with_columns(polars.col('TAGS').cast(polars.List(polars.Utf8)).list.join(", "))

        # Replace the TAGS for suspicious USER records with the corresponding explanation of the TAGS.
        pnr_data_list = pnr_data_list.with_columns(polars.col('VPS').replace(map_vps_tags))

        return pnr_data_list

    def isp_data(self):

        # Total count of tickets booked for current file
        total_count = col_file_handle.find_one({
            "hash" : self.analysed_file_reference
        },{
            "_id" : 0,
            "ticket_count" : 1})["ticket_count"]
        
        isp_data = []

        # Calculate Percentage of tickets booked by all ISPs along with their VPS Status for the given file 
        for pnr in col_pnr_handle.aggregate([
            { 
                "$match" : {
                    "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference
                }
            },{
                "$group" : { 
                    "_id": "$ASN",
                    "data" : {
                        "$first" : "$$ROOT"
                    },
                    "count" : {
                        "$sum" : 1
                    }
                }
            },{ 
                "$project" : { 
                    'VPS' : '$data.VPS',
                    'ISP' : '$data.ISP',
                    "count": 1, 
                    "PERCENTAGE" : { 
                        "$concat": [{ 
                            "$substr" : [{
                                "$multiply" : [{
                                    "$divide" : [
                                        "$count", {
                                            "$literal" : total_count 
                                        }
                                    ] 
                                },100 ] 
                            }, 0,4]
                        }, "", "%" ]
                    }
                }
            },{ 
                "$sort" : { 
                    "count" : -1 
                }
            }], allowDiskUse=True):

            temp_data={}
            temp_data["ISP"] = pnr['ISP']
            temp_data["COUNT"] = pnr["count"]
            temp_data["PERCENTAGE"] = pnr["PERCENTAGE"]
            temp_data["VPS"] = pnr['VPS']
            isp_data.append(temp_data)

        isp_data.append({
            "ISP":"Total Count",
            "COUNT":total_count,
            "PERCENTAGE":100,
            "VPS":True
        })

        return isp_data

    def vps_isp_data(self):
        vps_isp_data = []

        # Group IP Addresses using VPS with their ticket count for the given file
        for pnr in col_pnr_handle.aggregate([
            { 
                "$match" : {
                    "VPS" : True,
                    "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference
                }
            },{
                "$group" : {
                    "_id": "$IP_ADDRESS",
                    "count" : {
                        "$sum" : 1
                    }
                }
            },{
                "$sort": {
                    "count" : -1
                }
            }], allowDiskUse=True):

            temp_data = {}
            temp_data["IP_ADDRESS"] = pnr["_id"]
            temp_data["ISP"] = col_ip_handle.find_one({
                "IP_ADDRESS" : pnr["_id"]
            },{
                "_id" : 0,
                "ISP":1
            })["ISP"]

            temp_data["COUNT"] = pnr["count"]
            vps_isp_data.append(temp_data)
        return vps_isp_data
    
    def non_vps_isp_data(self):
        nonvps_isp_data = []

        # Group IP Addresses not using VPS(NON VPS) with their ticket count for the given file
        for pnr in col_pnr_handle.aggregate([{ "$match": {"VPS": False,"ANALYZED_FILE_REFERENCE":self.analysed_file_reference}},{"$group": { "_id": "$IP_ADDRESS","count" : {"$sum" : 1}}},{ "$sort": { "count": -1 }}],allowDiskUse=True):
            temp_data = {}
            temp_data["IP_ADDRESS"] = pnr["_id"]
            temp_data["ISP"] = col_ip_handle.find_one({"IP_ADDRESS":pnr["_id"]},{"_id":0,"ISP":1})["ISP"]
            temp_data["COUNT"] = pnr["count"]
            nonvps_isp_data.append(temp_data)
        return nonvps_isp_data

    def foreign_ip_data(self):

        # Return Foreign IP Addresses along with Country and ISP.
        if col_pnr_handle.count_documents({
            "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
            "COUNTRY" : {
                "$ne" : "IN"
            }
        }) == 0:
            
            return [{"IP":"","ISP":"","COUNTRY":""}]
        
        else:
            return list(col_pnr_handle.find({
                "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
                "COUNTRY" : {
                    "$ne" : "IN"
                }
            },{
                "_id" : 0,
                "IP_ADDRESS" : 1,
                "ISP" : 1,
                "COUNTRY" : 1
            }
        ))
    
    def time_bound_pnr_data40(self):

        # Check for filetype and fetch data based on tickte timings
        # fetch PNR records booked under 40 seconds.

        if self.file_type == "ARP" and col_pnr_handle.count_documents({
            "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
            "TICKET_TIME" : {
                "$lt" : 80041
            }
        }) != 0:
            
            return list(col_pnr_handle.find({
                "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
                "TICKET_TIME" : {
                    "$lt" : 80041
                }
            },{
                "_id" : 0,
                "ANALYZED_FILE_REFERENCE" : 0,
                "VPS" : 0,
                "TK_TYPE" : 0,
                "VENDOR_IP" : 0,
                "TICKET_TIME" : 0,
                "BOOKING DATE" : 0,
                "JOURNEY DATE" : 0,
                "Severity": 0
            }))
            
        elif self.file_type =="AC" and col_pnr_handle.count_documents({
            "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
            "TICKET_TIME" : {
                "$lt" : 100041
            }
        }) != 0:
            
            return list(col_pnr_handle.find({
                "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
                "TICKET_TIME" : {
                    "$lt" : 100041
                }
            },{
                "_id" : 0,
                "ANALYZED_FILE_REFERENCE" : 0,
                "VPS" : 0,
                "TK_TYPE" : 0,
                "VENDOR_IP" : 0,
                "TICKET_TIME" : 0,
                "BOOKING DATE" : 0,
                "JOURNEY DATE" : 0,
                "Severity": 0
            }))
            
        elif self.file_type =="NON_AC" and col_pnr_handle.count_documents({
            "ANALYZED_FILE_REFERENCE" : self.analysed_file_reference,
            "TICKET_TIME" : {
                "$lt" : 110041
            }}) != 0:

            return list(col_pnr_handle.find({"ANALYZED_FILE_REFERENCE":self.analysed_file_reference,"TICKET_TIME":{"$lt":110041}},{"_id":0,"ANALYZED_FILE_REFERENCE":0,"VPS":0,"TK_TYPE":0,"VENDOR_IP":0,"TICKET_TIME":0,"BOOKING DATE":0,"JOURNEY DATE":0}))
            
        # else return a list of empty values to be exported
        else:
            return [{
                "PNR NUMBER":"",
                "BOOKING DATE":"",
                "NGET_BOOKING_TIME":"",
                "JOURNEY DATE":"",
                "USER_ID":"",
                "USER_LOGINID":"",
                "BOOKING MOBILE":"",
                "TRAIN_NUMBER":"",
                "FROM":"",
                "TO":"",
                "Class":"",
                "IP_ADDRESS":"",
                "ISP":"",
                "ASN":"",
                "VPS":""
            }]
