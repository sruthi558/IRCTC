import React, { useEffect, useRef, useState } from "react";
import styles from "./case-management-IP.module.scss";
import Sidebar from "@/components/Sidebar";
import Board from "@/components/Board";
import Router, { useRouter } from "next/router";
import { useSelector, useDispatch } from 'react-redux'
import UserInfoIcon from '@rsuite/icons/UserInfo';

import { Circles } from "react-loader-spinner";
import CloseIcon from '@rsuite/icons/Close';
import SearchIcon from '@rsuite/icons/Search';

import {
  Whisper,
  Popover,
  SelectPicker,
  Nav,
} from "rsuite";

const { afterToday } = DateRangePicker;
import {
  Button,
  DateRangePicker,
  Dropdown,
  Modal,
  Pagination,
  Table,
} from "rsuite";
import { toast } from "react-toastify";
import { Input, InputGroup} from 'rsuite';
import { Icon } from '@rsuite/icons';
const { Column, HeaderCell, Cell } = Table;

// import CloseIcon from '@rsuite/icons/Close';

const selectedOption = [
  { label: ["ALL"], value: ["ALL"] },
  { label: ["HIGH"], value: ["HIGH"] },
  { label: ["MEDIUM"], value: ["MEDIUM"] },
  { label: ["LOW"], value: ["LOW"] },
 
];

