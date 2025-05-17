// Import Libraries
import { useEffect, useState, forwardRef } from 'react'
import {
  Button,
  Pagination,
  SelectPicker,
  Table,
  Modal,
  Loader,
  IconButton,
  Input,
  DateRangePicker,
  Rate,
  InputGroup,
  Whisper,
  Popover
} from 'rsuite'
import { validateUserCookiesFromSSR } from '../../utils/userVerification'
import { toast } from 'react-toastify'
import CollaspedOutlineIcon from '@rsuite/icons/CollaspedOutline'
import ExpandOutlineIcon from '@rsuite/icons/ExpandOutline'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSearch } from '@fortawesome/free-solid-svg-icons'
import SearchIcon from "@rsuite/icons/Search";
import { Circles } from 'react-loader-spinner'
const { Column, HeaderCell, Cell } = Table

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'
import Card from './card'
// Import Styles
import styles from './SuspiciousPNRs.module.scss'
import { useDispatch, useSelector } from 'react-redux'
import Router, { useRouter } from 'next/router'

import {
  zoneTrains,
  origTrains,
  zonalRailwayNames,
  zoneToStationNameMapping,
  stationNameToTrainNumberMapping,
  zonetotrainmap,
  SER_HWH,
  ER_HWH,
} from '../../utils/constant'

// A mapping object that maps tag codes to their corresponding descriptions
const tagMapping = {
	'USER_REG_BOOK_VPS': "User has registered from this VPS IP Address",
  'REG_MORE_THAN_5': "More than 5 User Registrations from this IP Address",
  'BOOKING_IP_VPS': "Booked PNR from VPS IP Address",
  'TK_MORE_THAN_20_ARP' : "More than 20 PNRs booked during ARP",
  'TK_MORE_THAN_20_AC' : "More than 20 PNRs booked during Tatkal AC",
  'TK_MORE_THAN_20_NON_AC' : "More than 20 PNRs booked during Tatkal Non-AC",
  'USED_BY_SUSPICIOUS_USER': "This IP has been used by a Suspicious User",
  'SUSPICIOUS_IP': "Booked from a Suspicious IP Address",
  'SUSPICIOUS_USER': "Booked by a Suspicious User",
  'USER_REG_SERIES_EMAIL': "Username is registered from a suspicious Email Address",
  'USER_SERIES_REG_VPS': "Username is a part of series, registered from VPS",
  'USER_REG_IP_ADDR_SAME_MORE_4':"Username is part of series, register from same IP and same address",
  'USER_SERIES_REG_NONVPS':"Username is a part of series, registered from NONVPS",
  'USER_REG_SERIES_NONVPS': "Username is a part of series, registered from NONVPS",
  'USER_REG_VPS': "User has been registered from a VPS IP Address",
  'USER_REG_SERIES_VPS' : "User has been registered from a VPS IP Address",
  'USER_SERIES_BOOK_VPS': "Username is a part of series, booked ticket from VPS",
  'USER_SERIES_BOOK_NONVPS':"Username is a part of series, booked ticket from Non-VPS",
  'USER_BOOK_VPS': "User has booked PNR from VPS",
  'USER_BOOK_MULTIPLE_IP': "User has booked PNR from multiple IP Addresses",
  'USER_REG_SAMEIP_SAMEADDR_MORE_4' : "User Registered from Same IP and Same Address More than 3 Times.",
  'USER_BOOK_SUSPICIOUS_MOBILE': "User Book Ticket through a suspicious mobile.",
  'INVALID_BOOKING_MOBILE' : "The mobile number does not have complete digit or formate incorrect",
  'INVALID_PIN_CODE': "Pincode does not have 6 digits",
  'DISPOSABLE_EMAIL' : "User Registered with Disposable domain",
  'USER_SERIES_REG_VPS': 'Username is a part of series, registered from VPS',

  'USER_SERIES_REG_NONVPS':
    'Username is a part of series, registered from NONVPS',
  // 'Register series from VPS IP Address',
  'USER_REG_VPS': 'User has been registered from a VPS IP Address',
  'USER_REG_SERIES_NONVPS': "Username is a part of series, registered from NONVPS",
  'USER_REG_VPS': "User has been registered from a VPS IP Address",
  'USER_REG_SERIES_VPS' : "User has been registered from a VPS IP Address",

  'SUS_REG_TIME_WITHIN_60_SEC':'Registered more than 3 times through same IP within 60 seconds',
  'SUS_FULLNAME_IP_MORE_5':'User registered with the suspicious fullname',
  'USER_REG_SERIES_COMMON_NAME':'Registered in series of Common Name of more than 15',
  'SUS_ADDRESS_IP_MORE_5':'User registered with the suspicious address',
  'SUS_EMAIL_IP_MORE_5':'User registered with the gibberish email',
  'SUS_USERNAME_IP_MORE_5':'User registered with the gibberish username',
  'INVALID_PINCODE':"Invalid pincode",
  'INVALID_REGISTERED_MOBILE':"Invalid registered mobile",
  'GIBBERISH_EMAIL' : "User Registered with an Email in series",
  'GIBBERISH_USERNAME' : "User Registered with a Username in series",
  'SUS_REG_TIME_60' : "More than 4 Users Registered through the same IP address within 60 seconds",
  'SUSPICIOUS_FULLNAME' : "More than 5 Users Registered with Same Full name and IP Address",
  'SUSPICIOUS_ADDRESS' : "More than 5 Users Registered with Same Physical Address and IP Address",
  'UNVERIFIED_USER' : "Unverified User",
  'GIBBERISH_FULLNAME' : "User registered with a Fullname in series",
  'GIBBERISH_ADDRESS' : "User registered with a Address in series",
  'SERIES_USERNAME' : "PNR booked with a Series of Username", 
  '5_PNR_BOOK_SAMEIP_60SEC' : "More than 5 PNR booked through the same IP address within 60 seconds",
  '5_PNR_BOOK_SAMEIP_SAMEDAY' : "More Than 5 PNR booked with same IP address in same day",
  'SAMEIP_MORE4_VPS' : "PNR booked using Same VPS IP more than 4 times",
  'TEMPORARY_NUMBER' : "PNR Booked using Suspicious Number",
  "4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL" : "More than 4 PNR booked using VPS and same IP pool",
  "4_USER_REGISTERED_USING_VPS_AND_SAME_IP_POOL" : "More than 4 Users Registered using VPS and same IP pool"
};

