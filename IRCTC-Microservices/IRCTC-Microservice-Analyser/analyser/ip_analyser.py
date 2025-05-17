import os
import json
import ipinfo
import dotenv
import requests
import icecream
import itertools
import maxminddb
import concurrent.futures
from gchat_notification import notify_gchat


class IPAnalyser:

    def __init__(self):

        dotenv.load_dotenv()
        
        # Directories and MMDB readers
        self.base_dir = os.path.expanduser('~')
        self.company_mmdb = self.base_dir + "/Databases/artifacts_v1_standard_company.mmdb"
        self.privacy_mmdb = self.base_dir + "/Databases/artifacts_v1_standard_privacy.mmdb"

        ## Privacy and Company MMDB reader
        self.reader_company = maxminddb.open_database(self.company_mmdb)
        self.reader_privacy = maxminddb.open_database(self.privacy_mmdb)
        
        # local statistics variables

        ## Set to store FAILED IPS - whose records are not found on mmdb, to be searched on IPINFO.
        self.failed_ips = set()

        ## Dictionary to store overall details of IP ADDRESS, IP ADDRESS as keys and details in nested dictionary as values
        self.ip_overall_info = dict()

        ## Lists to store IPINFO and IP REGISTRY tokens read from local environment
        self.ipregistry_tokens = list(set(json.loads(os.environ['IP_ANALYZER_IPREGISTRY_TOKENS'])))
        self.ipinfo_tokens = list(set(json.loads(os.environ['IP_ANALYZER_IPINFO_TOKENS'])))
        # self.ipinfo_tokens = ["9856331fcaa070", "a5dd07db73b440","a9e668faf838b3", "96269c96436649"]
    
    def fetch_ipinfo_data_to_main_dict(self,ipinfo_detail):

        ## function to update the details of IP Addresses to the main dictionary fetched from IP INFO
        self.ip_overall_info[ipinfo_detail['ip']] = {
            'COUNTRY' : ipinfo_detail['country'],
            'ASN' : ipinfo_detail['org'].split(" ", 1)[0],
            'ISP' : ipinfo_detail['org'].split(" ", 1)[1],
            'VPS' : False
        }

        ## IPINFO does not provide VPS Status
        ## Checks to update VPS Status of the IP Address

        ## fetch details of IP Address from MMDB Company Database
        ip_data = self.get_company_mmdb_data(ipinfo_detail['ip'])

        ## fetch details of IP Address from MMDB Privacy Database
        ip_privacy_data = self.get_privacy_mmdb_data(ipinfo_detail['ip'])

        ## Check for keys which store VPS status of the IP Address in Company MMDB
        if 'type' in ip_data.keys():
            if ip_data['type'] == 'hosting':
                self.ip_overall_info[ipinfo_detail['ip']]['VPS'] = True
            else:
                self.ip_overall_info[ipinfo_detail['ip']]['VPS'] = False

        ## Check for keys which store VPS status of the IP Address in Privacy MMDB
        elif 'hosting' in ip_privacy_data.keys():
            if ip_privacy_data['hosting'] == 'true':
                self.ip_overall_info[ipinfo_detail['ip']]['VPS'] = True
            else:
                self.ip_overall_info[ipinfo_detail['ip']]['VPS'] = False
        
        ## Check for VPS Status in IP Registry
        else:
            self.ipregistry_stats(ipinfo_detail['ip'])

    def ipinfo_ip_stats(self):

        ## initialise pointer for IP INFO tokens list
        token_pointer = 0
        ip_details = {}

        ## iterate over the list of tokens 
        while token_pointer < len(self.ipinfo_tokens):
            try:
                ## Initialise Handler of IP INFO
                ipinfo_handler = ipinfo.getHandler(self.ipinfo_tokens[token_pointer])

                ## get details of all the IP Addresses in the list
                ip_details = ipinfo_handler.getBatchDetails(list(self.failed_ips))

                ## Iterate over the fetched records to check if any token expired midway
                ## and send the notification to google chat and raise exception
                for ip in list(self.failed_ips):
                    if 'status' in ip_details[ip].keys():
                        notify_gchat(f"IP INFO TOKEN EXPIRED : {self.ipinfo_tokens[token_pointer]}")
                break

            ## increase the pointer for the next token if any exception occurs 
            except Exception as e:
                token_pointer += 1
        
        ## check if all the tokens are expired and send notification on google chat
        if token_pointer == len(self.ipinfo_tokens):
            ### raise google chat query
            notify_gchat("IP INFO ALL TOKENS EXPIRED")
            
        ## transform the fetched details into a list
        ipinfo_details = [ip_details[i] for i in ip_details.keys()]

        ## Threadpooling to map list of IP address details
        ## Map each element of list with a function call to write details
        ## of IP Addresses to the main dictionary
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.fetch_ipinfo_data_to_main_dict, ipinfo_details)

    ## function to fetch IP Address details present in Company MMDB
    def get_company_mmdb_data(self, ip_address):
        
        try:
            ## fetch and return the data
            ip_data = self.reader_company.get(ip_address)
            return ip_data
        
        except:
            ## return empty dictionary if data does not exist
            return {}
        
    ## function to fetch IP Address details present in Privacy MMDB
    def get_privacy_mmdb_data(self, ip_address):

        try:
            ## fetch and return the data
            ip_data = self.reader_privacy.get(ip_address)
            return ip_data
        
        except:
            ## return empty dictionary if data does not exist
            return {}

    def maxmind_ip_stats(self, ip_address):

        ## Initialise details for IP Address in the overall IP Address dictionary
        self.ip_overall_info[ip_address] = {'COUNTRY':'', 'ISP':'', 'ASN':'', 'VPS':False}

        try:

            ## fetch details of IP Address from MMDB Company Database
            ip_data = self.get_company_mmdb_data(ip_address)

            ## fetch details of IP Address from MMDB Privacy Database
            ip_privacy_data = self.get_privacy_mmdb_data(ip_address)
            
            if ip_data != {}:

                ## fetch corresponding COUNTRY and ASN fetched from company MMDB
                ## Store corresponding to the IP Address in the overall dictionary
                self.ip_overall_info[ip_address]['COUNTRY'] = ip_data.get('country')
                self.ip_overall_info[ip_address]['ASN'] = ip_data.get('asn')

                ## Check for keys in which ISP is stored and populate the overall dictionary
                if 'name' in ip_data.keys():
                    self.ip_overall_info[ip_address]['ISP'] = ip_data['name']
                elif 'as_name' in ip_data.keys():
                    self.ip_overall_info[ip_address]['ISP'] = ip_data['as_name']

                ## raise Exception if ISP is not found
                else:
                    raise Exception

                ## Check for keys which store VPS status of the IP Address in Company MMDB
                if 'type' in ip_data.keys():
                    if ip_data['type'] == 'hosting':
                        self.ip_overall_info[ip_address]['VPS'] = True
                    else:
                        self.ip_overall_info[ip_address]['VPS'] = False

                ## Check for keys which store VPS status of the IP Address in Privacy MMDB
                elif 'hosting' in ip_privacy_data.keys():
                    if ip_privacy_data['hosting'] == 'true':
                        self.ip_overall_info[ip_address]['VPS'] = True
                    else:
                        self.ip_overall_info[ip_address]['VPS'] = False
                
                ## Check for VPS Status in IP Registry
                else:
                    self.ipregistry_stats(ip_address)
            
            ## raise Exception to add IP Address in failed set of IPs if any error/exception occurs
            else:
                raise Exception
            
        ## Add the IP Address in failed set of IPs if any Exception is raised
        except Exception as e:
            self.failed_ips.add(ip_address)
                        
    def maxmind(self, ip_addresses):

        ## Threadpooling to map list of IP address
        ## Map each element of list with a function call to fetch details
        ## from MMDB databases. 
        with concurrent.futures.ThreadPoolExecutor(4) as executor:
            executor.map(
                self.maxmind_ip_stats,
                ip_addresses
            )
        
        ## Function call to fetch details from IP INFO for failed set of IPs
        self.ipinfo_ip_stats()

        ## return the final populated data with details of IP Addresses
        return self.ip_overall_info

    def ipregistry_stats(self, ip_address):

        ## function to fetch VPS Status of IP Address from IP REGISTRY
        try:

            ## fetch IP Address details
            api_request = requests.get(f"https://api.ipregistry.co/{ip_address}?key=rqyvaseh1ujvpvox")
            api_response = api_request.json()

            ## check for 'connection' key to populate VPS status
            if "connection" in api_response.keys() and api_request.status_code==200:
                con_type = api_response['connection']['type']
                if con_type == "hosting":
                    self.ip_overall_info[ip_address]['VPS'] = True
                else:
                    self.ip_overall_info[ip_address]['VPS'] = False

            ## check is the given IP Address is PRIVATE
            if "code" in api_response.keys() and api_response["code"]=="RESERVED_IP_ADDRESS":
                self.ip_overall_info[ip_address]['VPS'] = "Private_IP_Address"
                self.ip_overall_info[ip_address]['ISP'] = "Private_IP_Address"
        
        ## mark VPS as 'FAILED_IP' if VPS Status is not found for IP Address
        except Exception as e:
           self.ip_overall_info[ip_address]['VPS'] = "FAILED_IP"
           self.ip_overall_info[ip_address]['ISP'] = "FAILED_IP"