const CaseManagment = () => {

  // Initialize the router to get the routing info of the page
  const router = useRouter();

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector((state) => state.persistedReducer.user_pages);
  const allowed_action = useSelector((state) => state.persistedReducer.user_actions);

  // console.log(`Allowed Pages `, allowed_page);
  // console.log(`Allowed Actions `, allowed_action);

  useEffect(() => {
    if (!allowed_page?.casemanagement_user) {
      router.push("/overview");
    }
  }, []);

  const [isLoading, setIsLoading] = useState(false);
  const [tableData, setTableData] = useState([]);
  const [mainPageLoading, setMainPageLoading] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [selectedSeverityValue, setSelectedSeverityValue] = useState(["HIGH"]);
  const [currentPage, setCurrentPage] = useState(1);
  const [ipDateRangeValue, setIpDateRangeValue] = useState(getCurrentMonthDateRange());

  //  Modal History states and function start
  const [modalLoad, setModalLoad] = useState(false);  
  const [searchbar, setSearchbar] = useState('');

//   Modal States Start Here 
const [modalDisplayToggle, setModalDisplayToggle] = useState(false);
  const[ipAddress,setIpAddress]= useState('');
  const [currentModalPage, setCurrentModalPage] = useState(0)
  const [viewHistoryData, setViewHistoryData] = useState([]);
  const [currentDataType, setCurrentDataType] = useState('USER');
  const [viewHistoryTotalRows, setViewHistoryTotalRows] = useState(0);
  const [viewHistoryTotalPages, setViewHistoryTotalPages] = useState(0);
  const [modalCurrentPage, setModalCurrentPage] = useState(1);

 // Modal Functions Start Here ....
  const handleTabChange = (dataKey) => {
    setModalCurrentPage(1);
    let newDataType;
    switch (dataKey) {
      case "0":
        newDataType = "USER";
        break;
      case "1":
        newDataType = "PNR";
        break;
      default:
        break;
    }
    setCurrentDataType(newDataType);
    setCurrentModalPage(dataKey);
  };

  const getColumnHeaderDetails = () => {
    switch (currentDataType) {
      case "USER":
        return { text: "Username", color: "#1675E0"};
      case "PNR":
        return { text: "PNR", color: "#1675E0" };
      default:
        return { text: "Source Data", color: "red" };
    }
  };

  const openModal = (ipAddress) => {
    setModalDisplayToggle(true);
    setIpAddress(ipAddress);
    setCurrentDataType('USER');
    setCurrentModalPage(0);
    setModalCurrentPage(1);
    HistoryModalData(1, ipAddress, 'USER');
  };
 
  // closeModal removes the modal.
  const closeModal = () => {
    // Close the modal.
    setModalDisplayToggle(false);
    // resetModal();
  };
  
  const HistoryModalData = async (pageId, ip_address) => {
    setModalLoad(true);  
    try {
      const response = await fetch("/api/fetch-ip-history-modal", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageId,
          ip_addr: ip_address,
          source :currentDataType
        }),
      });
      const data = await response.json();
      setViewHistoryData(data?.data_list?.map((item) => JSON.parse(item)));
      setViewHistoryTotalRows(data?.total_rows); // Set the total rows
      setViewHistoryTotalPages(data?.total_pages); // Set the total pages
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setModalLoad(false);
  };

  // const tagCodes = {
  //   'DISPOSABLE_EMAIL' : 'UA5',
  //   'USER_REG_SAMEIP_SAMEADDR_MORE_4' : 'UA11',
  //   'INVALID_PINCODE' : 'UA2',
  //   'SUS_ADDRESS_IP_MORE_5' : 'UA8',
  //   'SUS_EMAIL_IP_MORE_5' : 'UA7',
  //   'SUS_USERNAME_IP_MORE_5' : 'UA6',
  //   'SUS_FULLNAME_IP_MORE_5' : 'UA9',
  //   'SUS_REG_TIME_WITHIN_60_SEC' : 'UA10',
  //   'USER_BOOK_SUSPICIOUS_MOBILE' : 'UA3',
  //   'USER_BOOK_VPS' : 'UB1',
  //   'USER_SERIES_BOOK_VPS' : 'UB1' ,
  //   'USER_REG_SERIES_COMMON_NAME' : 'UA4',
  //   'USER_REG_SERIES_NONVPS' : 'UA6',
  //   'USER_REG_SERIES_VPS' : 'UA6',
  //   'USER_SERIES_BOOK_NONVPS' : 'UB2',
  //   'SUSPICIOUS_IP' : 'UB1',
  //   'SUSPICIOUS_USER' : 'UB2',
  //   'DISPOSABLE_EMAIL' : 'UB3'
  // }

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

  const filterTableData = async (pageValue) => {
    setMainPageLoading(true);
    try {
      const response = await fetch("/api/ip-case-mgmt", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageValue,
          risk: selectedSeverityValue,
          ip_address :searchbar,
          starting_date:
          ipDateRangeValue && ipDateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(ipDateRangeValue[0]) 
            : formatDateToISOWithTimeZone(new Date(0)), 
        ending_date:
          ipDateRangeValue && ipDateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(ipDateRangeValue[1]) 
            : formatDateToISOWithTimeZone(new Date()),
        }),
      });
      const data = await response.json();
      
      const fetchdata = data?.data_list?.map((item) => {
        try {
          return JSON.parse(item);
        } catch (parseError) {
          console.error("Error parsing JSON:", parseError);
          return {};
        }
      });

      setTableData(fetchdata);
      setTotalRows(data?.total_rows);
      setTotalPages(data?.total_pages);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setMainPageLoading(false);
  };

  const downloadReport = async () => {
    setIsLoading(true);
    fetch("/api/export-ip-case", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        risk: selectedSeverityValue,
        ip_address :ipAddress,
        starting_date:
        ipDateRangeValue && ipDateRangeValue.length !== 0
          ? formatDateToISOWithTimeZone(ipDateRangeValue[0]) 
          : formatDateToISOWithTimeZone(new Date(0)), 
      ending_date:
        ipDateRangeValue && ipDateRangeValue.length !== 0
          ? formatDateToISOWithTimeZone(ipDateRangeValue[1]) 
          : formatDateToISOWithTimeZone(new Date()),
      }),
    })
      .then(async (response) => {
        setIsLoading(false);
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          // a.download = `User_History_${new Date().toDateString().replaceAll(" ", "_")}+_.xlsx`;
          a.download = `ip_case_management_${ipDateRangeValue[0].toDateString().replaceAll(' ', '_')}_to_${ipDateRangeValue[1].toDateString().replaceAll(' ', '_')}.csv`
          a.click();
          toast.success("File Download successfully");
        } else {
          toast.error("File download failed");
        }
      });
    setIsLoading(true);
  };

  const downloadModalReport = async (ipAddress) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/download-ip-modal", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ip_addr:ipAddress,
        source :currentDataType,
      }) 
      
    }).then(async (response) => {
      setIsLoading(false);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Suspicious_IP_${ipAddress}_${currentDataType}.csv`
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
  };
  const formatDateToISOWithTimeZone = (date) => {
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString();
  };

  const handleSearch = () => {
    // if (ipDateRangeValue && ipDateRangeValue.length === 2) {
    setTableData([]);
    setCurrentPage(1);
    setIpAddress(ipAddress);
    filterTableData(1, selectedSeverityValue, ipAddress);
    console.log('ipAddress', ipAddress)
    // } else {
    //   toast.error(errorText);
    // }
  };

  const handlePageChange = (pageValue, selectedSeverityValue) => {
    setTableData([]);
    setCurrentPage(pageValue);
    filterTableData(pageValue, selectedSeverityValue);
  };

  const handleOptionSelect = (Option) => {
    setSelectedSeverityValue(Option);
  };
 
  function getCurrentMonthDateRange() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    return [firstDayOfMonth, lastDayOfMonth];
  }
  const handleDateRangeSelect = (newvaluedate) => {
    setIpDateRangeValue([]);
    setIpDateRangeValue(newvaluedate);
  };
  const handleClearDateRange = () => {
    // Clear the date range manually
    setIpDateRangeValue([]);
  };
  const errorText = "Please Provide a valid DateRange"

  const handlePageChangeModal = ( ipAddress,pageId,page) => {
    setViewHistoryData([]);
    setModalCurrentPage(pageId); 
    HistoryModalData(pageId, ipAddress, page, currentDataType);
  };

  const renderTable = () => {
    return (
      <div>
        {/* Main Page Container*/}
        <div className={styles.main_container}>
        <div className={styles.headFilters}>
            <div className={styles.filterOne}>
              <SelectPicker
                title={selectedSeverityValue}
                value={selectedSeverityValue}
                data={selectedOption}
                label='Severity Type '
                appearance="subtle"
                onChange={(newValue) => handleOptionSelect(newValue)}
                className={styles.dropdownStyles}
                searchable={false}
              />
              <DateRangePicker
                isoWeek
                disabledDate={afterToday()}
                value={ipDateRangeValue || getCurrentMonthDateRange()}
                onChange={(newvaluedate) => handleDateRangeSelect(newvaluedate)}
                className={styles.userDatePicker}
                format="dd-MM-yyyy"
                appearance="subtle"
                onClick={handleClearDateRange}
                cleanable={false}
                ranges={[
                  {
                    label: 'Today',
                    value: [new Date(), new Date()],
                  },
                  {
                    label: 'This Month',
                    value: getCurrentMonthDateRange(), 
                  },
                ]}
              />

              <InputGroup className={styles.inputsearch}>
                <InputGroup.Addon className={styles.textColor}>
                IP Address:
                </InputGroup.Addon>
                
                <Input
                  className={styles.inputinnersearch}
                  placeholder="Search Ip Address"
                  value={searchbar}
                  onChange={(value, e) => setSearchbar(value)}
                />
              </InputGroup>
        
              </div>
            <div className={styles.filterTwo}>
              <Button
                appearance="primary"
                onClick={handleSearch}
                value={ipAddress}
                // onChange={handleChange}
                className={styles.searchBtn}
              >
                Search
              </Button>
              {allowed_action?.download && (
              <Button
                className={styles.exportBtn}
                appearance="primary"
                onClick={() => downloadReport()}
                disabled={ipDateRangeValue == null && searchbar == "" ? true : false}
              >
                Export
              </Button>
             )}
            </div>
          </div>
          {/* PNR Table Data Container */}
          <div className={styles.tableContainer + " col mx-auto"}>
            <table className={styles.data_table}>
              {mainPageLoading && (
                <div className={styles.loader_container}>
                  <p className={styles.loader_text} />
                  <div className={styles.loader} />
                </div>
              )}
              <thead className={styles.tables_head}>
                <tr>
                  <th>IP AddRESS</th>
                  <th>SUSPECTED DATE</th>
                  <th>ISP</th>
                  <th>ASN</th>
                  <th>VPS STATUS</th>
                  <th>RFI</th>
                  <th>RISK SEVERITY</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {tableData?.length > 0 ? (
                  // Render table rows
                  tableData.map((item, index) => (
                    <tr key={index.id}>
                      <td>{item?.IP_ADDRESS ? item?.IP_ADDRESS : "N.A."}</td>
                      <td>
                        {item?.DATE != undefined && item?.DATE != "N.A."
                          ? new Date(item?.DATE.$date).toDateString()
                          : "N.A."}
                      </td>
                      <td>{item?.ISP ? item?.ISP : "N.A."}</td>
                      <td>{item?.ASN ? item?.ASN : "N.A."}</td>
                      <td>{item?.VPS ? 'True' : 'False' } </td>
                      <td  className={styles.rfiStyles}>
                        {item?.RFI_RULE != [] ? (
                          <span>
                            <Whisper
                              placement="left"
                              followCursor
                              speaker={
                                <Popover>
                                  {item?.RFI_RULE?.map((x) => {
                                    return (
                                      <span key={x} className={styles.tagCodes}>
                                        <span className={styles.popovercode}>
                                          {x} : {tagCodes[x]}
                                        </span>
                                      </span>
                                    );
                                  })}
                                </Popover>
                              }
                            >
                              <span className={styles.rfiStyles}> {item?.RFI_RULE?.join(", ")} </span>
                            </Whisper>
                          </span>
                        ) : (
                          <span>
                            <Whisper
                              placement="left"
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
                              <span> N.A. </span>
                            </Whisper>
                          </span>
                        )}
                      </td>
                      {/* <td>{item?.RFI ? item?.RFI : "N.A"} </td> */}
                      <td>{item?.RISK ? item?.RISK : "N.A"} </td>
                      {allowed_action?.view && (
                          <td>
                             <Button
                              appearance="primary"
                              onClick={() =>{ openModal(item?.IP_ADDRESS);
                              setIpAddress(item?.IP_ADDRESS);
                              } }
                            >
                              View History
                            </Button>
                          </td>
                        )}
                    </tr>
                  ))
                ) : (
                  // Display a message when there is no data
                  <tr>
                    {/* <td colSpan="5">
                      <p>No data available.</p>
                    </td> */}
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className={styles.pagination}>
          {mainPageLoading ? (
            <div>
            </div>
          ) : (
            <Pagination
            prev
            next
            first
            last
            ellipsis
            boundaryLinks
            maxButtons={5}
            size="xs"
            limit={20}
            layout={["total", "-", "|", "pager", "skip"]}
            pages={totalPages}
            total={totalRows}
            activePage={currentPage}
            onChangePage={handlePageChange}
          />
          )}
          
        </div>
      </div>
    );
  };

  useEffect(() => {
    setTableData([])
    filterTableData(1);
  }, []);

  const hasMounted = useRef(false);
  
  useEffect(() => {
    if (hasMounted.current && modalDisplayToggle) {
      HistoryModalData(modalCurrentPage, ipAddress, currentDataType);
    } else {
      hasMounted.current = true;
    }
  }, [currentDataType]);
  return (
    <>
        <Modal open={modalDisplayToggle} onClose={() => closeModal()} size="lg" backdrop="static">
            <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
              <h3>History of IP Address :</h3>
              <Modal.Body>
              <Nav
                appearance="tabs"
                activeKey={currentModalPage.toString()}
                onSelect={handleTabChange}
                className={styles.navstyle}
              >
                <Nav.Item
                    eventKey="0"  
                    className={styles.textStyle} 
                    onSelect={() => handleTabChange("0")}
                  >
                    USER Data
                  </Nav.Item>
                  <Nav.Item 
                    eventKey="1"   
                    className={styles.textStyle}
                    onSelect={() => handleTabChange("1")}
                  >
                    PNR Data
                  </Nav.Item>
              </Nav>
                <div className={styles.modalStyles}>
                  <div className={styles.modalTable}>
                  {viewHistoryData && viewHistoryData.length > 0 ? (
                    <Table
                      loading={modalLoad}
                      rowHeight={45}
                      autoHeight={true}
                      data={viewHistoryData}
                    >
                      <Column fullText minWidth={80} flexGrow={0.4}>
                        <HeaderCell className={styles.headerstyling}>IP Address</HeaderCell>
                        <Cell  style={{ alignItems:"left" }}>
                          {(rowData) => rowData?.IP_ADDRESS}
                        </Cell>
                      </Column>
                      <Column minWidth={130} flexGrow={0.4} fullText>
                        <HeaderCell className={styles.headerstyling}>IP Log Date </HeaderCell>
                        <Cell>
                          {(rowData) => {
                            return rowData?.LOG_DATE != undefined
                              ? new Date(rowData.LOG_DATE.$date).toDateString()
                              : null;
                          }}
                        </Cell>
                      </Column>
                      <Column fullText minWidth={100} flexGrow={0.6}>
                        <HeaderCell className={styles.headerstyling}>Logged ISP</HeaderCell>
                        <Cell  style={{ alignItems:"center" }}>
                          {(rowData) => rowData?.ISP}
                        </Cell>
                      </Column>
                      <Column fullText minWidth={100} flexGrow={0.4}>
                        <HeaderCell className={styles.headerstyling}>Logged ASN</HeaderCell>
                        <Cell  style={{ alignItems:"center" }}>
                          {(rowData) => rowData?.ASN}
                        </Cell>
                      </Column>
                      
                      <Column fullText minWidth={30} flexGrow={0.3}>
                        <HeaderCell className={styles.headerstyling}>Source</HeaderCell>
                        <Cell  style={{ alignItems:"center" }}>
                          {(rowData) => rowData.SOURCE}
                        </Cell>
                      </Column>
                     
                      {/* <Column fullText minWidth={100} flexGrow={0.4}>
                        <HeaderCell className={styles.headerstyling1}>
                          {getColumnHeaderName()}
                        </HeaderCell>
                        <Cell style={{ alignItems: "center" }}>
                          {(rowData) => rowData.SOURCE_DATA}
                        </Cell>
                      </Column> */}

                      <Column fullText minWidth={100} flexGrow={0.4}>
                        <HeaderCell
                          className={styles.headerstyling}
                          // style={{ color: getColumnHeaderDetails().color }}
                        >
                          {getColumnHeaderDetails().text}
                        </HeaderCell>
                        <Cell style={{ alignItems: "center", color: "#1675E0" }}>
                          {(rowData) => rowData.SOURCE_DATA}
                        </Cell>
                      </Column>

                      <Column fullText minWidth={80} flexGrow={0.3}>
                        <HeaderCell className={styles.headerstyling}>VPS Status</HeaderCell>
                        <Cell  style={{ alignItems:"center" }}>
                          {(rowData) => rowData.VPS ? "True" : "False"}
                        </Cell>
                      </Column>
                    </Table>
                  ) : (
                    <span className={styles.noDataMsg}>{`No History details found for the source ${currentDataType}`}</span>

                  )
                }
                  </div>
                </div>
              </Modal.Body>
              <Modal.Footer>
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
                        limit={20}
                        layout={["total", "-", "|", "pager", "skip"]} // Updated layout prop
                        pages={viewHistoryTotalPages}
                        total={viewHistoryTotalRows}
                        activePage={modalCurrentPage}
                        onChangePage={(page) => handlePageChangeModal(ipAddress, page)}
                      />
                    </div>
                {allowed_action?.download && (
                  <Button
                    appearance="primary"
                    onClick={()=>downloadModalReport(ipAddress)}
                  >
                    Export
                  </Button>
                )}
                <Button onClick={() => closeModal()} appearance="subtle">
                  Close
                </Button>
              </Modal.Footer>
        </Modal>
      
      {/* MAIN Table */}
      {allowed_page?.casemanagement_user && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board heading="IP Case Management" router={Router} />
            {renderTable()}

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
          </div>
        </div>
      )}
    </>
  );
};

export default CaseManagment;