const tagCodes = {
  'UA1' : 'User Registered with an Email in series',
  'UA2' : 'User registered with a disposable Email Domain',
  'UA3' : 'User Registered with a Username in series',
  'UA4' : 'More than 4 Users Registered through the same IP address within 60 seconds',
  'UA5' : 'More than 4 users registered using VPS and same IP pool',
  'UA6' : "PNR booked using Same VPS IP more than 4 times",
  'UA7' : "More than 4 PNR booked using VPS and same IP pool",
  
  'UB1' : 'More than 5 Users Registered with Same Full name and IP Address',
  'UB2' : 'More than 5 Users Registered with Same Physical Address and IP Address',
  'UB3' : 'Unverified User',
  'UB4' : "PNR booked with a Series of Username",
  'UB5' : "More Than 5 PNR booked with same IP address in same day",
  'UB6' : "More than 5 PNR booked through the same IP address within 60 seconds",
  'UB7' : "PNR Booked using Suspicious Number",
  'UB8' : 'Registered in Series of Common Name of More than 15',

  'UC1' : 'User registered with a Fullname in series',
  'UC2' : 'User registered with a Address in series',
  'UC3' : 'Multi-IP Bookings',
  'UC4' : 'Username is a part of series, registered from NONVPS',
  'UC5' : 'User has been registered from a VPS IP Address',
  'UC6' : 'VPS Booking',
  'UC7' : 'User Series Booking',
  'UC8' : 'User Series Booking',
  'UC9' : 'User has been registered from a VPS IP Address',
  'UC10' : 'Username is a part of series, registered from NONVPS',
  'UC11' : 'Username part of series, registered from vps',
  'UC12' : 'IP Address used VPS to book ticket',
  'UC13' : 'IP Address used to register more than 5 users',
  'UC14' : 'More than 20 tickets booked using same IP',
  'UC15' : 'More than 20 tickets booked using same IP',
  'UC16' : 'More than 20 tickets booked using same IP',
  'UC17' : 'Username registered from suspicious Emai',
  "UC18" : "VPS used to book ticket",
  "UC19" : "Suspicious User", 
  "UC20" : "Invalid pincode",
  "UC21" : "Suspicious Booking Mobile Number",
  "UC22" : "Suspicious IP",
  "UC23" : "Suspicious User",
  "UC24" : "Invalid Mobile number used to book ticket",
  "UC25" : "Invalid registered mobile"
};

const rowKey = "PNR_NUMBER";

// A function that transforms tag codes into their corresponding descriptions and returns a JSX element.
const codeToTagTransform = (tags) => {
  return (
    <div className={styles.tagBubble}>
      {tags.map((tag) => {
        // For each tag code in the "tags" array, access its corresponding description in the
        return <p>{tagMapping[tag]}</p>
      })}
    </div>
  )
}

const ExpandCell = ({
  rowData,
  dataKey,
  expandedRowKeys,
  onChange,
  ...props
}) => (
  <Cell {...props} style={{ padding: 5 }}>
    <IconButton
      appearance="subtle"
      onClick={() => {
        onChange(rowData)
      }}
      icon={
        expandedRowKeys.some((key) => key === rowData[rowKey]) ? (
          <CollaspedOutlineIcon />
        ) : (
          <ExpandOutlineIcon />
        )
      }
    />
  </Cell>
)

