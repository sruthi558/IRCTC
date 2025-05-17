import React, { useEffect, useState } from "react";
import styles from "./case-managment-pnr.module.scss";
import Sidebar from "@/components/Sidebar";
import Board from "@/components/Board";
import Router, { useRouter } from "next/router";
import { useSelector, useDispatch } from 'react-redux'

import { Circles } from "react-loader-spinner";
import CloseIcon from '@rsuite/icons/Close';
import SearchIcon from '@rsuite/icons/Search';

const { afterToday } = DateRangePicker;
import {
  Button,
  DateRangePicker,
  Dropdown,
  Input,
  InputGroup,
  Modal,
  Pagination,
  SelectPicker,
  Table,
} from "rsuite";
import { tr } from "date-fns/locale";
import { toast } from "react-toastify";
import {
  Whisper,
  Popover,
} from "rsuite";

// const selectedOption = [
//   "ALL",
//   "LOW",
//   "MEDIUM",
//   "HIGH"
// ].map((item) => ({ label: item, value: item }));

const selectedSeverityOption = [
  { label: ["ALL"], value: ["ALL"] },
  { label: ["HIGH"], value: ["HIGH"] },
  { label: ["MEDIUM"], value: ["MEDIUM"] },
  { label: ["LOW"], value: ["LOW"] },
];

