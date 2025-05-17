map_pnr_tags = {
    "SERIES_USERNAME" : "PNR booked with a Series of Username", 
    "5_PNR_BOOK_SAMEIP_60SEC" : "More than 5 PNR booked through the same IP address within 60 seconds",
    "5_PNR_BOOK_SAMEIP_SAMEDAY" : "More Than 5 PNR booked with same IP address in same day",
    "SAMEIP_MORE4_VPS" : "PNR booked using Same VPS IP more than 4 times",
    "TEMPORARY_NUMBER" : "PNR Booked using Suspicious Number",
    "4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL" : "More than 4 PNR booked using VPS and same IP pool"
}

map_rfi_tags = {

    # user tags - HIGH
    'GIBBERISH_EMAIL' : 'UA1',
    'DISPOSABLE_EMAIL' : 'UA2',
    'GIBBERISH_USERNAME' : 'UA3',
    'SUS_REG_TIME_60' : 'UA4',
    "4_USER_REGISTERED_USING_VPS_AND_SAME_IP_POOL" : 'UA5',

    # pnr tags - HIGH
    "SAMEIP_MORE4_VPS" : 'UA6',
    "4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL" : 'UA7',

    # user tags - MEDIUM
    'SUSPICIOUS_FULLNAME' : 'UB1',
    'SUSPICIOUS_ADDRESS' : 'UB2',
    'UNVERIFIED_USER' : 'UB3',

    # pnr tags - MEDIUM
    "SERIES_USERNAME" : 'UB4',
    "5_PNR_BOOK_SAMEIP_SAMEDAY" : 'UB5',
    "5_PNR_BOOK_SAMEIP_60SEC" : 'UB6',
    "TEMPORARY_NUMBER" : 'UB7',

    # user tags - LOW
    'GIBBERISH_FULLNAME' : 'UC1',
    'GIBBERISH_ADDRESS' : 'UC2'
}


map_userid_tags = {
    'GIBBERISH_EMAIL' : "User Registered with an Email in series",
    'DISPOSABLE_EMAIL' : "User Registered with Disposable domain",
    'GIBBERISH_USERNAME' : "User Registered with a Username in series",
    'SUS_REG_TIME_60' : "More than 4 Users Registered through the same IP address within 60 seconds",
    'SUSPICIOUS_FULLNAME' : "More than 5 Users Registered with Same Full name and IP Address",
    'SUSPICIOUS_ADDRESS' : "More than 5 Users Registered with Same Physical Address and IP Address",
    'UNVERIFIED_USER' : "Unverified User",
    'GIBBERISH_FULLNAME' : "User registered with a Fullname in series",
    'GIBBERISH_ADDRESS' : "User registered with a Address in series",
    "4_USER_REGISTERED_USING_VPS_AND_SAME_IP_POOL" : "More than 4 Users registered using VPS and same IP pool",
    "TEMPORARY_NUMBER" : "User registered using Suspicious Office Mobile"
}

map_vps_tags = {
    0 : "False",
    1 : "True",
    True : "True",
    False : "False"
}

