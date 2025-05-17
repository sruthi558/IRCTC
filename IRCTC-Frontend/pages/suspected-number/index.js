import React, { useEffect, useState, useRef } from "react";
// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import Router, { useRouter } from "next/router";
import { useSelector, useDispatch } from 'react-redux'
import { toast } from "react-toastify";
import { Circles } from "react-loader-spinner";
import CloseIcon from '@rsuite/icons/Close';

import { SelectPicker } from "rsuite";
// Import Store
import {
  Button,
  DateRangePicker,
  Dropdown,
  Modal,
  Pagination,
  Table,
  Uploader,
} from "rsuite";

// Import Styles
import styles from "./suspectedNumber.module.scss";

const SuspectedNumberPage = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.suspected_number) {
      router.push('/overview')
    }
  }, [])
  
  const dispatch = useDispatch()
  const uploader = useRef();

  const [selectedMonth, setSelectedMonth] = useState('All');
  const [selectedYear, setSelectedYear] = useState('2024');
  const [monthYear, setMonthYear] = useState(""); 
  const [years, setYears] = useState([]);
  const [uploadSelectedMonth, setUploadSelectedMonth] = useState(null);
  const [uploadSelectedYear, setUploadSelectedYear] = useState(null);
  const [uploadModalFile, setUploadModalFile] = useState(false);
  const [uploadingFileList, setUploadingFileList] = useState([]);
  const [susMobileTotalRows, setSusMobileTotalRows] = useState(0);
  const [susMobileTotalPages, setSusMobileTotalPages] = useState(0);
  const [susCurrentPage, setSusCurrentPage] = useState(1);
  const [mainTableData, setMainTableData] = useState([]);

  const [isLoading, setIsLoading] = useState(false);
  const [dataLoader, setDataLoader] = useState(false)


  const months = [
    { label: 'All', value: 'All'}, 
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

  const uploadMonths = [
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
  ]

  // const years = [
  //   { label: "2022", value: "2022" },
  //   { label: "2023", value: "2023" },
  // ];

  const errorText = "Please Select Both Month and Year.."

   // API Call: /api/sus-mobile".
   const mainListData = async (page_value, monthYear) => {
    setDataLoader(true)
    // Check if monthYear is not empty
  if (!monthYear.trim()) {
    console.error("Error:", errorText);
    setDataLoader(false);
    return;
  }
    // await new Promise((resolve) => setTimeout(resolve, 2000));
    try {
      const response = await fetch("/api/sus-mobile", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: page_value, 
          month: monthYear, 
        }),
      });
        const data = await response.json();
        setMainTableData(data.data_list.map((item) => JSON.parse(item)));
        setSusMobileTotalRows(data?.total_rows);
        setSusMobileTotalPages(data?.total_pages);
    } catch (error) {
      console.error("Error:", error);
    }
    setDataLoader(false)
  };

  const downloadReport = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/sus-mobile-export", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
       month:monthYear,
      }),
    }).then(async (response) => {
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        // a.download =
        //   "Suspected_Number" +
        //   new Date().toDateString().replaceAll(" ", "_") +
        //   "_.xlsx";
        a.download ="Suspected_Number_" + monthYear +  "_.xlsx";
        a.click();

        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
    setIsLoading(false);
    
  };
  
  const itemsPerPage = 20;

  const handlePageChangeModal = (page_value) => {
    setDataLoader(true);
    setSusCurrentPage(page_value,monthYear);
    mainListData(page_value, monthYear);
  };
  
  const handleSearchClick = () => {
    if (selectedMonth && selectedYear) {
      setDataLoader(true);
      const monthYearValue = `${selectedMonth} ${selectedYear}`;
      setMonthYear(monthYearValue);
      mainListData(1, monthYearValue);
      setSusCurrentPage(1,monthYear);
      setDataLoader(false)
    } else {
      toast.error(errorText);
    }
  };
  
  const handleSubmitClick = () => {
    if (uploadSelectedMonth && uploadSelectedYear) {
    } else {
      toast.error(errorText);
    }
  };

  const closeModal = () => {
    setUploadModalFile(false);
    // setSelectedMonth(null);
    // setSelectedYear(null);
  };

  const openModal = () => {
    setUploadModalFile(true);
    setUploadingFileList([]);
  };

  const submitCloseModal = () => {
    setUploadModalFile(false);
  };

  const handleYearChange = (value) => {
    setSelectedYear(value);
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
      setMonthYear(monthYearValue);
      mainListData(1, monthYearValue);
    }
  },[]);

  // Check for loader status 
  useEffect(() => {
    if(selectedMonth === null || selectedYear === null) {
      setDataLoader(true)
      if(dataLoader) {
        setMainTableData([])
      }
    }
  }, [selectedMonth, selectedYear])

  
  return (
    <>
      {/* Modal Starts */}
      {allowed_actions?.upload && (
        <Modal
          open={uploadModalFile}
          onClose={closeModal}
          className={styles.modal}
          backdrop='static'
        >
        <CloseIcon onClick={()=> closeModal()} className={styles.clear} />
          <h3>Upload Suspected File</h3>
          <Modal.Body>
            <p className={styles.uploadText}> File Upload</p>
            <Uploader
              action="/api/sus-mobile-upload"
              accept=".xls,.xlsx"
              onError={async ({ response }, file, detail) => {
                await new Promise((resolve) => setTimeout(resolve, 1000));
                toast.error(response.detail);
              }}
              onSuccess={async (response, detail, status) => {
                if (detail.status === "finished") {
                  await new Promise((resolve) => setTimeout(resolve, 1000));
                  toast.success("File uploaded successfully.");
                  submitCloseModal();
                }
              }}
              uploadingFileList={uploadingFileList}
              autoUpload={false}
              onChange={setUploadingFileList}
              data={[uploadSelectedMonth + ' ' + uploadSelectedYear]}
              ref={uploader}
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
              disabled={!uploadingFileList.length}
              onClick={() => {
                uploader.current.start();
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
      
      {/* Export loader  code  */}
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

      {/* MAIN SUS MOBILE - Page */}
      <div>
        {(allowed_page?.suspected_number && allowed_actions?.view) && (
          <div className={styles.dashboard}>
            <div className={styles.sidebar}>
              <Sidebar />
            </div>
    
            <div className={styles.page}>
              <Board
                router={Router}
                heading="Suspected Number"
                action={{ label: "Upload Files", handler: openModal }}
              />
    
              <div className={styles.sus_main_container}>
                {/* Main Header Container */}
                <div className={styles.sus_div_header}>
                  <div className={styles.sus_div_sub_headers}>
                    <SelectPicker
                      data={months}
                      label="Month"
                      searchable={false}
                      value={selectedMonth}
                      onChange={setSelectedMonth}
                      className={styles.MainselectPicker}
                    />
                    <SelectPicker
                      data={years}
                      label="Year"
                      searchable={false}
                      value={selectedYear}
                      onChange={handleYearChange}
                      className={styles.MainselectPicker}
                    />
                    <div className={styles.div_header_btn}>
                      <Button
                        appearance="primary"
                        className={styles.searchBtn}
                        onClick={(monthYear) => handleSearchClick(1,monthYear)}
                      >
                        Search
                      </Button>
                      {allowed_actions?.download && (
                        <Button
                          className={styles.exportBtn}
                          appearance="primary"
                          onClick={() => downloadReport()}
                        >
                          Export
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
    
                {/* PNR Table Data Container */}
                {/* <div className={styles.susN_data_container}> */}
                <div className={`${styles.susN_data_container} ${dataLoader ? styles.blur : ''}`}>
                {mainTableData.length > 0 ? (
                  <table className={styles.data_table}  data={mainTableData}>
                    <thead className={styles.susN_tables_head}>
                      <tr>
                        <th className={styles.susN_tables_col}>S.No</th>
                        <th>Mobile Number</th>
                        <th>Source</th>
                        <th>Status</th>
                        <th>Uploaded By</th>
                        <th>Upload Month</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dataLoader ? 
                        (
                        <tr>
                          <td colSpan="6">
                            <div className={styles.loader_container}>
                              <div className={styles.loader} />
                            </div>
                          </td>
                        </tr>
                        ) : (
                          mainTableData.length > 0 && 
                          mainTableData.map((item, index) => (
                            <tr key={index}>
                              {/* <td>{index + 1}</td> */}
                              <td>{susCurrentPage > 1 ? (susCurrentPage - 1) * itemsPerPage + index + 1 : index + 1}</td>
                              <td>{item?.mobile_no}</td>
                              <td>{item?.source}</td>
                              <td>{item?.status}</td>
                              <td>{item?.latest_username}</td>
                              <td>{item?.month_str}</td>
                            </tr>
                          ))
                        )
                      }
                    </tbody>
                  </table>
                   ) : (
                    <div className={styles.noDataMessage}>
                      <p className={styles.noDataMessagemsg}>No data found for this Month and Year</p>
                    </div>
                  )}
                </div>
              
                <div className={styles.pagination}>
                  {!dataLoader && (
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
                      pages={susMobileTotalPages}
                      total={susMobileTotalRows}
                      activePage={susCurrentPage}
                      onChangePage={(page_value,monthYear) => handlePageChangeModal(page_value, monthYear)}
                    />
                  )}
                </div>       
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default SuspectedNumberPage;
