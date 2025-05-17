// endpoint
const endPoint = process.env.API_ENDPOINT

// Import Libraries
import { useEffect, useState } from 'react'
import { Table, Pagination, DateRangePicker, Button, Checkbox, Modal, Whisper, Popover, SelectPicker } from 'rsuite'
const { Column, HeaderCell, Cell } = Table
import { validateUserCookiesFromSSR } from '../../utils/userVerification'
const { afterToday } = DateRangePicker

import { toast } from 'react-toastify'

import Router, { useRouter } from 'next/router'
import { useDispatch, useSelector } from 'react-redux'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSearch } from '@fortawesome/free-solid-svg-icons'

import { Circles } from 'react-loader-spinner'

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'

// Import Styles
import styles from './SuspectedUsers.module.scss'

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
}
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
const sources = [
  { label: 'ALL', value: 'ALL'}, 
  { label: "USER", value: "USER" },
  { label: "PNR", value: "PNR" },
  { label: "USER/PNR", value: "USER/PNR" }
];
// A function that transforms tag codes into their corresponding descriptions and returns a JSX element.
const codeToTagTransform = (RFI_RULE) => {
  return (
    <div className={styles.displayrfi}>
      {RFI_RULE != [] ?
        (<span>
        <Whisper
          placement='left'
          followCursor
          speaker={
            <Popover>
              {RFI_RULE?.map((x) => {
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
            {RFI_RULE?.join(", ") || "N.A."}
          </span>
        </Whisper>
        </span>
      ) : (
        <span>
          <Whisper
            placement='left'
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
  )
}

// The CheckCell component is a custom component that likely renders a clickable cell in a table
const CheckCell = ({ rowData, onChange, checkedKeys, dataKey, ...props }) => (
  <Cell {...props} style={{ padding: 0 }}>
    <div style={{ lineHeight: '46px' }}>
      <Checkbox
        value={rowData[dataKey]}
        inline
        onChange={onChange}
        checked={checkedKeys.some((item) => item === rowData[dataKey])}
      />
    </div>
  </Cell>
)

// Dashboard Component
const SusUsers = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.suspected_users) {
      router.push('/overview')
    }
  }, [])
  
  // Local States Regarding Page

  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false)
  const [searchUsername, setSearchUsername] = useState('')
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1)
  // This state holds a piece of data  that contains information about the user IDs.
  const [susPendData, setSusPendData] = useState([])
  // This state holds data that contains the total number of pages for the user IDs.
  const [susPendCount, setSusPendCount] = useState(0)
  // Initialise the date to be searched through the data.
  const [searchDate, setSearchDate] = useState()
  // Initialise the date to be searched through the data.
  const [blockDate, setBlockDate] = useState()
  //Main Table pagination display total rows and total pages and there states
  const [suspendedUserRowsMainTable, setSuspendedUserRowsMainTable] = useState(0);
  const [suspendedUserPagesMainTable, setSuspendedUserPagesMainTable] = useState(0);
  const [selectedSource, setSelectedSource] = useState('ALL');

  //   CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} />

  // This state variable is used to determine whether the checkboxes for a table of users are currently checked or not.
  const [checkedKeys, setCheckedKeys] = useState([])
  // Initialize checked and indeterminate variables to false
  let checked = false
  let indeterminate = false

  // Check if all keys are checked or none are checked
  if (checkedKeys.length === susPendData?.length) {
    checked = true
  } else if (checkedKeys.length === 0) {
    checked = false
  } else if (
    checkedKeys.length > 0 &&
    checkedKeys.length < susPendData.length
  ) {
    indeterminate = true
  }
  
  // Handle checking all keys
  const handleCheckAll = (value, checked) => {
    const keys = checked ? susPendData?.map((item) => item.USERNAME) : [];
    setCheckedKeys(keys);
  };

  const handleCheck = (value, checked) => {
    const keys = checked
      ? [...checkedKeys, value]
      : checkedKeys.filter((item) => item !== value)
    setCheckedKeys(keys)
  }

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }

  const handleSearch = () => {
    handleUserSearch();
    console.log(searchUsername);
  }

  // Defines a function named pagiFuncPend that takes two parameters: page_value, sDate.
  async function pagiFuncPend(page_value, sdate) {
    setLoading(true)
    const data = await fetch('/api/fetch-sus-user', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
        search_user: searchUsername,
        // suspected_date: sdate != null ? sdate : new Date(0),
        status: [0],
        source: selectedSource,
        starting_date:
        searchDate != null && searchDate?.length != 0
          ? searchDate[0]
          : new Date(0),
          ending_date:
          searchDate != null && searchDate?.length != 0
          ? searchDate[1]
          : new Date(),
      }),
    }).then((res) => res.json())
    await setSusPendData(data?.data_list?.map((item) => JSON.parse(item)))
    // await setSusPendCount(data?.page_count)
    setSuspendedUserRowsMainTable(data?.total_rows)
    setSuspendedUserPagesMainTable(data?.total_pages)
    setLoading(false)
  }

  // Defines a function named pagiFuncPend that takes two parameters: username, userstatus.
  function changeUserIDStatus(username, userstatus) {
    fetch('/api/change-user-status', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userid: username,
        status: userstatus,
      }),
    })
      .then((response) => {
        if (response.ok) {
          toast.success(`${username} Status Changed`)
        } else {
          toast.error(`HTTP error, status = ${response.status}`)
        }
      })
      .catch((error) => {
        console.error(error)
      })
  }

  // Defines a function named APIblockAllUSer that takes one parameters: username, userstatus.
  function APIblockAllUSer(bDate) {
    fetch('/api/block-users-date', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        block_date: bDate,
      }),
    })
      .then((response) => {
        if (response.ok) {
          toast.success(`All Users Dated ${block_date} Status Blocked`)
        } else {
          toast.error(`HTTP error, status = ${response.status}`)
        }
      })
      .catch((error) => {
        console.error(error)
      })
  }

  const downloadReport = async (fdate, searchDate) => {
    setIsLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const response = await fetch('/api/download-sus-users', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          suspected_date: fdate,
          search_user:searchUsername,
          status: [0],
          source: selectedSource,
          starting_date:
            searchDate != null && searchDate?.length != 0
              ? searchDate[0]
              : new Date(0),
          ending_date:
            searchDate != null && searchDate?.length != 0
              ? searchDate[1]
              : new Date(),
        }),
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // a.download = 'Suspicious_User_List_' + new Date().toDateString() + '_.xlsx';
      a.download = `Suspicious_User_List_from_${searchDate[0].toDateString().replaceAll(' ', '_')}_to_${searchDate[1].toDateString().replaceAll(' ', '_')}.csv`
      a.click();
      
      toast.success('File downloaded successfully!', {
        position: toast.POSITION.TOP_CENTER,
      });
    } catch (error) {
      console.error('Error occurred while downloading the export:', error);
      toast.error('An error occurred while downloading the export.', {
        position: toast.POSITION.TOP_CENTER,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // This function will be called when the user clicks a page number in the pagination component,
  const handlePageChange = (dataKey) => {
    setLoading(true)
    setPage(dataKey)
    pagiFuncPend(dataKey, searchDate)
  }

  // This function will be called when the user clicks the search button,
  const handleUserSearch = () => {
    setLoading(true)
    setPage(1)
    pagiFuncPend(1, searchDate)
  }

  // Handle blocking all users on a specific date
  const handleAllBlock = () => {
    // Check if a blockDate is provided
    if (blockDate != undefined || blockDate != null) {
      setLoading(true)
      // Call API to block all users on the provided date
      APIblockAllUSer(blockDate)
      // Call function to update pending page after blocking users
      pagiFuncPend(page, searchDate)
    } else {
      // Display error message if blockDate is not provided
      toast.error(
        'Please enter date for blocking all users on the respective date!',
      )
    }
  }

  // // Handle exporting user data to a report
  // const handleUserExport = () => {
  //   setLoading(true)
  //   // Call function to download user report for searchDate
  //   downloadReport(searchDate)
  // }

  // Handle changing the status of a specific user
  
  const handleUserIDStatus = (username, userstatus) => {
    setLoading(true)
    // Call function to change user status
    changeUserIDStatus(username, userstatus)
    // Call function to update pending page after changing user status
    pagiFuncPend(page, searchDate)
  }

  // Use Effect Page Effectiveness
  useEffect(() => {
    pagiFuncPend(1, searchDate)
  }, [])

  const [isLoading, setIsLoading] = useState(false);

  // const handleUserExport = async () => {
  //   setLoading(true)
  //   setIsLoading(true);

  //   try {
  //     await downloadReport(true, searchDate);
  //   } catch (error) {
  //     console.error('Error occurred while downloading the VPS export:', error);
  //   } finally {
  //     setIsLoading(false);
  //   }
  // };
  
  const handleUserExport = async () => {
    // if (searchDate == null) {
    //   return;
    // }

    await downloadReport(true, searchDate);
  };
  
  // Render
  return (
    <>
      {(allowed_page?.suspected_users && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board heading="Suspected Users" router={Router} />
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
    
            <div style={{backgroundColor:'white', margin:'1rem'}}>
            <div className={styles.dailyrow + ' d-flex '}>
              <div className="me-auto p-2">
                <h4>Suspected Users</h4>
              </div>
              <div className={styles.searchSource + ' p-2'}>
                <SelectPicker
                    data={sources}
                    label="Source"
                    searchable={false}
                    value={selectedSource}
                    onChange={setSelectedSource}
                    className={styles.MainselectPicker}
                />
              </div>
              <div className={styles.searchContainer}>
                <input
                  type="text"
                  className={styles.searchInput}
                  placeholder="Search User"
                  value={searchUsername}
                  onChange={(e) => setSearchUsername(e.target.value)}
                  onKeyDown={handleKeyPress}
                />
              </div>
                
              <div className={styles.AllBtn}>
                <div className={styles.datepicker1 + ' p-2'}>
                  <DateRangePicker
                    disabledDate={afterToday()}
                    value={searchDate}
                    onChange={(newValueDate) => setSearchDate(newValueDate)}
                    style={{ width: 220}}
                    format="dd-MM-yyyy"
                    placement='leftStart'
                    className={styles.datepicker1}
                  />
                </div>
                <div className={styles.searchBtn}>
                  <Button appearance="primary" onClick={handleUserSearch}>
                    Search
                  </Button>
                </div>
              {allowed_actions?.download && (
                <div className={styles.exportBtn}>   
                  <Button
                    appearance="primary"
                    onClick={handleUserExport}
                    disabled={searchDate == null || isLoading}
                  >
                    Export
                  </Button>
                </div>
              )}
              <div className={styles.blockBtn}>
                <Button
                  appearance="primary"
                  color="red"
                  onClick={() => handleUserIDStatus(checkedKeys, 1)}
                  disabled={checked == true || indeterminate == true ? false : true}
                >
                  Block Selected
                </Button>
              </div>
              <div className={styles.ignorBtn}>
                <Button
                  appearance="primary"
                  color="green"
                  onClick={() => handleUserIDStatus(checkedKeys, 2)}
                  disabled={checked == true || indeterminate == true ? false : true}
                >
                  Ignore Selected
                </Button>
              </div>
              </div>
            </div>
            <div className={styles.tableContainer + ' col mx-auto'}>
              <Table loading={loading} bordered autoHeight data={susPendData}>
                <Column minWidth={50} flexGrow={0.3} fullText align="center">
                  <HeaderCell style={{ padding: 0 }}>
                    <div style={{ lineHeight: '40px' }}>
                      <Checkbox
                        inline
                        checked={checked}
                        indeterminate={indeterminate}
                        onChange={handleCheckAll}
                      />
                    </div>
                  </HeaderCell>
                  <CheckCell
                    dataKey="USERNAME"
                    checkedKeys={checkedKeys}
                    onChange={handleCheck}
                  />
                </Column>
                <Column minWidth={200}  flexGrow={1} fullText>
                  <HeaderCell>USERID</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.USER_ID != '' ? rowData.USER_ID : '-'
                    }}
                  </Cell>
                </Column>
                <Column minWidth={200}  flexGrow={1} fullText>
                  <HeaderCell>Username</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.USERNAME != ''
                        ? rowData.USERNAME
                        : '-';
                    }}
                  </Cell>
                </Column>
                <Column minWidth={200}  flexGrow={0.8} fullText>
                  <HeaderCell>Marked Date</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.SUS_DATE != undefined
                        ? new Date(rowData.SUS_DATE.$date).toDateString()
                        : null
                    }}
                  </Cell>
                </Column>
                <Column minWidth={100}  flexGrow={0.6} fullText>
                  <HeaderCell>Source</HeaderCell>
                  <Cell>
                    {(rowData) => {
                      return rowData.SOURCE != ''
                      ? rowData.SOURCE
                      : '-';
                    }}
                  </Cell>
                </Column>
                <Column minWidth={200}  flexGrow={0.8} fullText>
                  <HeaderCell>RFI Rules</HeaderCell>
                  <Cell>
                    {(rowData) => codeToTagTransform(rowData.RFI_RULE)}
                  </Cell>
                </Column>

                {allowed_actions?.view && (
                  <Column minWidth={100} flexGrow={0.5} fullText>
                    <HeaderCell>Block</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) => (
                        <Button
                          appearance="primary"
                          color="red"
                          disabled={ checked == true || indeterminate == true ? true : false }
                          onClick={() => handleUserIDStatus([rowData.USERNAME], 1) }
                        >
                          Block
                        </Button>
                      )}
                    </Cell>
                  </Column>
                )}

                {allowed_actions?.view && (
                  <Column minWidth={100} flexGrow={0.4} fullText>
                    <HeaderCell>Ignore</HeaderCell>
                    <Cell style={{ padding: '6px' }}>
                      {(rowData) => (
                        <Button
                          appearance="primary"
                          color="green"
                          disabled={ checked == true || indeterminate == true ? true : false }
                          onClick={() => handleUserIDStatus([rowData.USERNAME], 2)}
                        >
                          Ignore
                        </Button>
                      )}
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
                  limit={[10]}
                  layout={['total', '-', '|', 'pager', 'skip']}
                  total={suspendedUserRowsMainTable}
                  pages={suspendedUserPagesMainTable}
                  activePage={page}
                  onChangePage={handlePageChange}
                />
              </div>
            </div>
            </div>
          
            <div className={styles.dailyrow + ' d-flex shadow-sm mx-3'}>
              <div className="me-auto p-2">
                <h4>Bulk Block Users <span><h6>( by Date )</h6></span></h4>
              </div>
              <div className={styles.datepicker + ' p-2'}>
                <DateRangePicker
                  placement="topEnd"
                    disabledDate={afterToday()}
                    value={blockDate}
                    onChange={(newValueDate) => setBlockDate(newValueDate)}
                    style={{ width: 240 }}
                    format="dd-MM-yyyy"
                  />
              </div>
              {allowed_actions?.veiw && (
                <div className="p-2">
                  <Button appearance="primary" color="red" onClick={handleAllBlock}>
                    Block All
                  </Button>
                </div>
              )}
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
