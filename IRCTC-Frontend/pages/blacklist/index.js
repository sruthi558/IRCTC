// endpoint
const endPoint = process.env.API_ENDPOINT;

// Import Libraries
import Image from "next/image";
import { useEffect, useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import Router, { useRouter } from "next/router";
import { Table, Pagination, Input, SelectPicker, Popover } from "rsuite";

const { Column, HeaderCell, Cell } = Table;
import { Button, Modal, Uploader, Tooltip, Whisper } from "rsuite";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";
import { Circles } from "react-loader-spinner";
import { toast } from "react-toastify";
import CloseIcon from "@rsuite/icons/Close";

// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";

// Import Assets
import question from "../../public/static/images/questionmark.svg";

import styles from "./blacklist.module.scss";

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement, tooltip }) => (
  //  The Whisper component: displays a popover or tooltip
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
);

const months = [
  { label: "All", value: "All" },
  { label: "January", value: "January" },
  { label: "February", value: "February" },
  { label: "March", value: "March" },
  { label: "April", value: "April" },
  { label: "May", value: "May" },
  { label: "June", value: "June" },
  { label: "July", value: "July" },
  { label: "August", value: "August" },
  { label: "September", value: "September" },
  { label: "October", value: "October" },
  { label: "November", value: "November" },
  { label: "December", value: "December" },
];

