// endpoint
const endPoint = process.env.API_ENDPOINT

// Import Libraries
import Image from 'next/image'
import { useEffect, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'

const { afterToday } = DateRangePicker
const { Column, HeaderCell, Cell } = Table
import moment from 'moment'
import { validateUserCookiesFromSSR } from '../../utils/userVerification'

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'
import question from '../../public/static/images/questionmark.svg'
import Router, { useRouter } from 'next/router'

import { Circles } from 'react-loader-spinner'
import { toast } from 'react-toastify'
import CloseIcon from '@rsuite/icons/Close';


// Import Assets

import MoreIcon from '@rsuite/icons/legacy/More'

import { startOfDay, endOfDay, subDays } from 'date-fns'

// Import Styles
import styles from './SuspiciousIPAddresses.module.scss'

// A mapping object that maps tag codes to their corresponding descriptions
const tagMapping = {
  USER_REG_BOOK_VPS: 'User has registered from this VPS IP Address', //'User has registered from this VPS IP Address',
  REG_MORE_THAN_5: 'More than 5 User Registrations from this IP Address', // 'More than 5 User Registrations from this IP Address',
  BOOKING_IP_VPS: 'Booked PNR from VPS IP Address', // 'Booked PNR from VPS IP Address',
  TK_MORE_THAN_20_ARP: 'More than 20 PNRs booked during ARP', //'More than 20 PNRs booked during ARP',
  TK_MORE_THAN_20_AC: 'More than 20 PNRs booked during Tatkal AC', //'More than 20 PNRs booked during Tatkal AC',
  TK_MORE_THAN_20_NON_AC: 'More than 20 PNRs booked during Tatkal Non-AC', // 'More than 20 PNRs booked during Tatkal Non-AC',
  USED_BY_SUSPICIOUS_USER: 'This IP has been used by a Suspicious User', //'This IP has been used by a Suspicious User',
}

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

// Import Store
import {
  Button,
  DateRangePicker,
  Dropdown,
  Modal,
  Pagination,
  Table,
} from 'rsuite'

// ActionCell: Custom Component, likely renders a clickable cell in a table
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
const CustomComponent = ({ placement }) => (
  <Whisper
    trigger="hover"
    placement={placement}
    controlId={`control-id-${placement}`}
    speaker={
      <Tooltip arrow={false}>
        Today's finding updated to the Brand Monitoring Page.
      </Tooltip>
    }
  >
    {/* Render an Image component with a question mark icon and specified class */}
    <Image
      src={question}
      className={styles.questionmark}
      alt="Explanation"
    ></Image>
  </Whisper>
)

// An array of objects representing the dropdown items for the suspected ip table filter.
const dropdownItems = [
  { label: 'All', value: 'Select ISP type' },
  { label: 'VPS', value: 'VPS' },
  { label: 'Non-VPS', value: 'NON-VPS' },
]

// Dashboard Component
const SusUsers = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.suspected_ip_addresses) {
      router.push('/overview')
    }
  }, [])

  // Initialise the dispatcher.
  const dispatch = useDispatch()

  // useridData: This is a piece of data from the Redux store that contains information about the user IDs.
  const sususerData = useSelector((state) => state.sususer.data)
  // This is another piece of data from the Redux store that contains the total number of pages for the user IDs.
  const susPageCount = useSelector((state) => state.sususer.pageCount)
  // userRole contains the role of the user currently logged in for role-based restrictions.
  const userRole = useSelector((state) => state.persistedReducer.role)
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false)
  // This state variable determines the number of items to display per page.
  const [limit, setLimit] = useState(10)
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1)
  // This state defines a new state variable named "fileType" and sets its initial value to an empty string.
  const [viewFileType, setViewFileType] = useState('')
  // This state is initialized with a value of 0 and will be used to store the number of multiple VPS users.
  const [multiVps, setMultiVPS] = useState(0)
  // This state is initialized with a value of 0 and will be used to store the number of VPS users.
  const [vpsUser, setVpsUser] = useState(0)
  // This state is initialized with a value of 0 and will be used to store the number of non-VPS users.
  const [nonVpsUser, setNonVpsUser] = useState(0)
  // This state is initialized with a value of 0 and will be used to store the number of registrations from VPS users.
  const [vpsReg, setVpsReg] = useState(0)
  // This state is initialized with a value of 0 and will be used to store the number of registrations from VPS users.
  const [totalSus, setTotalSus] = useState(0)
  // This state is initialized without a value and will be used to store the difference in days between two dates.
  const [trendDiffDate, setTrendDiffDate] = useState()
  // `tableLength ` : This state is initialized with a value of 5 and will be used to store the number of rows to display in a table.
  const [tableLength, setTableLength] = useState(5)
  // `fileUploadDate`: This state is initialized without a value and will be used to store the date when a file was uploaded.
  const [fileUploadDate, setFileUploadDate] = useState()
  // susIPsVps`: This state is initialized as an empty array and will be used to store the list of suspicious IPs from VPS users.
  const [susIPsVps, setSusIpsVps] = useState([])
  // susIPsNotVps`: This state is initialized as an empty array and will be used to store the list of suspicious IPs from VPS counts.
  const [susIPsNotVps, setSusIpsNotVps] = useState([])
  // State variables for tracking the count of suspicious IP addresses and non-IP addresses.
  const [susIPCount, setSusIPCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1);
  // Count of suspicious non-IP addresses
  const [susNonIPCount, setSusNonIPCount] = useState(0)
  const [pageVPS, setPageVPS] = useState(1) // Current page number for VPS list pagination
  const [pageNON, setPageNON] = useState(1) // Current page number for non-VPS list
  // State variables for storing search dates for VPS and non-VPS lists
  const [searchVPSDate, setSearchVPSDate] = useState() // Search date for VPS list
  const [searchNONVPSDate, setSearchNONVPSDate] = useState() // Search date for non-VPS list
  // State variables for displaying modal data
  const [modalData, setModalData] = useState([]) // Data to display in modal
  const [modalCount, setModalCount] = useState(0) // Count of modal data items
  const [modalLoad, setModalLoad] = useState(false) // Flag to indicate whether modal data is being loaded
  const [query, setQuery] = useState('') // Query for filtering the data
  // State variable for tracking the currently selected option in a dropdown.
  const [selectedOption, setSelectedOption] = useState('Select ISP type')
  console.log('selectedOption', selectedOption)
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [modalDisplayToggle, setModalDisplayToggle] = useState(false)
  // CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: 'blue' }} />
  // viewLogDate is the date for which daily analytics is to be viewed.
  const [viewLogDate, setViewLogDate] = useState('')
  // Initialise the date to be searched through the data.
  const overviewDate = useSelector((state) => state.dashboard.searchDate)
  // This is a piece of data from the Redux store that contains information used to display charts on a dashboard.
  const chartsData = useSelector((state) => state.dashboard.data)
  const [isLoading, setIsLoading] = useState(false);
  // This state variable contains the number of items to display in a table on the dashboard.
  const displayCount = useSelector((state) => state.dashboard.tableLength)
  const [searchDate, setSearchDate] = useState([])
  // Initialise the filters to be used while searching through the data.
  const filterOverviewOptions = useSelector((state) => state.dashboard.filterOption)

  // Available filter options for this page.
  const options = [
    { label: 'ARP', value: 'ARP' },
    { label: 'Tatkal AC', value: 'AC' },
    { label: 'Tatkal Non-AC', value: 'NON_AC' },
  ]

  const paginationFunctionVPS = async (pageNumber, sdate) => {
    setLoading(true)
    const data = await fetch('/api/fetch-sus-ips', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: pageNumber,
        type_vps: true,
        starting_date:
          searchVPSDate != null && searchVPSDate?.length != 0
            ? searchVPSDate[0]
            : new Date(0),
        ending_date:
          searchVPSDate != null && searchVPSDate?.length != 0
            ? searchVPSDate[1]
            : new Date(),
      }),
    })
    .then((response) => response.json())
    setSusIpsVps(data?.data_list?.map((item) => JSON.parse(item)))
    setSusIPCount(data?.page_count)

    setLoading(false)
  }

  const paginationFunctionNON = async (pageNumber, sdate) => {
    const data = await fetch('/api/fetch-sus-ips', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: pageNumber,
        type_vps: false,
        suspected_ip_date: sdate,
      }),
    })
    .then((response) => response.json())
    setSusIpsNotVps(data.data_list.map((item) => JSON.parse(item)))
    setSusNonIPCount(data.page_count)
    // setCurrentPage(pageNumber);
  }

  useEffect(() => {
    paginationFunctionVPS(1, new Date(0))
    paginationFunctionNON(1, new Date(0))
  }, [])

  // This function `viewReport` is used to fetch and set data from an API endpoint.
  const viewReport = async (f_date, f_type) => {
    let data = await fetch('/api/fetch-sus-data?log_date=' + f_date + '&log_type=' + f_type,)
      .then((res) => res.json())
      .then((res) => JSON.parse(res['data']))

      // This line sets the value of the `multiVps` state variable to the value of the `MULTI_VPS` key in the `data` object.
      setMultiVPS(data['MULTI_VPS'])
      // This line sets the value of the `vpsUser` state variable to the value of the `VPS_SUS` key in the `data` object.
      setVpsUser(data['VPS_SUS'])
      // This line sets the value of the `vpsReg` state variable to the value of the `VPS_REG` key in the `data` object
      setVpsReg(data['VPS_REG'])
      // : This line sets the value of the `nonVpsUser` state variable to the value of the `NON_VPS_SUS` key in the `data` object.
      setNonVpsUser(data['NON_VPS_SUS'])
      //  This line sets the value of the `totalSus` state variable to the value of the `TOTAL_SUS` key in the `data` object.
      setTotalSus(data['TOTAL_SUS'])
  }

  // Represents the default date range to display data for:
  const defaultDate = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]

  // Defines a function named searchTrendRange that display date range for suspected ip.
  const searchTrendRange = async (search_date) => {
    if (search_date == undefined) {
      search_date = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]
    }
    const data = await fetch('/api/fetch-sus-trend', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        std: search_date[0],
        etd: search_date[1],
      }),
    }).then((res) => res.json())
    setTotalRange(data['TOTAL_USER'])
    setRegRange(data['VPS_REG'])
    setNonVPSRange(data['NON_VPS_USER'])
    setVpsRange(data['VPS_USER'])
    setMultiRange(data['MULTI_VPS'])
    // Calculate the difference in days between two search dates
    var Difference_In_days = (search_date[1] - search_date[0]) / (1000 * 3600 * 24)
    // Convert the difference to an integer and store it in the state variable "trendDiffDate"
    setTrendDiffDate(parseInt(Difference_In_days))
  }

  // This function will be called when the user clicks the search button,
  const handleSearch = () => {
    setLoading(true)
    OverviewSearchDate(overviewDate, filterOverviewOptions)
  }

  const handlePageChange = (dataKey) => {
    if (selectedOption === 'Select ISP type') {
      setPageVPS(dataKey);
      setPageNON(dataKey);
      paginationFunctionVPS(dataKey, searchVPSDate);
      paginationFunctionNON(dataKey, searchNONVPSDate);
    } else if (selectedOption === 'VPS') {
      setPageVPS(dataKey);
      paginationFunctionVPS(dataKey, searchVPSDate);
    } else if (selectedOption === 'NON-VPS') {
      setPageNON(dataKey);
      paginationFunctionNON(dataKey, searchNONVPSDate);
    }
  };
  

  // This function will be called when the user selects a new limit in the limit dropdown,
  const handleChangeLimit = (dataKey) => {
    setPage(1)
    setLimit(dataKey)
    pagiFunc(1, dataKey)
  }

  // tableLengthOptions provides different options for the number of entries to be displayed in charts.
  const tableLengthOptions = [5, 10, 15, 20].map((item) => ({
    label: item,
    value: item,
  }))

  // close or remove the opened Modal.
  const closeDaily = () => {
    setShowDaily(false)
  }

  // An array of objects representing the dropdown items for the logs table filter.
  const logs_options = [
    { label: 'ARP', value: 'ARP' },
    { label: 'Tatkal-AC', value: 'AC' },
    { label: 'Tatkal-NONAC', value: 'NON_AC' },
  ]

  const handleFileSearch = () => {
    searchFile(fileUploadDate)
  }


 
  const downloadReport = async (vps, searchVPSDate, onSuccess, onError) => {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    fetch('/api/download-sus-ips', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type_vps: vps,
        // suspected_ip_date: sdate,
        status: [0],
        starting_date:
          searchVPSDate != null && searchVPSDate?.length != 0
            ? searchVPSDate[0]
            : new Date(0),
        ending_date:
          searchVPSDate != null && searchVPSDate?.length != 0
            ? searchVPSDate[1]
            : new Date(),
      }),
    }).then((response) => {
      if (response.ok) {
        // If the response is successful (status code 200-299), create a downloadable file
        response.blob().then((blob) => {
          let url = window.URL.createObjectURL(blob);
          let a = document.createElement('a');
          a.href = url;
          a.download =
            'Suspicious ' +
            (vps ? 'VPS' : 'NON_VPS') +
            '_IP_' +
            new Date().toDateString().replaceAll(' ', '_') +
            '_.csv';
          a.click();
          onSuccess();
        });
      } else {
        onError();
      }
    });
  };

  const handleVPSExport = async () => {
    setIsLoading(true);
    try {
      await downloadReport(
        true,
        searchVPSDate,
        () => {
          // onSuccess callback
          setIsLoading(false);
          // Display a success toast notification
          toast.success('File downloaded successfully!', {
            // Toast options...
          });
        },
        () => {
          // onError callback
          setIsLoading(false);
          // Display an error toast notification
          toast.error('Error while downloading the file.', {
            // Toast options...
          });
        }
      );
    } catch (error) {
      console.error('Error occurred while downloading the VPS export:', error);
      setIsLoading(false);
    }
  };
 
  const deleteIP = async (rowString) => {
    const data = await fetch('/api/delete-sus-ip?f_id=' + rowString)
  }

  // This function will be called when the user clicks the VPS search button,
  const handleVPSSearch = () => {
    setPageVPS(1)
    paginationFunctionVPS(1, searchVPSDate)
  }

  // This function will be called when the user clicks the NON-VPS search button,
  const handleNONVPSSearch = () => {
    setPageNON(1)
    paginationFunctionNON(1, searchNONVPSDate)
  }
 
  // Function for handling NON-VPS export button click
  const handleNONVPSExport = () => {
    downloadReport(false, searchNONVPSDate)
  }

  // State variable for tracking whether to show suspected IP addresses in the history section.
  const [
    suspectedIPAddressForHistory,
    setSuspectedIPAddressForHistory,
  ] = useState(false)

  const [searchModalDate, setSearchModalDate] = useState();

  const fetchModalData = async (page_no, ipaddr) => {
    const data = await fetch('/api/fetch-ip-all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_no,
        ip_addr: ipaddr,
        starting_date:
        searchModalDate != null && searchModalDate?.length != 0
          ? searchModalDate[0]
          : new Date(0),
          ending_date:
          searchModalDate != null && searchModalDate?.length != 0
          ? searchModalDate[1]
          : new Date(),
      }),
    }).then((response) => response.json())

    setModalData(data.data_list.map((item) => JSON.parse(item)))
    setModalCount(data.page_count)
    setModalLoad(false)
  }

  // openModal displays the modal.
  const openModal = (ipAddress) => {
    setModalLoad(true)
    setModalDisplayToggle(true)
    setSuspectedIPAddressForHistory(ipAddress)
    fetchModalData(1, ipAddress)
  }

  // closeModal removes the modal.
  const closeModal = () => {
    setModalDisplayToggle(false)
  }

  // Function for handling the change event of the dropdown
  function handleOptionChange(event) {
    setSelectedOption(event.target.value)
  }
  // Function for handling the select event of the dropdown
  function handleOptionSelect(option) {
    setSelectedOption(option)
    setCurrentPage(1);
  }

  // The "tabledata" variable is a filtered array of data based on the selected option in the dropdown.
  const tableData = [...susIPsVps, ...susIPsNotVps]?.filter((item, index) => {
    if (selectedOption === 'Select ISP type') {
      return true
    } else if (selectedOption === 'VPS' && item.VPS) {
      return true
    } else if (selectedOption === 'NON-VPS' && !item.VPS) {
      return true
    }
  })

  const handleSubmit = (event) => {
    event.preventDefault()
    // Perform search using the query state
    console.log(`Searching for: ${query}`)
  }

  // handleChange function update the changed search in the search input .
  const handleChange = (event) => {
    setQuery(event.target.value)
  }
 
  const renderTable = () => {
    return (
      <div style={{backgroundColor:'white' , margin:'1rem'}}>
        {/* VPS Table Start Here  */}

        <div className={styles.dailyrow + ' d-flex '}>
          {/* <label className={styles.label}>ISP Type</label> */}
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
          <div className=" me-auto p-2 ">
            <Dropdown
              title={selectedOption}
              value={selectedOption}
              onSelect={handleOptionSelect}
            >
              {dropdownItems.map((item) => (
                <Dropdown.Item key={item.value} eventKey={item.value}>
                  {item.label}
                </Dropdown.Item>
              ))}
            </Dropdown>
            <h6>
              {viewLogDate
                ? viewLogType +
                  ' Logs Dated ' +
                  new Date(viewLogDate).toDateString()
                : null}
            </h6>
          </div>
          <div className={styles.datePicker} >
            <DateRangePicker
              isoWeek
              disabledDate={afterToday()}
              value={searchVPSDate}
              placement="leftStart"
              onChange={(newvaluedate) => setSearchVPSDate(newvaluedate)}
              style={{ width: 200 }}
              format="dd-MM-yyyy"
            />
          </div>
          <div className={styles.allBtn}>
              <form onSubmit={handleSubmit}>
                <Button
                  appearance="primary"
                  onClick={handleVPSSearch}
                  value={query}
                  onChange={handleChange}
                  className={styles.searchBtn}
                >
                  Search
                </Button>
              </form>
            
                {allowed_actions?.download && (
                  <div className="p-2">
                    <Button
                      className={styles.exportBtn}
                      appearance="primary"
                      onClick={handleVPSExport}
                      disabled={searchVPSDate == null ? true : false}
                    >
                      Export
                    </Button>
                  </div>
                )}
              </div>
        </div>

        <div className={styles.tableContainer + ' col mx-auto'}>
          <Table
            loading={loading}
            rowHeight={50}
            autoHeight={1}
            data={tableData}
          >
            <Column width={150}>
              <HeaderCell>IP Address</HeaderCell>
              <Cell dataKey="IP_ADDRESS" />
            </Column>
            <Column width={250}>
              <HeaderCell>Autonomous System Number (Latest)</HeaderCell>
              <Cell style={{ padding: '6px' }}>{(rowData) => rowData.ASN}</Cell>
            </Column>
            <Column fullText minWidth={200} flexGrow={1}>
              <HeaderCell>Internet Service Provider (Latest)</HeaderCell>
              <Cell style={{ padding: '6px' }}>{(rowData) => rowData.ISP}</Cell>
            </Column>
            <Column flexGrow={1}>
              <HeaderCell>Type of IP Adress:</HeaderCell>
              <Cell>{(rowData) => (rowData.VPS ? 'VPS' : 'NON VPS')}</Cell>
            </Column>
            <Column flexGrow={1}>
              <HeaderCell>Ticket Count :</HeaderCell>
              <Cell>{(rowData) => rowData.TK_COUNT}</Cell>
              </Column>
            <Column width={125}>
              <HeaderCell>Action</HeaderCell>
              <Cell style={{ padding: '6px' }}>
                {(rowData) => (
                  <Button
                    appearance="primary"
                    onClick={() => openModal(rowData.IP_ADDRESS)}
                  >
                    View History
                  </Button>
                )}
              </Cell>
            </Column>
          </Table>
          <div className={styles.pagination}>
            {/* <Pagination
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
              total={susIPCount}
              activePage={pageVPS}
              onChangePage={handlePageChangeVPS}
            /> */}
            {/* <Pagination
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
              total={selectedOption === 'VPS' ? susIPCount : susNonIPCount}
              activePage={selectedOption === 'VPS' ? pageVPS : pageNON}
              onChangePage={handlePageChange}
            /> */}
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
          total={selectedOption === 'Select ISP type' ? (susIPCount + susNonIPCount) : (selectedOption === 'VPS' ? susIPCount : susNonIPCount)}
          activePage={selectedOption === 'VPS' ? pageVPS : pageNON}
          onChangePage={handlePageChange}
        />
          </div>
        </div>
        <Modal
          open={modalDisplayToggle}
          onClose={() => closeModal()}
          size="full"
          backdrop='static'
        >
          <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          <h3>History of IP Address :</h3>
          <Modal.Body>
            <div className={styles.modalStyles}>
              {true ? (
                <div className={styles.modalTable}>
                  <Table
                    loading={modalLoad}
                    rowHeight={50}
                    autoHeight={1}
                    data={modalData}
                  >
                    <Column width={200} fullText>
                      <HeaderCell>Log Date</HeaderCell>
                      <Cell>
                        {(rowData) => {
                          return rowData.DATE != undefined
                            ? new Date(rowData.DATE.$date).toDateString()
                            : null
                        }}
                      </Cell>
                    </Column>
                    <Column width={150}>
                      <HeaderCell>ASN</HeaderCell>
                      <Cell style={{ padding: '6px' }}>
                        {(rowData) => rowData.ASN}
                      </Cell>
                    </Column>
                    <Column fullText minWidth={500} flexGrow={1}>
                      <HeaderCell>Internet Service Provider</HeaderCell>
                      <Cell style={{ padding: '6px' }}>
                        {(rowData) => rowData.ISP}
                      </Cell>
                    </Column>
                    <Column minWidth={1500} flexGrow={1} fullText>
                      <HeaderCell>Tags</HeaderCell>
                      <Cell style={{ padding: '6px' }}>
                        {(rowData) => codeToTagTransform(rowData.TAGS)}
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
                      boundaryLinks
                      maxButtons={5}
                      size="xs"
                      limit={[10]}
                      layout={['total', '-', '|', 'pager', 'skip']} // Updated layout prop
                      total={modalCount}
                      activePage={pageVPS}
                      // onChangePage={handlePageChangeVPS}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={() => closeModal()} appearance="subtle">
              Close
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    )
  }

  // Render
  return (
    <>
      {(allowed_page?.suspected_ip_addresses && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board heading="Suspected IP Addresses" router={Router} />
            {renderTable()}
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
