// endpoint
const endPoint = process.env.API_ENDPOINT;

// Import Libraries
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { useSelector, useDispatch } from "react-redux";

const { afterToday } = DateRangePicker;
const { Column, HeaderCell, Cell } = Table;
import moment from "moment";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";

// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import question from "../../public/static/images/questionmark.svg";
import Router, { useRouter } from "next/router";

import { Circles } from "react-loader-spinner";
import { toast } from "react-toastify";
import { Input, InputGroup, Nav } from "rsuite";
import SearchIcon from "@rsuite/icons/Search";
import CloseIcon from '@rsuite/icons/Close';
// Import Assets

import MoreIcon from "@rsuite/icons/legacy/More";

import { startOfDay, endOfDay, subDays } from "date-fns";

// Import Styles
import styles from "./IpHistory.module.scss";

// A mapping object that maps tag codes to their corresponding descriptions
const tagMapping = {
  USER_REG_BOOK_VPS: "User has registered from this VPS IP Address", //'User has registered from this VPS IP Address',
  REG_MORE_THAN_5: "More than 5 User Registrations from this IP Address", // 'More than 5 User Registrations from this IP Address',
  BOOKING_IP_VPS: "Booked PNR from VPS IP Address", // 'Booked PNR from VPS IP Address',
  TK_MORE_THAN_20_ARP: "More than 20 PNRs booked during ARP", //'More than 20 PNRs booked during ARP',
  TK_MORE_THAN_20_AC: "More than 20 PNRs booked during Tatkal AC", //'More than 20 PNRs booked during Tatkal AC',
  TK_MORE_THAN_20_NON_AC: "More than 20 PNRs booked during Tatkal Non-AC", // 'More than 20 PNRs booked during Tatkal Non-AC',
  USED_BY_SUSPICIOUS_USER: "This IP has been used by a Suspicious User", //'This IP has been used by a Suspicious User',
};

// A function that transforms tag codes into their corresponding descriptions and returns a JSX element.
const codeToTagTransform = (tags) => {
  return (
    <div className={styles.tagBubble}>
      {tags.map((tag) => {
        // For each tag code in the "tags" array, access its corresponding description in the
        return <p>{tagMapping[tag]}</p>;
      })}
    </div>
  );
};

// Import Store
import {
  Button,
  DateRangePicker,
  Dropdown,
  Modal,
  Pagination,
  Table,
} from "rsuite";

// ActionCell: Custom Componen, likely renders a clickable cell in a table
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
  );
};

// The renderMenu function renders a Popover component that contains a Dropdown.Menu component,
const renderMenu = ({ onClose, left, top, className }, ref) => {
  const handleSelect = (eventKey) => {
    onClose();
    console.log(eventKey);
  };
  return (
    // The if...else if... statements inside handleSelect likely determine what action to take
    <Popover ref={ref} className={className} style={{ left, top }} full>
      <Dropdown.Menu onSelect={handleSelect}>
        <Dropdown.Item eventKey={1}>Block</Dropdown.Item>
        <Dropdown.Item eventKey={2}>Ignore</Dropdown.Item>
      </Dropdown.Menu>
    </Popover>
  );
};

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
);