const selectedDateOptions = ["Booking Date", "Journey Date"].map((item) => ({
  label: item,
  value: item,
}));
const CaseManagment = () => {

  // Initialize the router to get the routing info of the page
  const router = useRouter();

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector((state) => state.persistedReducer.user_pages);
  const allowed_action = useSelector((state) => state.persistedReducer.user_actions);

  // console.log(`Allowed Pages `, allowed_page);
  // console.log(`Allowed Actions `, allowed_action);

  useEffect(() => {
    if (!allowed_page?.casemanagement_pnr) {
      router.push("/overview");
    }
  }, []);

  const [isLoading, setIsLoading] = useState(false);
  const [tableData, setTableData] = useState([]);
  const [mainPageLoading, setMainPageLoading] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [selectedSevirityPnr, setSelectedSevirityPnr] = useState(["MEDIUM"]);
  const [currentPage, setCurrentPage] = useState(1);
  const [inputValue, setInputValue] = useState("");
  const [dateRangeValue, setDateRangeValue] = useState(getCurrentMonthDateRange());

  //  Modal History states and function start
  const [openHistoryModal, setOpenHistoryModal] = useState(false);
  const [modalLoad, setModalLoad] = useState(false);
  const [modalTabledata, setModalTabledata] = useState([]);
  const [detailModalTotalPages, setDetailModalTotalPages] = useState(0);
  const [detailModalTotalRows, setDetailModalTotalRows] = useState(0);
  const [detailModalCurrentPage, setDetailModalCurrentPage] = useState(1);
  const [modalPnrNumber, setModalPnrNumber] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("Booking Date");
  const [searchPnrNumber, setSearchPnrNumber] = useState('')

  // closeModal removes the modal.
  const openModal = (modalPnrNumber) => {
    // Close the modal.
    setOpenHistoryModal(true);
    detailPnrModalData(modalPnrNumber);
  };
  // closeModal removes the modal.
  const closeModal = () => {
    // Close the modal.
    setOpenHistoryModal(false);
    // resetModal();
  };

  const detailPnrModalData = async (modalPnrNumber) => {
    setModalLoad(true);
    try {
      const response = await fetch("/api/case_pnr_data_detail", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pnr_number: modalPnrNumber,
        }),
      });

      const data = await response.json();
      setModalTabledata(data?.data_list?.map((item) => JSON.parse(item)));
      setDetailModalTotalRows(data?.total_rows);
      setDetailModalTotalPages(data?.total_pages);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setModalLoad(false);
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

  const mainTableData = async (pageValue) => {
    setMainPageLoading(true);
    try {
      const response = await fetch("/api/case_pnr_data", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          risk: selectedSevirityPnr,
          page_id: pageValue,
          filter_date:selectedSeverity,
          search_pnr:searchPnrNumber,         
        starting_date:
          dateRangeValue && dateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(dateRangeValue[0]) 
            : formatDateToISOWithTimeZone(new Date(0)), 
        ending_date:
          dateRangeValue && dateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(dateRangeValue[1]) 
            : formatDateToISOWithTimeZone(new Date()),
        }),
        timeout: 5 * 60 * 1000, // timer Set for 5 min
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
    fetch("/api/pnr_case_export", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        risk: selectedSevirityPnr,
        filter_date:selectedSeverity,
        search_pnr:searchPnrNumber, 
        starting_date:
          dateRangeValue && dateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(dateRangeValue[0]) 
            : formatDateToISOWithTimeZone(new Date(0)), 
        ending_date:
          dateRangeValue && dateRangeValue.length !== 0
            ? formatDateToISOWithTimeZone(dateRangeValue[1]) 
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
          a.download = `Pnr_case_management_${dateRangeValue[0].toDateString().replaceAll(' ', '_')}_to_${dateRangeValue[1].toDateString().replaceAll(' ', '_')}.csv`
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
    // if (dateRangeValue && dateRangeValue.length === 2) {
    setTableData([]);
    setCurrentPage(1);
    mainTableData(1, selectedSevirityPnr);
    // } else {
    //   toast.error(errorText);
    // }
  };

  const handlePageChange = (pageValue, selectedSevirityPnr) => {
    setTableData([]);
    setCurrentPage(pageValue);
    mainTableData(pageValue, selectedSevirityPnr);
  };

  const handleClearDateRange = () => {
    // Clear the date range manually
    setDateRangeValue([]);
  };

  const handleSelectSeverity = (Option) => {
    setSelectedSeverity(Option);
  };

  const   renderTable = () => {
    return (
      <div>
        {/* Main Page Container*/}
        <div className={styles.main_container}>
          {/* Search Input Bar */}
          <div className={styles.headFilters}>
            <div className={styles.filterOne}>
              {/* <CheckPicker
                value={selectValues}
                data={selectedOption}
                placeholder="Select a severity"
                searchable={false}
                onChange={(value)=>setSelectValues(value)}
               className={styles.checkPicker}
                /> */}
               
              {/* <Dropdown
                title={selectedSevirityPnr}
                value={selectedSevirityPnr}
                onSelect={handleOptionSelect}
                className={styles.dropdownStyles}
              >
                {selectedSeverityOption.map((item) => (
                  <Dropdown.Item key={item.value} eventKey={item.value}>
                    {item.label}
                  </Dropdown.Item>
                ))}
              </Dropdown> */}

              <SelectPicker
                // styles={{'backgroudColor': 'black'}}
                value={selectedSevirityPnr}
                data={selectedSeverityOption}
                label='Severity Type '
                onChange={(newValue) => handleOptionSelect(newValue)}
                className={styles.dropdownStyles}
                searchable={false}
                appearance="subtle" 
              />
              <DateRangePicker
                className={styles.datePicker}
                isoWeek
                disabledDate={afterToday()}
                value={dateRangeValue || getCurrentMonthDateRange()}
                onChange={(newvaluedate) => handleDateRangeSelect(newvaluedate)}
                onClick={handleClearDateRange}
                cleanable={false}
                appearance="subtle"
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
              
                // style={{ width: 200 }}
                format="dd-MM-yyyy"
              />

              <SelectPicker
                value={selectedSeverity}
                data={selectedDateOptions}
                label='Filter By '
                searchable={false}
                className={styles.severitySelectPicker}
                onChange={(newValue) => handleSelectSeverity(newValue)}
                appearance="subtle" 
              />

            <InputGroup className={styles.Inputouter}>
              <InputGroup.Addon className={styles.textColor}>
                PNR : 
              </InputGroup.Addon>
              <Input
                className={styles.inputsearch}
                placeholder="Search PNR No."
                // appearance="subtle" 
                value={searchPnrNumber}
                onChange={(value) => setSearchPnrNumber(value)}
              />
              {/* <InputGroup.Addon >
                <SearchIcon  />
              </InputGroup.Addon> */}
            </InputGroup>
            </div>

            <div className={styles.filterTwo}>
              <Button
                appearance="primary"
                onClick={handleSearch}
                value={searchPnrNumber}
                className={styles.searchBtn}
              >
                Search
              </Button>
              {allowed_action?.download && (
              <Button
                className={styles.exportBtn}
                appearance="primary"
                onClick={() => downloadReport()}
                disabled={dateRangeValue == null && searchPnrNumber == "" ? true : false}
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
                  <th>PNR</th>
                  <th>Booking Date</th>
                  <th>Journey Date</th>
                  <th>RFI RULE</th>
                  <th>USER SEVERITY</th>
                  <th>PNR Details</th>
                </tr>
              </thead>
              <tbody>
                {tableData?.map((item, index) => (
                  <tr key={index}>
                    <td>{item?.USERNAME}</td>
                    <td>{item?.PNR_NUMBER}</td>

                    <td>
                      {item?.BOOKING_DATE != undefined &&
                      item?.BOOKING_DATE != "N.A."
                        ? new Date(item?.BOOKING_DATE.$date).toDateString()
                        : "N.A."}
                    </td>
                    <td>
                      {item?.JOURNEY_DATE != undefined &&
                      item?.JOURNEY_DATE != "N.A."
                        ? new Date(item?.JOURNEY_DATE.$date).toDateString()
                        : "N.A."}
                    </td>
                    {/* <td className={styles.rfiStyles}>{item?.TAGS.join(",")}</td> */}
                    <td className={styles.rfiStyles}>
                        {item?.TAGS != [] ? (
                          <span>
                            <Whisper
                              placement="left"
                              followCursor
                              speaker={
                                <Popover >
                                  {item?.TAGS?.map((x) => {
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
                              <span className={styles.rfiStyles}> {item?.TAGS?.join(", ")} </span>
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
                    <td>{item?.Severity}</td>

                    <td>
                      <Button
                        appearance="primary"
                        color="blue"
                        className={styles.userBtn}
                        onClick={() => {
                          setModalPnrNumber(item?.PNR_NUMBER);
                          openModal(item?.PNR_NUMBER);
                        }}
                      >
                        {" "}
                        PNR Details
                      </Button>
                    </td>
                  </tr>
                ))}
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

  const handleOptionSelect = (Option) => {
    setSelectedSevirityPnr(Option);
  };

  function getCurrentMonthDateRange() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    return [firstDayOfMonth, lastDayOfMonth];
  }

  const handleDateRangeSelect = (newvaluedate) => {
    setDateRangeValue([]);
    setDateRangeValue(newvaluedate);
  };
  const errorText = "Please Provide a valid DateRange"

  useEffect(() => {
    setTableData([]);
    setOpenHistoryModal(false)
    mainTableData(1);
  }, []);

  return (
    <>
      {/* PNR Details Modal */}
      {allowed_action?.view && (
        <Modal open={openHistoryModal} onClose={() => closeModal()} size="xs" className={styles.modalStyle}  backdrop='static'>
        <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          <Modal.Body>
            <div className={styles.vertical_table_container}>
              <h3>PNR Details</h3>
              <table className={styles.vertical_table}>
                <thead>
                  {/* <tr>
                    <th className={styles.table_header}>USER</th>
                    <th className={styles.table_header}>DATA</th>
                  </tr> */}
                </thead>
                {modalTabledata?.length > 0 ? (
                  modalTabledata?.map((data) => (
                    <tbody>
                      <tr>
                        <td className={styles.table_cell}>User Name</td>
                        <td className={styles.table_cell1}>{data?.USERNAME}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>PNR Number</td>
                        <td className={styles.table_cell1}>{data?.PNR_NUMBER}</td>
                      </tr>
                      
                      <tr>
                        <td className={styles.table_cell}>Booking Date</td>
                        {/* <td className={styles.table_cell}>{data?.REGISTRATION_DATETIME}</td> */}
                        <td className={styles.table_cell1}> 
                        {data?.BOOKING_DATE != undefined && data?.BOOKING_DATE != "N.A."
                            ? new Date(data?.BOOKING_DATE.$date).toDateString()
                            : "N.A."}</td>
                      </tr>
                    
                      <tr>
                        <td className={styles.table_cell}>Journey Date</td>
                        {/* <td className={styles.table_cell}>{data?.REGISTRATION_DATETIME}</td> */}
                        <td className={styles.table_cell1}> 
                        {data?.JOURNEY_DATE != undefined && data?.JOURNEY_DATE != "N.A."
                            ? new Date(data?.JOURNEY_DATE.$date).toDateString()
                            : "N.A."}</td>
                      </tr>

                      <tr>
                        <td className={styles.table_cell}>Booking From</td>
                        <td className={styles.table_cell1}>{data?.FROM}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Journey To</td>
                        <td className={styles.table_cell1}>{data?.TO}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Train Number</td>
                        <td className={styles.table_cell1}>{data?.TRAIN_NUMBER}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Ticket Type</td>
                        <td className={styles.table_cell1}>{data?.TK_TYPE}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Ticket Class</td>
                        <td className={styles.table_cell1}>{data?.CLASS}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>Booking Mobile</td>
                        <td className={styles.table_cell1}>{data?.BOOKING_MOBILE}</td>
                      </tr>
                      <tr>
                        <td className={styles.table_cell}>IP Address</td>
                        <td className={styles.table_cell1}>{data?.IP_ADDRESS}</td>
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
      {allowed_page?.casemanagement_pnr && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            {" "}
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board heading="PNR Case Management " router={Router} />
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
