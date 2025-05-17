import hashlib
import os
import numpy
import datetime
import calendar
import icecream
import xlsxwriter
import ipaddress
from utils import *
import pandas as pd
from status_codes import *
from datetime import datetime
from collections import Counter
from datetime import date, datetime

class IPBlacklist():       
    def __init__(self, start_date, end_date):

        self.base_dir = os.path.expanduser('~')

        self.start_date = start_date

        self.all_isp_file_hash = dict()

        self.end_date = end_date

        # Firewall Blocked Subnet
        self.Firewall_Blocked_Subnet = Vendor_IP + IP_Blocked_IRCTC + whitelisted_subnet

        self.top_isps_pipeline = self.generate_top_isps_pipeline(start_date, end_date)

        self.top_isps = list(Main_PNR_collection.aggregate(self.top_isps_pipeline))

        message = f'TOP ISPS DATA COLLECTED'
        icecream.ic(message)

        self.top_isps_list = [data["_id"] for data in self.top_isps]

        ip_tags_pipeline = self.generate_ip_tags_pipeline(start_date, end_date, self.top_isps_list)

        Subent_with_tags = list(Main_PNR_collection.aggregate(ip_tags_pipeline))

        message = f'SUBNETS WITH THEIR TAGS DATA FETCHED'
        icecream.ic(message)
        
        self.data_list = self.process_documents(Subent_with_tags)

        self.generate_excel_files(self.data_list)

        icecream.ic("SHEET DATA GENERATED")

        self.collect_stat()
        
        message = f"Blacklist between the dates {start_date} and {end_date} generated"
        icecream.ic(message)

        self.update_data_to_db()

        icecream.ic("DATA UPDATED TO DB")
        icecream.ic("BLACKLIST CREATED")
    

    def update_data_to_db(self):
        files = os.listdir(self.base_dir + "/IRCTC-Microservice-ISP/isp/Final_Blacklist")
        
        blacklist_status = {
            "BLS1": "Pinaca Flagged for Blacklisting & Confirmation awaited from ITAF",
            "BLS2": "Subnets Blacklisted by ITAF"
        }
        for file in files:
            try:
                isp = file.split(".xlsx")[0]
                df = pd.read_excel(f'Final_Blacklist/{file}', sheet_name="Blacklist_Subnets")
                df.rename(columns={'TAGS': 'Reason'}, inplace=True)
                req_header = ['ISP','Blacklist Date','Subnet','Status', 'Reason']
                req_header.sort()

                column_list = df.columns.values.tolist()
                column_list.sort()

                if column_list != req_header:

                    return {
                        'detail': f'Headers format incorrect in file {file}!'
                    }
                
                subnets = df['Subnet'].to_list()
                total_subnets = len(subnets)
                
                subnet_reasons = df["Reason"].to_list()
                subnet_reasons = list(set([str(subnet_reason).replace("[", "").replace("]", "").replace("'","") for subnet_reason in subnet_reasons]))
                
                subnet_status = df["Status"].iloc[0]
                isp = df["ISP"].iloc[0]

                nan_check_list = [subnet_reasons, subnet_status, isp]

                if isp == "" or subnet_reasons == "" or subnet_status == "" or (numpy.nan in nan_check_list):
                    raise Exception
                
                reason = {}
                for reason_code in suspected_rfi:
                    if suspected_rfi[reason_code] in subnet_reasons:
                        reason[reason_code] = suspected_rfi[reason_code]

                status = {}
                for status_code in blacklist_status:
                    if blacklist_status[status_code].lower() in subnet_status.lower():
                        status[status_code] = blacklist_status[status_code]
                
                black_date = df["Blacklist Date"].iloc[0]

                if isinstance(black_date, str):
                    black_date = datetime.strptime(black_date, '%d-%m-%Y')

                black_month = str(calendar.month_name[black_date.month]) + " " + str(black_date.year)

                ip_addresses = dict()
                for subnet in subnets:
                    ip_address = [str(ip) for ip in ipaddress.IPv4Network(subnet)]
                    ip_addresses[subnet] = ip_address

                total_ip = 0
                subnets_data = list()
                for subnet, ip in ip_addresses.items():
                    total_ip += len(ip)
                    data = dict()
                    data['SUBNET'] = subnet
                    data['IP_COUNT'] = len(ip)
                    subnets_data.append(data)

                file_path = 'Final_Blacklist/'
                with open(file_path + file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    file_hash_name = str(file_hash) + '.xlsx'
                    os.rename(file_path + file, file_path + file_hash_name)

                Blacklist_collection.update_one(
                    {
                        "ISP" : isp,
                        "REPORT_MONTH" : black_month
                    },{
                        '$set' : {
                            "REASON" : reason,
                            "STATUS" : status,
                            "FLAGGED_DATE" : black_date,
                            "BLACKLIST_DATE" : black_date,
                            "BLACKLIST_FILE_REF" : file_hash_name
                        }, 
                        '$inc' : {
                            "TOTAL_BLACKLIST_SUBNET" : total_subnets,
                            "TOTAL_BLACKLIST_IPS" : total_ip,
                        }, 
                        '$addToSet' : {
                            "BLACKLIST_DETAILS" : subnets_data,
                            "UPLOAD_HISTORY" : datetime.now()
                        }
                    },
                    upsert = True
                )

                Blacklist_collection.update_one({
                    'name' : 'Blacklist_Status'
                },{
                    '$set' : {
                        'status' : 1
                    }
                })

                col_dashboard.update_one(
                    {
                        'NAME' : "OVER_DATA",
                    },{
                        '$inc' : {
                            'BLACKLIST_IP' : total_ip,
                            'BLACKLIST_SUBNET' : total_subnets
                        }
                    }
                )
            except Exception as e:
                print(e.msg())

    # Getting TOP VPS ISP
    def generate_top_isps_pipeline(self, start_date, end_date):
        match_condition = {
            "$match": {"BOOKING_DATE": {"$gte": start_date, "$lt": end_date}, "VPS": True}
        }
        group_condition = {"$group": {"_id": "$ISP", "count": {"$sum": 1}}}
        sort_condition = {"$sort": {"count": -1}}
        limit_condition = {"$limit": 5}

        return [match_condition, group_condition, sort_condition, limit_condition]

    # Getting IPs who are flagged at least once
    def generate_ip_tags_pipeline(self, start_date, end_date, top_isps_list):
        match_condition = {
            "$match": {
                "BOOKING_DATE": {"$gte": start_date, "$lt": end_date},
                "VPS": True,
                "ISP": {"$in": top_isps_list},
            }
        }
        project_condition = {"$project": {"_id": 0, "IP_ADDRESS": 1, "TAGS": 1, "ISP": 1}}
        sort_condition = {"$sort": {"ISP": 1}}

        return [match_condition, project_condition, sort_condition]

    # Process the Statistics data
    def process_documents(self, Subent_with_tags):
        data_list = []
        ip_counter = Counter(doc["IP_ADDRESS"] for doc in Subent_with_tags)
        processed_ips = set()

        for data in Subent_with_tags:
            ip = data["IP_ADDRESS"]

            if data["TAGS"] and ip not in processed_ips and ip_counter[ip] >= 4:
                processed_ips.add(ip)
                parts = ip.split(".")
                parts[-1] = "0/24"
                new_ip = ".".join(parts)
                final = {
                    "IP ADDRESS": data["IP_ADDRESS"],
                    "PNR COUNT": ip_counter[ip],
                    "Subnet": new_ip,
                    "ISP": data["ISP"],
                    "TAGS": data["TAGS"],
                }
                data_list.append(final)

        return sorted(data_list, key=lambda x: x["PNR COUNT"], reverse=True)
    
    def blacklisted_pinaca(self):
        # Assuming Blacklist_collection and Firewall_Blocked_Subnet are defined elsewhere
        already_blacklist_subnet = []
        for document_list in Blacklist_collection.find({"BLACKLIST_DETAILS": {"$exists": True, "$type": "array"}}):
            for inner_list in document_list["BLACKLIST_DETAILS"]:
                for subnet_data in inner_list:
                    subnet_value = subnet_data.get("SUBNET")
                    if subnet_value:
                        already_blacklist_subnet.append(subnet_value)
        self.Firewall_Blocked_Subnet.extend(already_blacklist_subnet)

    # generate Statistics data 
    def generate_excel_files(self, data_list):
        unique_isps = set(entry["ISP"] for entry in data_list)

        for isp in unique_isps:
            filtered_data = [entry for entry in data_list if entry["ISP"] == isp]
            df = pd.DataFrame(filtered_data)
            file_path = f"Blacklistfiles/{isp}.xlsx"
            df.to_excel(file_path, index=False)
            with pd.ExcelWriter("Final_Blacklist/" + "Blacklist_" + isp +".xlsx", engine='openpyxl') as writer:
                df.to_excel(writer,sheet_name="Blacklist_Statistics",index=False)

        print("Stats are generated")

    def savefile(self, Final_black, isp):
        black_subnets = pd.DataFrame(Final_black)
        black_subnets.to_excel(f"Blacklist_Subnets/IPv4subnets_{isp}_blacklist.xlsx", index=False)
        with pd.ExcelWriter("Final_Blacklist/" + "Blacklist_" + isp + ".xlsx", engine='openpyxl', mode='a') as writer:
            black_subnets.to_excel(writer,sheet_name="Blacklist_Subnets",index=False)

    def checkoverlap(self, subnetlist, checksubnet):
        for subnet in subnetlist:
            check = ipaddress.ip_network(checksubnet).overlaps(ipaddress.ip_network(subnet))
            if subnet != checksubnet and check is True:
                return checksubnet

    def subnetchecker(self, subnetlist):
        final_list = []
        for subnet in subnetlist:
            checker = self.checkoverlap(subnetlist, subnet)
            if checker is not None:
                final_list.append(checker)

        for sub in final_list:
            if sub in subnetlist:
                subnetlist.remove(sub)    
        return subnetlist

    def collect_stat(self):
        files = os.listdir(self.base_dir + "/IRCTC-Microservice-ISP/isp/Blacklistfiles")
        for i in files:
            isp = i.split(".xlsx")[0]
            data = pd.read_excel(f"Blacklistfiles/{i}")
            subnet = list(set(data["Subnet"]))

            final_black_list = subnet
            final_list = list(set(final_black_list))
            final_black_list_update = self.subnetchecker(final_list)

            final_black_list_check = final_black_list
            for subnet in final_black_list_update:
                for check_subnet in final_black_list_check:
                    if check_subnet != subnet and ipaddress.ip_network(check_subnet).overlaps(ipaddress.ip_network(subnet)):
                        final_black_list_update.remove(check_subnet)

            for check_subnet in final_black_list_update:
                for subnet in final_black_list_update:
                    if check_subnet != subnet and ipaddress.ip_network(check_subnet).overlaps(ipaddress.ip_network(subnet)):
                        final_black_list_update.remove(check_subnet)

            for subnet in self.Firewall_Blocked_Subnet:
                for check_subnet in final_black_list_update:
                    if check_subnet == subnet:
                        final_black_list_update.remove(check_subnet)

            for subnet in self.Firewall_Blocked_Subnet:
                for check_subnet in final_black_list_update:
                    if check_subnet != subnet and ipaddress.ip_network(check_subnet).overlaps(ipaddress.ip_network(subnet)):
                        final_black_list_update.remove(check_subnet)

            blacklist_subnet = []
            blacklist_subnet.extend(final_black_list_update)
            blacklist_subnet.extend(self.Firewall_Blocked_Subnet)

            # ip_blacklist_instance = self(datetime.now(), datetime.now(), [], [])
            block_list = self.process_blacklist(self.Firewall_Blocked_Subnet, final_black_list_update)  # <-------

            today = date.today()
            formatted_date = today.strftime("%d-%-m-%Y")
            
            Final_blacklist = list()

            for j in block_list:
                subnet = j.split("/")[0] + "/24"
                filtered_data = data[data["Subnet"] == subnet]
                tags = filtered_data["TAGS"].values[0] if not filtered_data.empty and "TAGS" in filtered_data.columns else None

                final = {
                    "Subnet": j,
                    "ISP": isp,
                    "Blacklist Date": formatted_date,
                    "TAGS": tags,
                    "Status": "Pinaca Flagged for Blacklisting & Confirmation awaited from ITAF",
                }

                Final_blacklist.append(final)


            self.savefile(Final_blacklist, isp)

    def _exclude_ip_from_subnet(self, subnet_key, ip_address_list):

        # Convert IP addresses into individual subnets.
        ip_subnets = [ipaddress.ip_network(str(ip_address) + "/32") for ip_address in ip_address_list]

        # Construct a dictioanry to dereference an IP addresses sole subnet.
        ip_dict = dict()
        for ip_address in ip_address_list:
            ip_dict[ip_address] = ipaddress.ip_network(str(ip_address) + "/32")

        # Maintain a list of subnets as they keep getting broken into different parts.
        subnets = [ipaddress.ip_network(subnet_key)]

        # Loop through all IP subnets to iteratively break down subnets.
        for ip_subnet in ip_subnets:

            for subnet in subnets:

                if ip_subnet.subnet_of(subnet):

                    subnets.extend(list(subnet.address_exclude(ip_subnet)))
                    subnets.remove(subnet)
                    break

        # Collapse subnets back together if possible.
        subnets = ipaddress.collapse_addresses(subnets)

        # Construct a set of subnets as strings.
        blacklist_subnet_set = set()

        for subnet in subnets:
            blacklist_subnet_set.add(subnet)

        return blacklist_subnet_set 

    def _test_blacklist(self, excluded_ipvx, blacklisted_subnets):
        # Check for any excluded IP addresses that lie in the blacklisted subnet.
        ip_in_subnet = set()

        for ip_address in excluded_ipvx:

            for blacklisted_subnet in blacklisted_subnets:

                if ip_address in blacklisted_subnet:

                    ip_in_subnet.add(ip_address)

        if len(ip_in_subnet):
            # self.logger.error("Test failed. Following IP addresses were found to be in blacklisted subnets: {}".format(', '.join(ip_in_subnet)))
            return False
        
        else:
            # self.logger.debug("Test passed. All vendor IP addresses are safe from the blacklisted subnets.")
            return True

    def process_blacklist(self, exclusion_ip_addresses, all_subnets):
        
        full_form = True

        # self.logger.debug("Creating blacklist subnets.")

        excluded_ipvx = [ipaddress.ip_address(ip_address) for ip_address in exclusion_ip_addresses]

        all_subnets = [ipaddress.ip_network(subnet) for subnet in all_subnets]

        blacklist_subnets = set()
        subnets_with_excluded_ip = set()
        subnet_with_excluded_ips_dict = dict()

        for subnet in all_subnets:
            
            blacklist_subnet_flag = True

            for ip_address in excluded_ipvx:
                
                if ip_address in subnet:

                    subnets_with_excluded_ip.add(subnet)

                    if subnet in subnet_with_excluded_ips_dict:
                        subnet_with_excluded_ips_dict[subnet].add(ip_address)
                    else:
                        subnet_with_excluded_ips_dict[subnet] = set([ip_address])

                    blacklist_subnet_flag = False

            if blacklist_subnet_flag:
                blacklist_subnets.add(subnet)

        # self.logger.debug("Breaking subnets with excluded IPs.")

        for subnet_key, ip_address_list in subnet_with_excluded_ips_dict.items():
            blacklist_subnets = blacklist_subnets.union(self._exclude_ip_from_subnet(subnet_key, ip_address_list))

        if self._test_blacklist(excluded_ipvx, blacklist_subnets):

            if full_form:

                return list(map(lambda subnet: subnet.with_netmask, blacklist_subnets))

            else:
                return list(map(str, blacklist_subnets))

        else:
            return None

