// endpoint
const endPoint = process.env.API_ENDPOINT

// Import Libraries
import Image from 'next/image'
import { useEffect, useState, useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import {
  Table,
  Pagination,
  Whisper,
  IconButton,
  Popover,
  Dropdown,
  Tooltip,
  Checkbox,
  Button,
  Modal,
  DatePicker,
  Uploader,
  SelectPicker,
  DateRangePicker,
  Loader,
} from 'rsuite'
const { Column, HeaderCell, Cell } = Table
import { validateUserCookiesFromSSR } from '../../utils/userVerification'
import { startOfDay,endOfDay, subDays, startOfMonth, endOfMonth } from 'date-fns'
import Router, { useRouter } from 'next/router'

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'
import StackBarChart1 from '../../components/StackBar1'
import StackBarChart2 from '../../components/StackBar2'
import PiApexChart from '../../components/PiChart.jsx'
import question from '../../public/static/images/questionmark.svg'
import CloseIcon from '@rsuite/icons/Close';

// Import Assets
import users from '../../public/static/images/users.svg'
import ipAddress from '../../public/static/images/ip-address.svg'
import MoreIcon from '@rsuite/icons/legacy/More'
import { toast } from 'react-toastify'

import { Circles } from 'react-loader-spinner'


// Import Styles
import styles from './Users.module.scss'

// Import Store
import {
  initData
} from '../../store/slice/userreg'

const { afterToday } = DateRangePicker


// The ActionCell component is a custom component that likely renders a clickable cell in a table
const ActionCell = ({ rowData, dataKey, ...props }) => {
  return (
    <Cell {...props} className="link-group">
      <Whisper
        placement="autoVerticalStart"
        trigger="click"
        speaker={renderMenu}
      >
        <IconButton appearance="subtle" icon={<MoreIcon />} />
      </Whisper>
    </Cell>
  )
}

// The renderMenu function renders a Popover component that contains a Dropdown.Menu component,
const renderMenu = ({ onClose, left, top, className }, ref) => {
  const handleSelect = (eventKey) => {
    onClose()
    console.log(eventKey)
  }
  return (
    <Popover ref={ref} className={className} style={{ left, top }} full>
      <Dropdown.Menu onSelect={handleSelect}>
        <Dropdown.Item eventKey={1}>Block</Dropdown.Item>
        <Dropdown.Item eventKey={2}>Ignore</Dropdown.Item>
      </Dropdown.Menu>
    </Popover>
  )
}

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement, tooltip }) => (
  <Whisper
    trigger="hover"
    placement={placement}
    controlId={`control-id-${placement}`}
    speaker={<Tooltip arrow={false}>{tooltip}</Tooltip>}
  >
    {/* Render an Image component with a question mark icon and specified class */}
    <Image
      src={question}
      className={styles.questionmark}
      alt="Explanation"
    ></Image>
  </Whisper>
)

// The ActionCell component is a custom component that likely renders a clickable cell in a table
const CheckCell = ({ rowData, onChange, checkedKeys, dataKey, ...props }) => (
  <Cell {...props} style={{ padding: 0 }}>
    <div style={{ lineHeight: '46px' }}>
      <Checkbox
        value={rowData[dataKey]}
        inline
        onChange={() => onChange(rowData[dataKey])}
        checked={checkedKeys?.includes(rowData[dataKey])}
      />
    </div>
  </Cell>
);

const defaultDate = [subDays(new Date(), 7), endOfDay(new Date())]


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
  '4_PNR_BOOKED_USING_VPS_AND_SAME_IP_POOL' : 'More than 4 PNR booked using VPS and same IP pool'
  }


// A function that transforms tag codes into their corresponding descriptions and returns a JSX element.
const codeToTagTransform = (tags) => {
  return (
    <div className={styles.tagBubble}>
      {tags?.map((tag) => {
        return <p>{tagMapping[tag]}</p>
      })}
    </div>
  )
}