const renderRowExpanded = (rowData) => {
  console.log('render expanded called')
  return (
    <div classname={styles.displayrfi}>
        RFIs: 
        <div>
          {rowData?.RFI_RULE != [] ?
            (<span>
            <Whisper
              followCursor
              speaker={
                <Popover>
                  {rowData?.RFI_RULE?.map((x) => {
                    return (
                      <span
                        key={x}
                        className={styles.tagCodes}
                      >
                        <span
                          className={styles.popovercode}
                        >
                          {x} : {tagCodes[x]}
                        </span>
                      </span>
                    );
                  })}
                </Popover>
              }
            >
              <span className={styles.rfiStyles}>
                {rowData?.RFI_RULE?.join(", ") || "N.A."}
              </span>
            </Whisper>
          </span>
        ) : (
          <span>
            <Whisper
              followCursor
              speaker={
                <Popover>
                  <span className={styles.tagCodes}>
                    <span className={styles.popovercode}>
                      NOT AVAILABLE
                    </span>
                  </span>
                </Popover>
              }
            >
              <span>N.A.</span>
            </Whisper>
          </span>)}
        </div>
    </div>
  )
}

const selectData = ["Booking Date", "Journey Date"].map((item) => ({
  label: item,
  value: item,
}));
 
// Suspicious PNRs Page
const SuspiciousPNRsPage = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.suspected_pnrs) {
      router.push('/overview')
    }
  }, [])

  // This code defines a React functional component that uses the useState hook to manage
  const [expandedRowKeys, setExpandedRowKeys] = useState([])
  const dispatch = useDispatch()
  const userDept = useSelector((state) => state.persistedReducer.dept)

  // ------------------------------ Page Setup ------------------------------ //
  const [loading, setLoading] = useState(false)
  // ------------------------------ Search Section ------------------------------ //
  const [trainList, setTrainList] = useState([])
  // zonalRailway contains the zonal railway value specified by the user for the filter.
  const [zonalRailway, setZonalRailway] = useState('');
  // stationName contains the station name value specified by the user for the filter.
  const [stationName, setStationName] = useState('')
  // zonalStationNames contains the station names available in the zonal railway as specified by the user for the filter.
  const [zonalStationNames, setZonalStationNames] = useState([])
  // stationList contains the station list value specified by the user for the filter.
  const [stationList, setStationList] = useState([])
  // trainNumber contains the train number value specified by the user for the filter.
  const [trainNumber, setTrainNumber] = useState([])
  // trainNumberSelect contains selected the train number specified by the user for the filter.
  const [trainNumberSelect, setTrainNumberSelect] = useState(0)
  // stationTrainNumbers contains the train numbers starting from the station name as specified by the user for the filter.
  const [stationTrainNumbers, setStationTrainNumbers] = useState([])
  //  `dateRange`: stores an array representing the selected date range.
  const [dateRange, setDateRange] = useState([])
  // - `suspectedPNRsData`: stores an array of data representing suspected PNRs.
  const [suspectedPNRsData, setSuspectPNRData] = useState([])
  // - `supectPNRCount`: stores the count of suspected PNRs.
  const [supectPNRCount, setSuspectPNRCount] = useState(0)
  // - `open`: a boolean value representing whether a modal window is open or not.
  const [open, setOpen] = useState(false)
  // - `rows`: stores the number of rows to be displayed in a table.
  const [rows, setRows] = useState(0)
  // - `handleOpen`: a function that sets the `open` state to true when called.
  const handleOpen = () => setOpen(true)
  // - `handleClose`: a function that sets the `open` state to false when called.
  const handleClose = () => setOpen(false)
  // - `modalComment`: stores the comment entered by the user in a modal window.
  const [modalComment, setModalComment] = useState('')
  // - `formValue`: an object storing the value of the textarea in a modal window.
  const [formValue, setFormValue] = useState({ textarea: '' })
  // - `rateValue`: stores the value selected by the user in a rating field.
  const [rateValue, setRateValue] = useState(0)
  // - `inputValue`: stores the input value entered by the user in a search field.
  const [inputValue, setInputValue] = useState('')
  // - `query`: stores the current search query entered by the user.
  const [query, setQuery] = useState('')
  // - `commData`: stores the comments data fetched from an external API.
  const [commData, setCommData] = useState()
  // - `commentPNR`: stores the PNR number associated with a specific comment.
  const [commentPNR, setCommentPNR] = useState()
  // page is the state of the page number in pagination.
  const [page, setPage] = useState(1)
  // set date to get suspicious pnrs of a specific date
  const [suspiciousPnrDate, setSuspiciousPnrDate] = useState()
  //Main Table pagination display total rows and total pages and there states
  const [totalRowsMainTable, setTotalRowsMainTable] = useState(0);
  const [totalPagesMainTable, setTotalPagesMainTable] = useState(0);

  const [stationSelected, setStationSelected] = useState([]);
  const [selectedDateFormat, setSelectedDateFormat] = useState('Booking Date');
  
  //  The `handleExpanded` function is used to update the `expandedRowKeys` state whenever a row is expanded or collapsed.
  const handleExpanded = (rowData, dataKey) => {
    console.log(expandedRowKeys)
    let open = false
    const nextExpandedRowKeys = []
    expandedRowKeys.forEach((key) => {
      if (key === rowData[rowKey]) {
        open = true
      } else {
        nextExpandedRowKeys.push(key)
      }
    })
    if (!open) {
      nextExpandedRowKeys.push(rowData[rowKey])
    }
    setExpandedRowKeys(nextExpandedRowKeys)
  }
  //  This is the start of a useEffect hook, which will be executed after the component has mounted.
  useEffect(() => {
    let fp = [];
    for (
      let j = 0;
      j < Object.keys(stationNameToTrainNumberMapping).length;
      j++
    ) {
      fp = fp.concat(
        stationNameToTrainNumberMapping[
        Object.keys(stationNameToTrainNumberMapping)[j]
        ]
      );
    }
    setStationTrainNumbers(fp.map((item) => ({ label: item, value: item })));
    // Set the `zonalStationNames` state to an array of objects with `label` and `value` properties,
    setZonalStationNames(
      Object.keys(stationNameToTrainNumberMapping).map((item) => ({
        label: item,
        value: item,
      }))
    );
  }, []);

  // changeZonalRailway sets the zonal railway filter as selected by the user and updates the names of the stations for the next filter.
  const changeZonalRailway = (zonalRailwaySelected) => {
    setTrainNumberSelect(0);
    let jp = [];
    for (
      let i = 0;
      i < zoneToStationNameMapping[zonalRailwaySelected].length;
      i++
    ) {
      // console.log(zoneToStationNameMapping[zonalRailwaySelected][i])
      for (
        let j = 0;
        j < zoneToStationNameMapping[zonalRailwaySelected][i].length;
        j++
      ) {
        // console.log(zoneToStationNameMapping[zonalRailwaySelected][i])
        jp = jp.concat(
          stationNameToTrainNumberMapping[
            zoneToStationNameMapping[zonalRailwaySelected][i]
          ].map(String),
        )
      }

      // jp.concat(zoneToStationNameMapping[zonalRailwaySelected][i].map(String))
    }
    setTrainNumber(Array.from(new Set(jp)))
    // setTrainNumber(jp);
    // If new zonal railway is selected, clear out the train numbers as station name will have to be selected again.

    if (zonalRailwaySelected !== zonalRailway) {
      setStationTrainNumbers([])
    }

    // Update the zonal railway selected.
    setZonalRailway(zonalRailwaySelected)

    // Update the station names list available in the zone for the next filter.
    setZonalStationNames(
      zoneToStationNameMapping[zonalRailwaySelected].map((item) => ({
        label: item,
        value: item,
      })),
    )

    setStationTrainNumbers(
      zonetotrainmap[zonalRailwaySelected].map((item) => ({
        label: item,
        value: item,
      })),
    )

    try {
      // Check if the station name is 'HOWRAH JN (HWH)'
      if (stationName == 'HOWRAH JN (HWH)') {
        try {
          // If the zonal railway selected is South Eastern Railway (SER), set the station and train
          if (zonalRailwaySelected == 'South Eastern Railway (SER)') {
            setStationTrainNumbers(
              SER_HWH.map((item) => ({
                label: item,
                value: item,
              })),
            )
            setTrainNumber(SER_HWH.map((item) => item.toString()))
            // If the zonal railway selected is Eastern Railway (ER), set the station and train numbers accordingly.
          } else if (zonalRailwaySelected == 'Eastern Railway (ER)') {
            setStationTrainNumbers(
              ER_HWH.map((item) => ({
                label: item,
                value: item,
              })),
            )
            setTrainNumber(ER_HWH.map((item) => item.toString()))
          }
          // If an error occurs, set the station train numbers to the default mapping
        } catch {
          setStationTrainNumbers(
            stationNameToTrainNumberMapping[stationName].map((item) => ({
              label: item,
              value: item,
            })),
          )
        }
        // If the station name is not 'HOWRAH JN (HWH)', set the station train numbers to the default mapping.
      } else {
        setStationTrainNumbers(
          stationNameToTrainNumberMapping[stationName].map((item) => ({
            label: item,
            value: item,
          })),
        )
      }
      // If an error occurs, set the station train numbers and train numbers to the default,
      // mapping for the selected zonal railway.
    } catch (e) {
      setStationTrainNumbers(
        zonetotrainmap[zonalRailwaySelected].map((item) => ({
          label: item,
          value: item,
        })),
      )
      setTrainNumber(
        zonetotrainmap[zonalRailwaySelected].map((item) => item.toString()),
      )
    }

    // Initialize empty arrays for storing train numbers and station names
    let op = []
    let slist = []
    // Loop through each train in the selected zonal railway
    for (
      let i = 0;
      i < zoneTrains[zonalRailwaySelected]['trains'].length;
      i++
    ) {
      // Loop through each originating train in the data set
      for (let j = 0; j < origTrains.length; j++) {
        // Add the current train to the station list array
        slist.push(zoneTrains[zonalRailwaySelected]['trains'][i])
        // If the current originating train matches the selected zonal railway and station
        if (
          origTrains[j]['Originating Rly'] ==
          zoneTrains[zonalRailwaySelected]['code'] &&
          origTrains[j]['From'] == zoneTrains[zonalRailwaySelected]['trains'][i]
        ) {
          op.push(origTrains[j]['Train No.'].toString())
        }
      }
    }
    // Remove any duplicates from the train number array and set the state
    setTrainNumber(Array.from(new Set(op)))
    // Convert the train number array into an array of objects and set the state
    setStationTrainNumbers(
      op.map((item) => ({
        label: item,
        value: item,
      }))
    );
    // Convert the station list array into an array of strings and set the state.
    setStationList(Array.from(new Set(slist)).map((item) => item.toString()));
  };

  // changeZonalRailway sets the zonal railway filter as selected by the user and updates the names of the stations for the next filter.
  const changeTrainNumbers = (stationNameSelected) => {
    console.log('stationNameSelected', stationNameSelected)
    setTrainNumberSelect(0);

    setTrainNumber(
      stationNameToTrainNumberMapping[stationNameSelected].map(String),
    )
    // Update the zonal railway selected.
    setStationName(stationNameSelected)

    // Update the station names list available in the zone for the next filter.
    // Check if the station name is 'HOWRAH JN (HWH)'
    if (stationNameSelected == 'HOWRAH JN (HWH)') {
      try {
        // If the zonal railway selected is South Eastern Railway (SER), set the station and
        //  train numbers accordingly
        if (zonalRailway == 'South Eastern Railway (SER)') {
          setStationTrainNumbers(
            SER_HWH.map((item) => ({
              label: item,
              value: item,
            })),
          )
          setTrainNumber(SER_HWH.map((item) => item.toString()))
        }
        if (zonalRailway == 'Eastern Railway (ER)') {
          setStationTrainNumbers(
            ER_HWH.map((item) => ({
              label: item,
              value: item,
            })),
          )
          setTrainNumber(ER_HWH.map((item) => item.toString()))
        }
        // If an error occurs, set the station train numbers and train numbers to the default,
        // mapping for the selected zonal railway.
      } catch (e) {
        setStationTrainNumbers(
          stationNameToTrainNumberMapping[stationNameSelected].map((item) => ({
            label: item,
            value: item,
          })),
        )
        setTrainNumber(
          stationNameToTrainNumberMapping[stationNameSelected].map((item) =>
            item.toString(),
          ),
        )
      }
    } else {
      setStationTrainNumbers(
        stationNameToTrainNumberMapping[stationNameSelected].map((item) => ({
          label: item,
          value: item,
        })),
      )
      setTrainNumber(
        stationNameToTrainNumberMapping[stationNameSelected].map((item) =>
          item.toString(),
        ),
      )
    }
  }

  // searchHandler fetches the suspicious PNRs for the filter values specified by the user.
  const searchHandler = () => {
    setPage(1)
    if (trainNumberSelect) {
      paginationFunction(1, [trainNumberSelect.toString()])
    } else {
      paginationFunction(1, trainNumber)
    }
  }

  // Defines a function named downloadReport that takes one parameters: 'train'.
  // The function is declared as an fetch function, which means it can data from the given endpoints.
  //  Sends a POST request to the URL'/api/download-sus-pnrs'.
 
  const downloadReport = async (train_no) => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const response = await fetch('/api/download-sus-pnrs', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          station_list: stationSelected.length > 0 ? stationSelected : stationList,
          search_pnr:query,
          filter_date:selectedDateFormat != null?selectedDateFormat:"",
          starting_date:
            dateRange != null && dateRange?.length != 0
              ? dateRange[0]
              : new Date(0),
              ending_date:
            dateRange != null && dateRange?.length != 0
              ? dateRange[1]
              : new Date(),
        }),
      });
  
      if (response.ok) {
        // File download successful
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // a.download = `SUSPECTED_PNR_from_${dateRange[0].toDateString().replaceAll(' ', '_')}_to_${dateRange[1].toDateString().replaceAll(' ', '_')}_${selectedDateFormat}.csv`
        // a.download = 'Suspicious_PNR_List_' + new Date().toDateString().replaceAll(' ', '_') + '.xlsx';

        const startDateString = dateRange && dateRange.length !== 0
        ? dateRange[0]?.toDateString().replaceAll(' ', '_')
        : new Date().toDateString().replaceAll(' ', '_');

        const endDateString = dateRange && dateRange.length !== 0
          ? dateRange[1]?.toDateString().replaceAll(' ', '_')
          : new Date().toDateString().replaceAll(' ', '_');

        const selectedDateSuffix = selectedDateFormat ? `_${selectedDateFormat}` : '';

        const fileName = `SUSPECTED_PNR_from_${startDateString}_to_${endDateString}${selectedDateSuffix}.csv`;

        a.download = fileName;
        a.click();
  
        toast.success('File downloaded successfuly !', {
          position: 'top-center',
          autoClose: 3000, // 3 seconds
        });
      } 
      else {
        // File download failed
        toast.error('Error while downloading the file. Please try again later.', {
          position: 'top-center',
          autoClose: 4000, // 4 seconds
        });
      }
    } catch (error) {
      // Error while making the API request
      toast.error('An error occurred while processing your request.', {
        position: 'top-center',
        autoClose: 4000, // 4 seconds
      });
    }
  };
  

  // clearHandler sets the filter parameters to empty string.
  const clearHandler = () => {
    
    // Set the Zonal Railway to empty string.
    setZonalRailway("");

    // Set the Station Name to empty string.
    setStationName("");

    // Set the Train Number to '0'.
    setTrainNumber([]);
    setDateRange([]);
    setStationList([]);
    setQuery('');
    setSelectedDateFormat([]);

    setTrainNumberSelect(0);

    let fp = [];
    for (
      let j = 0;
      j < Object.keys(stationNameToTrainNumberMapping).length;
      j++
    ) {
      fp = fp.concat(
        stationNameToTrainNumberMapping[
          Object.keys(stationNameToTrainNumberMapping)[j]
        ],
      )
    }
    // set the station train numbers to the default mapping.
    setStationTrainNumbers(fp.map((item) => ({ label: item, value: item })))

    // Set the `zonalStationNames` state to an array of objects with `label` and `value` properties,
    // where `label` and `value` are the same value from the `zone`.
    setZonalStationNames(
      Object.keys(stationNameToTrainNumberMapping).map((item) => ({
        label: item,
        value: item,
      })),
    )

  };

  // ------------------------------ Data Section ------------------------------ //

  // paginationFunction fetches values from backend based on the page number.
  const paginationFunction = async (pageNumber, train_no) => {
    setLoading(true)
    const data = await fetch('/api/fetch-sus-pnrs', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: pageNumber,
        // trainno: train_no,
        station_list: stationSelected.length > 0 ? stationSelected : stationList,
        search_pnr:query,
        filter_date:selectedDateFormat != null?selectedDateFormat:"",
        starting_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[0]
            : new Date(0),
            ending_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[1]
            : new Date(),
      }),
    })
    .then((response) => response.json())
    // Setup the data list from the parsed res  ponse.
    setSuspectPNRData(data?.data_list?.map((item) => JSON.parse(item)))
    // setSuspectPNRCount(data?.page_count)
    setTotalRowsMainTable(data?.total_rows)
    setTotalPagesMainTable(data?.total_pages)
    // Set the loading parameter to be 'false' once API calls are completed to remove the loader.
    setLoading(false)
  }

  // handlePageChange changes the page number to the value passed as parameter.
  const handlePageChange = (pageNumber) => {
    // Set the page number.
    setPage(pageNumber)

    // Fetch the data for the specified page number.
    if (trainNumberSelect) {
      paginationFunction(pageNumber, [trainNumberSelect.toString()])
    } else {
      paginationFunction(pageNumber, trainNumber)
    }
  }

  // Defines a function named fetchPNRComments that takes one parameters: pnr .
  async function fetchPNRComments(pnr) {
    const data = await fetch('/api/fetch-pnr-comments', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pnr_no: pnr,
      }),
    }).then((res) => res.json())
    await setCommData(data.data_list.map((item) => JSON.parse(item)))
    if (data.data_list.length > 0) {
      await setCommData(JSON.parse(data?.data_list[0]))
      await setRateValue(JSON.parse(data?.data_list[0])['RATE'])
    }
  }

  // Defines a function named submitPNRComment that takes two parameters: pnr, comment_data.
  function submitPNRComment(pnr, comment_data) {
    fetch('/api/submit-pnr-comment', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pnr_no: pnr,
        comment: comment_data,
        rate: rateValue,
      }),
    })
      .then((response) => {
        if (response.ok) {
          toast.success(`Comment Added to PNR ${pnr}`)
        } else {
          toast.error(`HTTP error, status = ${response.status}`)
        }
      })
      .catch((error) => {
        console.error(error)
      })
  }

  // Defines a function named deletePNRComment that takes two parameters: pnr, comment_id.
  function deletePNRComment(pnr, comment_id) {
    fetch('/api/delete-pnr-comment', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pnr_no: pnr,
        cid: comment_id,
      }),
    })
      .then((response) => {
        if (response.ok) {
          toast.success(`Comment Deleted to PNR ${pnr}`)
        } else {
          toast.error(`HTTP error, status = ${response.status}`)
        }
      })
      .catch((error) => {
        console.error(error)
      })
  }

  const handleViewComments = (pnr) => {
    setModalComment('')
    setRateValue(0)
    setCommentPNR(pnr)
    handleOpen()
    fetchPNRComments(pnr)
  }

  const handleCommentSubmit = (pnr, comment_data) => {
    if ((comment_data.length > 0) & (rateValue > 0)) {
      submitPNRComment(pnr, comment_data);
      handleClose(true);
    } else {
      toast.error('Please enter data comment as well as rating!')
    }

  };

  // For view comments modal
  const handleEntered = () => {
    setTimeout(() => setRows(80), 2000)
  }

  const Textarea = forwardRef((props, ref) => (
    <Input {...props} as="textarea" ref={ref} />
  ))

  const handleSearch = () => {
    searchHandler();
    console.log(query);
  }
  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }
 
  const handleChange = (event) => {
    setQuery(event.target.value);
  };
  const [isLoading, setIsLoading] = useState(false);  

  // Function for handling export button click.
  // It check if train Number is Selected then show download and report other wise not.
  const exportHandler = async () => {
    setIsLoading(true);
   try {
     await downloadReport(trainNumber);
   } catch (error) {
     console.error('Error occurred while downloading the VPS export:', error);
   } finally {
     setIsLoading(false);
   }
  //  if (trainNumberSelect) {
  //    downloadReport([trainNumberSelect.toString()])
  //  } //if uncomment this code toast is displaying 2 times
 }
  // Render the page.
  return (
    <div className={styles.dashboard}>
      {isLoading && (
        <div className={styles.loadingPopup}>
          <div className={styles.loadingOverlay}></div>
          <div className={styles.loadingContent}>
          <Circles
            height="50"
            width="50"
            color="black"
            ariaLabel="circles-loading"
            wrapperStyle={{}}
            wrapperClass=""
            visible={true}
          />
            <span className={styles.loadingText}>Loading...</span>
          </div>
        </div>
      )}

      {/* MODAL FOR COMMENTS IN SUSPICIOUS PNR'S */}
      <Modal
        open={open}
        onClose={handleClose}
        onEntered={handleEntered}
        onExited={() => {
          setRows(0);
        }}
       >
        <Modal.Header>
          <Modal.Title><h4>Review & Feedback!</h4></Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {rows ? (
            <div>
              <Card key={commData?.CID} card={commData} />
              <br />
              {/* {commData?.CID ? (
                    <div>
                      <label>
                        <h4>
                          Feedback : <br />
                        </h4>
                      </label>
                      <Rate readOnly value={rateValue} />
                    </div>
                  ) : null} */}
            </div>
          ) : (
            <div style={{ textAlign: "center" }}>
              <Loader size="md" />
            </div>
          )}
        </Modal.Body>
        {rows ? (
          <label>
            Feedback Comment:
            <textarea
              rows={5}
              cols={80}
              value={modalComment}
              style={{
                backgroundColor: 'white',
              }}
              onChange={(e) => setModalComment(e.target.value)}
            />
            <br />
            <br />
            <h5>
              <b>Feedback:</b>
            </h5>
            <Rate
              value={rateValue}
              size="md"
              onChange={(newRate) => setRateValue(newRate)}
            />
          </label>
        ) : null}
        <Modal.Footer>
          {rows ? (
            <Button
              onClick={() => handleCommentSubmit(commentPNR, modalComment)}
              appearance="primary"
            >
              Submit
            </Button>
          ) : null}
          <Button onClick={handleClose} appearance="subtle">
            Cancel
          </Button>
        </Modal.Footer>
      </Modal>

      {/* MAIN SUS PNR: Page */}
      {(allowed_page?.suspected_pnrs && allowed_actions?.view) && (
        <>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board heading="Suspected PNRs" router={Router} />
                
            <div className={styles.search + ' card shadow-sm col display-4'}>
              <SelectPicker
                label="Originating Railway"
                className="mb-3"
                data={
                  // userDept?.length > 0
                  //   ? [{ label: userDept, value: userDept }]
                  //   : zonalRailwayNames
                  zonalRailwayNames
                }
                value={zonalRailway}
                cleanable={false}
                onChange={(newvalue) => changeZonalRailway(newvalue)}
                style={{ width: 800 }}
              />

              <SelectPicker
                label="Originating Station"
                className="mb-3"
                data={zonalStationNames}
                value={stationName}
                cleanable={false}
                // onChange={(newvalue) => setStationName(newvalue)}
                // onChange={(newvalue) => changeTrainNumbers(newvalue)}
                onChange={(newvalue) => {
                  setStationName(newvalue);
                  setStationSelected(() => newvalue)
              }}
                style={{ width: 800 }}
              />

              {/* <SelectPicker
                label="Train Number"
                data={stationTrainNumbers}
                cleanable={false}
                onChange={(newvalue) => setTrainNumberSelect(newvalue)}
                value={trainNumberSelect}
                style={{ width: 800 }}
              /> */}

                <div className={styles.buttonsContainer}>
                 <DateRangePicker
                  className="float-end"
                  placement="topStart"
                  placeholder="Select Date Range"
                  style={{ width: 250 }}
                  cleanable={false}
                  value={dateRange}
                  onChange={(newValueDate) => setDateRange(newValueDate)}
                /> 
              </div>
               <div className={styles.subContainer2}>
               <SelectPicker
                label="Filter by"
                searchable={false}
                style={{ width: 250 }}
                className={styles.selectBoxes + "float-end"}
                data={selectData}
                value={selectedDateFormat}
                onChange={(newValue) => setSelectedDateFormat(newValue)}
              />
              </div>
              <div className={styles.buttonsContainer}>
                <div className={styles.allbtn}>      
                <div className={styles.searchContainer}>
                  <input
                    type="text"
                    className={styles.searchInput}
                    placeholder="Search PNR"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyPress}
                  />
                  <InputGroup.Addon>
                  <SearchIcon  style={{height: "17px", border:"transparent"}}  onClick={handleSearch} />
                </InputGroup.Addon>      
                </div>    
               
                <Button
                  className={styles.submitButton}
                  onClick={searchHandler}
                  appearance="primary"
                > Submit
                </Button>

                {allowed_actions?.download && (
                  <Button
                    className={styles.exportButton}
                    onClick={exportHandler}
                    appearance="primary"
                    // disabled={!allSelectsFilled}
                    disabled={zonalRailway == '' && stationName == '' && trainNumberSelect == 0  && dateRange == '' && query == '' ? true : false}
                    // disabled={dateRange == ''? true : false}   
                  > Export
                  </Button>
                )}
                
                <Button
                  className={styles.clearButton}
                  onClick={clearHandler}
                  appearance="ghost"
                > Clear
                </Button>
                </div>
              </div>
            </div>

            {/* suspectedPNRsData.length > 0 && */}
            <div className={styles.tableContainer + ' col'}>
              <Table
                shouldUpdateScroll={false}
                loading={loading} // Prevent the scrollbar from scrolling to the top after the table content area height changes.
                autoHeight={1}
                rowExpandedHeight={75}
                data={suspectedPNRsData}
                rowKey={rowKey}
                expandedRowKeys={expandedRowKeys}
                onRowClick={(data) => {
                  console.log(data)
                }}
                renderRowExpanded={renderRowExpanded}
              >
                <Column minWidth={50} flexGrow={0.1} fullText align="center">
                  <HeaderCell>#</HeaderCell>
                  <ExpandCell
                    dataKey="PNR_NUMBER"
                    expandedRowKeys={expandedRowKeys}
                    onChange={handleExpanded}
                  />
                </Column>

                <Column minWidth={100} flexGrow={0.2} fullText >
                  <HeaderCell>PNR</HeaderCell>
                  <Cell>{(rowData) => rowData['PNR_NUMBER']}</Cell>
                </Column>

                <Column minWidth={110} flexGrow={0.2} fullText >
                  <HeaderCell>Journey Date</HeaderCell>
                  <Cell>
                    {(rowData) =>
                      new Date(rowData.JOURNEY_DATE.$date).toDateString()
                        ? new Date(rowData.JOURNEY_DATE.$date).toDateString()
                        : null
                    }
                  </Cell>
                </Column>

                <Column minWidth={110} flexGrow={0.2} fullText >
                  <HeaderCell>Booking Date</HeaderCell>
                  <Cell>
                    {(rowData) =>
                      new Date(rowData.BOOKING_DATE.$date).toDateString()
                        ? new Date(rowData.BOOKING_DATE.$date).toDateString()
                        : null
                    }
                  </Cell>
                </Column>

                <Column minWidth={100} flexGrow={0.3} fullText >
                  <HeaderCell>Passenger Mobile Number</HeaderCell>
                  <Cell>{(rowData) => rowData['BOOKING_MOBILE']}</Cell>
                </Column>
                <Column minWidth={100} flexGrow={0.2} fullText >
                  <HeaderCell>Train Number</HeaderCell>
                  <Cell>{(rowData) => rowData.TRAIN_NUMBER}</Cell>
                </Column>
                <Column minWidth={100} flexGrow={0.2} fullText >
                  <HeaderCell>Boarding Station</HeaderCell>
                  <Cell>{(rowData) => rowData.FROM}</Cell>
                </Column>
                <Column minWidth={100} flexGrow={0.2} fullText >
                  <HeaderCell>Destination Station</HeaderCell>
                  <Cell>{(rowData) => rowData.TO}</Cell>
                </Column>
                <Column minWidth={100} flexGrow={0.2} fullText >
                  <HeaderCell>Ticket Type</HeaderCell>
                  <Cell>{(rowData) => rowData.TK_TYPE}</Cell>
                </Column>
                <Column minWidth={150} flexGrow={0.2} fullText >
                  <HeaderCell>Feedbacks</HeaderCell>
                  <Cell style={{ padding: '6px' }}>
                    {(rowData) => (
                      <Button
                        appearance="primary"
                        onClick={() => handleViewComments(rowData['PNR_NUMBER'])}
                      >
                        View Feedback
                      </Button>
                    )}
                  </Cell>
                </Column>
              </Table>

              <div className={styles.pagination}>
                <Pagination
                  prev
                  next
                  first
                  last
                  ellipsis
                  placement='RightStart'
                  boundaryLinks
                  maxButtons={5}
                  size="xs"
                  layout={['total',"-", '|', 'pager', 'skip']}
                  total={totalRowsMainTable}
                  pages={totalPagesMainTable}
                  limit={[10]}
                  activePage={page}
                  onChangePage={handlePageChange}
                />
              </div>
            </div>
          </div>
        </>
      )}
      
    </div>
  )
}

export default SuspiciousPNRsPage

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res)
}
