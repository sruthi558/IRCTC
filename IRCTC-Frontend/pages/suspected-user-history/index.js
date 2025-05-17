import React from 'react'
// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import Router, { useRouter } from "next/router";
import { useDispatch, useSelector } from 'react-redux'

import { useEffect, useState } from "react";
import { Circles } from "react-loader-spinner";
import { toast } from "react-toastify";
import { Input, InputGroup } from "rsuite";
const { Column, HeaderCell, Cell } = Table;

const { afterToday } = DateRangePicker;
import {
  Button,
  DateRangePicker,
  Dropdown,
  Modal,
  Pagination,
  Table,
} from "rsuite";
// Import Styles
import styles from "./suspected-users.module.scss";

const SusUserHistory = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.suspected_user_history) {
      router.push('/overview')
    }
  }, [])
  
  // const router = useRouter()
  const [isLoading, setIsLoading] = useState(false);
  const [searchDateValue, setSearchDateValue] = useState();
  const [query, setQuery] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  // const [modalPage, setModalPage] = useState(1);
  const [openHistoryModal, setOpenHistoryModal] = useState(false);
  const [modalLoad, setModalLoad] = useState(false);
  const [viewHistoryData, setViewHistoryData] = useState([]);
  const [viewHistoryModalTotalRows, setViewHistoryTotalRows] = useState(0);
  const [viewHistoryModalTotalPages, setViewHistoryModalTotalPages] = useState(0);
  const [historyModalCurrentPage, setHistoryModalCurrentPage] = useState(1);
  const [ipAddress, setIpAddress] = useState()
  const [modalTabledata, setModalTabledata] = useState([]);
  const [tableData, setTableData] = useState([]);

  const [modalUserName, setModalUserName] = useState('');
  const [modalId, setModalId] = useState('');
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedUsername, setSelectedUsername] = useState('');
  const [searchExportValue, setSearchExportValue] = useState("");
  const [mainPageLoading, setMainPageLoading] = useState(false);

  const openModal = (pageId, userId, username) => {
    // Display the modal.
    setOpenHistoryModal(true);
    HistoryModalData(1, pageId, userId, username); 
    setHistoryModalCurrentPage(1)
  };

  // closeModal removes the modal.
  const closeModal = () => {
    // Close the modal.
    setOpenHistoryModal(false);
    resetModal();
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // Perform search using the query state
  };

  const filterTableData = async (pageValue) => {
    // Sets the loading parameter to be 'true' while API calls are being performed to display the loader.
    setMainPageLoading(true);
    try {
      const response = await fetch("/api/fetch-user-history", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageValue,
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
        timeout: 10 * 60 * 1000, // Set for 10 min
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

  const HistoryModalData = async (pageId, modalId, modalUserName) => {
    setModalLoad(true);
    try {
      const response = await fetch("/api/view-user-history", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          "page_id": pageId,
          "userid": modalId,
          "username": modalUserName,
        }),
      });

      const data = await response.json();

      console.log(`log API Data: ${data}`);

      setModalTabledata(data?.data_list?.map((item) => JSON.parse(item)));
      setViewHistoryTotalRows(data?.total_rows); // Set the total rows
      setViewHistoryModalTotalPages(data?.total_pages); // Set the total pages
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setModalLoad(false);

  };

  const handleSearch = () => {
    filterTableData(1);
    setCurrentPage(1)
    setTableData([])
  };

  // handleChange function update the changed search in the search input .
  // Calling the setQuery function that holds the updated search.
  const handleChange = (event) => {
    setQuery(event.target.value);
  };

  const handlePageChange = (page, pageId) => {
    setTableData([]);
    setCurrentPage(page); // Update the current page state
    filterTableData(page);
  };
  
  const downloadReport = async (pageValue) => {
    setIsLoading(true);
    fetch("/api/download-user-history", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_id: pageValue,
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
    })
      .then(async (response) => {
        setIsLoading(false);
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          // a.download = `User_History_${new Date().toDateString().replaceAll(" ", "_")}+_.xlsx`;
          a.download = `User_History_from_${searchDateValue[0].toDateString().replaceAll(' ', '_')}_to_${searchDateValue[1].toDateString().replaceAll(' ', '_')}.csv`
          a.click();
          toast.success("File Download successfully");
        } else {
          toast.error("File download failed");
        }
      });
    setIsLoading(true);
  };

  const downloadModalReport = async (pageNumber) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/download-user-modal", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_id: pageNumber,
        userid: modalId,
        username: modalUserName,
      })

    }).then(async (response) => {
      setIsLoading(false);
      setOpenHistoryModal(false)
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        // a.download =
        //   "Suspicious_IP_" +
        //   new Date().toDateString().replaceAll(" ", "_") +
        //   "_.xlsx";
        a.download = `Suspicious_IP_UserName_${modalUserName}.csv`
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
  };

  const handlePageChangeModal = (pageId, modalId, modalUserName) => {
    setModalTabledata([]);
    setHistoryModalCurrentPage(pageId, modalId, modalUserName);
    HistoryModalData(pageId, modalId, modalUserName);
  };

  useEffect(() => {
    filterTableData(1)
  }, []);

  const resetModal = () => {
    setModalId(null);
    setModalUserName(null)
    setModalTabledata([])
  };

  function containsNAInAddress(address) {
    const parts = [
      address.ADDRESS,
      address.STREET,
      address.COLONY,
      address.DISTRICT,
      address.STATE,
      address.PIN_CODE
    ];
    return parts.some(part => typeof part  === 'string' && part.trim().toLowerCase() === "n.a.");
  }

  function isValidDate(dateString) {
    const date = new Date(dateString);
    return !isNaN(date) && dateString.trim() !== "";
  }

  const renderTable = () => {
    return (
      <div>
        {/* Main Page Container*/}
        <div className={styles.main_container}>
          {/* Search Input Bar */}
          <div className={styles.headFilters}>
            <div className={styles.filterOne}>
              <Input
                placeholder="Search by Username"
                Name="text"
                onChange={(value, e) => setInputValue(value)}
                className={styles.searchBar}
              />
              <DateRangePicker
                className={styles.datePicker}
                isoWeek
                disabledDate={afterToday()}
                value={searchDateValue}
                onChange={(newvaluedate) => setSearchDateValue(newvaluedate)}
                // style={{ width: 200 }}
                format="dd-MM-yyyy"
              />
            </div>

            <div className={styles.filterTwo}>
              <Button
                appearance="primary"
                onClick={handleSearch}
                value={inputValue}
                onChange={handleChange}
                className={styles.searchBtn}
              > 
                Search
              </Button>
              {allowed_actions?.download && (
                <Button
                  className={styles.exportBtn}
                  appearance="primary"
                  onClick={() => downloadReport(1)}
                  disabled={searchDateValue == null && inputValue == "" ? true : false}
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
                  <th>User ID</th>
                  <th>Username</th>
                  <th>Full Name</th>
                  <th>Reg. Date</th>
                  <th>Reg. Email</th>
                  <th>Reg. Phone</th>
                  <th>Reg. IP</th>
                  <th>Reg. Address</th>
                  <th>Suspected Date</th>
                  <th>Suspected Codes</th>
                  <th>Total Booked Tickets</th>
                  {allowed_actions?.view && (
                    <th>History</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {tableData?.map((item) => (
                  <tr>
                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.USER_ID ? styles.redBackground : '' }>
                          {(item?.USER_ID) ? item?.USER_ID : "N.A."}
                        </span>
                      }
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.REG_USERNAME ? styles.redBackground : '' }>
                          {(item?.REG_USERNAME) ? item?.REG_USERNAME : "N.A."}
                        </span>
                      }
                    </td>

                    <td className={styles.tables_fName_col}>
                      {
                        <span
                          className={item?.SUSPECTED_STATUS.REG_FULLNAME ? styles.redBackground : ''}
                        > {(item?.REG_FULLNAME) ? item?.REG_FULLNAME : "N.A."}
                        </span>
                      }
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.REGISTRATION_DATETIME ? styles.redBackground : '' }>
                          {(item?.REGISTRATION_DATETIME != undefined && item?.REGISTRATION_DATETIME != "N.A.")
                          ? new Date(item?.REGISTRATION_DATETIME.$date).toDateString()
                          : "N.A."}
                        </span>
                      }
                    </td>

                    <td className={styles.tables_fName_col}>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.REG_EMAIL ? styles.redBackground : '' }>
                          {(item.REG_EMAIL) ? item?.REG_EMAIL : 'N.A.'}
                        </span>
                      }
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.REG_PHONE ? styles.redBackground : '' }>
                          {(item?.REG_PHONE) ? item?.REG_PHONE : "N.A."}
                        </span>
                      }
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.REG_IP_ADDRESS ? styles.redBackground : '' }>
                          {(item?.REG_IP_ADDRESS) ? item?.REG_IP_ADDRESS : "N.A."}
                        </span>
                      }
                    </td>

                    <td className={styles.tables_add_col}>
                      <span className={item?.SUSPECTED_STATUS.REG_ADDRESS ? styles.redBackground : ""}>
                        {containsNAInAddress(item?.REG_ADDRESS) ? "N.A." : `${item?.REG_ADDRESS?.ADDRESS}, ${item?.REG_ADDRESS?.STREET}, ${item?.REG_ADDRESS?.COLONY}, ${item?.REG_ADDRESS?.DISTRICT}, ${item?.REG_ADDRESS?.STATE} - ${item?.REG_ADDRESS?.PIN_CODE}`}
                      </span>
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS?.SUSPECTED_DATE ? styles.redBackground : '' }>
                          {(item?.SUSPECTED_DATE != undefined && item?.SUSPECTED_DATE != "N.A.")
                            ? new Date(item?.SUSPECTED_DATE.$date).toDateString()
                            : "N.A."}
                        </span>
                      }
                    </td>

                    <td>
                      {
                        <span
                          className={ item?.SUSPECTED_STATUS.SUSPECTED_CODES ? styles.redBackground : '' }>
                          {(item?.SUSPECTED_CODES) ? item?.SUSPECTED_CODES:"N.A"}
                        </span>
                      }
                    </td>
                    <td>
                      {(item?.TOTAL_BOOKED_TICKETS) ? item?.TOTAL_BOOKED_TICKETS : 0}
                    </td>
                    {allowed_actions?.view && (
                      <td>
                        <Button
                          appearance="primary"
                          color="blue"
                          className={styles.userBtn}
                          onClick={() => {
                            setModalId(item?.USER_ID);
                            setModalUserName(item?.REG_USERNAME);
                            openModal(item?.USER_ID, item?.REG_USERNAME);
                          }}
                        > PNR History
                        </Button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

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
            layout={["total", "-", "|", "pager", "skip"]}
            pages={totalPages}    // displayed tottal pages on the right side.
            total={totalRows}    // displayed total rows on the left side.
            activePage={currentPage}
            onChangePage={handlePageChange}
          />
        </div>
      </div>
    );
  };

  return (
    <>
      {(allowed_page?.suspected_user_history && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}> 
            <Sidebar /> 
          </div>
          <div className={styles.page}>
            <Board heading="Suspected User History" router={Router} />
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
            <Modal open={openHistoryModal} onClose={() => closeModal()} size="full">
              <Modal.Header as="h1">
                <Modal.Title as="h1">User PNR History</Modal.Title>
              </Modal.Header>
              <Modal.Body>
                {modalLoad && (
                  <div className={styles.modal_loader_container}>
                    <div className={styles.modal_loader} />
                  </div>
                )}
                {/* <div className={styles.modalStyles}> */}
                <Table
                  data={modalTabledata}
                  height={520}
                  className={styles.modal}
                >
                  <Column fullText  minWidth={120} flexGrow={1.1} >
                    <HeaderCell className={styles.modalHeader}>User ID</HeaderCell>
                    <Cell dataKey="USER_ID" />
                  </Column>

                  <Column fullText  minWidth={140} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}>Username</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                          dataKey?.PNR_SUSPECTED_STATUS?.USERNAME
                            ? styles.specialUserClass
                            : ''
                        }
                      >
                        {dataKey?.USERNAME}
                      </span>
                    )}
                    </Cell>
                  </Column>

                  <Column fullText minWidth={140} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}> Booking Mobile</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                          dataKey?.PNR_SUSPECTED_STATUS?.BOOKING_MOBILE
                            ? styles.specialUserClass
                            : ''
                        }
                      >
                        {dataKey?.BOOKING_MOBILE}
                      </span>
                    )}

                    </Cell>
                  </Column>

                  <Column fullText  minWidth={130} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}>Booking IP</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                          dataKey?.PNR_SUSPECTED_STATUS?.IP_ADDRESS
                            ? styles.specialUserClass
                            : ''
                        }
                      >
                        {dataKey?.IP_ADDRESS}
                      </span>
                    )}
                    </Cell>
                  </Column>

                  <Column fullText  minWidth={120} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}>Booked PNR</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                          dataKey?.PNR_SUSPECTED_STATUS?.PNR_NUMBER ? styles.specialUserClass : ''
                        }
                      >
                        {dataKey?.PNR_NUMBER}
                      </span>
                    )}
                    </Cell>
                  </Column>
                  <Column fullText  minWidth={120} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}>Booked From</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                          dataKey?.PNR_SUSPECTED_STATUS?.FROM ? styles.specialUserClass : ''
                        }
                      >
                        {dataKey?.FROM}
                      </span>
                    )}
                    </Cell>
                  </Column>
                  <Column fullText  minWidth={120} flexGrow={0.8}>
                    <HeaderCell className={styles.modalHeader}>Booked To</HeaderCell>
                    <Cell>{(dataKey) => (
                      <span
                        className={
                        dataKey?.PNR_SUSPECTED_STATUS?.TO ? styles.specialUserClass : ''
                        }
                      >
                        {dataKey?.TO}
                      </span>
                    )}
                    </Cell>
                  </Column>
                  <Column fullText  minWidth={100} flexGrow={0.8}>
                    <HeaderCell className={styles.modalHeader}>Ticket Type </HeaderCell>
                    <Cell align='center'>{(dataKey) => (
                      <span
                        className={
                      dataKey?.PNR_SUSPECTED_STATUS?.TK_TYPE ? styles.specialUserClass : ''
                        }
                      >
                        {dataKey?.TK_TYPE}
                      </span>
                    )}
                    </Cell>
                  </Column>
                  <Column fullText  minWidth={140} flexGrow={1}>
                    <HeaderCell className={styles.modalHeader}>Booking Date </HeaderCell>
                    <Cell>
                      {(dataKey) => (
                        <span
                          className={
                            dataKey?.PNR_SUSPECTED_STATUS?.BOOKING_DATE
                              ? styles.specialUserClass
                              : ''
                          }
                        >
                          {(dataKey?.BOOKING_DATE != undefined && dataKey?.BOOKING_DATE != "N.A.")
                            ? new Date(dataKey?.BOOKING_DATE.$date).toDateString()
                            : "N.A."}
                        </span>
                      )}
                    </Cell>
                  </Column>
                  <Column fullText  minWidth={140} flexGrow={0.6}>
                    <HeaderCell className={styles.modalHeader}>Journey Date </HeaderCell>
                    <Cell >
                      {(dataKey) => (
                        <span
                          className={
                            dataKey?.PNR_SUSPECTED_STATUS?.JOURNEY_DATE
                              ? styles.specialUserClass
                              : ''
                          }
                        >
                          {(dataKey?.JOURNEY_DATE != undefined && dataKey?.JOURNEY_DATE != "N.A.")
                            ? new Date(dataKey?.JOURNEY_DATE.$date).toDateString()
                            : "N.A."}
                        </span>
                      )}
                    </Cell>
                  </Column>

                  <Column fullText  minWidth={120} flexGrow={1.1}>
                    <HeaderCell className={styles.modalHeader}>Suspected Code</HeaderCell>
                    <Cell align='center' >
                      {(dataKey) => (dataKey?.SUSPECTED_CODES) ? dataKey?.SUSPECTED_CODES.join(', ') : 'N.A.'}
                    </Cell>
                  </Column>
                </Table>

                {/* </div> */}
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
                    layout={["total", "-", "|", "pager", "skip"]} // Updated layout prop
                    pages={viewHistoryModalTotalPages}
                    total={viewHistoryModalTotalRows}
                    activePage={historyModalCurrentPage}
                    onChangePage={(pageId) =>
                      handlePageChangeModal(pageId, modalId, modalUserName)
                    }
                  />
                </div>
              </Modal.Body>
              <Modal.Footer className={styles.modalFooter}>
                {allowed_actions?.download && (
                  <Button
                    appearance="primary"
                    onClick={() => downloadModalReport(1, modalId, modalUserName)}
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
  )
}

export default SusUserHistory;