// blacklist_page Component
const blacklist_page = () => {
  // Initialize the router to get the routing info of the page
  const router = useRouter();

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_action = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  useEffect(() => {
    if (!allowed_page?.blacklist) {
      router.push("/overview");
    }
  }, []);

  // Initialise the dispatcher.
  const dispatch = useDispatch();

  // Declare a reference to the Upload component for tracking the files in a persistant manner across reloads.
  const uploader = useRef();

  // userRole contains the role of the user currently logged in for role-based restrictions.
  const userRole = useSelector((state) => state.persistedReducer.role);
  const [showNewUser, setShowNewUser] = useState(false); // Create New User Form (state)
  const [fileList, setFileList] = useState([]);

  // CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: "blue" }} />;

  // HandleTakedownModal Closing
  const handleTakeDownModalClose = () => {
    setOpenBlackListModal(false);
  };

  // new  section states
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [selectedMonth, setSelectedMonth] = useState("All");
  const [selectedYear, setSelectedYear] = useState("2024");
  const [monthYear, setMonthYear] = useState("");
  const [years, setYears] = useState([]);

  const [susCurrentPage, setSusCurrentPage] = useState(1);
  const [openBlackListModal, setOpenBlackListModal] = useState(false);
  const [tableLoader, setTableLoader] = useState(false);
  const [ispSearchValue, setIspSearchValue] = useState("");
  const [mainTableData, setMainTabledata] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [viewModalData, setViewModalData] = useState([]);

  const pagiFunc = async (page_value, ispSearchValue, monthYear) => {
    setTableLoader(true);
    if (!monthYear.trim()) {
      console.error("Error:", errorText);
      setTableLoader(false);
      return;
    }
    const data = await fetch("/api/isp_list_all", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_id: page_value,
        search: ispSearchValue,
        month: monthYear,
      }),
    }).then((res) => res.json());

    setMainTabledata(data?.data_list?.map((item) => JSON.parse(item)));
    setTotalRows(data?.total_rows);
    setTotalPages(data?.total_pages);
    setTableLoader(false);
  };

  const downloadBlackISP = (ispSearchValue) => {
    setIsLoading(true);
    fetch("/api/download-black-isp", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        search: ispSearchValue,
        month: monthYear,
      }),
    }).then(async (response) => {
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        const filename = `blacklist_data_${monthYear}_.xlsx`;
        a.href = url;
        a.download = filename;
          a.click();
        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
      setIsLoading(false);
    });
  };

  const summaryModalData = async () => {
    // setModalLoad(true);
    try {
      const response = await fetch("/api/isp_overview", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      const data = await response.json();
      console.log(`log API Data: ${data}`);
      setViewModalData(data?.data_list?.map((item) => JSON.parse(item)));
      // setViewHistoryTotalRows(data?.total_rows); // Set the total rows
      // setViewHistoryModalTotalPages(data?.total_pages); // Set the total pages
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    // setModalLoad(false);
  };

  const downloadFunction = async (ispSearchValue, monthYear) => {
    setIsLoading(true);
    const formattedDate = monthYear.replaceAll(" ", "_");
    const fileName = `${ispSearchValue}_${formattedDate}.xlsx`;
    fetch("/api/isp_subnet_export", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        isp: ispSearchValue,
        month: monthYear,
      }),
    }).then(async (response) => {
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        a.click();
        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
      setIsLoading(false);
    });
  };

  const handleSearchClick = async () => {
    setTableLoader(true);
    if (selectedMonth && selectedYear) {
      const monthYearValue = `${selectedMonth} ${selectedYear}`;
      setMonthYear(monthYearValue);
      await pagiFunc(1, ispSearchValue, monthYearValue);
      setSusCurrentPage(1, ispSearchValue, monthYear);
      setTableLoader(false);
    } else {
      toast.error(errorText);
    }
  };

  // Handle Close Modal
  const closeModal = () => {
    setShowNewUser(false);
    resetModal();
  };

  // Handle Open Modal
  const openModal = () => {
    setShowNewUser(true);
  };

  const blackListModalOpen = () => {
    setOpenBlackListModal(true);
    summaryModalData();
  };

  const errorText = "Please Select Both Month and Year..";
  const itemsPerPage = 10;

  const reasonData = {
    BLR1: "IP used VPS for book PNR",
    BLR2: "Booked more than 4 PNR using same IP address",
  };

  const statusData = {
    BLS1: "Pinaca Flagged for Blacklisting & Confirmation awaited from ITAF",
    BLS2: "Subnets Blacklisted by ITAF",
  };

  const renderTable = () => {
    return (
      <>
        {allowed_page?.blacklist && allowed_action?.view && (
          <div>
            {/* TABLE */}
            <div className={styles.main_container}>
              <div className={styles.headFilters}>
                <div className={styles.bothSelectPicker}>
                  <Input
                    placeholder="Search by ISP"
                    Name="text"
                    onChange={(value, e) => setIspSearchValue(value)}
                    // className={styles.searchBar}
                    style={{ width: 200 }}
                  />
                  <SelectPicker
                    appearance={"default"}
                    data={months}
                    searchable={false}
                    placeholder="Select Month"
                    value={selectedMonth}
                    onChange={setSelectedMonth}
                    style={{ width: 150 }}
                    // className={styles.MonthselectPicker}
                  />
                  <SelectPicker
                    searchable={false}
                    data={years}
                    placeholder="Select Year"
                    value={selectedYear}
                    onChange={setSelectedYear}
                    className={styles.MonthselectPicker}
                  />
                </div>
                <div className={styles.filterTwo}>
                  <Button
                    appearance="primary"
                    value={ispSearchValue}
                    onClick={(monthYear) => handleSearchClick(monthYear)}
                    className={styles.searchBtn}
                  >
                    {" "}
                    Search
                  </Button>
                  {allowed_action.download && (
                    <Button
                      className={styles.exportBtn}
                      appearance="primary"
                      onClick={() =>
                        downloadBlackISP(ispSearchValue, monthYear)
                      }
                      // disabled={searchDateValue == null && inputValue == "" ? true : false}
                    >
                      {" "}
                      Export
                    </Button>
                  )}
                </div>
              </div>

              {/* PNR Table Data Container */}
              <div className={styles.tableContainer + " col mx-auto"}>
                <table className={styles.data_table}>
                  <thead>
                    <tr>
                      <th className={styles.srNumber}>Sr No</th>
                      <th>ISP</th>
                      <th className={styles.subCount}>Subnet Count</th>
                      <th>IP Address Count</th>
                      <th>Reason for blacklist</th>
                      <th>Flagged by Pinaca </th>
                      <th>Blacklisted by ITAF</th>
                      <th className={styles.repMonth}>Report Month</th>
                      <th className={styles.rowStatus}>Status</th>
                      {allowed_action?.download && <th>Download Subnet</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {tableLoader ? (
                      <tr>
                        <td colSpan="10">
                          <div className={styles.loader_container}>
                            <div className={styles.loader} />
                          </div>
                        </td>
                      </tr>
                    ) : (
                      mainTableData?.map((item, index) => (
                        <tr key={index}>
                          <td className={styles.srNumber}>
                            {susCurrentPage > 1
                              ? (susCurrentPage - 1) * itemsPerPage + index + 1
                              : index + 1}
                          </td>
                          <td>{item.ISP}</td>
                          <td className={styles.subCount}>
                            {item?.TOTAL_BLACKLIST_SUBNET}
                          </td>
                          <td>{item?.TOTAL_BLACKLIST_IPS}</td>
                          <td>
                            {item?.REASON !== undefined &&
                            item?.REASON !== null ? (
                              <span>
                                <Whisper
                                  followCursor
                                  speaker={
                                    <Popover>
                                      {Object.keys(item?.REASON).map((x) => {
                                        return (
                                          <span
                                            key={x}
                                            className={styles.tagCodes}
                                          >
                                            <span
                                              className={styles.popovercode}
                                            >
                                              {x} : {reasonData[x]}
                                            </span>
                                          </span>
                                        );
                                      })}
                                    </Popover>
                                  }
                                >
                                  <span>
                                    {Object.keys(item?.REASON).join(", ")}
                                  </span>
                                </Whisper>
                              </span>
                            ) : (
                              <span>
                                <Whisper
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
                              </span>
                            )}
                          </td>

                          <td>
                            {item?.FLAGGED_DATE != undefined
                              ? new Date(
                                  item?.FLAGGED_DATE.$date
                                ).toDateString()
                              : null}
                          </td>
                          <td>
                            {item?.BLACKLIST_DATE != undefined
                              ? new Date(
                                  item?.BLACKLIST_DATE.$date
                                ).toDateString()
                              : null}
                          </td>
                          <td className={styles.repMonth}>
                            {item?.REPORT_MONTH}
                          </td>
                          <td className={styles.rowStatus}>
                            {item?.STATUS !== undefined &&
                            item?.STATUS !== null ? (
                              <span>
                                <Whisper
                                  placement="left"
                                  followCursor
                                  speaker={
                                    <Popover>
                                      {Object.keys(item?.STATUS).map((x) => {
                                        return (
                                          <span
                                            key={x}
                                            className={styles.tagCodes}
                                          >
                                            <span
                                              className={styles.popovercode}
                                            >
                                              {x} : {statusData[x]}
                                            </span>
                                          </span>
                                        );
                                      })}
                                    </Popover>
                                  }
                                >
                                  <span>
                                    {Object.keys(item?.STATUS).join(", ")}
                                  </span>
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
                                  <span>N.A.</span>
                                </Whisper>
                              </span>
                            )}
                          </td>
                          <td>
                            {allowed_action?.download && (
                              <Button
                                appearance="primary"
                                color="blue"
                                className={styles.userBtn}
                                onClick={() => {
                                  downloadFunction(
                                    item?.ISP,
                                    item?.REPORT_MONTH
                                  );
                                }}
                              >
                                {" "}
                                Download
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* PAGINATION */}
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
                layout={["total", "-", "|", "pager", "skip"]}
                pages={totalPages}
                total={totalRows}
                activePage={susCurrentPage}
                onChangePage={(page_value) => handleChange(page_value)}
              />
            </div>
          </div>
        )}
      </>
    );
  };

  const resetModal = () => {
    setFileList([]);
  };

  const handleChange = (page_value) => {
    setTableLoader(true);
    if (selectedMonth && selectedYear) {
      const monthYearValue = `${selectedMonth} ${selectedYear}`;
      setMonthYear(monthYearValue);
      setSusCurrentPage(page_value);
      pagiFunc(page_value, ispSearchValue, monthYear);
      setTableLoader(false);
    } else {
      toast.error(errorText);
    }
  };

  useEffect(() => {
    const currentYear = new Date().getFullYear();
    const yearsArray = [];
    for (let year = 2022; year <= currentYear; year++) {
      yearsArray.push({ label: year.toString(), value: year.toString() });
    }
    setYears(yearsArray);
    setSelectedYear(currentYear.toString());
    setMonthYear(`All ${currentYear}`);
  }, []);

  useEffect(() => {
    if (selectedMonth && selectedYear) {
      const monthYearValue = `${selectedMonth} ${selectedYear}`;
      setIspSearchValue(ispSearchValue);
      pagiFunc(1, ispSearchValue, monthYearValue);
    }
  }, []);

  // Check for loader status
  useEffect(() => {
    if (selectedMonth === null || selectedYear === null) {
      setTableLoader(true);
      if (tableLoader) {
        setTableLoader([]);
      }
    }
  }, [selectedMonth, selectedYear]);

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

      {/* UPLOAD MODAL */}
      {allowed_action?.upload && (
        <Modal
          open={showNewUser}
          onClose={closeModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <h3>Upload Scan Results</h3>
          <Modal.Body>
            File Upload:
            <Uploader
              action="/api/upload_blacklist"
              onError={(response, detail) => {
                if (response.status != 200) {
                  toast.error(response?.msg || "Please try again..");
                }
                closeModal();
              }}
              onSuccess={(response, detail, status) => {
                if (response.status === 500) {
                  toast.error(response?.detail);
                } else if (response.status === 200) {
                  toast.success(response?.detail);
                } else {
                  toast.error(response?.detail);
                }
                closeModal();
              }}
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
              ref={uploader}
              // data={[modelValueDateString]}
              draggable
              multiple
            >
              <div
                style={{
                  height: 200,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <span>Click or Drag files to this area to upload</span>
              </div>
            </Uploader>
          </Modal.Body>
          <Modal.Footer>
            <Button
              disabled={!fileList.length}
              onClick={() => {
                uploader.current.start();
                // closeModal()
              }}
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

      {/* PREV: Not in use in the new structure: Blaclklist Modal Start Here */}
      <Modal
        keyboard={false}
        size="lg"
        // size="full"
        overflow={true}
        open={openBlackListModal}
        onClose={handleTakeDownModalClose}
        // className={styles.modal}
        backdrop="static"
      >
        <CloseIcon onClick={() => closeModal()} className={styles.clear} />
        <h3> Blacklisted History</h3>
        <Modal.Body>
          <Table bordered height={500} data={viewModalData}>
            <Column width={80} fullText>
              <HeaderCell className={styles.modalHeader}>Sr No</HeaderCell>
              <Cell className={styles.cellHeader} />
            </Column>
            <Column width={130} fullText>
              <HeaderCell className={styles.modalHeader}>Month</HeaderCell>
              <Cell className={styles.cellHeader} dataKey="MONTH" />
            </Column>
            <Column width={180} fullText>
              <HeaderCell className={styles.modalHeader}>
                Count of ISP Reported
              </HeaderCell>
              <Cell className={styles.cellHeader} dataKey="ispCout" />
            </Column>
            <Column width={150} fullText>
              <HeaderCell className={styles.modalHeader}>
                Subnet Count
              </HeaderCell>
              <Cell className={styles.cellHeader} dataKey="subnetCount" />
            </Column>
            <Column width={180} fullText>
              <HeaderCell className={styles.modalHeader}>
                {" "}
                IP Address Count
              </HeaderCell>
              <Cell className={styles.cellHeader} dataKey="ipAddCount" />
            </Column>
            <Column width={200} fullText>
              <HeaderCell className={styles.modalHeader}>
                Download Blacklist File
              </HeaderCell>
              <Cell style={{ padding: "6px" }}>
                {(rowData) => (
                  <Button
                    appearance="primary"
                    // onClick={() =>
                    //   downloadDateISP(modalIsp, rowData?.DATE.$date)
                    // }
                    style={{ width: 100 }}
                    className={styles.downloadBtn}
                  >
                    Download
                  </Button>
                )}
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
              layout={["total", "-", "|", "pager", "skip"]} // Updated layout prop
            />
          </div>
        </Modal.Body>
      </Modal>
      {/* Blaclklist Modal Ends Here */}

      {/* MAIN BLACKLIST Section */}
      {allowed_page?.blacklist && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            {userRole == "admin" ? (
              <Board
                heading="Blacklist"
                router={Router}
                action={{
                  label: "Upload Blacklist",
                  handler: openModal,
                }}
              />
            ) : (
              <Board heading="Blacklist" router={Router} />
            )}
            {renderTable()}
          </div>
        </div>
      )}
    </>
  );
};

export default blacklist_page;

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res);
}
