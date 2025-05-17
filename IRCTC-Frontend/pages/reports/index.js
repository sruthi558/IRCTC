// endpoint
const endPoint = process.env.API_ENDPOINT;

// Import Libraries
import Image from "next/image";
import Router, { useRouter } from "next/router";
import { useEffect, useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Table, Whisper, Pagination, Tooltip, SelectPicker } from "rsuite";
const { Column, HeaderCell, Cell } = Table;
import { Button, Modal, Uploader, DatePicker } from "rsuite";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";
import { Circles } from "react-loader-spinner";
import CloseIcon from '@rsuite/icons/Close';

// Import archive-list
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import FilterBar from "../../components/FilterBar";

// Import Assets
import question from "../../public/static/images/questionmark.svg";

// Import Styles
// import styles from "./Analysis.module.scss";
import styles from "./Report.module.scss";

// Import Store
import {
  changeFilterOption,
  changeSearchValue,
  initReportData,
  initPageCount,
} from "../../store/slice/report";
import { toast } from "react-toastify";

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement }) => (
  // Render a Whisper component with trigger "hover", and specified placement and control ID.
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
      className={styles.questionmark + " col"}
      alt="Explanation"
    ></Image>
  </Whisper>
);

// Dashboard Component
const SusUsers = (props) => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  const user_role = useSelector((state) => state.persistedReducer.role)
  // console.log(`user_role: `, user_role);

  useEffect(() => {
    if(!allowed_page?.reports) {
      router.push('/overview')
    }
  }, [])

  // Initialise the dispatcher.
  const dispatch = useDispatch();
  // userRole contains the role of the user currently logged in for role-based restrictions.
  const userRole = useSelector((state) => state.persistedReducer.role);
  // This state variable is used to determine whether to show a form or UI for creating a new user.
  const [showNewUser, setShowNewUser] = useState(false);
  // This is another piece of data from the Redux store that contains the total number of pages for the user IDs.
  const analysisPageCount = useSelector((state) => state.report.pageCount);
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false);
  // searchValue is a state variable that holds the search value for the table.
  const searchValue = useSelector((state) => state.report.searchValue);
  // This state defines a new state variable named "modelValueDate" and sets its initial value to an empty string.
  const [modelValueDate, setModelValueDate] = useState();
  // This state defines a new state variable named "fileList" and sets its initial value to an empty array.
  const [fileList, setFileList] = useState([]);
  // This state defines a new state variable named "fileType" and sets its initial value to an empty string.
  const [fileType, setFileType] = useState("");
  const [dateRange, setDateRange] = useState([]);
  const [pageId, setPageId] = useState(1);
  // Declare a reference to the Upload component for tracking the files in a persistant manner across reloads.
  const uploader = useRef();
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1);
  const [option, setOption] = useState("");

  //CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} />;

  // Initialise the date to be searched through the data.
  const analysisDate = useSelector((state) => state.analysis.searchDate);
  // This state variable contains the number of items to display in a table on the dashboard.
  const displayCount = useSelector((state) => state.analysis.tableLength);

  // Initialise the filters to be used while searching through the data.
  const filterOverviewOptions = useSelector((state) => state.report.filterOption);
  const [mainTableTotalRows, setMainTableTotalRows] = useState(0)
  const [mainTableTotalPages, setMainTableTotalPages] = useState(0)
  const [filterOption, setFilterOption] = useState("");
  const [filteredReportData, setFilteredReportData] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(false)
  
  useEffect(() => {
    setSelectedOptions(Object.values(filterOption)); 
  }, [filterOption])

  // Available filter options for this page.
  const options = [
    "Brand Monitoring",
    "Cyber Threat Intelligence",
    "General Report",
    "Infrastructure Monitoring",
    "Minutes of the Meeting",
    "Monthly Report",
    "OSINT Analysis",
    "Software Analysis",
    "Special Analysis",
    "Web Server Access Logs",
  ].map((item) => ({ label: item, value: item }));

  // API Call: /api/archive-list".
  const pagiFunct = async (page_value, selectedOptions) => {
    setPageLoading(true);
    const data = await fetch("/api/archive-list", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        page_id: page_value || 1,
        search: Object.values(selectedOptions),
        starting_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[0].toISOString()
            : new Date(0),
        ending_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[1].toISOString()
            : new Date(),
      }),
    }).then((res) => res.json());
   
    setFilteredReportData(data?.data_list?.map((item) => JSON.parse(item)));
    setMainTableTotalRows(data?.total_rows);
    setMainTableTotalPages(data?.total_pages);
    setPageLoading(false);
  };

  const handleSearch = () => {
    setFilteredReportData(null);
    setPageLoading(true);
    setPage(1);
    pagiFunct(1, selectedOptions); 
  };

  const handlePageChange = (page_value) => {
    setFilteredReportData(null);
    setLoading(true);
    setPage(page_value);   
    pagiFunct(page_value, selectedOptions);
  };


  // API Call: '/api/userid_pagecount_all'
  const initTotalPageCount = async () => {
    const data = await fetch("/api/archive-list-count", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    }).then((res) => res.json());

    dispatch(initPageCount(data?.data_count));
  };

  // This code creates a downloadable file from the response blob.
  const downloadReport = async(f_name, f_hash) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/archive-download?f_hash=" + f_hash).then((response) => {
      response.blob().then((blob) => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        a.download = f_name.replaceAll(" ", "");
        a.click();
      });
    });
    setIsLoading(false);
  };

  const deleteReport = async(f_hash) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/archive-delete?f_hash=" + f_hash).then((response) =>
      response.json()
    );
    setTimeout(function () {
      Router.reload();
    }, 1500);
    setIsLoading(false);
  };

  // This useEffect hook will be executed only once when the component mounts,
  useEffect(() => {
    setLoading(true);
    pagiFunct(1,[]);
  }, []);
  
  // Close or remove the opened Modal.
  const closeModal = () => {
    setShowNewUser(false);
  };

  // Function to open Modal
  const openModal = () => {
    setShowNewUser(true);
  };

  const filetypes = [
    "Cyber Threat Intelligence",
    "Web Server Access Logs",
    "Minutes of the Meeting",
    "Infrastructure Monitoring",
    "Brand Monitoring",
    "Special Analysis",
    "Monthly Report",
    "Software Analysis",
    "OSINT Analysis",
    "General Report",
  ].map((item) => ({ label: item, value: item }));

  const modelValueDateString = modelValueDate
    ? modelValueDate.toISOString()
    : null;

  const reportData = useSelector((state) => {
    if (filterOption === "All") {
      return state?.report?.data; 
    } else {
      return state?.report?.data?.filter(
        (rowData) => rowData?.field === filterOption
      );
    }
  });

    // This function closed the modal whenever submit button is clicked.
  const onSubmitCloseModal = () => {
    setShowNewUser(false)
    resetModal()
  }

  const resetModal = () =>{
    setModelValueDate(null);
    setFileType();
    setFileList([]);
  }

  
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
      {/* REPORT UPLOAD - Modal */}
      {(allowed_actions?.upload && user_role === 'admin') && (
        <Modal open={showNewUser} onClose={closeModal} className={styles.modal} backdrop='static'>
            <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          <h3>File Upload</h3>
          <Modal.Body>
            <DatePicker
              label="Date of Report"
              className="mb-3"
              placeholder="Select Date"
              style={{ width: 300 }}
              value={modelValueDate}
              onChange={(newValueDate) => setModelValueDate(newValueDate)}
            />
            <SelectPicker
              label="Report Category"
              className="mb-3"
              data={filetypes}
              value={fileType}
              onChange={(newvalue) => setFileType(newvalue)}
              style={{ width: 400 }}
            />
            <br />
            <p>Upload Report:</p>
            <Uploader
              action='/api/archive-upload'
              accept="application/pdf, .xlx, .xlsx"
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
              onSubmit={onSubmitCloseModal} 
              ref={uploader}
              data={[modelValueDateString, fileType]}
              draggable
              multiple            
              onSuccess={(response) => {
                console.log('onSuccess called:', response.detail);
                console.log('onSuccess status called:', response.status);
                if (response.detail === 'File Uploaded Successfully') {
                  toast.success('File uploaded successfully.');
                } else if (response.detail === 'File already exists') {
                  toast.info('File already exists.');
                } else {
                  toast.error('File upload failed.');
                }
              }}
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
                onSubmitCloseModal()
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
      
      {/* REPORTS MAIN - Page */}
      {allowed_page?.reports && allowed_actions?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board
              heading="Report Archives"
              action={{ label: "File Upload", handler: openModal }}
              router={Router}
            />

            <FilterBar
              handleDateRangeChange={setDateRange}
              setFilterOption={setFilterOption}
              dateRange={dateRange}
              availableFilterOptions={options}
              tableLength={displayCount}
              changeOptions={changeFilterOption}
              pageSource="Overview"
              onsearch={handleSearch}
              onclear={() => Router.reload()}
              dispatch={dispatch}
            />
            
            <div className={`${styles.tableContainer} col mx-auto ${pageLoading ? styles.blur : ''}`}>
              <div className={styles.susN_data_container}>
                <table  className={`${styles.data_table} ${pageLoading ? 'blur' : ''}`}>
                  {pageLoading && (
                    <div className={styles.loader_container}>
                      <p className={styles.loader_text} />
                      <div className={styles.loader} />
                    </div>
                  )}
                  <thead  className={styles.susN_tables_head}>
                    <tr>
                      <th className={styles.col_name_header}>Name of the Report</th>
                      <th className={styles.susN_tables_file_col}>File Size</th>
                      <th className={styles.susN_tables_col}>Date of Report</th>
                      <th className={styles.susN_tables_col}>Report Type</th>
                      {allowed_actions?.download && (
                        <th>Download</th>
                      )}
                      {/* {userRole === 'admin' && <th>Delete</th>} */}
                      {(allowed_actions?.delete && user_role === 'admin') && (
                        <th>Delete</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredReportData?.map((rowData, index) => (
                      <tr key={index}>
                        <td className={styles.col_name_header}>
                          {rowData.filename ? rowData.filename.toString().replaceAll('_', ' ') : null}
                        </td>
                        <td>{rowData.filesize ? rowData.filesize + ' MB' : null}</td>
                        <td>
                          {rowData.file_date ? new Date(rowData.file_date.$date).toDateString() : null}
                        </td>
                        <td>{rowData.field}</td>

                        {allowed_actions?.download && (
                          <td clasName={styles.reportBtn}>
                            <Button 
                              appearance="primary"
                              size="md"
                              onClick={() => downloadReport(rowData.filename, rowData.ref_hash)}
                            > Download
                            </Button>
                          </td>
                        )}
                        {(allowed_actions?.delete && user_role === 'admin') && (
                          <td  clasName={styles.reportBtn}>
                            <Button 
                              appearance="primary" 
                              size="md"
                              color="red"
                              onClick={() => deleteReport(rowData.ref_hash)}
                            >Delete</Button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
                  layout={["total", "-", "|", "pager", "skip"]} // Updated layout prop
                  pages={mainTableTotalPages}
                  total={mainTableTotalRows}
                  limit={[10]}
                  activePage={page}
                  onChangePage={(datakey)=>handlePageChange(datakey)}
                />
              </div>
            </div>
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