// Dashboard Component
const SusUsers = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.ip_history) {
      router.push('/overview')
    }
  }, [])

  // Initialise the dispatcher.
  const dispatch = useDispatch();
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false);
  // This state variable determines the number of items to display per page.
  const [limit, setLimit] = useState(20);
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1);

  // State variables for tracking the count of suspicious IP addresses and non-IP addresses.
  const [susIPCount, setSusIPCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [modalPage, setModalPage] = useState(1); // Current page number for VPS list pagination
  // State variables for storing search dates for VPS and non-VPS lists
  const [searchDateValue, setSearchDateValue] = useState(); // Search date for VPS list
  const [searchNONVPSDate, setSearchNONVPSDate] = useState(); // Search date for non-VPS list

  // State variables for displaying modal data
  const [modalData, setModalData] = useState([]); // Data to display in modal
  const [modalCount, setModalCount] = useState(0); // Count of modal data items
  const [modalLoad, setModalLoad] = useState(false); // Flag to indicate whether modal data is being loaded
  const [query, setQuery] = useState(""); // Query for filtering the data
  const [searchModalDate, setSearchModalDate] = useState();
  const [tableData, setTableData] = useState([]);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [modalDisplayToggle, setModalDisplayToggle] = useState(false);
  // CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: "blue" }} />;
  const [isLoading, setIsLoading] = useState(false);
  const [searchDate, setSearchDate] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [searchVPSDate, setSearchVPSDate] = useState();
  const[ipAddress,setIpAddress]= useState()
  const [viewHistoryData, setViewHistoryData] = useState([]);
  const [viewHistoryIpCount, setViewHistoryIpCount] = useState();
  const [modalCurrentPage, setModalCurrentPage] = useState(1);
  const [modalIpAddress, setModalIpAddress] = useState('');
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [modalDivide, setModalDivide] = useState(10);


  //  View History Modal pagination display total rows and total pages and there states
  const [viewHistoryTotalRows, setViewHistoryTotalRows] = useState(0);
  const [viewHistoryTotalPages, setViewHistoryTotalPages] = useState(0);

  // New Table All States Starts 
  const [mainPageLoading, setMainPageLoading] = useState(false);
  const [currentDataType, setCurrentDataType] = useState('USER');
  const [currentModalPage, setCurrentModalPage] = useState(0)


  const filterTableData = async (pageNumber) => {
    setMainPageLoading(true);
    try {
      const response = await fetch("/api/fetch_ip_history", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageNumber,
          search: inputValue, // Assuming inputValue contains the entered IP address
          starting_date:
            searchDateValue != null && searchDateValue?.length != 0
              ? searchDateValue[0]
              : new Date(0),
          ending_date:
            searchDateValue != null && searchDateValue?.length != 0
              ? searchDateValue[1]
              : new Date(),
        }),
      });

      const data = await response.json();
      setTableData(data?.data_list?.map((item) => JSON.parse(item)));
      setTotalRows(data?.total_rows); // Set the total rows
      setTotalPages(data?.total_pages); // Set the total pages
    } catch (error) {
      console.error("Error fetching data:", error);
    }

    setMainPageLoading(false);
  };

  useEffect(() => {
    filterTableData(1)
  }, []);

  // HandleFileSeach 
  const handleFileSearch = () => {
    searchFile(fileUploadDate);
  };

  const downloadReport = async (pageValue) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/download-ip-history", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        search: inputValue,
        starting_date:
          searchDateValue != null && searchDateValue?.length != 0
            ? searchDateValue[0]
            : new Date(0),
        ending_date:
          searchDateValue != null && searchDateValue?.length != 0
            ? searchDateValue[1]
            : new Date(),
      }),
    }).then(async (response) => {
      setIsLoading(false);

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Suspicious_IP_from_${searchDateValue[0].toDateString().replaceAll(' ', '_')}_to_${searchDateValue[1].toDateString().replaceAll(' ', '_')}.csv`
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
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
        a.download = `Suspicious_IP_${modalIpAddress}.csv`
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
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

  // Handle VPS Search 
  const handleVPSSearch = () => {
    setTableData([]);
    setModalPage(1);
    filterTableData(1);
    setCurrentPage(1)
  };

  // Handle Non VPS Seach 
  const handleNONVPSSearch = () => {
    setPageNON(1);
    paginationFunctionNON(1, searchNONVPSDate);
  };

  const openModal = (ip_add) => {
    setModalLoad(true);
    setModalDisplayToggle(true);
    setModalIpAddress(ip_add);
    setCurrentDataType('USER');
    setCurrentModalPage(0);
    setModalCurrentPage(1);
    HistoryModalData(1, ip_add, 'USER');
  };

  // closeModal removes the modal.
  const closeModal = () => {
    setModalDisplayToggle(false);      
    setCurrentDataType('USER');
  };

  // Function for handling the change event of the dropdown
  function handleOptionChange(event) {
    setSelectedOption(event.target.value);
  }
  // Function for handling the select event of the dropdown
  function handleOptionSelect(option) {
    setSelectedOption(option);
    setCurrentPage(1);
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    // Perform search using the query state
  };

  // handleChange function update the changed search in the search input .
  const handleChange = (event) => {
    setQuery(event.target.value);
  };
  const inputstyles = {
    width: 250,
    // marginBottom: 5,
    marginLeft:10,
  };
  
  const handlePageChange = (page) => {
    setTableData([]);
    setCurrentPage(page);
    filterTableData(page);
  };

  // View History Modal Functions

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
  
  
  const handlePageChangeModal = (ip_address,pageId, page) => {
    setViewHistoryData([]);
    setModalCurrentPage(pageId, ip_address, page); 
    HistoryModalData(pageId, ip_address, page, currentDataType);
  };
  const hasMounted = useRef(false);
  
  useEffect(() => {
    if (hasMounted.current && modalDisplayToggle) {
      HistoryModalData(modalCurrentPage, modalIpAddress, currentDataType);
    } else {
      hasMounted.current = true;
    }
  }, [currentDataType]);

  const renderTable = () => {
    return (
      <>
      {(allowed_page?.ip_history && allowed_actions?.view) && (
      <div className={styles.main_container}>
          {/* VPS Table Start Here  */}
          {/* <div className={styles.dailyrow + " d-flex "}> */}
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
            <div className={styles.mainContainer}>
            <div className={styles.headFilters}>
            <div className={styles.filterOne}>
              <InputGroup style={inputstyles}>
                <Input
                  placeholder="Search IP ...."
                  Name="text"
                  onChange={(value, e) => setInputValue(value)}
                />
                <InputGroup.Addon>
                  <SearchIcon />
                </InputGroup.Addon>
              </InputGroup>

              <DateRangePicker
                isoWeek
                disabledDate={afterToday()}
                value={searchDateValue}
                onChange={(newvaluedate) => setSearchDateValue(newvaluedate)}
                style={{ width: 240 }}
                format="dd-MM-yyyy"
                className={styles.datePickerStyle}
              />
            </div>
            
            <div className={styles.filterTwo}>
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

              <div className="p-2">
              {allowed_actions?.download && (
                <Button
                  className={styles.exportBtn}
                  appearance="primary"
                  onClick={downloadReport}
                  disabled={
                    searchDateValue == null && inputValue == "" ? true : false
                  }
                >
                  Export
                </Button>
              )}
              </div>
            </div>
          </div>
          {/* </div> */}
          <div className={styles.tableContainer}>
          <div className={styles.pnr_data_container}>
                  <table className={styles.data_table}>
                  {mainPageLoading && (
                <div className={styles.loader_container}>
                  <p className={styles.loader_text} />
                  <div className={styles.loader} />
                </div>
              )}
                    <thead className={styles.pnr_tables_head}>
                      <tr>
                        <th>IP Address</th>
                        <th>ISP (Latest)</th>
                        <th>ASN (Latest)</th>
                        <th>VPS</th>
                        <th>IP LOG (Latest)</th>
                        {allowed_actions?.view && (
                          <th>Action</th>
                        )}
                      </tr>
                    </thead>
                   <tbody>
                      {tableData?.map((item)=>(
                        <tr>
                          <td>{item?.IP_ADDRESS}</td>
                          <td className={styles.ispStyle}>{item?.ISP}</td>
                          <td>{item?.ASN}</td>
                          <td>{item?.VPS ? "True" : "False"}</td>
                          <td>
                            {item?.DATE != undefined &&
                            item?.DATE != "N.A."
                            ? new Date(item?.DATE.$date).toDateString()
                            : "N.A."}
                          </td>
                          {allowed_actions?.view && (
                          <td>
                             <Button
                              appearance="primary"
                              onClick={() =>{ openModal(item?.IP_ADDRESS);
                              setIpAddress(item?.IP_ADDRESS);
                              setCurrentDataType('USER')
                              } }
                            >
                              View History
                            </Button>
                          </td>
                        )}
                        </tr>
                      ))}
                   </tbody>
                  </table>
             
                </div>
                <div className={styles.mainTablePagination}>
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
                limit={[20]}
                layout={["total", "-", "|", "pager", "skip"]}
                pages={totalPages}    // displayed tottal pages on the right side.
                total={totalRows}    // displayed total rows on the left side.
                activePage={currentPage}
                onChangePage={handlePageChange}
              />
          )}
            </div>
           </div>
           </div>
          
      </div>
      )}
   </> );
  };

  // Render
  return (
    <>
      {(allowed_page?.ip_history && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          
          <div className={styles.page}>
            <Board heading="Suspected IP Addresses" router={Router} />
            {renderTable()}

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
                    <Table
                      loading={modalLoad}
                      rowHeight={50}
                      autoHeight={3}
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
                        limit={[20]}
                        layout={["total", "-", "|", "pager", "skip"]} // Updated layout prop
                        pages={viewHistoryTotalPages}
                        total={viewHistoryTotalRows}
                        activePage={modalCurrentPage}
                        onChangePage={(page) => handlePageChangeModal(modalIpAddress, page)}
                      />
                    </div>
                {allowed_actions?.download && (
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
          </div>
        </div>
      )}
    </>
  );
};

export default SusUsers;

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res);
}
