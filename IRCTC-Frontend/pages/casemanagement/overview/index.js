import React, { useEffect, useState, useRef } from "react";
import styles from "./case_overview.module.scss";
import Sidebar from "@/components/Sidebar";
import Board from "@/components/Board";
import Router, { useRouter } from "next/router";
import { useSelector, useDispatch } from "react-redux";

import { Circles } from "react-loader-spinner";
import CloseIcon from "@rsuite/icons/Close";
import CheckIcon from "@rsuite/icons/Check";
import { Loader } from "rsuite";

const { afterToday } = DateRangePicker;
const { Column, HeaderCell, Cell } = Table;

// Chart Components
import Piechart from "./pichart";
import Barchart from "./barchart";

import {
  Button,
  ButtonToolbar,
  DateRangePicker,
  Modal,
  Pagination,
  Table,
  IconButton,
  SelectPicker,
  Tooltip,
} from "rsuite";

import { toast } from "react-toastify";
import { Whisper, Popover } from "rsuite";

const selectStatus = ["Accepted", "Rejected"].map((item) => ({
  label: item,
  value: item,
}));

const CaseManagment = () => {
  // Initialize the router to get the routing info of the page
  const router = useRouter();

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_action = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  //   console.log(`Allowed Pages `, allowed_page);
  //   console.log(`Allowed Actions `, allowed_action);

  useEffect(() => {
    if (!allowed_page?.casemanagement_overview) {
      router.push("/overview");
    }
  }, []);

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

  // Main Table States.
  const [isLoading, setIsLoading] = useState(false);
  const [mainPageTotalRows, setMainPageTotalRows] = useState(0);
  const [mainPageTotalPages, setMainPageTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [mainPageLoading, setMainPageLoading] = useState(false);
  const [tableData, setTableData] = useState([]);

  // Modal History states and function start
  const [openHistoryModal, setOpenHistoryModal] = useState(false);
  const [modalLoad, setModalLoad] = useState(false);
  const [modalTabledata, setModalTabledata] = useState([]);
  const [detailModalTotalPages, setDetailModalTotalPages] = useState(0);
  const [detailModalTotalRows, setDetailModalTotalRows] = useState(0);
  const [modalCurrentPage, setModalCurrentPage] = useState(1);
  const [modalCaseNumber, setModalCaseNumber] = useState(0);
  const [modalMessage, setModalMessage] = useState("");

  const [modalUserName, setModalUserName] = useState("");
  const [acceptButtonText, setAcceptButtonText] = useState("Accept");
  const [rejectButtonText, setRejectButtonText] = useState("Reject");
  const [modalStates, setModalStates] = useState({});
  const [modalIdentifier, setModalIdentifier] = useState(null);

  const [usernameStatus, setUsernameStatus] = useState({});
  const [modalStatus, setModalStatus] = useState({});
  const [modalIpAddress, setModalIpAddress] = useState("");

  const [item, setItem] = useState(null);
  const [acceptStatus, setAcceptStatus] = useState(null);

  const [isAccepting, setIsAccepting] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isComponentMounted, setIsComponentMounted] = useState(false);

  const mainTableData = async (pageValue) => {
    setMainPageLoading(true);
    try {
      const response = await fetch("/api/overview-main", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageValue,
        }),
        timeout: 5 * 60 * 1000, // timer Set for 5 min
      });

      const data = await response.json();
      // Parse each string item in data_list into an object
      const parsedDataList = data?.data_list?.map((item) => JSON.parse(item));

      setTableData(parsedDataList);
      setMainPageTotalRows(data?.total_rows);
      setMainPageTotalPages(data?.total_pages);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setMainPageLoading(false);
    }
  };

  const handlePageChange = (pageValue) => {
    setTableData([]);
    setCurrentPage(pageValue);
    mainTableData(pageValue);
  };

  const detailPnrModalData = async (usernameValue, pageId) => {
    setModalLoad(true);
    try {
      const response = await fetch("/api/case_overview_detail", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageId,
          username: usernameValue,
          // ip_address: modalIpAddress,
        }),
      });

      const data = await response.json();

      if (data.data_list && data.data_list.length > 0) {
        // PNR data exists
        const modalData = data.data_list.map((item) => JSON.parse(item));
        setModalTabledata(modalData);
        setDetailModalTotalRows(data?.total_rows);
        setDetailModalTotalPages(data?.total_pages);
        setModalMessage("");
      } else {
        setModalTabledata([]);
        setModalMessage("PNR Data Does Not Exists for This User");
      }
    } catch (error) {
      throw error;
    } finally {
      setModalLoad(false);
    }
  };

  const formatGeoLocation = (coordinates) => {
    if (coordinates && coordinates.length === 2) {
      const [latitude, longitude] = coordinates;
      return `${latitude}, ${longitude}`;
    } else {
      return "N.A.";
    }
  };

  const downloadModalData = async (ipAddress) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/overview_case_detail_export", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: modalUserName,
      }),
    }).then(async (response) => {
      setIsLoading(false);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `case_overview_${modalUserName}.csv`;
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
  };

  const calculateCaseNumber = (index) => (currentPage - 1) * 10 + index + 1;
  const getSeverityColor = (severity) => {
    switch (severity) {
      case "HIGH":
        return "red";
      case "MEDIUM":
        return "limegreen";
      case "LOW":
        return "#ffc107";
      default:
        return "inherit"; // or any default color
    }
  };

  const renderTable = () => {
    return (
      <div>
        {/* Main Page Container*/}
        <div className={styles.main_container}>
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
                  <th>Cases</th>
                  <th>Username</th>
                  <th>pnr</th>
                  <th>Suspected Date</th>
                  <th>IP</th>
                  <th>RFI RULE</th>
                  <th>Severity</th>
                  <th>View Details</th>
                </tr>
              </thead>
              <tbody>
                {tableData?.map((item, index) => (
                  <tr key={index}>
                    <td>{`Case ${calculateCaseNumber(index)}`}</td>
                    <td>{item?.USERNAME}</td>

                    <td
                      className={styles.mainPnrColumn}
                      data-tooltip={
                        item?.PNR_NUMBER === "N.A."
                          ? "Data is Not Available for this User"
                          : ""
                      }
                    >
                      {item?.PNR_NUMBER}
                    </td>
                    <td>
                      {item?.SUS_DATE != undefined && item?.SUS_DATE != "N.A."
                        ? new Date(item?.SUS_DATE.$date).toDateString()
                        : "N.A."}
                    </td>
                    <td>{item?.IP_ADDRESS}</td>
                    <td className={styles.rfiStyles}>
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
                            <span> {item?.RFI_RULE?.join(",") || "N.A."} </span>
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
                    <td
                      style={{ color: getSeverityColor(item?.SEVERITY) }}
                      className={styles.severityRow}
                    >
                      {item?.SEVERITY}
                    </td>

                    <td>
                      <Button
                        appearance="primary"
                        color="blue"
                        className={styles.userBtn}
                        onClick={() => {
                          openModal(
                            item,
                            index,
                            item?.USERNAME,
                            item?.ACCEPT_STATUS
                          );
                        }}
                      >
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className={styles.mainPagination}>
          <Pagination
            prev
            next
            first
            last
            ellipsis
            boundaryLinks
            maxButtons={5}
            size="xs"
            limit={10}
            layout={["total", "-", "|", "pager", "skip"]}
            pages={mainPageTotalPages}
            total={mainPageTotalRows}
            activePage={currentPage}
            onChangePage={handlePageChange}
          />
        </div>
      </div>
    );
  };

  const isModalOpen = useRef(false);

  const openModal = (item, index, usernameValue, pageId) => {
    if (isModalOpen.current) {
      return;
    }

    isModalOpen.current = true;

    setOpenHistoryModal(true);
    setModalCurrentPage(1);
    setModalTabledata([]);
    setModalCaseNumber(calculateCaseNumber(index));
    setModalIdentifier(index);
    setUsernameStatus((prevStatus) => ({
      ...prevStatus,
      [index]: prevStatus[index] || { accepted: false, rejected: false },
    }));
    setItem(item);
    setAcceptStatus(item?.ACCEPT_STATUS);
    setModalUserName(usernameValue);
    detailPnrModalData(usernameValue, 1);
    isModalOpen.current = false;
  };

  const closeModal = () => {
    // Close the modal.
    setOpenHistoryModal(false);
    // Reset the state for the current modal
    setModalStates((prevStates) => ({
      ...prevStates,
      [modalIdentifier]: {
        accepted: false,
        rejected: false,
      },
    }));

    setModalUserName("");
    // Reset isModalOpen ref
    isModalOpen.current = false;
  };

  const handlePageChangeModal = async (page) => {
    // Update the modalCurrentPage state
    setModalCurrentPage(page);
    detailPnrModalData(modalUserName, page);
  };

  useEffect(() => {
    // Ensure 'item' is defined and then update acceptStatus
    if (item && typeof item?.ACCEPT_STATUS !== "undefined") {
      setAcceptStatus(item?.ACCEPT_STATUS);
      updateButtonText(item?.ACCEPT_STATUS);
    }
  }, [item?.ACCEPT_STATUS, item]);

  const updateButtonText = (acceptStatus) => {
    if (acceptStatus === 1) {
      console.log("acceptStatus", acceptStatus);
      setAcceptButtonText((prevText) => {
        if (prevText !== "Accepted") {
          return "Accepted";
        }
        return prevText;
      });
      setRejectButtonText("Reject"); // Reset Reject button text
    } else if (acceptStatus === 0) {
      setRejectButtonText((prevText) => {
        if (prevText !== "Rejected") {
          return "Rejected";
        }
        return prevText;
      });
      setAcceptButtonText("Accept"); // Reset Accept button text
    } else {
      // Handle null case, reset both buttons to their initial state
      setAcceptButtonText("Accept");
      setRejectButtonText("Reject");
    }
  };

  const handleAccept = async () => {
    if (!modalUserName) {
      // Handle the case where modalUserName is not set
      return;
    }

    try {
      // Make an API call to update modal status
      const response = await fetch("/api/overview-status-update", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: modalUserName,
          status: 1, // 1 for Accepted, 0 for Rejected
        }),
      });

      const res_data = await response.json();
      setAcceptStatus(1);
      updateButtonText(1);

      // Show a toast message
      toast.success(res_data?.msg);
    } catch (error) {
      console.error("Error accepting:", error);
    } finally {
      setTimeout(function () {
        Router.reload();
      }, 5000);
      setIsAccepting(false);
    }
  };

  const handleReject = async () => {
    if (!modalUserName) {
      return;
    }

    try {
      // Make an API call to update modal status
      const response = await fetch("/api/overview-status-update", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: modalUserName,
          status: 0, // 1 for Accepted, 0 for Rejected
        }),
      });

      const res_data = await response.json();
      setAcceptStatus(0);
      updateButtonText(0);

      // Show a toast message
      toast.error(res_data?.msg);
    } catch (error) {
      console.error("Error rejecting:", error);
    } finally {
      setTimeout(function () {
        Router.reload();
      }, 5000);
      setIsRejecting(false);
    }
  };

  useEffect(() => {
    setIsComponentMounted(true);

    // Cleanup function to run when the component unmounts
    return () => {
      setIsComponentMounted(false);
      setOpenHistoryModal(false);
      setModalStates((prevStates) => ({
        ...prevStates,
        [modalIdentifier]: {
          accepted: false,
          rejected: false,
        },
      }));
      setModalUserName("");
    };
  }, []);

  useEffect(() => {
    if (isComponentMounted && openHistoryModal) {
      // detailPnrModalData(modalUserName, modalCurrentPage);
    }
  }, [isComponentMounted, openHistoryModal, modalUserName, modalCurrentPage]);

  useEffect(() => {
    mainTableData(currentPage);
  }, []);

  return (
    <>
      {/* MAIN Table */}
      {allowed_page?.casemanagement_pnr && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board heading="Overview Case Management" router={Router} />

            {/* Chart Components */}
            <div className={styles.main_container}>
              <div className={styles.main_child_container}>
                {/* Pie Chart Container */}
                <div className={styles.main_child_left}>
                  <Piechart />
                </div>

                {/* Linebar Chart Container */}
                <div className={styles.main_child_right}>
                  <Barchart />
                </div>
              </div>
            </div>

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

      {allowed_action?.view && (
        <Modal
          open={openHistoryModal}
          onClose={() => closeModal()}
          size="lg"
          backdrop="static"
          className={styles.mainModalStyling}
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <div className={styles.modalHeader}>
            <div className={styles.headerText}>
              <span>Case {modalCaseNumber}:</span>
              <span>{modalUserName}</span>
            </div>
          </div>
          <Modal.Body>
            <ButtonToolbar>
              <Button
                appearance="primary"
                className={`${styles.AcceptBtn} ${
                  usernameStatus[modalIdentifier]?.accepted
                    ? styles.disabledBtn
                    : ""
                }`}
                onClick={() => handleAccept()}
              >
                <IconButton
                  icon={<CheckIcon />}
                  color="green"
                  appearance="primary"
                  size="xs"
                  circle
                  className={styles.checkIconStyles}
                />
                {acceptStatus === 1 ? "Accepted" : "Accept"}
              </Button>
              <Button
                color="red"
                appearance="primary"
                startIcon={<CloseIcon />}
                className={`${styles.rejectBtn} ${
                  usernameStatus[modalIdentifier]?.rejected
                    ? styles.disabledBtn
                    : ""
                }`}
                onClick={() => handleReject()}
              >
                <IconButton
                  icon={<CloseIcon />}
                  color="red"
                  appearance="primary"
                  size="xs"
                  circle
                  className={styles.checkIconStyles}
                />
                {acceptStatus === 0 ? "Rejected" : "Reject"}
              </Button>
            </ButtonToolbar>
            {/* {modalMessage ? (
            <div className={styles.modalMessage}>{modalMessage}</div>
          ) : ( */}
            <div className={styles.modalStyles}>
              <div className={styles.modalTable}>
                <div className={styles.modalTable}>
                  {modalLoad ? (
                    <Loader backdrop content="Loading..." vertical />
                  ) : (
                    <table
                      className={styles.modal_data_table}
                      loading={modalLoad}
                    >
                      <thead>
                        <tr>
                          <th>User Name</th>
                          <th>Email</th>
                          <th>IP Address</th>
                          <th>Registered Mobile</th>
                          <th>Registered Date</th>
                          <th>Location</th>
                          <th>Geo Location</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modalTabledata?.map((rowData, index) => (
                          <tr key={index}>
                            <td>{rowData?.USERNAME || "N.A."}</td>
                            <td>{rowData?.EMAIL || "N.A."}</td>
                            <td>{rowData?.IP_ADDRESS || "N.A."}</td>
                            <td>{rowData?.REGISTERED_MOBILE || "N.A."}</td>

                            <td>
                              {rowData?.REGISTRATION_DATETIME != undefined
                                ? new Date(
                                    rowData?.REGISTRATION_DATETIME.$date
                                  ).toDateString()
                                : "N.A."}
                            </td>
                            <td>
                              <div
                                className={`${styles.Modaltooltip} ${styles.defaultStyle}`}
                                data-content={rowData?.Location || "N.A."}
                                data-column="Location"
                              >
                                {rowData?.Location || "N.A."}
                              </div>
                            </td>
                            <td>
                              <div
                                className={`${styles.Modaltooltip} ${styles.defaultStyle}`}
                                data-content={formatGeoLocation(
                                  rowData?.Geolocation || "N.A."
                                )}
                                data-column="GeoLocation"
                              >
                                {formatGeoLocation(
                                  rowData?.Geolocation || "N.A."
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>

            {/* )} */}
          </Modal.Body>
          <Modal.Footer>
            <div className={styles.pagination}>
              {modalLoad ? (
                <div></div>
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
                  limit={10}
                  layout={["total", "-", "|", "pager", "skip"]}
                  pages={detailModalTotalPages}
                  total={detailModalTotalRows}
                  activePage={modalCurrentPage}
                  // onChangePage={(page) =>
                  //   handlePageChangeModal(modalUserName,page)
                  // }
                  onChangePage={handlePageChangeModal}
                />
              )}
            </div>
            {allowed_action?.download && (
              <Button
                className={styles.exportBtn}
                appearance="primary"
                onClick={() => downloadModalData()}
              >
                Export
              </Button>
            )}
            <Button
              onClick={() => closeModal()}
              appearance="ghost"
              className={styles.closeBtn}
            >
              Close
            </Button>
          </Modal.Footer>
        </Modal>
      )}
    </>
  );
};

export default CaseManagment;
