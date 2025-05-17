// endpoint
const endPoint = process.env.API_ENDPOINT

// Import Libraries
import Image from 'next/image'
import { useEffect, useState, forwardRef, useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import Router, { useRouter }  from 'next/router'
import {
  Pagination,
  Modal,
  Button,
  Input,
  Whisper,
  Tooltip,
  Table,
  CheckPicker,
  Uploader,
} from 'rsuite'
const { Column, HeaderCell, Cell } = Table

import { DateRangePicker } from 'rsuite'
const { afterToday } = DateRangePicker

import { Circles } from 'react-loader-spinner';
import CloseIcon from '@rsuite/icons/Close';

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'
import FilterBar from '../../components/FilterBar'
import BrandMonitoringResult from '../../components/BrandMonitoringResult'
import { validateUserCookiesFromSSR } from '../../utils/userVerification'
import { toast } from 'react-toastify'

// Import Assets
import question from '../../public/static/images/questionmark.svg'

// Import Styles
import styles from './BrandMonitoring.module.scss'

// Import Store
import {
  changeFilterOption,
  initalizeData,
  initPageCount,
  changeSearchValue,
  changeSearchDate,
} from '../../store/slice/brandMonitoring'

import { enableImageModal } from '../../store/slice/ModalPopup'

const selectedOption = [
  { label: 'Low', value: 'Low' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Normal', value: 'Normal' },
  { label: 'High', value: 'High' },
  { label: 'Critical', value: 'Critical' },
]

const threatSourceOptions = [
  { label: 'Domain', value: 'Domain' },
  { label: 'Facebook', value: 'Facebook' },
  { label: 'Instagram', value: 'Instagram' },
  { label: 'Website', value: 'Website' },
  { label: 'Mobile Application', value: 'Mobile Application' },
  { label: 'Telegram', value: 'Telegram' },
  { label: 'Twitter', value: 'Twitter' },
  { label: 'Youtube', value: 'Youtube' }
];

const BrandMonitoring = () => {

  // Initialize the router to get the routing info of the page
  const router = useRouter();

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector((state) => state.persistedReducer.user_pages);
  const allowed_action = useSelector((state) => state.persistedReducer.user_actions);

  console.log(`Allowed Pages `, allowed_page);
  console.log(`Allowed Actions `, allowed_action);

  useEffect(() => {
    if (!allowed_page?.brand_monitoring) {
      router.push("/overview");
    }
  }, []);
  
  const CompactCell = (props) => <Cell {...props} />
  const dispatch = useDispatch()
  const [openModal, setOpenModal] = useState(false)
  const [openTakeDownModal, setopenTakeDownModal] = useState()
  // Get brand monitoring search text from the reducer.
  // const brandMonitoringSearchValue = useSelector((state) => state.brandMonitoring.searchValue)
  const [loading, setLoading] = useState(false)
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false);
  const [openTakeDownModalFirst, setOpenTakeDownModalFirst] = useState()
  // Initialise the date to be searched through the data, default is today's date.
  // const brandMonitoringDate = useSelector((state) => state.brandMonitoring.searchDate)
  const [searchClicked, setSearchClicked] = useState(false);
  const [ModalDateRange, setModalDateRange] = useState(null);

  //  New Section state start here ..
  const [takedownData, setTakedownData] = useState()
  const [searchTerm, setSearchTerm] = useState("");
  const [fileList, setFileList] = useState([]);
  const [mainPageData, setMainPageData] = useState([]);
  const uploader = useRef();
  const [takedownSeverity, setTakedownSeverity] = useState([]);
  const [takedownSource, setTakedownSource] = useState([]);

  const [takedownAction , setTakedownAction] = useState('');
  const [serialNumber, setSerialNumber] = useState(1);
  const [secondModalSerialNumber, setSecondModalSerialNumber] = useState(1);
  const [firstCardTotalPages, setFirstCardTotalPages] = useState(0);
  const [firstCardTotalRows, setFirstCardTotalRows] = useState(0);
  const [firstCardActivePage, setFirstCardActivePage] = useState(1);
  const [mainPageTotalPages, setMainPageTotalPages] = useState(0);
  const [mainPageTotalRows, setMainPageTotalRows] = useState(0);
  const [secondModalCurrentPage, setSecondModalCurrentPage] = useState(1);
  const [takedownInitiatedCount, setTakedownInitiatedCount] = useState();
  const [takedownCompleteCount, setTakedownCompleteCount] = useState();
  const [pageLoading, setPageLoading] = useState(false);
  const [isSearch, setIsSearch] = useState(false)
  const [searchDate, setSearchDate]= useState([])
  const [searchValue, setSearchValue]= useState('')


  // API Call '/api/bm_card_list'.
  const cardList = async (page_value, takedownAction) => {
    setLoading(true);
    const data = await fetch('/api/bm_card_list', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
        takedownAction:takedownAction,
        severity:takedownSeverity,
        threatSource:takedownSource,
        starting_date:
          ModalDateRange != null && ModalDateRange?.length != 0
            ? ModalDateRange[0].toISOString()
            : new Date(0),
        ending_date:
          ModalDateRange != null && ModalDateRange?.length != 0
            ? ModalDateRange[1].toISOString()
            : new Date(),
      }),
    }).then((response) => response?.json());
    setTakedownData(data?.data_list?.map((item) => JSON.parse(item)));
    setFirstCardTotalRows(data?.total_rows)
    setFirstCardTotalPages(data?.total_pages)
    setLoading(false);
    setSearchClicked(true);
  };


  // API Call/api/brandmon_list_all.
  const pagiFunc = async (page_value, searchDate, searchValue) => {
    setPageLoading(true)
    try {
    const data = await fetch('/api/brandmon_list_all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
        starting_date:
        searchDate != null && searchDate?.length != 0
          ? searchDate[0]
          : new Date(0),
          ending_date:
          searchDate != null && searchDate?.length != 0
          ? searchDate[1]
          : new Date(),
        search: searchValue,
      }),
    })
    const response = await data.json();
    setIsSearch(false)
    // setMainPageData(response?.data_list)
    setMainPageData(response?.data_list?.map((item) => JSON.parse(item)));
    setMainPageTotalRows(response?.total_rows);
    setMainPageTotalPages(response?.total_pages); 
    setTakedownInitiatedCount(response?.takedown_initiated)
    setTakedownCompleteCount(response?.takedown_completed)
  } catch (error) {
    console.error("Error fetching data:", error);
  }
  setPageLoading(true)
  }

  // Renders an Image component with a tooltip when hovered over.
  const CustomComponent = ({ placement }) => (
    // Whisper component: displays a popover or tooltip when triggered
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
        className={styles.questionmark + ' col'}
        alt="Explanation"
      ></Image>
    </Whisper>
  )

  // HandleSearch 
  const handleSearch = async() => {
    setIsSearch(true)
    await new Promise((resolve) => setTimeout(resolve, 4000));
    setPage(1)
    pagiFunc(1, searchDate, searchValue)
  }

  // HandlePageChange: User
  const handlePageChange = (page_value) => {
   setLoading(true);
    setPage(page_value)
    pagiFunc(page_value, searchDate, searchValue)
  }
  const handleModalOpen = () => {
    setOpenModal(true)
  }

  const handleModalClose = () => {
    setOpenModal(false);
    setFileList([]);
  }

  const handleTakeDownModalClose = () => {
    setopenTakeDownModal(false);
    setSecondModalSerialNumber(1)
    resetModal();
  }

  const downloadReport = async(takedownAction) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    fetch('/api/bm_card_list_download', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        takedownAction:takedownAction,
        severity:takedownSeverity,
        threatSource:takedownSource,
        starting_date:
          ModalDateRange != null && ModalDateRange?.length != 0
            ? ModalDateRange[0].toISOString()
            : new Date(0),
        ending_date:
          ModalDateRange != null && ModalDateRange?.length != 0
            ? ModalDateRange[1].toISOString()
            : new Date(), 
      }),
    }).then(async(response) => {
     if(response.ok) {
      const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${takedownAction}_${new Date().toDateString().replaceAll(" ", "_")}.xlsx`
        // document.body.appendChild(a);
        a.click();
        // document.body.removeChild(a);
        toast.success("File Download successfully");
      } else {
       
        toast.error("File Download Failed!");
      }
    })
      setIsLoading(false);
    }

    //  Takedown Initiated code start here..
    const handleExport = () => {
      downloadReport(takedownAction)
    }

    const handleModalSearchFirst = () => {
      setOpenTakeDownModalFirst(true);
      setLoading(true);
      // setTakedownAction('Takedown Initiated');
      const getTakedownAction = 'Takedown Initiated';
      setTakedownAction(getTakedownAction);
      cardList(page,getTakedownAction, takedownAction, takedownSeverity, takedownSource);
    };

    const handleCardModalFirst = (page_value, status) => {
      setOpenTakeDownModalFirst(true);
      setLoading(true);
      setFirstCardActivePage(1)
      const getTakedownAction = 'Takedown Initiated';
      setTakedownAction(getTakedownAction);
      cardList(page_value, getTakedownAction);
    };
  
    const handleFirstCardPageChange = (page_value) =>{
      setLoading(true);
      setFirstCardActivePage(page_value)
      const getTakedownAction = 'Takedown Initiated';
      setTakedownAction(getTakedownAction);
      setSerialNumber((page_value - 1) * 10 + 1);
      cardList(page_value,getTakedownAction, takedownAction, takedownSeverity, takedownSource);
    }
  const handledateRangerange = () => {
    setModalDateRange;
  }

  // takedown complete moda functions started

  const handleCardModal = (page_value, status) => {
    setopenTakeDownModal(true);
    setLoading(true);
    setSecondModalCurrentPage(page_value)
    const getTakedownAction = 'Takedown Completed';
    setTakedownAction(getTakedownAction);
    cardList(page_value, getTakedownAction);
  };

  const secondModalSearch = (page) => {
    setLoading(true);
    setSecondModalCurrentPage(1)
    const getTakedownAction = 'Takedown Completed';
    setTakedownAction(getTakedownAction);
    cardList(page,getTakedownAction, takedownAction, takedownSeverity, takedownSource);
  };

  const handletakedownPageChange = (page_value) => {
    setLoading(true);
    setSecondModalCurrentPage(page_value);
    const getTakedownAction = 'Takedown Completed';
    setTakedownAction(getTakedownAction);
    setSecondModalSerialNumber((page_value - 1) * 10 + 1);
    cardList(page_value,getTakedownAction, takedownAction, takedownSeverity, takedownSource);
  }
 
   // This function open a takedown modal .
   const handleTakeDownModalCloseFirst = () => {
    setOpenTakeDownModalFirst(false);
    setSerialNumber(1);
    resetModal();
  }

const handleSearchChange = (value) => {
    setSearchTerm(value);
  };

  const closeModal = () =>{
    setOpenTakeDownModalFirst(false)
    setOpenModal(false)
    setFileList([]);
  }

  const resetModal = () =>{
    setModalDateRange(null)
    setTakedownSeverity([])
    setTakedownSource([])
    setModalDateRange(null)
  }

  useEffect((page_value,searchValue) => {
    pagiFunc(1, page_value, searchValue)
  }, [])

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
      {/* UPLOAD Modal Starts */ }
      {allowed_action?.upload && (
        <Modal
          keyboard={false}
          open={openModal}
          onClose={handleModalClose}
          className={styles.modal}
          backdrop='static'
        >
         <CloseIcon onClick={()=> closeModal()} className={styles.clear}/>
          {/* <Modal.Header>
            <Modal.Title>Request a custom takedown!</Modal.Title>
          </Modal.Header> */}
          <h3>Request a custom takedown!</h3>
          <Modal.Body>
            File Upload:
            <Uploader
              action="/api/brandmon-upload-file"
              onError={({ response }, detail) => {
                if (detail.status != 200) {
                  toast.error(response.detail);
                }
                closeModal();
              }}
              onSuccess={(response, detail, status) => {
                if (detail.status === "finished") {
                  toast.success("File uploaded successfully.");
                }
                closeModal();
                closeModal();
                setTimeout(function () {
                  Router.reload();
                }, 4000);
              }}
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
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
              disabled={!fileList.length}
              onClick={() => {
                uploader.current.start();
              }}
              appearance="primary"
            >
              Submit
            </Button>
            <Button onClick={handleModalClose} appearance="subtle">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}
      
      {/* MODAL: Takedown Complete */}
      {allowed_action?.view && (
        <Modal 
          keyboard={false}
          size="full"
          open={openTakeDownModal}
          onClose={handleTakeDownModalClose}
          // className={styles.modal}
          backdrop='static'
        >
        <CloseIcon onClick={()=> handleTakeDownModalClose()} className={styles.clear}/>
          <h3>Takedown Complete!</h3>
          <div className={styles.mainActionDiv}>
                <div className={styles.subActionDiv}>
                <label className={styles.label1}>Severity:</label>
                <CheckPicker
                searchable={false}
                  placeholder="Severity"
                  data={selectedOption.map((option) => ({
                    value: option.value,
                    label: option.label
                  }))}
                  value={takedownSeverity}
                  onChange={(value) => setTakedownSeverity(value, 'takedownSeverity')}
                  style={{ marginBottom: '20px', width: 180 }}
                />
                  <label className={styles.label}>Threat Source:</label>
                  <CheckPicker
                  searchable={false}
                  placeholder="Threat Source"
                  data={threatSourceOptions?.map((option) => ({
                    value: option?.value,
                    label: option?.label
                  }))}
                  value={takedownSource}
                  onChange={(value) =>  setTakedownSource(value)} 
                  style={{ marginBottom: '20px', marginLeft: '20px', width: 180 }}
                />

              <DateRangePicker
                isoWeek
                disabledDate={afterToday()}
                value={ModalDateRange}
                onChange={(newvaluedate) => setModalDateRange(newvaluedate)}
                format="dd-MM-yyyy"
                style={{  width:"14rem" , marginLeft: '20px',  marginBottom: '20px'}}
                >
                </DateRangePicker>
              </div>
              </div>
              <div className={styles.mainModalCalenderBtn}>
                <div className={styles.subModalCalenderBtn}>
              <Button
                appearance="primary"
                style={{ width: 120}}
                // onClick={()=>handleModalSearch()}
                onClick={()=>secondModalSearch(page,takedownAction, takedownSeverity, takedownSource)}
              >
                Search
              </Button>
              </div>
              </div>
          <Modal.Body>
        
            <Table
              virtualized
              loading={loading}
              bordered
              cellBordered
              rowHeight={45}
              autoHeight={1}
              data={takedownData}
            >
              <Column fullText  minWidth={50} flexGrow={0.2} >
                    <HeaderCell className={styles.modalHeader}>#</HeaderCell>
                    {/* <Cell>{(rowData, rowIndex) => serialNumber + rowIndex}</Cell> */}
                    <Cell>{(rowData, rowIndex) => {
                      return secondModalSerialNumber + rowIndex;
                    }}</Cell>
                  </Column>
                  <Column fullText minWidth={100} flexGrow={0.4}>
                    <HeaderCell className={styles.modalHeader}>Severity</HeaderCell>
                    <Cell dataKey='Severity'/>              
                  </Column>
              <Column width={100} fullText  flexGrow={0.6}>
                <HeaderCell className={styles.modalHeader}>Threat Source</HeaderCell>
                <CompactCell dataKey="threatSource" />
              </Column>
            
                  <Column fullText  minWidth={100} flexGrow={0.8}>
                    <HeaderCell className={styles.modalHeader}>Link</HeaderCell>
                    <Cell dataKey='Link'/>
                  </Column>
                  <Column fullText  minWidth={100} flexGrow={0.6}>
                    <HeaderCell className={styles.modalHeader}>Requested Date</HeaderCell>
                    <Cell>
                          {(rowData) => {
                            return rowData.requestedDate != undefined
                              ? new Date(rowData.requestedDate.$date).toDateString()
                              : null
                          }}
                        </Cell>
                  </Column>
                  <Column fullText minWidth={100} flexGrow={0.4}>
                    <HeaderCell className={styles.modalHeader}>Present Status</HeaderCell>
                    <Cell>{(rowData) => {
                      const presentStatus = rowData.presentStatus;
                      if (presentStatus === 'Processing') {
                        return <span className={styles.processStyle}>Processing...</span>;
                      } else {
                        return presentStatus;
                      }
                    }}</Cell>
                  </Column>

                  <Column fullText  minWidth={100} flexGrow={0.8}>
                    <HeaderCell className={styles.modalHeader}>Remarks </HeaderCell>
                    <CompactCell dataKey='Remarks'/>
                  </Column>
            </Table>
          </Modal.Body>
          <div>
              <Pagination
                prev
                next
                first
                last
                ellipsis
                boundaryLinks
                maxButtons={5}
                limit={[10]}
                size="xs"
                layout={['total', "-", '|', 'pager', 'skip']}
                pages={firstCardTotalPages}
                total={firstCardTotalRows}
                activePage={secondModalCurrentPage}
                onChangePage={(page_value)=> handletakedownPageChange(page_value, takedownAction, takedownSeverity, takedownSource)}
              />
            </div>
          <Modal.Footer className={styles.tableFooter}>
            <Button
              onClick={() => downloadReport(takedownAction)} 
              appearance="primary"
            >
              Export
            </Button>
            <Button onClick={handleTakeDownModalClose} appearance="subtle">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}
      
      {/* MODAL: Takedown Initiated */}
      {allowed_action?.view && (
        <Modal 
          keyboard={false}
          size="full"
          open={openTakeDownModalFirst}
          onClose={handleTakeDownModalCloseFirst}
          backdrop='static'
        >
          <CloseIcon onClick={()=> handleTakeDownModalCloseFirst()} className={styles.clear}/>
          <h3>Takedown Initiated!</h3>
          <div className={styles.mainActionDiv}>
            <div className={styles.subActionDiv}>
            <label className={styles.label1}>Severity:</label>
            <CheckPicker
            searchable={false}
              placeholder="Severity"
              data={selectedOption.map((option) => ({
                value: option.value,
                label: option.label
              }))}
              value={takedownSeverity}
              onChange={(value) => setTakedownSeverity(value, 'takedownSeverity')}
              style={{ marginBottom: '20px', width: 180 }}
            />
              <label className={styles.label}>Threat Source:</label>
              <CheckPicker
              searchable={false}
              placeholder="Threat Source"
              data={threatSourceOptions?.map((option) => ({
                value: option?.value,
                label: option?.label
              }))}
              value={takedownSource}
              onChange={(value) =>  setTakedownSource(value)} 
              style={{ marginBottom: '20px', marginLeft: '20px', width: 180 }}
            />
              <DateRangePicker
                  isoWeek
                  disabledDate={afterToday()}
                  value={ModalDateRange}
                  placement="leftStart"
                  onChange={(newvaluedate) => setModalDateRange(newvaluedate)}
                  format="dd-MM-yyyy"
                  style={{  width:"14rem" , marginLeft: '20px',  marginBottom: '20px'}}
                >
                </DateRangePicker>
            </div>
            </div>
            <div className={styles.mainModalCalenderBtn}>
              <div className={styles.subModalCalenderBtn}>
                
                <Button
                  appearance="primary"
                  style={{ width: 120}}
                  onClick={()=>handleModalSearchFirst(page,takedownAction, takedownSeverity, takedownSource)}
                  className={styles.modalSearchBtn}
                >
                  Search
                </Button>
                </div>
              </div>
          <Modal.Body>
            <Table
                virtualized
                loading={loading}
                bordered
                cellBordered
                rowHeight={45}
                autoHeight={1}
                data={takedownData}
            >
              <Column fullText  minWidth={20} flexGrow={0.2} >
                <HeaderCell className={styles.modalHeader}>#</HeaderCell>
                {/* <Cell>{(rowData, rowIndex) => serialNumber + rowIndex}</Cell> */}
                <Cell>{(rowData, rowIndex) => {
                  return serialNumber + rowIndex;
                }}</Cell>
              </Column>
              <Column fullText  minWidth={120} flexGrow={0.6}>
                <HeaderCell className={styles.modalHeader}>Threat Source</HeaderCell>
                <Cell dataKey='threatSource'/>
              </Column>
              <Column fullText minWidth={100} flexGrow={0.5}>
                <HeaderCell className={styles.modalHeader}>Severity</HeaderCell>
                <Cell dataKey='Severity'/>              
              </Column>
              <Column fullText  minWidth={130} flexGrow={1.2}>
                <HeaderCell className={styles.modalHeader}>Link</HeaderCell>
                <Cell dataKey='Link'/>
              </Column>
              <Column fullText  minWidth={100} flexGrow={0.6}>
                <HeaderCell className={styles.modalHeader}>Requested Date</HeaderCell>
                <Cell>
                      {(rowData) => {
                        return rowData.requestedDate != undefined
                          ? new Date(rowData.requestedDate.$date).toDateString()
                          : null
                      }}
                    </Cell>
              </Column>
              <Column fullText  minWidth={100} flexGrow={0.5}>
                <HeaderCell className={styles.modalHeader}>Present Status</HeaderCell>
                <Cell>{(rowData) => {
                  const presentStatus = rowData.presentStatus;
                  if (presentStatus === 'Processing') {
                    return <span className={styles.processStyle}>Processing...</span>;
                  } else {
                    return presentStatus;
                  }
                }}</Cell>
              </Column>
              <Column fullText  minWidth={100} flexGrow={0.8}>
                <HeaderCell className={styles.modalHeader}>Remarks </HeaderCell>
                <Cell dataKey='Remarks'/>
              </Column>
            </Table>

            {/* </div> */}
            
          </Modal.Body>
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
                pages={firstCardTotalPages}
                total={firstCardTotalRows}
                activePage={firstCardActivePage}
                onChangePage={(page_value) =>
                  handleFirstCardPageChange(page_value, takedownAction, takedownSeverity, takedownSource)
                }
              />
            </div>
          <Modal.Footer className={styles.tableFooter}>

            <Button
              appearance="primary"
              onClick={() => handleExport()}
            >
              Export
            </Button>
            <Button onClick={() => closeModal()} appearance="subtle">
              Close
            </Button>
          </Modal.Footer>
        </Modal>
      )}
      
      {/* MAIN PAGE: Brand Monitoring */}
      {allowed_page?.brand_monitoring && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <Board
              heading="Brand Monitoring"
              router={Router}
              action={{
                label: 'Upload File',
                handler: handleModalOpen,
              }}
            />
            <FilterBar
              changeOptions={changeFilterOption}
              pageSource="Overview"
              changeDate={changeSearchDate}
              valuedate={searchDate}
              searchValue={searchValue}
              setSearchValue={setSearchValue}
              searchDate={searchDate}
              setSearchDate={setSearchDate}
              onsearch={handleSearch}
              setIsSearch={setIsSearch}
              pageLoading={pageLoading}
              onclear={() => Router.reload()}
              dispatch={dispatch}
            />
            <div className={styles.cardsRow + ' row mb-3'}>
              <div
                onClick={() => handleCardModalFirst(page, 'Takedown Initiated')}
                className={styles.cardTwo + ' card align-items-center mx-auto'}
              >
                <p className="m-b-0">{takedownInitiatedCount}</p>
                <h6 className="m-b-20">Takedown Initiated</h6>
              </div>

              <div
                onClick={() => handleCardModal(page, 'Takedown Completed')}
                className={styles.cardThree + ' card align-items-center mx-auto'}
              >
                <p className="m-b-0">{takedownCompleteCount}</p>
                <h6 className="m-b-20">Takedown Completed</h6>
              </div>
            </div>

            <div className="keyword-responseult">
              {isSearch ? (
                  <div className={styles.loader_container}>
                    <div className={styles.loader} />
                  </div>
                
              ) : (
                <div className={styles.brandMonitoringGrid + ' grid mx-auto'}>
                  {/* mainPageData */}
                  {mainPageData && mainPageData?.map((data) => {
                    return data != null ? (
                      <div
                        className={styles.brandMonitoringCardWrapper + ' g-col-6'}
                      >
                        <BrandMonitoringResult
                          data={data}
                        />
                      </div>
                    ) : (
                      <></>
                    )
                  })}
                </div>
              )}
              
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
                  limit={[10]}
                  layout={['total', '-', '|', 'pager', 'skip']}
                  pages={mainPageTotalPages}
                  total={mainPageTotalRows}
                  activePage={page}
                  onChangePage={handlePageChange}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default BrandMonitoring

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res)
}
