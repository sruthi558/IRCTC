import React, { useEffect, useState } from "react";
import styles from "./case-user.module.scss";
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

  console.log(`Allowed Pages `, allowed_page);
  console.log(`Allowed Actions `, allowed_action);

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

  const [selectValues, setSelectValues] = useState(["HIGH"]);
  const [currentPage, setCurrentPage] = useState(1);
  const [inputValue, setInputValue] = useState("");
  const [userDateRangeValue, setUserDateRangeValue] = useState(getCurrentMonthDateRange());

  //  Modal History states and function start
  const [openHistoryModal, setOpenHistoryModal] = useState(false);
  const [modalLoad, setModalLoad] = useState(false);
  const [modalTabledata, setModalTabledata] = useState([]);
  const [historyModalTotalPages, setHistoryModalTotalPages] = useState(0);
  const [historyModalTotalRows, setHistoryModalTotalRows] = useState(0);
  const [historyModalCurrentPage, setHistoryModalCurrentPage] = useState(1);
  const [modalUserName, setModalUserName] = useState("");
  const [searchbar, setSearchbar] = useState('');


  const openModal = (modalUserName) => {
    setOpenHistoryModal(true);
    HistoryModalData(modalUserName);
  };

  // closeModal removes the modal.
  const closeModal = () => {
    // Close the modal.
    setOpenHistoryModal(false);
    // resetModal();
  };
  
  const HistoryModalData = async (modalUserName) => {
    setModalLoad(true);
    try {
      const response = await fetch("/api/case-mgmt-user", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: modalUserName,
        }),
      });
      const data = await response.json();
      setModalTabledata(data?.data_list?.map((item) => JSON.parse(item)));
      setHistoryModalTotalRows(data?.total_rows); 
      setHistoryModalTotalPages(data?.total_pages);
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
      const response = await fetch("/api/case-mgmt", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          risk: selectValues,
          username:searchbar,
          page_id: pageValue,
          starting_date:
          userDateRangeValue && userDateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(userDateRangeValue[0]) 
            : formatDateToISOWithTimeZone(new Date(0)), 
        ending_date:
          userDateRangeValue && userDateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(userDateRangeValue[1]) 
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
    fetch("/api/export-case-mgmt", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        risk: selectValues,
        username:searchbar,
        starting_date:
        userDateRangeValue && userDateRangeValue.length !== 0
          ? formatDateToISOWithTimeZone(userDateRangeValue[0]) 
          : formatDateToISOWithTimeZone(new Date(0)), 
      ending_date:
        userDateRangeValue && userDateRangeValue.length !== 0
          ? formatDateToISOWithTimeZone(userDateRangeValue[1]) 
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
          a.download = `User_case_management_${userDateRangeValue[0].toDateString().replaceAll(' ', '_')}_to_${userDateRangeValue[1].toDateString().replaceAll(' ', '_')}.csv`
          a.click();
          toast.success("File Download successfully");
        } else {
          toast.error("File download failed");
        }
      });
    setIsLoading(true);
  };

  const formatDateToISOWithTimeZone = (date) => {
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString();
  };

  const handleSearch = (pageValue) => {
    // if (userDateRangeValue && userDateRangeValue.length === 2) {
    setTableData([]);
    setCurrentPage(1);
    filterTableData(1, selectValues);
    // } else {
    //   toast.error(errorText);
    // }
  };

  const handlePageChange = (pageValue, selectValues) => {
    setTableData([]);
    setCurrentPage(pageValue);
    filterTableData(pageValue, selectValues);
  };

  const handleOptionSelect = (Option) => {
    setSelectValues(Option);
  };
 

  function getCurrentMonthDateRange() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    return [firstDayOfMonth, lastDayOfMonth];
  }
  const handleDateRangeSelect = (newvaluedate) => {
    setUserDateRangeValue([]);
    setUserDateRangeValue(newvaluedate);
  };
  const handleClearDateRange = () => {
    // Clear the date range manually
    setUserDateRangeValue([]);
  };
  const errorText = "Please Provide a valid DateRange"

  const renderTable = () => {
    return (
      <div>
        {/* Main Page Container*/}
        <div className={styles.main_container}>
          {/* Search Input Bar */}
          <div className={styles.headFilters}>
            <div className={styles.filterOne}>
              {/* <Dropdown
                value={selectValues}
                data={selectedOption}
                placeholder="Select a severity"
                searchable={false}
                onChange={(value)=>setSelectValues(value)}
               className={styles.checkPicker}
              /> */}
              {/* <Dropdown
                title={selectValues}
                value={selectValues}
                label='Filter by'
                onSelect={handleOptionSelect}
                className={styles.dropdownStyles}
              >
                {selectedOption.map((item) => (
                  <Dropdown.Item key={item.value} eventKey={item.value}>
                    {item.label}
                  </Dropdown.Item>
                ))}
              </Dropdown> */}

              <SelectPicker
                title={selectValues}
                value={selectValues}
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
                value={userDateRangeValue || getCurrentMonthDateRange()}
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
                Username:
                </InputGroup.Addon>
                
                <Input
                  className={styles.inputinnersearch}
                  placeholder="Search Username"
                  value={searchbar}
                  onChange={(value, e) => setSearchbar(value)}
                />
          
              </InputGroup>
        
              </div>

            <div className={styles.filterTwo}>
              <Button
                appearance="primary"
                onClick={handleSearch}
                value={searchbar}
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
                disabled={userDateRangeValue == null && searchbar == "" ? true : false}
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
                  <th>USER NAME</th>
                  <th>Email</th>
                  <th>SUSPECTED DATE</th>
                  <th>RFI RULE</th>
                  <th>USER SEVERITY</th>
                  <th>User Details</th>
                </tr>
              </thead>
              <tbody>
                {tableData?.length > 0 ? (
                  // Render table rows
                  tableData.map((item, index) => (
                    <tr key={index}>
                      <td>{item?.USERNAME ? item?.USERNAME : "N.A."}</td>
                      <td>{item?.EMAIL ? item?.EMAIL : "N.A."}</td>
                      <td>
                        {item?.SUS_DATE != undefined && item?.SUS_DATE != "N.A."
                          ? new Date(item?.SUS_DATE.$date).toDateString()
                          : "N.A."}
                      </td>
                      <td >
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
                      <td>{item?.USR_RISK ? item?.USR_RISK : "N.A"} </td>
                      <td>
                        <Button
                          appearance="primary"
                          onClick={() => {
                            setModalUserName(item?.USERNAME);
                            openModal(item?.USERNAME);
                          }}
                        >
                          View Details
                        </Button>
                      </td>
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

  function containsNAInAddress(address) {
    const parts = [
      address?.ADDRESS,
      address?.STREET,
      address?.COLONY,
      address?.DISTRICT,
      address?.STATE,
      address?.PIN_CODE,
    ];

    return parts.some(
      (part) => typeof part === "string" && part.trim().toLowerCase() === "n.a."
    );
  }

  useEffect(() => {
    setOpenHistoryModal(false);
    setTableData([])
    filterTableData(1);
  }, []);

  return (
    <>
      {/* USER Details Modal */}
      {allowed_action?.view && (
        <Modal open={openHistoryModal} onClose={() => closeModal()} size="xs" className={styles.modalStyle} backdrop='static'>
          <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>

          <Modal.Body>
            <div className={styles.vertical_table_container}>
              {/* <h1>{<UserInfoIcon/>}</h1> */}
              <h3> User Details </h3>
              <table className={styles.vertical_table}>
                <thead>
                </thead>
                {modalTabledata?.length > 0 ? (
                  modalTabledata?.map((data) => (
                    <tbody>
                      <tr>
                        <td className={styles.table_cell}>Full Name</td>
                        <td className={styles.table_cell1}>{data?.FIRST_NAME} {data?.MIDDLE_NAME} {data?.LAST_NAME}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>User Name</td>
                        <td className={styles.table_cell1}>{data?.USERNAME}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Source</td>
                        <td className={styles.table_cell1}>{data?.SOURCE}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Vendor</td>
                        <td className={styles.table_cell1}>{data?.VENDOR_REGISTRATION ? 'True' : 'False' }</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Reg. Date</td>
                        {/* <td className={styles.table_cell}>{data?.REGISTRATION_DATETIME}</td> */}
                        <td className={styles.table_cell1}> 
                        {data?.REGISTRATION_DATETIME != undefined && data?.REGISTRATION_DATETIME != "N.A."
                            ? new Date(data?.REGISTRATION_DATETIME.$date).toDateString()
                            : "N.A."}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Reg. Email</td>
                        <td className={styles.table_cell1}>{data?.EMAIL}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Reg. Phone</td>
                        <td className={styles.table_cell1}>{data?.REGISTERED_MOBILE}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Reg. Address</td>
                        {/* <td className={styles.table_cell}>{data?.ADDRESS}</td> */}
                        <td className={styles.table_cell1}> {data?.ADDRESS}, {data?.STREET}, {data?.COLONY}, {data?.POSTOFFICE}, {data?.DISTRICT}, {data?.STATE}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Reg. IP</td>
                        <td className={styles.table_cell1}>{data?.IP_ADDRESS}</td>
                      </tr>
                    
                      <tr>
                        <td className={styles.table_cell}>
                          Total Booked Tickets
                        </td>
                        <td className={styles.table_cell1}>{data?.TOTAL_BOOKED_TICKETS}</td>
                      </tr>
                    </tbody>
                  ))
                ) : (
                  <div className={styles.modal_loader_container}>
                    <div className={styles.modal_loader} />
                  </div>
                )}
              </table>
            </div>
          </Modal.Body>
        </Modal>
      )}
      
      {/* MAIN Table */}
      {allowed_page?.casemanagement_user && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board heading="User Case Management" router={Router} />
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
