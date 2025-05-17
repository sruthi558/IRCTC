import React, { useEffect, useRef, useState, useMemo } from "react";
import Router, { useRouter } from "next/router";
import _ from "lodash";
import styles from "./SoftwareProcurement.module.scss";
import Sidebar from "@/components/Sidebar";
import Board from "@/components/Board";
import { Button, DatePicker, Input, Modal, Table, Pagination } from "rsuite";
const { Column, HeaderCell, Cell, CompactCell } = Table;
import { Uploader, Checkbox } from "rsuite";

import FilterBar from "@/components/FilterBar";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "react-toastify";
import { Circles } from "react-loader-spinner";
import CloseIcon from '@rsuite/icons/Close';

const SoftwareProcurement = () => {

  // Initialising the router 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  const user_role = useSelector((state) => state.persistedReducer.role)

  // console.log(`User role: `, user_role);

  useEffect(() => {
    if(!allowed_page?.software_procurement) {
      router.push('/overview')
    }
  }, [])

  const dispatch = useDispatch();
  const uploader = useRef();

  const [tableData, setTableData] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [showNewUser, setShowNewUser] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [modelValueDate, setModelValueDate] = useState();
  const [selectedDate, setSelectedDate] = useState(null);
  const [fileType, setFileType] = useState("");
  const [dateRange, setDateRange] = useState([]);
  const [searchValue, setSearchValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [softwarePageCount, setSoftwarePageCount] = useState(10);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(10);
  const [pagesCount, setPagesCount] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [approvalDate, setApprovalDate] = useState(null);
  const [purchaseDate, setPurchaseDate] = useState(null);
  const [mainTableTotalRows, setMainTableTotalRows] = useState(0)
  const [mainTableTotalPages, setMainTableTotalPages] = useState(0)
  const [loading, setLoading] = useState(false);
  const [softMainLoading, setSoftMainLoading] = useState(false);

  const [allInputs, setAllInputs] = useState({
    software_name: "",
    purpose: "",
    software_price: "",
    purchase_date: new Date(),
    approval_date: new Date(),
    current_status: "",
    remarks: "",
    // filedate: new Date(),
    ftype: "",
  });

  const closeModal = () => {
    setShowNewUser(false);
    setSelectedDate(null);
    resetModal();
  };

  const handleUpload = () => {
    setShowModal(true);
  };

  const handleModalClick = () => {
    setShowModal(false);
    if (uploader.current) {
      uploader.current.start();
    }
  };

  const onSubmitCloseModal = () => {
    setShowNewUser(false);
    setSelectedDate(null);
    resetModal();
    setTimeout(function () {
      Router.reload();
    }, 3000);
  };

  // Function to open Modal
  const openModal = () => {
    setShowNewUser(true);
  };

  const resetModal = () => {
    setSelectedDate(null);
    setModelValueDate(null);
    setAllInputs(null)
    setFileList([]);
  };

  const modelValueDateString = selectedDate ? selectedDate.toISOString() : null;

  // Function to handle changes in the column name inputs
  const handleColumnNameChange = (e) => {
    const { name, value } = e.target;
    setAllInputs((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const apiEndpoint = async (allInputs) => {
    const payload = {
      0: null,
      1: {
        // filedate: allInputs.filedate,
        software_name: allInputs.softwarename,
        purpose: allInputs.purpose,
        software_price: allInputs.softwareprice,
        approval_date: allInputs.approvalDate,
        purchase_date: allInputs.purchaseDate,
        current_status: allInputs.currentstatus,
        remarks: allInputs.remarks,
      },
    };

    try {
      const response = await fetch("/api/upload_software_procurement", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      // Handle the response data here
    } catch (error) {
      // Handle any errors that occurred during the API call
      console.error("Error:", error);
    }
  };

  const handleAPICall = async () => {
    try {
      await apiEndpoint(allInputs); // we have allInputs state defined somewhere
      onSubmitCloseModal(); //  close the modal after the API call is successful
    } catch (error) {}
  };

  const downloadReport = async (f_name, f_hash) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
  

    fetch("/api/software-report-download?f_hash=" + f_hash).then((response) => {
      response.blob().then((blob) => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        a.download = f_name?.replaceAll(" ", "");
        a.click();
      });
    });
    setIsLoading(false);
  };

  const deleteReport = async(f_hash) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/software-procurement-delete?f_hash=" + f_hash)
      .then((response) => response.json())
      .then((data) => {
        if (data.detail === "File successfully deleted") {
          toast.success("File deleted successfully");
        } else {
          toast.error("Failed to delete file");
        }
      });
    setTimeout(function () {
      Router.reload();
    }, 3000);
    setIsLoading(false);
  };

  const handleTableCall = async () => {
    const payload = {
      0: null,
      1: {
        // filedate: allInputs.filedate,
        software_name: allInputs.softwarename,
        purpose: allInputs.purpose,
        software_price: allInputs.softwareprice,
        approval_date: allInputs.approvalDate,
        purchase_date: allInputs.purchaseDate,
        current_status: allInputs.currentstatus,
        remarks: allInputs.remarks,
      },
    };
    
    try {
   
      // Perform the API call to submit the form data and uploaded file
      const response = await fetch(" /api/software-procurement-list ", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload), // Assuming allInputs contains the form data
      });

      if (response.status == 200) {
        onSubmitCloseModal(); // Close the modal after successful submission
        setSelectedDate(null); // Reset the selected date
        fetchTableData(); // Fetch the updated data for the table
      } else {
        console.error("Error submitting the form:", response);
      }
    } catch (error) {
      console.error("Error submitting the form:", error);
    }
  
  };

  const fetchTableData = async (page_value, searchValue) => {
    try {
      setSoftMainLoading(true)
      const response = await fetch("/api/software-procurement-list", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: page_value,
          search: searchValue,
          starting_date:
            dateRange != null && dateRange?.length != 0
              ? dateRange[0].toISOString()
              : new Date(0),
          ending_date:
            dateRange != null && dateRange?.length != 0
              ? dateRange[1].toISOString()
              : new Date(),
        }),
      })
        .then((res) => res.json())
        .then((response) => {
          setTableData(response?.data_list?.map((item) => JSON.parse(item)));
          setMainTableTotalRows(response?.total_rows);
          setMainTableTotalPages(response?.total_pages);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching table data:", response);
        });
    } catch (error) {
      console.error("Error fetching table data:", error);
    }
    setSoftMainLoading(false)
  };

  const exportReport = async (page_value, searchValue) => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch("/api/export-software-report", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        page_id: page_value,
        search: searchValue,
        starting_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[0].toISOString()
            : new Date(0),
        ending_date:
          dateRange != null && dateRange?.length != 0
            ? dateRange[1].toISOString()
            : new Date(),
      }),
    }).then((response) => {
      // This code creates a downloadable file from the response blob.
      response.blob().then((blob) => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        // a.download = "software_procurement" + new Date().toDateString().replaceAll(" ", "_") + ".xlsx";
        a.download = `SOFTWARE_PROCUREMENT_from_${dateRange[0].toDateString().replaceAll(' ', '_')}_to_${dateRange[1].toDateString().replaceAll(' ', '_')}.xlsx`

        a.click();
      });
    });
  };

  const handleVPSExport = async () => {
    setIsLoading(true);

    try {
      await exportReport(1, searchValue);
    } catch (error) {
      console.error("Error occurred while downloading the VPS export:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (dataKey) => {
    setTableData(null)
    setPage(1);
    fetchTableData(1, searchValue);
  };

  const handlePageChange = (dataKey) => {
    setTableData(null)
    setPage(dataKey);
    fetchTableData(dataKey, searchValue);
  };

  const handleChangeLimit = (dataKey) => {
    setPage(1);
    setLimit(dataKey);
    fetchTableData(1, dataKey);
  };

  useEffect(() => {
    // fetchTableData();
    fetchTableData(1, searchValue);
  }, []);

  // Function to format the date as a string
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date) || dateString.trim() === "") {
        return "N/A"; // Return a message for invalid or empty dates
      }
      return date.toDateString(); // Format the date as a string
    } catch (error) {
      return "N/A"; // Return a message for any other errors
    }
  };

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

      {/* SOFTWARE REPORT UPLOAD - Modal */}
      {(allowed_actions?.upload && user_role === 'admin') && (
        <Modal
          open={showNewUser}
          // onClose={closeModal}
          onClose={() => {
            closeModal();
            setSelectedDate(null); // Reset the selected date when the modal is closed
          }}
          className={styles.modal}
          size="sm"
          backdrop='static'
        >
           <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          <h3>File Upload</h3>
          <Modal.Body>
            <Input
              name="software_name"
              type="text"
              value={allInputs?.software_name}
              onChange={(_, e) => handleColumnNameChange(e)}
              placeholder="Software Name"
              className={styles.inputBoxes}
            />
            <Input
              name="purpose"
              type="text"
              value={allInputs?.purpose}
              onChange={(_, e) => handleColumnNameChange(e)}
              placeholder="Purpose"
              className={styles.inputBoxes}
            />
            <Input
              name="software_price"
              type="text"
              value={allInputs?.software_price}
              onChange={(_, e) => handleColumnNameChange(e)}
              placeholder="Software Price"
              className={styles.inputBoxes}
            />
            <DatePicker
              // label="Date of S/W"
              className="mb-3"
              placeholder="Select Purchase Date"
              name={purchaseDate}
              style={{ width: 250, marginRight: "30px", marginTop: "10px" }}
              onChange={(date) => {
                setPurchaseDate(date); // Update the selected date in the DatePicker
                setAllInputs((prev) => ({
                  ...prev,
                  purchase_date: date,
                }));
              }}
            />

            <DatePicker
              // label="Date of S/W"
              className="mb-3"
              placeholder="Select Approval Date"
              name={approvalDate}
              style={{ width: 240, marginTop: "10px" }}
              onChange={(date) => {
                setApprovalDate(date); // Update the selected date in the DatePicker
                setAllInputs((prev) => ({
                  ...prev,
                  approval_date: date,
                }));
              }}
            />

            <Input
              name="current_status"
              type="text"
              value={allInputs?.current_status}
              onChange={(_, e) => handleColumnNameChange(e)}
              placeholder="Current Status"
              className={styles.inputBoxes}
            />
            <Input
              name="remarks"
              type="text"
              value={allInputs?.remarks}
              onChange={(_, e) => handleColumnNameChange(e)}
              placeholder="Remarks "
              className={styles.inputBoxes}
            />
            <br />
            <p>Upload File : </p>
            <Uploader
              action="/api/upload_software_procurement"
              accept="application/pdf"
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
              ref={uploader}
              data={[modelValueDateString, JSON.stringify(allInputs)]}
              draggable
              multiple
              className={styles.uploader}
              onSuccess={(response) => {
                if (response.detail === "File Uploaded Successfully") {
                  toast.success("File uploaded successfully.");
                } else if (response.detail === "File already exists") {
                  toast.info("File already exists.");
                } else {
                  toast.error("File upload failed.");
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
                onSubmitCloseModal();
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
      
      {/* MAIN SOFTWARE PREC - Page */}
      {(allowed_page?.software_procurement && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <div className={styles.header}>
              <Board
                heading="Software Procurement and Analysis"
                action={{ label: "Upload Files", handler: openModal }}
                router={Router}
              />
            </div>

            <FilterBar
              handleDateRangeChange={setDateRange}
              dateRange={dateRange}
              setDateRange={setDateRange}
              onsearch={(page_value) => handleSearch(page_value)}
              handleVPSExport={handleVPSExport}
              // onclear={() => Router.reload()}
              fetchTableData={(page_value) => fetchTableData(page_value, searchValue)}
              searchValue={searchValue}
              setSearchValue={setSearchValue}
            /> 
            
            {/* <div className={styles.tableContainer + " col mx-auto"}> */}
            <div className={`${styles.tableContainer} ${softMainLoading ? styles.blur : ''}`}>
              <div className={styles.sw_data_container}>
                {/* <table className={styles.tableContainer}> */}
                <table className={styles.sw_data_table}>
                  {softMainLoading && (
                    <div className={styles.loader_container}>
                      <p className={styles.loader_text} />
                      <div className={styles.loader} />
                    </div>
                  )}
                  <thead className={styles.sw_tables_head}>
                    <tr>
                      <th>Software Name</th>
                      <th>File Size </th>
                      <th>Purpose</th>
                      <th>Software Price</th>
                      <th>Purchase Date</th>
                      <th>Approval Date</th>
                      <th>Current Status</th>
                      <th>Remarks</th>
                      {allowed_actions?.download && (
                        <th>Download</th>
                      )}
                      {(allowed_actions?.delete && user_role === 'admin') && (
                        <th>Delete</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData?.map((item) => (
                      <tr key={item.ref_hash}>
                        <td>{item.software_name}</td>
                        <td>{item.filesize + "MB"}</td>
                        <td>{item.purpose}</td>
                        <td>{item.software_price}</td>
                        <td>{formatDate(item.purchase_date?.$date)}</td>
                        <td>{formatDate(item.approval_date?.$date)}</td>
                        <td>{item.current_status}</td>
                        <td>{item.remarks}</td>
                        {allowed_actions?.download && (
                          <td>
                            <Button
                              className={styles.button}
                              onClick={() => downloadReport(item.filename, item.ref_hash)}
                              appearance="primary"
                            >
                              Download
                            </Button>
                          </td>
                        )}
                        {(allowed_actions?.delete && user_role === 'admin') && (
                          <td>
                            <Button
                              className={`${styles.button} ${styles.buttonred}`}
                              onClick={() => deleteReport(item.ref_hash)}
                              color="red"
                              appearance="primary"
                            >
                              Delete
                            </Button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div style={{ padding: 10 }}>
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
                onChangePage={handlePageChange}
                onChangeLimit={handleChangeLimit}
                onGoTo={(page) => setPage(page)}
              />
            </div>
          </div>
        </div>
      )}
      
    </>
  );
};

export default SoftwareProcurement;
