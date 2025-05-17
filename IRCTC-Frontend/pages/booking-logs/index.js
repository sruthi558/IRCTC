// Import Libraries
import Image from 'next/image'
import { useEffect, useState, useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import Router, { useRouter } from 'next/router'
import {
  Table,
  Whisper,
  Button,
  Modal,
  DatePicker,
  Uploader,
  DateRangePicker,
  Pagination,
  SelectPicker,
  Tooltip,
  Dropdown,
} from 'rsuite'
import { startOfDay, endOfDay, subDays } from 'date-fns'

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'
import DonutApexChart from '../../components/DonutApexChart'
import PiApexChart from '../../components/PiChart'
import { validateUserCookiesFromSSR } from '../../utils/userVerification'

const { afterToday } = DateRangePicker
import CloseIcon from '@rsuite/icons/Close';

// Import Assets
import ipAddress from '../../public/static/images/ip-address.svg'
import question from '../../public/static/images/questionmark.svg'

// Import Styles
import styles from './BookingLogs.module.scss'

// Import Store
import { initData } from '../../store/slice/bookingLogs'
import AreaApexChartBook from '@/components/AreaApexChartBook'

import { toast } from 'react-toastify'

// Destructure the Table component import.
const { Column, HeaderCell, Cell } = Table

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement, tooltip }) => (
  // Whisper component: "hover" over specified placement and control ID.
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

// Represents the default date range to display data for:
// [startOfDay(subDays(new Date(), 7))], it calculates the start of the day 7 days ago from the current date.
// [endOfDay(new Date())], it calculates the end of the current day.
// Combines the start and end dates to create the default date range array.
const defaultDate = [subDays(new Date(), 7), endOfDay(new Date())]

// An array of objects representing the dropdown items for the booking table filter.
const bookingDropdownItems = [
  { label: 'All', value: 'All' },
  { label: 'ARP', value: 'ARP' },
  { label: 'Tatkal AC', value: 'AC' },
  { label: 'Tatkal Non-AC', value: 'NON_AC' },
]

// Booking Logs Page
const BookingLogsPage = () => {

  // Intialising router
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_action = useSelector((state) => state.persistedReducer.user_actions)
  // console.log('alolowed', allowed_action);

  useEffect(() => {
    if(!allowed_page?.booking_logs) {
      router.push("/overview")
    }
  }, [])


  const dispatch = useDispatch()

  // bookingLogsData contains the default booking data for when the user navigates back to the same page.
  const bookingLogsData = useSelector((state) => state.bookingLogs.data)
  const userRole = useSelector((state) => state.persistedReducer.role) // role of the user currently logged in

  // totalRowsCount contains the total number of files that are to be shown in the file list table.
  const totalRowsCount = useSelector((state) => state.bookingLogs.totalRowsCount)

  // State of the page number in pagination, default 1. 
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  // Start and the end date selected in the date range filter, default previous 7 days. 
  const [dateRange, setDateRange] = useState([
    subDays(new Date(), 7),
    endOfDay(new Date()),
  ])

  // Count of date between the start and the end date set in the 'dateRange' state, default a week (7 days)
  const [dateRangeDayCount, setDateRangeDayCount] = useState(7)  
  const [totalTicketsBookedCount, setTotalTicketsBookedCount] = useState(0) // Count of total tickets booked
  // Total no. of tickets booked through VPS
  const [totalTicketsBookedVPSCount, setTotalTicketsBookedVPSCount] = useState(0)
  // Date-wise count of tickets booked in ARP
  const [arpTicketsBookedTotal, setARPTicketsBookedTotal] = useState({})
  // Date-wise count of tickets booked in Tatkal AC
  const [tatkalACTicketsBookedTotal, setTatkalACTicketsBookedTotal] = useState({})
  // Date-wise count of tickets booked in Tatkal Non-AC
  const [tatkalNonACTicketsBookedTotal, setTatkalNonACTicketsBookedTotal] = useState({})
  // Date-wise count of tickets booked in ARP through VPS
  const [arpTicketsBookedVPS, setARPTicketsBookedVPS] = useState({})
  // Date-wise count of tickets booked in Tatkal AC through VPS
  const [tatkalACTicketsBookedVPS, setTatkalACTicketsBookedVPS] = useState({})
  // Date-wise count of tickets booked in Tatkal Non-AC through VPS
  const [tatkalNonACTicketsBookedVPS, setTatkalNonACTicketsBookedVPS] = useState({})
  // Top VPS ISPs uptill 20 and their respective ticket count
  const [trendsVPSASN, setTrendsVPSASN] = useState([])
  const [searchDateValue, setSearchDateValue] = useState();

  // Data series for tickets booked in each booking type.
  let totalTicketsBookedSeries = []

  if(
    JSON.stringify(tatkalACTicketsBookedTotal) !== undefined && JSON.stringify(tatkalACTicketsBookedTotal) !== '{}' &&
    JSON.stringify(tatkalNonACTicketsBookedTotal) !== undefined && JSON.stringify(tatkalNonACTicketsBookedTotal) !== '{}' &&
    JSON.stringify(arpTicketsBookedTotal) !== undefined && JSON.stringify(arpTicketsBookedTotal) !== '{}'
    ) {
    totalTicketsBookedSeries = [
      {
        name: 'Tatkal AC',
        data: Object.values(tatkalACTicketsBookedTotal),
      },
      {
        name: 'Tatkal Non-AC',
        data: Object.values(tatkalNonACTicketsBookedTotal),
      },
      {
        name: 'ARP',
        data: Object.values(arpTicketsBookedTotal),
      },
    ]
  }  
  let totalTicketsBookedVPSSeries = []

  if(
    JSON.stringify(tatkalACTicketsBookedVPS) !== undefined && JSON.stringify(tatkalACTicketsBookedVPS) !== '{}' && 
    JSON.stringify(tatkalNonACTicketsBookedVPS) !== undefined && JSON.stringify(tatkalNonACTicketsBookedVPS) !== '{}' && 
    JSON.stringify(arpTicketsBookedVPS) !== undefined && JSON.stringify(arpTicketsBookedVPS) !== '{}'
    ) {
    totalTicketsBookedVPSSeries = [
      {
        name: 'Tatkal AC',
        data: Object.values(tatkalACTicketsBookedVPS),
      },
      {
        name: 'Tatkal Non-AC',
        data: Object.values(tatkalNonACTicketsBookedVPS),
      },
      {
        name: 'ARP',
        data: Object.values(arpTicketsBookedVPS),
      },
    ]
  }

  // searchDateRange is the date range for which data is to be searched, default previous week (last 7 days)
  const searchTrend = async (dateRange) => {   
    // if (searchDateRange == undefined) {
    //   searchDateRange = [
    //     startOfDay(subDays(new Date(), 7)),
    //     endOfDay(new Date()),
    //   ]
    // }
    const data = await fetch('/api/fetch-book-trend', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        // std: dateRange[0],
        // etd: dateRange[1],
        std: dateRange ? dateRange[0] : "",
        etd: dateRange ? dateRange[1] : "",
      }),
    })
      .then((response) => response.json())

    // Skip if an invalid response is received.
    if (data['detail'] !== 'INVALID_REQUEST') {
      // Update the 'tatkalACTicketsBookedTotal' state with the 'AC_TOT' property of the retrieved data.
      setTatkalACTicketsBookedTotal(data['AC_TOT'])
      // Update the 'arpTicketsBookedTotal' state with the 'ARP_TOT' property of the retrieved data.
      setARPTicketsBookedTotal(data['ARP_TOT'])
      // Update the 'tatkalNonACTicketsBookedTotal' state with the 'NON_AC_TOT' property of the retrieved data.
      setTatkalNonACTicketsBookedTotal(data['NON_AC_TOT'])
      // Update the 'tatkalACTicketsBookedVPS' state with the 'AC_VPS' property of the retrieved data.
      setTatkalACTicketsBookedVPS(data['AC_VPS'])
      // Update the 'tatkalNonACTicketsBookedVPS' state with the 'NON_AC_VPS' property of the retrieved data.
      setTatkalNonACTicketsBookedVPS(data['NON_AC_VPS'])
      // Update the 'arpTicketsBookedVPS' state with the 'ARP_VPS' property of the retrieved data.
      setARPTicketsBookedVPS(data['ARP_VPS'])
      // Update the 'trendsVPSASN' state with the 'TOP_ISP' property of the retrieved data.
      setTrendsVPSASN(data['TOP_ISP'])
      // Update the 'dateRangeDayCount' state as per the date range provided in the parameter for data retrieval.
      // // setDateRangeDayCount(
      // //   parseInt(
      // //     (searchDateRange[1] - searchDateRange[0]) / (1000 * 3600 * 24),
         
      // //   ),
      // )
    }
  }
      
  // ------------------------------ Daily Analytics Section ------------------------------ //

  // State of whether the Daily Analytics section is to be displayed or not
  const [showDaily, setShowDaily] = useState(false)
  // Contains the top VPS ISPs uptill 20 and their respective ticket count
  const [dailyAnalyticsVPSASN, setDailyAnalyticsVPSASN] = useState([])
  // Contains the top Non-VPS ISPs uptill 20 and their respective ticket count
  const [dailyAnalyticsNonVPSASN, setDailyAnalyticsNonVPSASN] = useState([])
  // The number of entries to show in charts and cards of daily analytics
  const [dailyAnalyticsNumberOfEntriesToDisplay, setDailyAnalyticsNumberOfEntriesToDisplay] = useState(5)
  // Contains the count of total unique IP addresses observed from VPS
  const [vpsIpCount, setVpsIpCount] = useState(0)
  // The date for which daily analytics is to be viewed, view btmn of file hist section
  const [viewLogDate, setViewLogDate] = useState(false)
  // The booking type for which daily analytics is to be viewed, view btn of hist section
  const [viewLogType, setViewLogType] = useState('')
  //  View History Modal pagination display total rows and total pages and there states
  const [bookMainTableTotalRows, setBookMainTableTotalRows] = useState(0);
  const [bookMainTableTotalPages, setBookMainTableTotalPages] = useState(0);

  // dailyAnalyticsNumberOfEntriesToDisplayOptions provides different options for the number of entries to be displayed in charts.
  // Values are in multiples of 5, default value is set to '5'.
  const dailyAnalyticsNumberOfEntriesToDisplayOptions = [5, 10, 15, 20].map((item) => ({ label: item, value: item }))
  
  // closeDailyAnalyticsSection closes the data displayed in the Daily Analytics section.
  const closeDailyAnalyticsSection = () => {
    // Remove the Daily Analytics section.
    setShowDaily(false)
    setViewLogDate(false)
  }

  // Retrieves data for a particular date and type of log to display in daily analytics.
  // logDate is the date for which the data is being retrieved.
  // logType is the type of booking for which the data is being retrieved.
  const viewDailyAnalytics = async (logDate, logType) => {
    const data = await fetch(
      '/api/fetch-book-data?log_date=' + logDate + '&log_type=' + logType,
    )
      .then((response) => response.json())
      .then((response) => JSON.parse(response['data']))
      // Update the 'totalTicketsBookedCount' variable with the value of the 'TOT_TK' property of the 'logType' object in the 'data' variable.
      setTotalTicketsBookedCount(data[logType]['TOT_TK'])
      // Update the 'totalTicketsBookedVPSCount' variable with the value of the 'VPS_TK' property of the 'logType' object in the 'data' variable.
      setTotalTicketsBookedVPSCount(data[logType]['VPS_TK'])
      // Update the 'vpsIp' variable with the value of the 'VPS_POOL' property of the 'logType' object in the 'data' variable.
      setVpsIpCount(data[logType]['VPS_POOL'])
      // Update the 'vpsAsn' variable with the value of the 'VPS_ISP' property of the 'logType' object in the 'data' variable.
      setDailyAnalyticsVPSASN(data[logType]['VPS_ISP'])
      // Update the 'nonVpsAsn' variable with the value of the 'NON_VPS_ISP' property of the 'logType' object in the 'data' variable.
      setDailyAnalyticsNonVPSASN(data[logType]['NON_VPS_ISP'])
      // Display the Daily Analytics section.
      setShowDaily(true)
      // Set the date for which data is being viewed in the Daily Analytics section.
      setViewLogDate(logDate)
  }

  // ------------------------------ File Upload Modal ------------------------------ //

  const [fileRowCount, setFileRowCount] = useState(0)
  // Toggles the state of modal to be displayed
  const [uploadModalDisplayToggle, setUploadModalDisplayToggle] = useState(false)
  // The date set by the user for which they are uploading the booking logs
  const [bookingLogFileDate, setBookingLogFileDate] = useState()
  // The list of file that has been selected to be uploaded
  const [uploadingFileList, setUploadingFileList] = useState([])

  // Declare a reference to the Upload component for tracking the files in a persistant manner across reloads.
  const uploader = useRef()

  // uploader file data testing msg state
  const [validationMessage, setValidationMessage] = useState('');

  // openModal displays the modal.
  const openModal = () => {
    setUploadModalDisplayToggle(true)
    setValidationMessage('');
    setUploadingFileList([])
  }

  // closeModal removes the modal.
  const closeModal = () => {
    setUploadModalDisplayToggle(false);
    setValidationMessage('');
  }

  ////////////////////////////////// TO BE FIXED /////////////////////////////////////////////

  // submitCloseModal
  const submitCloseModal = () => {
    // setUploadModalDisplayToggle(false)

    // setTimeout(function () {
    //   Router.reload()
    // }, 60000)
  }

  ////////////////////////////////// CLOSE FIX /////////////////////////////////////////////

  // ------------------------------ File Upload History Section ------------------------------ //

  // The date of file that has been selected to be uploaded
  const [logFileHistoryDateFilter, setLogFileHistoryDateFilter] = useState()
  // filterFileHistory filters the log files in the File Upload History section.
  const filterFileHistory = () => {
    // Filter the log files as per the date provided.
    filesFilterDate(logFileHistoryDateFilter)
  }

  // ------------------------------ Page Render ------------------------------ //
  // useEffect fetches the initial data and sets up the default values for the initial render.
  useEffect(() => {
    setLoading(true)
    searchTrend(defaultDate)
    paginationFunction(1)
  }, [])

  // Takes pageNumber as the function parameter for which data is to be fetched.
  const paginationFunction = async (pageNumber) => {
    setLoading(true)
    const data = await fetch('/api/analysis_list_all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: pageNumber,
      }),
    })
      .then((response) => response.json())
      // Setup the data list from the parsed response.
      dispatch(initData(data?.data_list?.map((item) => JSON.parse(item))))
      // setFileRowCount(data?.page_count)
      setBookMainTableTotalRows(data?.total_rows)
      setBookMainTableTotalPages(data?.total_pages)
      // Set the loading parameter to be 'false' once API calls are completed to remove the loader.
      setLoading(false)
  }

  // downloadAnalyzedFile downloads the requested file.
  // Name of the downloaded file is of the format "Analysed_{DATA_TYPE}_{DATE}".
  // analyzedFileMetadata is the type and date, for example, Tatkal AC Data.
  // analyzedFileHash is the hash of analyzed file.
  const downloadAnalyzedFile = (analyzedFileMetadata, analyzedFileHash) => {
    fetch('/api/log-download?fileHash=' + analyzedFileHash).then((response) => {
      response.blob().then((blob) => {
        // Create the URL for the file bytes received.
        let url = window.URL.createObjectURL(blob)
        // Create the anchor tag as link for the file.
        let anchorElement = document.createElement('a')
        // Set the href link to the URL created.
        anchorElement.href = url
        // Set the name of the file to be downloaded.
        anchorElement.download = "Analysed_" + analyzedFileMetadata.split('.')[0]+'.xlsx';
        // Download button functionality.
        anchorElement.click()
      })
    })
  }

  const helloworld = (vuln) => {
    console.log('test')
  }

  // Provides the list of log files for the date provided as the parameter.
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
      }),
    })
      .then((response) => response.json())
      // Dispatch an action with the initial page count data.
      dispatch(initData(data?.data_list?.map((item) => JSON.parse(item))))
      // Dispatch an action to set the total rows in the table for the filtered data, setFileRowCount(data?.page_count)
      setBookMainTableTotalRows(data?.total_rows)
      setBookMainTableTotalPages(data?.total_pages)
      // Set the loading parameter to be 'false' once API calls are completed to remove the loader.
      setLoading(false)
  }

  // handlePageChange changes the page number to the value passed as parameter.
  const handlePageChange = (pageNumber) => {
    setPage(pageNumber)
    paginationFunction(pageNumber)
  }

  // deleteAnalyzedFile deletes the analyzed file.
  // analyzedFileMetadata is the type and date, for example, Tatkal AC Data.
  // analyzedFileHash is the hash of analyzed file.
  const deleteAnalyzedFile = (analyzedFileMetadata, analyzedFileHash) => {
    fetch(
      '/api/log-delete?f_hash=' +
        analyzedFileHash +
        '&f_type=' +
        analyzedFileMetadata,
    )
      .then((response) => response.json())
  }

  // A state variable selectedDropdownItem is initialized with the default value of 'All' and a
  // corresponding setselectedDropdownItem function is created to update the value of the state variable.
  const [selectedDropdownItem, setselectedDropdownItem] = useState('All')

  // function that sets the selectedDropdownItem state variable based on the value of the option selected in the dropdown.
  function handleSelectedItemChange(event) {
    setselectedDropdownItem(event.target.value)
  }
  
  // A function that sets the selectedDropdownItem state variable based on the value passed in as an argument
  function handleSelectedItems(value) {
    setPage(1);
    setselectedDropdownItem(value)
  }

  // A filtered array of bookingLogsData is created based on the selected value in the dropdown filter.
  // The filter function checks if the selectedDropdownItem state variable is equal to 'All' and returns,
  // true for all items if it is. Otherwise, it checks if the ftype property of each item is equal to,
  // the corresponding dropdown option and returns true if it is.
  const bookingTableData = [...bookingLogsData].filter((item) => {
    if (selectedDropdownItem === 'All') {
      return true
    }
    if (selectedDropdownItem === 'ARP' && item.ftype === 'ARP') {
      return true
    } else if (selectedDropdownItem === 'AC' && item.ftype === 'AC') {
      return true
    } else if (selectedDropdownItem === 'NON_AC' && item.ftype === 'NON_AC') {
      return true
    }
  })

  
    // function for, sort the date by year month and then date wise..
    const sortedLabels = Object.keys(tatkalACTicketsBookedTotal).sort((a, b) => {
      const [dateA, monthA, yearA] = a.split('-').map(Number);
      const [dateB, monthB, yearB] = b.split('-').map(Number);

      // Compare years first, then months, and finally dates
      if (yearA !== yearB) return yearA - yearB;
      if (monthA !== monthB) return monthA - monthB;
      return dateA - dateB;
    });

    const handleSubmission = async () => {
      try {
        setValidationMessage('Validating File Data...');
        await uploader.current.start();
        setValidationMessage('Validating File Data...');
      } catch (error) {
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
  // Render the page.
  return (
    <>
      {/* UPLOAD - Modal */}
      {allowed_action?.upload && (
        <Modal
          open={uploadModalDisplayToggle}
          onClose={closeModal}
          className={styles.modal}
          backdrop='static'
          >
         <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          <h3>Upload Daily Booking Log</h3>
          <Modal.Body>
            File Upload:
            <Uploader
              action="/api/upload-file"
              onError={async ({response}, file,detail) => {
                await new Promise((resolve) => setTimeout(resolve, 1000)); 
                toast.error(response.detail,{
                  autoClose: 6000,
                })
                setValidationMessage('');
                // setTimeout(() => {
                //   setValidationMessage('');
                // }, 5000);
              }}
              onSuccess={async (response, detail, status) => {
                if(response.status === 500) {
                  toast.warn(response?.detail)
                } else if (response.status === 200) {
                  // toast.success(response?.detail)
                  toast.success("File uploaded successfully.");
                } else {
                  toast.error(response?.detail)
                }
                closeModal();
              }}
              uploadingFileList={uploadingFileList}
              autoUpload={false}
              // onChange={setUploadingFileList}
              ref={uploader}
              // data={[bookingLogFileDate]}
              draggable
              multiple={false}
              onDragOver={(e) => {
                e.preventDefault();
              }}
              onChange={(uploadingFileList) => {
                setUploadingFileList(uploadingFileList);
                if (uploadingFileList.length > 1) {
                  // toast.warning("Only one File can be Uploaded at a time.");
                  toast.warning("Only one file can be uploaded at a time.", {
                    autoClose: 6000, 
                  });
                }
              }}
              onDrop={(e) => {
                const droppedFiles = e.dataTransfer.files;
              
                if (droppedFiles.length === 1 && droppedFiles.length > 1 ) {
                  setUploadingFileList([droppedFiles[0]]);
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
            {validationMessage && <div className={styles.validateMsg}>{validationMessage}
            <div className={styles.loader_container}>
                  <p className={styles.loader_text} />
                  <div className={styles.loader} />
                </div>
            </div>}
          </Modal.Body>
          <Modal.Footer>
            <Button
              // disabled={!uploadingFileList.length}
              // disabled={uploadingFileList.length > 1}
              disabled={uploadingFileList.length !== 1}
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
      
      {/* MAIN DAILY BOOKING LOGS - Page */}
      {(allowed_page?.booking_logs && allowed_action?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board
              router={Router}
              heading="Daily Booking Log Analysis"
              action={{ label: 'Upload Files', handler: openModal }}
            />

            <div style ={{backgroundColor:'white' , margin:'1rem'}}>
            <div className={styles.dailyrow + ' row '}>
              <div className="col-4">
                <h1>Trends </h1>
                </div>

              <div className={styles.buttons_main_div}>
                <div className={styles.buttons_sub_div}>
                <span className="col-6 mx-auto pt-3">
                  <DateRangePicker
                    disabledDate={afterToday()}
                    className={styles.bookDate}
                    placement="leftStart"
                    placeholder="Select Date"
                    format="dd-MM-yyyy"
                    style={{ width: 300 }}
                    value={dateRange}
                    onChange={(newValueDate) => setDateRange(newValueDate)}
                  />
                </span>
                  <Button
                  className={styles.bookSearch}
                    appearance="primary"
                    onClick={() => searchTrend(dateRange)}
                    style={{ width: 100 }}
                  >
                    Search
                  </Button>
                </div>
              </div>
              
              
            </div>
            {trendsVPSASN ? (
              <div className={styles.cardsRowTop + ' row mb-20 mx-3'}>
                <div
                  className={
                    styles.cardContainer +
                    ' card mx-auto align-items-center'
                  }
                >
                  {/* <CustomComponent
                    className="mx-auto"
                    placement="auto"
                    tooltip={
                      'Total Tickets Booked (Last ' + dateRangeDayCount + ' Days)'
                    }
                  /> */}
                  <AreaApexChartBook
                    // labels={Object.keys(tatkalACTicketsBookedTotal)}
                    labels={sortedLabels}
                    series={totalTicketsBookedSeries}
                    title={'Total Tickets Booked (Last ' + dateRangeDayCount + ' Days)'}
                    height={350}
                    width="100%"
                  />
                </div>
                <div
                  className={
                    styles.cardContainer + ' card align-items-center'
                  }
                >
                  {/* <CustomComponent
                    placement="auto"
                    tooltip={
                      'Tickets Booked through VPS (Last ' +
                      dateRangeDayCount +
                      ' Days)'
                    }
                  /> */}
                  <AreaApexChartBook
                    // labels={Object.keys(tatkalACTicketsBookedTotal).reverse()}
                    labels={sortedLabels}
                    series={totalTicketsBookedVPSSeries}
                    title={'Tickets Booked through VPS (Last ' +dateRangeDayCount +' Days)'}
                    height={350}
                    width="100%"
                  />
                </div>
                <div className={styles.cardContainer + ' card align-items-center'}>
                  {/* <CustomComponent
                    placement="auto"
                    tooltip={
                      'Top 10 VPS ISP Booked Tickets (Last ' +
                      dateRangeDayCount +
                      ' Days)'
                    }
                  /> */}
                  <DonutApexChart
                    label={trendsVPSASN?.slice(0, 10).map((item) => item['ISP'])}
                    series={trendsVPSASN?.slice(0, 10).map((item) => item['TK_COUNT'])}
                    event_func={helloworld}
                    title={'Top 10 ISP Booked Tickets (Last ' +dateRangeDayCount +' Days)'}
                    height={350}
                    width="100%"
                  />
                </div>
              </div>
            ) : null}
            </div>
            <div style={{backgroundColor:'white', margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex '}>
              <div className="me-auto p-2">
                <h3>Daily Analytics</h3>
                <h6>
                  {viewLogDate ? viewLogType + ' Logs Dated ' + new Date(viewLogDate).toDateString() : null}
                </h6>
              </div>
              <div className="p-2">
                <SelectPicker
                  className={styles.analyticsEntries}
                  label="No. of Entries"
                  data={dailyAnalyticsNumberOfEntriesToDisplayOptions}
                  value={dailyAnalyticsNumberOfEntriesToDisplay}
                  onChange={(newvalue) => setDailyAnalyticsNumberOfEntriesToDisplay(newvalue)}
                  style={{ width: 200 }}
                />
              </div>
              <div className="p-2">
                <Button
                className={styles.analyticsClose}
                  appearance="primary"
                  onClick={closeDailyAnalyticsSection}
                  style={{ width: 100 }}
                >
                  Close
                </Button>
              </div>
            </div>

            {/* bar charts first vps start  */}
            {showDaily ? (
              <div className={styles.cardsRow + ' row mb-20 mx-3'}>
                <div className={styles.cardContainer + ' card  align-items-center'}>
                  {/* <CustomComponent
                    placement="auto"
                    tooltip="Tickets Booked through VPS"
                  /> */}
                  <PiApexChart
                    total={totalTicketsBookedVPSCount}
                    title={'Tickets Booked through VPS'}
                    label={dailyAnalyticsVPSASN?.map((item) => item['ISP']).slice(0, dailyAnalyticsNumberOfEntriesToDisplay)}
                    series={dailyAnalyticsVPSASN?.map((item) => item['TK_COUNT']).slice(0, dailyAnalyticsNumberOfEntriesToDisplay)}
                    height={300}
                    event_func={helloworld}
                    width="100%"
                  />
                </div>
                {/* bar charts first vps Ends  */}

                {/* bar charts seconds non vps start  */}
                <div className={styles.cardContainer + ' card align-items-center'}>
                  
                  <PiApexChart
                    total={totalTicketsBookedCount - totalTicketsBookedVPSCount}
                    title={'Tickets Booked through NON VPS'}
                    label={dailyAnalyticsNonVPSASN?.map((item) => item['ISP']).slice(0, dailyAnalyticsNumberOfEntriesToDisplay)}
                    series={dailyAnalyticsNonVPSASN?.map((item) => item['TK_COUNT']).slice(0, dailyAnalyticsNumberOfEntriesToDisplay)}
                    event_func={helloworld}
                    height={300}
                    width="100%"
                  />
                </div>

                {/* bar charts seconds non vps staEndsrt  */}

                <div className={styles.cardContainer + ' align-items-center'}>
                  <div 
                    className={styles.cardTwo + ' card align-items-center mx-auto'}
                    style={{ boxShadow: "none"}}
                  >
                    <Image
                      src={ipAddress}
                      className={styles.subnet}
                      alt="Foreign IP"
                    ></Image>

                    <p className="m-b-0">{vpsIpCount}</p>
                    <h6 className="m-b-20">Count of IP's found in VPS Pool</h6>
                  </div>
                </div>
              </div>
            ) : null}
            </div>
          

            <div style ={{backgroundColor:'white' , margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex '}>
              <div className="me-auto p-2">
                <h3>File Upload History</h3>
              </div>
              <div>
                <Dropdown
                  title={selectedDropdownItem}
                  value={selectedDropdownItem}
                  onSelect={handleSelectedItems}
                  className={styles.dropdown}
                >
                  {bookingDropdownItems.map((item) => (
                    <Dropdown.Item key={item.value} eventKey={item.value}>
                      {item.label}
                    </Dropdown.Item>
                  ))}
                </Dropdown>
              </div>
              <div className="p-2">
                <DatePicker
                  disabledDate={afterToday()}
                  className={styles.uploadDate}
                  placement="leftStart"
                  format="dd-MM-yyyy"
                  value={logFileHistoryDateFilter}
                  onChange={(newValueDate) => setLogFileHistoryDateFilter(newValueDate)}
                  style={{ width: 200 }}
                />
              </div>
              <div className="p-2">
                <Button
                  className={styles.uploadSearch}
                  appearance="primary"
                  onClick={filterFileHistory}
                >
                  Search
                </Button>
              </div>
              <div className="ml-auto p-2">
                <Button appearance="ghost" onClick={() => Router.reload()} className={styles.uploadClear}>
                  Clear
                </Button>
              </div>
            </div>

            <div className={styles.tableContainer + ' col mx-auto'}>
              <Table
                loading={loading}
                bordered
                autoHeight
                data={selectedDropdownItem === 'All' ? bookingLogsData : bookingTableData}
              >
                <Column minWidth={200} flexGrow={2} fullText>
                  <HeaderCell>File Name</HeaderCell>
                  <Cell style={{color:"blue"}} dataKey="name" />
                </Column>
                <Column width={100}>
                  <HeaderCell>FileSize</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.filesize != undefined
                        ? rowData.filesize + ' MB'
                        : null
                    }}
                  </Cell>
                </Column>
                <Column width={100} fullText>
                  <HeaderCell>File Type</HeaderCell>
                  <Cell dataKey="ftype" style={{color:"blue"}}/>
                </Column>
                <Column width={180} fullText>
                  <HeaderCell>Log Date</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.fdate != undefined
                        ? new Date(rowData.fdate.$date).toDateString()
                        : null 
                    }}
                  </Cell>
                </Column>
                {/* file upload date */}
                <Column width={200} fullText>
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
                {allowed_action?.download && (
                  <Column width={170} fullText>
                    <HeaderCell>Download Analyzed File</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) => (
                        <Button
                          appearance="primary"
                          onClick={() => downloadAnalyzedFile(rowData.name, rowData.hash)}
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
                <Column width={150} fullText>
                  <HeaderCell>View Daily Analytics</HeaderCell>
                  <Cell style={{ padding: '6px' }}>
                    {(rowData) => (
                      <Button
                        appearance="primary"
                        onClick={() => viewDailyAnalytics(rowData.fdate.$date, rowData.ftype)}
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
                  <Column minWidth={80} flexGrow={1} fullText>
                    <HeaderCell>Error</HeaderCell>
                    <Cell style={{ fontWeight: 'bold' }}>
                      {(rowData) => {
                        return rowData.err != undefined
                         ? 'Error processing the file, please contact the administrator.'
                         : 'Null'
                      }}
                    </Cell>
                  </Column>
                ) : null}
                {userRole == 'admin' ? (
                  <Column width={150}>
                    <HeaderCell>Delete File</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) =>
                        rowData.err != undefined ? (
                          <Button
                            appearance="primary"
                            onClick={() => deleteAnalyzedFile(rowData.ftype, rowData.hash)}
                            disabled={rowData.status != 'Error' ? true : true}
                            style={{ width: 100 }}
                          >
                            {rowData.status == 'Error' ? 'Delete' : 'Processing'}
                          </Button>
                        ) : (
                          <Button
                            appearance="primary"
                            onClick={() => deleteAnalyzedFile(rowData.ftype, rowData.hash)}
                            disabled={rowData.status != 'Error' ? true : true}
                            style={{ width: 100 }}
                          >
                            {rowData.status == 'Error' ? 'Delete' : 'Processing'}
                          </Button>
                        )
                      }
                    </Cell>
                  </Column>
                ) : null}
                {userRole == 'admin' ? (
                  <Column width={150} flexGrow={1} fullText>
                    <HeaderCell>Error</HeaderCell>
                    <Cell style={{ fontWeight: 'bold' }}>
                      {(rowData) => {
                        return rowData.err != undefined ? rowData.err : 'Null'
                      }}
                    </Cell>
                  </Column>
                ) : null}
              </Table>
              <div className={styles.pagination}>
                <Pagination
                  prev
                  next
                  first
                  last
                  ellipsis
                  boundaryLinks
                  maxButtons={5}
                  size="xs"
                  limit={[10]}
                  layout={['total', '-', '|', 'pager', 'skip']}
                  total={bookMainTableTotalRows}
                  pages={bookMainTableTotalPages}
                  activePage={page}
                  onChangePage={handlePageChange}
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

export default BookingLogsPage

export async function getServerSideProps({ req, response }) {
  return validateUserCookiesFromSSR(req, response)
}