// Dashboard Component
const SusUsers = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.user_registration_logs) {
      router.push('/overview')
    }
  }, [])

  // Initialise the dispatcher.
  const dispatch = useDispatch()
  // useridData: This is a piece of data from the Redux store that contains information about the user IDs.
  const userregData = useSelector((state) => state.userreg.data)
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false)
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1)
  // State variable for VPS ASN data
  const [vpsASN, setVpsAsn] = useState([])
  // State variable for non-VPS ASN data
  const [NonVpsASN, setNonVpsAsn] = useState([])
  // State variable for vendor user count
  const [vendorUser, setVendorUser] = useState(0)
  // State variable for VPS IP count
  const [vpsIP, setVpsIp] = useState(0)
  // State variable for total user count
  const [totalUser, setTotalUser] = useState(0)
  // State variable for total VPS count
  const [totalVps, setTotalVps] = useState(0)
  // State variable for date range in trend graph
  
  // State variable for number of rows per page in table
  const [pageRowCount, setPageRowCount] = useState(0)
  // State variable for table length
  const [tableLength, setTableLength] = useState(5)
  // State variable for viewing file date
  const [viewFileDate, setViewFileDate] = useState('')
  // State variable for daily flag
  const [showDaily, setShowDaily] = useState(false)
  // State variable for model value date
  const [modelValueDate, setModelValueDate] = useState()
  // State variable for file list
  const [fileList, setFileList] = useState([])
  // Reference for file uploader component
  const uploader = useRef()
  // State variable for non-VPS user data
  const [nonvpsUser, setNonVpsUser] = useState([])
  // State variable for VPS user data
  const [vpsUser, setVpsUser] = useState([])
  // State variable for vendor registration data
  const [vendorReg, setVendorReg] = useState([])
  // State variable for top VPS IP data
  const [topVpsIP, setTopVpsIP] = useState([])
  // State variable for log file history date filter
  const [logFileHistoryDateFilter, setLogFileHistoryDateFilter] = useState()
  // Define states for storing data and updating the UI
  const [susPendData, setSusPendData] = useState([])
  // const susPendData = [];
  const [susPendCount, setSusPendCount] = useState([])
  const [searchSusDate, setSearchSusDate] = useState()
  const [pageSus, setPageSus] = useState(1)
  const [checkedKeys, setCheckedKeys] = useState([])
  //  View History Modal pagination display total rows and total pages and there states
  const [uploadHistoryTableTotalRows, setUploadHistoryTableTotalRows] = useState(0);
  const [uploadHistoryTableTotalPages, setUploadHistoryTableTotalPages] = useState(0);
  //  View History Modal pagination display total rows and total pages and there states
  const [suspendedMainTableRows, setSuspendedMainTableRows] = useState(0);
  const [suspendedMainTablePages, setSuspendedMainTablePages] = useState(0);
  const [searchDateValue, setSearchDateValue] = useState();

  const [loadings, setLoadings] = useState(false);
  const [suspendedTableActivePage, setSuspendedTableActivePage] = useState(1);

  // Retrieve user role from the Redux store
  const userRole = useSelector((state) => state.persistedReducer.role)

  // uploader file data testing msg state
  const [validationMessage, setValidationMessage] = useState('');

  
  // Count of date between the start and the end date set in the 'dateRange' state, default a month (30 days)
  const [dateRangeDayCount, setDateRangeDayCount] = useState(30)  

  const [trendRange, setTrendRange] = useState([
    // startOfMonth(new Date()),
    // endOfMonth(new Date())
    subDays(new Date(), 7), 
    endOfDay(new Date())
  ])

  // tableLengthOptions provides different options for the number of entries to be displayed in charts.
  const tableLengthOptions = [5, 10, 15, 20].map((item) => ({
    label: item,
    value: item,
  }))

  const [uploadModal, setUploadModal] = useState()

  const CompactCell = (props) => <Cell {...props} style={{ color: 'blue' }} />

  // Initialise the date to be searched through the data.
  const overviewDate = useSelector((state) => state.dashboard.searchDate)

  // Defines a function named pagiFunc that takes three parameters: page_value, bDate, and searchValue.
  const pagiFunc = async (page_value, not_user) => {
    setLoading(true)
    //  Sends a POST request to the URL /api/analysis_list_all'.
    const data = await fetch('/api/analysis_list_all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
        notuser: false,
      }),
    }).then((res) => res.json())
    dispatch(initData(data?.data_list?.map((item) => JSON.parse(item))))
    // setPageRowCount(data?.page_count)
    setUploadHistoryTableTotalRows(data?.total_rows)
    setUploadHistoryTableTotalPages(data?.total_pages)
    setLoading(false)
  }

  const helloworld = (vuln) => {
    console.log('test')
  }

  const filesFilterDate = async (dateFilter) => {
    const data = await fetch('/api/analysis_list_find', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        searchDate: dateFilter,
        notuser: false,
      }),
    })
    .then((response) => response.json())
    // Dispatch an action with the initial page count data.
    dispatch(initData(data?.data_list?.map((item) => JSON.parse(item))))
    // Dispatch an action to set the total rows in the table for the filtered data.
    // setPageRowCount(data?.page_count)
    setUploadHistoryTableTotalRows(data?.total_rows)
    setUploadHistoryTableTotalPages(data?.total_pages)
    setLoading(false)
  }

  // Defines a function named downloadReport that takes one parameters: 'train'.
  const downloadReport = (f_name, f_hash) => {
    fetch('/api/log-download?f_hash=' + f_hash).then((response) => {
      response.blob().then((blob) => {
        let url = window.URL.createObjectURL(blob)
        let a = document.createElement('a')
        a.href = url
        a.download = 'Analysed_' + f_name
        a.click()
      })
    })
  }

  // This line sends a GET request to the API endpoint with the specified parameters and waits for
  const viewReport = async (f_date) => {
    const data = await fetch('/api/fetch-userid-data?log_date=' + f_date)
      .then((res) => res.json())
      .then((res) => JSON.parse(res['data'][0]))
      if(data) {
        setVpsAsn(data['VPS_ASN'])
        setNonVpsAsn(data['NON_VPS_ASN'])
        setVendorUser(data['VENDOR_USERS_COUNT'])
        setVpsIp(data['VPS_IP_POOL'])
        setTotalVps(data['TOTAL_VPS_USERS_REG'])
        setTotalUser(data['TOTAL_USERS_REG'])
        setShowDaily(true)
        setViewFileDate(f_date)
      }
  }

  // This function will be called when the user clicks the search button,
  const handleSearch = () => {
    setLoading(true)
    OverviewSearchDate(overviewDate, filterOverviewOptions)
  }


  // This function will be called when the user clicks the search button,
  const handleUserSearch = (page_value, searchDateValue) => {
    setLoadings(true);
    setPageSus(1);
    setSuspendedTableActivePage(1);
    pagiFuncPend(1,page_value, searchDateValue)
  }

  const handlePageChange = (dataKey) => {
    setLoading(true)
    setPage(dataKey)
    pagiFunc(dataKey)
  }


  const handleMainPageChange = (dataKey, page_value) => {
    setLoadings(true)
    setSuspendedTableActivePage(dataKey)
    pagiFuncPend(dataKey,page_value)
  }

  // This function will be called when the user selects a new limit in the limit dropdown,
  const handleChangeLimit = (dataKey) => {
    setPage(1)
    setLimit(dataKey)
    pagiFunc(1, dataKey)
  }

  // Function to open the modal
  const openModal = () => {
    setUploadModal(true);
    setValidationMessage('');
    setFileList([])
  }

  // Onsubmit close or remove the modal
  const SubmitcloseModal = () => {
    setUploadModal(false)
    // setTimeout(function () {
    //   Router.reload()
    // }, 60000)
  }

  // Function to close the modal
  const closeModal = () => {
    setValidationMessage('');
    setUploadModal(false)
  }

  // Defines a function named searchTrendRange that display date range for suspected ip.
  const searchTrendRange = async (trendRange) => {
   
    if(trendRange === null || trendRange === undefined || trendRange?.length < 2) {
      alert('Select a valid date range')
      console.log('date', trendRange)
    } else {
      const data = await fetch('/api/fetch-userid-trend', {
        method: 'POST',
        credentials: 'include',
        headers: {  
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          starting_date: trendRange ? trendRange[0] : "",
          ending_date: trendRange ? trendRange[1] : "",
        }),
      }).then((res) => res.json())
      if(data) {
        setNonVpsUser(data['NON_VPS_USERS'])
        setVpsUser(data['VPS_USERS'])
        setVendorReg(data['VENDORS_USERS'])
        setTopVpsIP(data['TOP_VPS_ISP'])
      }
    }
  }

  const handleFileSearch = () => {
    // setBookMainTableTotalRows(dataKey)
    setPage(1)
    filesFilterDate(logFileHistoryDateFilter)
  }

  // closeDailyAnalyticsSection closes the data displayed in the Daily Analytics section.
  const closeDailyAnalyticsSection = () => {
    // Remove the Daily Analytics section.
    setShowDaily(false)
    setViewFileDate(false)
  }

  // Defines a function named pagiFuncPend that takes three parameters: page_value, bDate, and searchValue.
  const pagiFuncPend = async (page_value) => {
    setLoadings(true)
    const data = await fetch('/api/fetch-sus-user', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
        // starting_date: sdate?.length > 0 ? sdate[0] : new Date(0),
        // ending_date: sdate?.length > 0 ? sdate[1] : new Date(), 
        starting_date:
        searchSusDate != null && searchSusDate?.length != 0
          ? searchSusDate[0]
          : new Date(0),
      ending_date:
        searchSusDate != null && searchSusDate?.length != 0
          ? searchSusDate[1]
          : new Date(),
        search_user: "",
        // status:[0], 
        status: [1, 2],
        // suspected_date: sdate != null ? sdate : new Date(0),
      }),
    }).then((res) => res.json())
    // await setSusPendCount(data?.page_count)
    setSuspendedMainTableRows(data?.total_rows)
    setSuspendedMainTablePages(data?.total_pages)
    let jp = []
    for (let i = 0; i < data?.data_list?.length; i++) {
      jp.push(JSON.parse(data?.data_list[i]))
    }
    setSusPendData(jp)
    setLoadings(false)
    // await setSusPendData(data.data_list.map((item) => console.log(item)));
  };

  const  downloadSusReport = async(fdate)=> {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch('/api/download-sus-users', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        suspected_date: fdate,
        starting_date: Object.keys(fdate).length > 0 ? fdate[0] : new Date(0),
        ending_date: Object.keys(fdate).length > 0 ? fdate[1] : new Date(),
        // s_date: fdate,
        // starting_date
        status: [1, 2],
      }),
    }).then((response) => {
      response.blob().then((blob) => {
        let url = window.URL.createObjectURL(blob)
        let a = document.createElement('a')
        a.href = url
        // a.download = 'Suspicious_Action_User_List_' + new Date().toDateString() + '_.xlsx'
        a.download = `Suspicious_Action_User_List_from_${fdate[0].toDateString().replaceAll(' ', '_')}_to_${fdate[1].toDateString().replaceAll(' ', '_')}.xlsx`

        a.click()
        setLoading(false)
      })
    })
  }

  const handleSusPageChange = (dataKey) => {
    setPageSus(dataKey)
    pagiFuncPend(dataKey, searchSusDate)
  }

  // Initialize the checked and indeterminate variables with false
  let checked = false
  let indeterminate = false

  // Check the number of checked keys and set the checked and indeterminate variables accordingly
  if (checkedKeys.length === susPendData.length) {
    checked = true;
  } else if (checkedKeys.length === 0) {
    checked = false;
  } else if (checkedKeys.length > 0 && checkedKeys.length < susPendData.length) {
    indeterminate = true;
  }

