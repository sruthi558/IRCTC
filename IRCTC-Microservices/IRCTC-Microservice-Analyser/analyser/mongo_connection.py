# Import required libraries.
import pymongo
import pydantic_settings


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

settings = Settings()

db_connection = pymongo.MongoClient(settings.MONGO_URI)

db = db_connection[settings.MONGO_DB]

col_pnr_handle = db.irctc_pnr_test_1
col_file_handle = db.irctc_file_test_1
col_pnr_trend_handle = db.irctc_dash_test_1
col_asn_handle = db.asn_collection
col_ip_handle = db.ip_collection
col_user_trend_handle = db.irctc_user_dash_test_1
col_sus_ips_handle = db.irctc_sus_ips_test_1
col_sus_userid_handle = db.irctc_userid_data_test_1
col_userid_handle = db.irctc_userid_data
col_overdash_handle = db.irctc_over_dash_const_1
col_sus_mobile_handle = db.irctc_sus_mobile_numbers_test_1
col_case_overview = db.irctc_case_overview_trend

try:
    col_asn_handle.create_index("asn",unique=True, dropDups=True)
except:
    pass
try:
    col_userid_handle.create_index('USERNAME')
except:
    pass

