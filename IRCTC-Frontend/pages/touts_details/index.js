import React from "react";
// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import { useEffect, useRef, useState } from "react";
import { useSelector} from "react-redux";
import Router, { useRouter } from "next/router";
import { Loader, Pagination } from "rsuite";
import CloseIcon from "@rsuite/icons/Close";
import { Circles } from "react-loader-spinner";
// labrary Imports
import { Button, Modal, Uploader } from "rsuite";
import ThreatCards from "./ThreatCards";

// Import Styles
import styles from "./touts-details.module.scss";
import FilterBar from "@/components/FilterBar";
import { toast } from "react-toastify";

function ToutsDetails() {
  const router = useRouter();
  const uploader = useRef();

  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_actions = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  useEffect(() => {
    if(!allowed_page?.touts_details) {
      router.push('/overview')
    }
  }, [])

  // Modal All states Start Here
  const [modelValueDate, setModelValueDate] = useState();
  const [fileType, setFileType] = useState("");
  const [fileList, setFileList] = useState([]);
  const [showNewUser, setShowNewUser] = useState(false);

  
  const [mainCardData, setMainCardData] = useState([]);
  const [mainPageLoading, setMainPageLoading] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchInputText, setSearchInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const [isLoading, setIsLoading] = useState(false);

  // Function to open Modal
  const openModal = () => {
    setShowNewUser(true);
  };

  // Close or remove the opened Modal.
  const closeModal = () => {
    setShowNewUser(false);
  };

  // This function closed the modal whenever submit button is clicked.
  const onSubmitCloseModal = () => {
    setShowNewUser(false);
    resetModal();
  };

  const resetModal = () => {
    setModelValueDate(null);
    setFileType();
    setFileList([]);
  };

  const getMainTableCards = async (pageValue) => {
    try {
      setLoading(true);
      // await new Promise((resolve) => setTimeout(resolve, 3000));
      const response = await fetch("/api/tout_card_detail", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_id: pageValue,
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

      setMainCardData(fetchdata);
      setTotalRows(data?.total_rows);
      setTotalPages(data?.total_pages);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  const searchApiCall = async (pageValue) => {
    try {
      setLoading(true);
      // await new Promise((resolve) => setTimeout(resolve, 3000));

      // Perform a null check on searchInputText
      // const searchTerms = (searchInputText || '')
      //   ?.split(/[\s,]+/) // Split the search input by spaces and commas
      //   ?.filter((term) => term.trim() !== ''); // Remove empty terms
  
      const response = await fetch("/api/tout_card_detail", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          page_id: pageValue,
          search: searchInputText,
        }),
      });
  
      const responseData = await response.json();
  
      // Assuming the API response contains a 'data_list' property
      const fetchedData = responseData?.data_list?.map((item) => {
        try {
          return JSON.parse(item);
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError);
          return {};
        }
      });
  
      // Filtering based on the search input text
      // const filteredData = fetchedData?.filter((card) => {
      //   // Check if any of the search terms exist in any of the keys
      //   return searchTerms?.some((term) => {
      //     return Object.values(card).some((values) => {
      //       return Array.isArray(values) && values?.some((value) => value.includes(term));
      //     });
      //   });
      // });
  
      setMainCardData(fetchedData);
      setTotalRows(responseData?.total_rows || 0);
      setTotalPages(responseData?.total_pages || 0);
    } finally {
      setLoading(false); // Set loading to false when the API call completes, whether successful or not
    }
  };
  
  
  const handleSearchClick = async () => {
    // Assuming you have a way to get the search input text
    const trimmedSearchInput = searchInputText?.trim();
    setCurrentPage(1);
  
    if (trimmedSearchInput !== "") {
      // If searching, call the search function with the new page and search input
      await searchApiCall(1, trimmedSearchInput);
    } else {
      // If not searching, simply update the current page
      await getMainTableCards(1);
    }
  };
  
 const handlePageChange = async (newPage) => {
  const trimmedSearchInput = searchInputText.trim();

  setCurrentPage(newPage);  // Update the page in the state

  if (trimmedSearchInput !== "") {
    await searchApiCall(newPage, trimmedSearchInput);
  } else {
    await getMainTableCards(newPage, trimmedSearchInput);
  }
};

const downloadReport = async () => {
  setIsLoading(true);
  fetch("/api/export_tout_details", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
     search:searchInputText
    }),
  }).then(async (response) => {
    setIsLoading(false);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      // a.download = `Touts_Data_${new Date().toDateString().replaceAll(" ", "_")}+_.xlsx`;
      a.download = `Touts_Data_.xlsx`;
      a.click();

      toast.success("File Download successfully");
    } else {
      toast.error("File download failed");
    }
  });
};

const handleExportBtn = async () => {
  downloadReport();
};

  useEffect(() => {
    getMainTableCards(1);
  }, []);
  

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
    
      {allowed_actions?.upload && (
        <Modal
          open={showNewUser}
          onClose={closeModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <h3>File Upload</h3>
          <Modal.Body>
            <p>Upload Report:</p>
            <Uploader
              action="/api/tout_data_upload"
              accept="application/ .xlx, .xlsx, .csv"
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
              onSubmit={onSubmitCloseModal}
              ref={uploader}
              draggable
              multiple
              onSuccess={(response) => {
                if (response?.detail) {
                  toast.success(response?.detail);
                  onSubmitCloseModal()
                  setTimeout(function () {
                    Router.reload();
                  }, 3000);
                }
              }}
              onError={async ({ response }, file, detail) => {
                await new Promise((resolve) => setTimeout(resolve, 1000));
                toast.error(response.detail);
                onSubmitCloseModal()
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
                // onSubmitCloseModal()
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
      {(allowed_page?.touts_details && allowed_actions?.view) && (
        <div className={styles.dashboard}>
         
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
          {loading && (
       <div className={styles.loadingPopup}>
       <div className={styles.loadingOverlay}></div>
       <div className={styles.loadingContent}>
      <div
        style={{
          position: "fixed",
          top: "55%",
          left: "60%",
          // transform: "translate(-50%, -50%)",
          zIndex: 9999, // Set an appropriate z-index value
        }}
      >
        <Loader /><br></br>
         Loading...
      </div>
      </div>
      </div>
    )}
            <Board
              heading="Touts Details"
              action={{ label: "File Upload", handler: openModal }}
              router={Router}
            />
            <FilterBar
            searchFilter={handleSearchClick}
            searchChange={(page_value) => handleSearchChange(page_value)}
            searchInputText={searchInputText}
            setSearchInputText={setSearchInputText}
            handleExportBtn={handleExportBtn}
            />

            <ThreatCards data={mainCardData} />

            <div className={styles.Pagination}>
              <Pagination
                prev
                next
                first
                last
                ellipsis
                boundaryLinks
                size="xs"
                maxButtons={5}
                limit={9}
                layout={["total", "-",  "|", "pager", "skip"]}
                pages={totalPages}
                activePage={currentPage}
                onChangePage={handlePageChange}
                total={totalRows}
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default ToutsDetails;