const handleCheckAll = () => {
  if (checkedKeys.length === susPendData.length) {
    // If all are checked, uncheck all
    setCheckedKeys([]);
  } else {
    // Otherwise, check all
    const keys = susPendData.map((item) => item.USER_ID);
    setCheckedKeys(keys);
  }
};
 
const handleCheck = (value) => {
  if (checkedKeys.includes(value)) {
    // If the value is already in checkedKeys, remove it
    setCheckedKeys(checkedKeys.filter((item) => item !== value));
  } else {
    // If the value is not in checkedKeys, add it
    setCheckedKeys([...checkedKeys, value]);
  }
};

  useEffect(() => {
    setLoading(true)
    searchTrendRange(defaultDate)
    pagiFunc(1, false)
    pagiFuncPend(1, searchSusDate)
  }, [])

  const [isLoading, setIsLoading] = useState(false);

  // This function will be called when the user clicks the export button,
  const handleUserExport = async () => {
    setIsLoading(true);
    setLoading(true)
    // downloadSusReport(searchSusDate)

    try {
      await downloadSusReport(searchSusDate);
    } catch (error) {
      console.error('Error occurred while downloading the VPS export:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDateChange = (newValueDate) => {
    setLogFileHistoryDateFilter(newValueDate);
  }

    // Extract and sort the labels
    const sortedLabels = vpsUser && Object.keys(vpsUser)?.sort((a, b) => {
      const [dateA, monthA, yearA] = a.split('-').map(Number);
      const [dateB, monthB, yearB] = b.split('-').map(Number);

      // Compare years first, then months, and finally dates
      if (yearA !== yearB) return yearA - yearB;
      if (monthA !== monthB) return monthA - monthB;
      return dateA - dateB;
    });

    const handleDataSearch = () =>{

      searchTrendRange(trendRange)
    }
    // ...

    const handleSubmission = async () => {
      try {
        setValidationMessage('Validating File Data');
        await uploader.current.start();
        setValidationMessage('Validating File Data...');
      } catch (error) {
        // setValidationMessage(' validating stop');
        console.error('Error submitting file:', error);
        setValidationMessage('');
      }
    };

        // When we drag a file on the page instead of uploader, so that file is getting downloaded. To stop this behavior, a positive effect is written.
    useEffect(() => {
      const preventDefault = (e) => {
        e.preventDefault();
      };
  
      const handleDrop = (e) => {
        e.preventDefault();
  
        // You can add additional logic here if needed
      };
  
      // Attach event listeners to prevent the default behavior
      document.addEventListener('dragover', preventDefault);
      document.addEventListener('drop', handleDrop);
  
      // Clean up the event listeners when the component unmounts
      return () => {
        document.removeEventListener('dragover', preventDefault);
        document.removeEventListener('drop', handleDrop);
      };
    }, []);

  // Render
  return (
    <>
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

      {/* Modal Starts */}
      {allowed_actions?.upload && (
        <Modal open={uploadModal} onClose={closeModal} className={styles.modal}  backdrop='static'>
        <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          {/* 
          <Modal.Header as="h1">
            <Modal.Title as="h1">Upload Scan Results</Modal.Title>
          </Modal.Header> */}
          <h3>Upload Scan Results</h3>
          <Modal.Body>
            File Upload:     
            <Uploader
              action="/api/upload-file"
              onError={({response}, file,detail) => {
                toast.error(response.detail,{
                  autoClose: 6000,
                })
                setValidationMessage('');
                // setTimeout(() => {
                //   setValidationMessage('');
                // }, 5000);
              }}
                
              onSuccess={(response, detail, status) => {
                if(response.status === 500) {
                  toast.warn(response?.detail)
                } else if (response.status === 200) {
                  // toast.success(response?.detail)
                  toast.success("File uploaded successfully.");
                } else {
                  toast.error(response?.detail)
                }
                SubmitcloseModal()
              }}
              fileList={fileList} 
              autoUpload={false}
              // onChange={setFileList}
              
              onChange={(fileList) => {
                setFileList(fileList);
                if (fileList.length > 1) {
                  toast.warning("Only one file can be uploaded at a time.", {
                    autoClose: 6000, 
                  });
                }
              }}
              ref={uploader}
              // data={[modelValueDate]}
              draggable
              multiple={false}
              onDragOver={(e) => {
                e.preventDefault();
              }}
              onDrop={(e) => {
                const droppedFiles = e.dataTransfer.files;
              
                if (droppedFiles.length === 1 && droppedFiles.length > 1 ) {
                  setFileList([droppedFiles[0]]);
                }
              }}
            >
              <div
                style={{
                  height: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span>Click or Drag files to this area to upload</span>
              </div>
            </Uploader>
            {/* <Loader size="sm" className={styles.msgLoader} /> */}
            {validationMessage && <div className={styles.validateMsg}>{validationMessage} 
            <div className={styles.loader_container}>
                  <p className={styles.loader_text} />
                  <div className={styles.loader} />
                </div>
            </div>}
            
          </Modal.Body>
          <Modal.Footer>
            <Button
              // disabled={!fileList.length}
              disabled={fileList.length !== 1}
              onClick={handleSubmission}
                appearance="primary"
              >
                Submit
            </Button>
            <Button onClick={closeModal} appearance="subtle">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* USR REG MAIN - Page */}
      {(allowed_page?.user_registration_logs && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board
              heading="User Registration Logs"
              router={Router}
              action={{ label: 'Upload Logs', handler: openModal }}
            />

            <div style={{backgroundColor:'white', margin:'1rem'}}>
              <div className={styles.dailyrow + ' d-flex '}>
                <div className="me-auto p-2">
                  <h3>Trends <span><h6> (Last 7 days)</h6></span> </h3>
                </div>
                <div className={styles.DatePicker}>
                  <DateRangePicker
                    // className="float-end"
                    className={styles.dateRange}
                    placement="leftStart"
                    disabledDate={afterToday()}
                    placeholder="Select Date"
                    style={{ width: 230 }}
                    value={trendRange}
                    format="dd-MM-yyyy"
                    onChange={(newValueDate) => {
                      setTrendRange(newValueDate);
                      console.log(`newValueDate `, newValueDate)
                    }}
                  />
                </div>
                <div className={styles.searchBox}>
                  <Button
                    className={styles.searchBox}
                    appearance="primary"
                    // onClick={() => searchTrendRange(trendRange)}
                    onClick={handleDataSearch}
                  >
                    Search
                  </Button>
                </div>
              </div>

              {sortedLabels ? (
                <div className={styles.cardsRowTop + ' row mb-20 mx-3'}>
                  <div className={styles.cardContainer + ' card align-items-center'}>
                    <StackBarChart2
                      labels={sortedLabels}
                      vps_count_name={'VPS'}
                      non_vps_count_name={'NON VPS'}
                      vps_count={sortedLabels.map(date => vpsUser[date])}
                      non_vps_count={sortedLabels.map(date => nonvpsUser[date])}
                      title={'Average Users Registered  (Last 7 days)'}
                      height={350}
                      width="100%"
                    />
                  </div>
                  <div className={styles.cardContainer + ' card align-items-center'}>
                    <StackBarChart1
                      vps_count_name={'COUNT'}
                      labels={sortedLabels}
                      vps_count={sortedLabels.map(date => vendorReg[date])}
                      height={350}
                      width="100%"
                      title={'Average Users Registered through Vendors  (Last 7 days)'}
                    />
                  </div>
                  <div className={styles.cardContainer + ' card align-items-center'}>
                    <PiApexChart
                      label={topVpsIP?.map((item) => item['ISP']).slice(0, 10)}
                      series={topVpsIP?.map((item) => item['TK_COUNT']).slice(0, 10)}
                      title={'Top ISP Registered Users  (Last 7 days)'}
                      height={350}
                      width="100%"
                      event_func={helloworld}
                    />
                  </div>
                </div>
              ) : null}
            </div>
            <div style={{backgroundColor:'white', margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex'}>
              <div className="me-auto p-2">
                <h3> Daily Analytics </h3>{' '}
                <h6>
                  {viewFileDate ? new Date(viewFileDate).toDateString() : null}
                </h6>
              </div>
              <div className="p-2">
                <SelectPicker
                  className="float-end"
                  label="No. of Entries"
                  data={tableLengthOptions}
                  value={tableLength}
                  onChange={(newvalue) => setTableLength(newvalue)}
                  style={{ width: 200 }}
                />
              </div>
              <div className={styles.closeBtn}>
                <Button appearance="primary" onClick={closeDailyAnalyticsSection}>
                  Close
                </Button>
              </div>
            </div>
            {showDaily ? (
              <div className={styles.cardsRow + ' row mb-20 mx-3'}>
                <div className={styles.cardContainer + ' card align-items-center'}
                >
                  <PiApexChart
                    total={totalVps}
                    title={'User Registered Via VPS ISP'}
                    label={vpsASN?.map((item) => item['ISP']).slice(0, tableLength)}
                    series={vpsASN?.map((item) => item['TK_COUNT']).slice(0, tableLength)}
                    height={350}
                    width="100%"
                    event_func={helloworld}
                  />
                </div>
                <div className={styles.cardContainer + ' card align-items-center'}>
                  <PiApexChart
                    total={totalUser - totalVps}
                    title={'Users Registered Via Non VPS'}
                    label={NonVpsASN?.map((item) => item['ISP']).slice(0,tableLength)}
                    series={NonVpsASN?.map((item) => item['TK_COUNT']).slice(0,tableLength)}
                    event_func={helloworld}
                    height={350}
                    width="100%"
                  />
                </div>
                <div
                  className={styles.cardContainerSmall + ' align-items-center'}
                >
                  <div className={styles.cardOne + ' card align-items-center mx-auto'}>
                    <Image
                      src={users}
                      className={styles.network}
                      alt="Blacklisted Subnets"
                    ></Image>
                    <p className="m-b-0">{vendorUser}</p>
                    <h6 className="m-b-20">User's Registered through Vendors</h6>
                  </div>
                  <div className={styles.cardTwo + ' card align-items-center mx-auto'}>
                    <Image
                      src={ipAddress}
                      className={styles.subnet}
                      alt="Foreign IP"
                    ></Image>
                    <p className="m-b-0">{vpsIP}</p>
                    <h6 className="m-b-20">Count of IP's found in VPS Pool</h6>
                  </div>
                </div>
              </div>
            ) : null}
            </div>
            <div style={{backgroundColor:'white', margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex'}>
              <div className="me-auto p-2">
                <h3>File Upload History</h3>
              </div>
              <div className={styles.fileUploadDate}>
                <DatePicker
                  className="float-end"
                  placement="leftStart"
                  value={logFileHistoryDateFilter}
                  onChange={handleDateChange}
                  style={{ width: 200 }}
                  disabledDate={afterToday()}
                  format="dd-MM-yyyy"
                />
              </div>
              <div className={styles.FileUploadSearch}>
                <Button
                  className="float-end"
                  appearance="primary"
                  onClick={handleFileSearch}
                >
                  Search
                </Button>
              </div>
              <div className={styles.clearBtn}>
                <Button appearance="ghost" onClick={() => Router.reload()}>
                  Clear
                </Button>
              </div>
            </div>

            <div className={styles.tableContainer + ' col mx-auto'}>
              <Table
                className="mb-1"
                loading={loading}
                bordered
                autoHeight
                data={userregData}
              >
                <Column minWidth={180} flexGrow={1} fullText>
                  <HeaderCell>File Name</HeaderCell>
                  <CompactCell dataKey="name" />
                </Column>
                <Column  minWidth={100} fullText>
                  <HeaderCell>FileSize</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.filesize != undefined
                        ? rowData.filesize + ' MB'
                        : null
                    }}
                  </Cell>
                </Column>
                <Column  minWidth={100} flexGrow={0.6} fullText>
                  <HeaderCell>File Type</HeaderCell>
                  <CompactCell dataKey="ftype" /> 
                </Column>
                <Column  minWidth={100} flexGrow={1} fullText>
                  <HeaderCell>Log Date</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return new Date(rowData.fdate.$date).toDateString()
                    }}
                  </Cell>
                </Column>

                {/* file upload date */}
                <Column  minWidth={100} flexGrow={1} fullText>
                  <HeaderCell>File Upload Date</HeaderCell>
                  <Cell>
                    {/* {(rowData) => new Date(rowData?.ingest_date?.$date).toDateString()} */}
                    {(rowData) => new Date(rowData?.ingest_date?.$date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      // second: '2-digit',
                      // timeZoneName: 'short'
                    })}
                  </Cell>
                </Column>
                
                {allowed_actions?.download && (
                  <Column minWidth={170} flexGrow={0.8} fullText>
                    <HeaderCell>Download Analyzed File</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) => (
                        <Button
                          appearance="primary"
                          onClick={() => downloadReport(rowData.name, rowData.hash)}
                          disabled={rowData.status != 'Processed' ? true : false}
                          style={{ width: 100 }}
                        >
                          {rowData.status == 'Processed'
                            ? 'Download'
                            : rowData.status == 'Processing'
                            ? 'Processing'
                            : 'Error'}
                        </Button>
                      )}
                    </Cell>
                  </Column>
                )}
                
                <Column minWidth={100} flexGrow={0.7} fullText>
                  <HeaderCell>View Daily Analytics</HeaderCell>
                  <Cell style={{ padding: '6px' }}>
                    {(rowData) => (
                      <Button
                        appearance="primary"
                        onClick={() => viewReport(rowData.fdate.$date, rowData.ftype)}
                        disabled={rowData.status != 'Processed' ? true : false}
                        style={{ width: 100 }}
                      >
                        {rowData.status == 'Processed'
                          ? 'View'
                          : rowData.status == 'Processing'
                          ? 'Processing'
                          : 'Error'}
                      </Button>
                    )}
                  </Cell>
                </Column>
                {userRole == 'admin' ? (
                  <Column minWidth={80} flexGrow={0.1} fullText>
                    <HeaderCell>Error</HeaderCell>
                    <Cell style={{ fontWeight: 'bold' }}>
                      {(rowData) => {
                        return rowData.err != undefined ? rowData.err : 'Null'
                      }}
                    </Cell>
                  </Column>
                ) : null}
                {/* {userRole == 'admin' ? (
                  <Column width={200} fullText>
                    <HeaderCell>Delete File</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) =>
                        rowData.err != undefined ? (
                          <Button
                            appearance="primary"
                            onClick={() => deleteReport(rowData.hash)}
                            disabled={rowData.status != 'Error' ? true : false}
                            style={{ width: 100 }}
                          >
                            {rowData.status == 'Error' ? 'Delete' : 'Processing'}
                          </Button>
                        ) : null
                      }
                    </Cell>
                  </Column>
                ) : null} */}
                {allowed_actions?.delete && (
                  <Column minWidth={100} flexGrow={0.7} fullText>
                    <HeaderCell>Delete File</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) =>
                        rowData.err != undefined ? (
                          <Button
                            appearance="primary"
                            onClick={() => deleteReport(rowData.hash)}
                            disabled={rowData.status != 'Error' ? true : false}
                            style={{ width: 100 }}
                          >
                            {rowData.status == 'Error' ? 'Delete' : 'Processing'}
                          </Button>
                        ) : null
                      }
                    </Cell>
                  </Column>
                )}
              </Table>
              <div style={{ padding: 20 }}>
                <Pagination
                  prev
                  next
                  first
                  last
                  ellipsis
                  boundaryLinks
                  maxButtons={5}
                  size="xs"
                  layout={['total', '-', '|', 'pager', 'skip']}
                  total={uploadHistoryTableTotalRows}
                  pages={uploadHistoryTableTotalPages}
                  activePage={page}
                  onChangePage={handlePageChange}
                  onChangeLimit={handleChangeLimit}
                />
              </div>
            </div>
            </div>
            
            <div style={{backgroundColor:'white', margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex'}>
              <div className="me-auto p-2">
                <h3>Suspended Users</h3>
              </div>
              <div className={styles.SuspendedDatepicker + ' p-2'}>
                <DateRangePicker
                  disabledDate={afterToday()}
                  value={searchSusDate}
                  onChange={(newValueDate) => setSearchSusDate(newValueDate)}
                  style={{ width: 220 }}
                  format="dd-MM-yyyy"
                />
              </div>
              <div className={styles.SuspendedSearch}>
                <Button appearance="primary" onClick={handleUserSearch}>
                  Search
                </Button>
              </div>
              {allowed_actions?.download && (
                <div className={styles.SuspendedExport}>
                  <Button
                    appearance="primary"
                    onClick={handleUserExport}
                    disabled={searchSusDate == null ? true : false}
                  >
                    Export
                  </Button>
                </div>
              )}
              <div className={styles.SuspendedBlock}>
                <Button
                  appearance="primary"
                  color="red"
                  // onClick={() => handleUserIDStatus(checked, 1)}
                  disabled={
                    checked == true || indeterminate == true ? false : true
                  }
                >
                  Block Selected
                </Button>
              </div>
              <div className={styles.SuspendedIgnore}>
                <Button
                  appearance="primary"
                  color="green"
                  // onClick={() => handleUserIDStatus(checked, 2)}
                  disabled={checked == true || indeterminate == true ? false : true}
                >
                  Ignore Selected
                </Button>
              </div>
            </div>
            <div className={styles.tableContainer + ' col mx-auto'}>
              <Table bordered autoHeight data={susPendData} loading={loadings}>
                <Column minWidth={50} flexGrow={0.1} align="center">
                  <HeaderCell style={{ padding: 0 }}>
                    <div style={{ lineHeight: '40px' }}>
                      <Checkbox
                        inline
                        checked={checkedKeys.length === susPendData.length}
                        indeterminate={checkedKeys.length > 0 && checkedKeys.length < susPendData.length}
                        onChange={handleCheckAll}
                      />
                    </div>
                  </HeaderCell>
                  <CheckCell
                    dataKey="USER_ID"
                    checkedKeys={checkedKeys}
                    onChange={handleCheck}
                  />
                </Column>
                <Column minWidth={100} flexGrow={0.7} fullText>
                  <HeaderCell>USERID</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.USER_ID != '' ? rowData.USER_ID : '-'
                    }}
                  </Cell>
                </Column>
                <Column  minWidth={100} flexGrow={0.6} fullText>
                  <HeaderCell>Username</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.USERNAME != ''
                        ? rowData.USERNAME
                        : '-'
                    }}
                  </Cell>
                </Column>
                <Column width={200}  flexGrow={0.8} fullText>
                  <HeaderCell>Marked Date</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.SUS_DATE != undefined
                        ? new Date(rowData.SUS_DATE.$date).toDateString()
                        : null
                    }}
                  </Cell>
                </Column>
                <Column minWidth={600} flexGrow={2} fullText>
                  <HeaderCell>Tags</HeaderCell>
                  <Cell style={{ fontWeight: 'bold' }}>
                    {(rowData) => codeToTagTransform(rowData.TAGS)}
                  </Cell>
                </Column>
                <Column minWidth={100} flexGrow={1} fullText>
                  <HeaderCell >Status</HeaderCell>
                  <Cell style={{ padding: '6px'}}>
                    {(rowData) =>
                      rowData.status == 2 ? (
                        <Button
                          appearance="primary"
                          color="red"
                          disabled={
                            checked == true || indeterminate == true
                              ? true
                              : false
                          }
                          // onClick={() =>
                          //   handleUserIDStatus([rowData.USER_LOGINID], 1)
                          // }
                        >
                          Block
                        </Button>
                      ) : (
                        <Button
                          appearance="primary"
                          color="green"
                          disabled={
                            checked == true || indeterminate == true
                              ? true
                              : false
                          }
                          // onClick={() =>
                          //   handleUserIDStatus([rowData.USER_LOGINID], 2)
                          // }
                        >
                          Ignore
                        </Button>
                      )
                    }
                  </Cell>
                </Column>
              
              </Table>
              <div style={{ padding: 20 }}>
                <Pagination
                  prev
                  next
                  first
                  last
                  ellipsis
                  boundaryLinks
                  maxButtons={5}
                  size="xs"
                  layout={['total', '-', '|', 'pager', 'skip']}
                  total={suspendedMainTableRows}
                  pages={suspendedMainTablePages}
                  activePage={suspendedTableActivePage}
                  onChangePage={handleMainPageChange}
                  // onChangeLimit={handleChangeLimit}
                />
              </div>
            </div>
            </div>
          
          </div>
        </div>
      )}
      
    </>
  )
}

export default SusUsers

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res)
}
