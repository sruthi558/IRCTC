// endpoint
const endPoint = process.env.API_ENDPOINT;

// Import Libraries
import Image from "next/image";
import { useEffect, useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import Router, { useRouter } from "next/router";
import { toast } from "react-toastify";

import {
  Table,
  Pagination,
  DateRangePicker,
  SelectPicker,
  Input,
  Icon,
  CheckPicker,
} from "rsuite";
const { Column, HeaderCell, Cell } = Table;
import {
  Button,
  Modal,
  Uploader,
  DatePicker,
  Tooltip,
  Whisper,
  IconButton,
} from "rsuite";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";

// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import PiApexChart from "../../components/PiChart.jsx";
import LineApexChart from "../../components/LineApexCharts";

// Import Assets
import question from "../../public/static/images/questionmark.svg";
import { Circles } from "react-loader-spinner";
import CloseIcon from "@rsuite/icons/Close";

// Import Styles
import styles from "./InfrastructureMonitoring.module.scss";

// Import Store
import { initData, initPageCount } from "../../store/slice/inframon";
const { afterToday } = DateRangePicker;

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement, tooltip }) => (
  // Whisper: UI Component that displays popover or tooltip
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

const monthOptions = [
  { value: "January", label: "January" },
  { value: "February", label: "February" },
  { value: "March", label: "March" },
  { value: "April", label: "April" },
  { value: "May", label: "May" },
  { value: "June", label: "June" },
  { value: "July", label: "July" },
  { value: "August", label: "August" },
  { value: "September", label: "September" },
  { value: "October", label: "October" },
  { value: "November", label: "November" },
  { value: "December", label: "December" },
];

const ModalDetailMonths = [
  { value: "January", label: "January" },
  { value: "February", label: "February" },
  { value: "March", label: "March" },
  { value: "April", label: "April" },
  { value: "May", label: "May" },
  { value: "June", label: "June" },
  { value: "July", label: "July" },
  { value: "August", label: "August" },
  { value: "September", label: "September" },
  { value: "October", label: "October" },
  { value: "November", label: "November" },
  { value: "December", label: "December" },
];

const ModalDetailSeverity = [
  // { value: "All", label: "All" },
  { value: "Critical", label: "Critical" },
  { value: "High", label: "High" },
  { value: "Medium", label: "Medium" },
  { value: "Low", label: "Low" },
  { value: "Informative", label: "Informative" },
];

// const mainTableYears = [
//   { label: "2022", value: "2022" },
//   { label: "2023", value: "2023" },
// ];

// const years = [
//   { label: "2022", value: "2022" },
//   { label: "2023", value: "2023" },
// ];

// InfrastructureMonitoring Component
const InfrastructureMonitoring = () => {
  // Initialising the router
  const router = useRouter();

  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_actions = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  useEffect(() => {
    if (!allowed_page?.infrastructure_monitoring) {
      router.push("/overview");
    }
  }, []);

  // Initialise the dispatcher.
  const dispatch = useDispatch();
  // userRole contains the role of the user currently logged in for role-based restrictions.
  const userRole = useSelector((state) => state.persistedReducer.role);
  // infraData contains the default booking data for when the user navigates back to the same page.
  const infraData = useSelector((state) => state.inframon.data);
  // This state variable is used to determine whether to show a form or UI for creating a new user.
  const [showNewUser, setShowNewUser] = useState(false);
  // This is another piece of data from the Redux store that contains the total number of pages for the user IDs.
  const infraPageCount = useSelector((state) => state.inframon.pageCount);
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false);
  const [resolutionActionStatus, setResolutionActionStatus] = useState(0);
  const [modelValueDate, setModelValueDate] = useState();
  // uploadingFileList holds the list of file that has been selected to be uploaded.
  const [fileList, setFileList] = useState([]);
  // Declare a reference to the Upload component for tracking the files in a persistant manner across reloads.
  const uploader = useRef();
  // This state variable determines the number of items to display per page.
  const [limit, setLimit] = useState(10);
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1);
  //   CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: "blue" }} />;

  // handleTakeDownModalClose
  const handleTakeDownModalClose = () => {
    setTakeDownModal(false);
  };

  // modalVuln is a state variable that holds the vulnerability data for the "Take Down Modal".
  const [modalVuln, setModalVuln] = useState("");

  // handleTakeDownModalOpen is a function that sets modalVuln state to the selected vulnerability,
  const handleTakeDownModalOpen = (vuln) => {
    setModalPageSecondCurrent(1);
    setModalVuln(vuln);
    modalCall(1, vuln);
    setOpenTakeDownModalSecond(true);
  };

  // determine Resoltion Action button text based on current status
  let buttonText;
  switch (resolutionActionStatus) {
    case 0:
      buttonText = "Assign to IRCTC";
      break;
    case 1:
      buttonText = "Assign to Pinaca";
      break;
    case 2:
      buttonText = "Mark as Resolved";
    default:
      buttonText = "";
  }

  // infraModalData is a state variable that holds the data for the infrastructure modal.
  const [infraModalData, setInfraModalData] = useState([]);
  // pageModal is a state variable that holds the current page number for the infrastructure modal.
  const [pageModal, setPageModal] = useState(1);
  // statusVuln is a state variable that holds the statusVuln value for the status call.
  const [statusVuln, setStatusVuln] = useState("");
  // monthCount is a state variable that holds the monthCount value for the month Count in pi-chart.
  const [monthCount, setMonthCount] = useState({});
  // vulnCount is a state variable that holds the vulnCount value for the month Count in pi-chart.
  const [vulnCount, setVulnCount] = useState();
  // notInfo is a state variable that holds the notInfo value for the month Count in pi-chart.
  const [notInfo, setNotInfo] = useState();
  // totalVuln is a state variable that holds the totalVuln value for the month Count in pi-chart.
  const [totalVuln, setTotalVuln] = useState();
  //This state defines a new state variable named "vulnChart" and sets its initial value to an empty array.
  const [vulnChart, setVulnChart] = useState([]);
  //This state defines a new state variable named "openVuln" and sets its initial value to 0.
  const [openVuln, setOpenVuln] = useState(0);

  // Initialise the date to be searched through the data.
  const infraDate = useSelector((state) => state.inframon.searchDate);

  // Initialise the filters to be used while searching through the data.
  const filterOverviewOptions = useSelector(
    (state) => state.inframon.filterOption
  );
  const [modalLimit, setModalLimit] = useState(10);
  const [modalPage, setModalPage] = useState(1);
  const [modalPageCount, setModalPageCount] = useState(10);

  // /First PieChart states start here --------------------------
  const [openTakeDownModal, setTakeDownModal] = useState(false);
  const [pieApexFirstPage, setPieApexFirstPage] = useState(10);
  const [PieApexFirstCurrentPage, setPieApexFirstCurrentPage] = useState(1);
  const [pieApexModalPageNumber, setPieApexModalPageNumber] = useState(10);
  const [modalLimitFirst, setModalLimitFirst] = useState(10);

  // /First PieChart states ends here --------------------------

  // /Second LineApecChart states start here --------------------------
  const [openTakeDownModalSecond, setOpenTakeDownModalSecond] = useState(false);
  const [pieApexSecondPage, setPieApexSecondPage] = useState(10);
  const [pieApexModalSecondPageNumber, setPieApexModalSecondPageNumber] =
    useState(10);
  // /Second LineApecChart states Ends  here --------------------------

  // /Second LineApecChart states start here --------------------------
  const [infraOpen, setInfraOpen] = useState(false);
  const [linePage, setLinePage] = useState(1);
  const [totalPages, setTotalPages] = useState(10);
  const [infraLineModalData, setInfraLineModalData] = useState([]);

  const [barApexModalPageNumber, setBarApexModalPageNumber] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [secondModalpage, setSecondModalpage] = useState(10);
  // /Second LineApecChart states Ends here --------------------------

  //  const infraData = [...];
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredData, setFilteredData] = useState(infraData);
  const [isLoading, setIsLoading] = useState(false);
  const [modalPageSecondCurrent, setModalPageSecondCurrent] = useState(1);
  const [modalLimitSecond, setModalLimitSecond] = useState(10); // Set your desired limit
  const [paginationMonth, setPaginationMonth] = useState(null);

  //First PieApexChart Modal pagination display total row and total pages there states
  const [totalRowsFirstPieChart, setTotalRowsFirstPieChart] = useState(0);
  const [totalPagesFirstPieChart, setTotalPagesFirstPieChart] = useState(0);

  //Second PieApexChart Modal pagination display total row and total pages there  states
  const [totalRowsSecondPieChart, setTotalRowsSecondPieChart] = useState(0);
  const [totalPagesSecondPieChart, setTotalPagesSecondPieChart] = useState(0);

  //Second LineApexChart Modal pagination display total row and total pages and there states
  const [totalRowsSecondLineChart, setTotalRowsSecondLineChart] = useState(0);
  const [totalPagesSecondLineChart, setTotalPagesSecondLineChart] = useState(0);

  //Main Table pagination display total rows and total pages and there states
  const [totalRowsMainPage, setTotalRowsMainPage] = useState(0);
  const [totalPagesMainPage, setTotalPagesMainPage] = useState(0);

  // vernability section states
  const [mainPageLoader, setMainPageLoader] = useState(false);
  const [mainTableData, setMainTableData] = useState([]);
  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [detailModalData, setDetailModalData] = useState([]);
  const [pageNumber, setPageNumber] = useState(1);
  const [selectedRowMonth, setSelectedRowMonth] = useState("");
  const [totalRowsDetailModal, setTotalRowsDetailModal] = useState(0);
  const [totalPagesDetailModal, setTotalPagesDetailModal] = useState(0);
  const [detailModalCurrentPage, setDetailModalCurrentPage] = useState(1);
  const [selectedSeverity, setSelectedSeverity] = useState([]);

  // Year month Picker states
  const [selectedMonth, setSelectedMonth] = useState("All");
  const [mainTableSelectedYear, setMainTableSelectedYear] = useState("");
  const [monthYear, setMonthYear] = useState("");
  const [years, setYears] = useState([]);

  const modalCall = async (page_value, vuln) => {
    const response = await fetch("/api/infra_mon_find", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_number: page_value,
        risk_severity_of_vulnerabilities: [vuln],
      }),
    });
    const data = await response.json();
    setInfraModalData(data.data_list.map((item) => JSON.parse(item)));
    setTotalRowsSecondPieChart(data?.total_rows); // Set the total rows
    setTotalPagesSecondPieChart(data?.total_pages); // Set the total pages
    setLoading(false);
  };

  const handlePageModalChange = (dataKey) => {
    if (modalVuln === "Vuln") {
      otherModalCall(dataKey, statusVuln);
    } else {
      modalCall(dataKey, modalVuln);
    }
    setModalPageSecondCurrent(dataKey, modalVuln); // Update the current page
    setModalLimitSecond(dataKey, modalVuln); // Reset the limit if needed
  };

  // API Call'/api/infra_mon_find'.
  const otherModalCall = async (page_value, status_up) => {
    const data = await fetch("/api/infra_status_find", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_number: page_value,
        status: [status_up],
      }),
    }).then((res) => res.json());

    setInfraModalData(data.data_list.map((item) => JSON.parse(item)));
    setTotalRowsFirstPieChart(data?.total_rows);
    setTotalPagesFirstPieChart(data?.total_pages);

    const totalPages = Math.ceil(data.page_count / pieApexFirstPage);
    setPieApexModalPageNumber(totalPages);

    if (page_value > totalPages) {
      setPieApexFirstCurrentPage(totalPages);
    } else {
      setPieApexFirstCurrentPage(page_value);
    }

    setLoading(false);
  };

  const handleModalFirstPiePageChange = (page_value, status_up) => {
    setPieApexFirstPage(page_value, status_up);
    setPieApexFirstCurrentPage(page_value, status_up);

    // Determine the status based on the status_up value
    // const status = status_up === "Vulnerabilities Open" &&  "Vulnerabilities Resolved" ? true : false;
    const status = statusVuln === "Vulnerabilities Open" ? true : false;

    // Pass the determined status to otherModalCall
    otherModalCall(page_value, status);
  };

  const handleStatusCall = (vuln) => {
    setStatusVuln(vuln);
    setPieApexFirstPage(1);
    setPieApexFirstCurrentPage(1);

    // Determine the status based on the selected vulnerability
    const status = vuln === "Vulnerabilities Open" ? true : false;

    // Pass the determined status to otherModalCall
    otherModalCall(1, status);

    // Show the take down modal
    setTakeDownModal(true);
  };

  // Available filter options for this page.
  const options = [
    "Vulnerabilities Discovered",
    "Vulnerabilities Patched",
    "Vulnerabilities Open",
  ].map((item) => ({ label: item, value: item }));

  // API Call /api/infra_mon_find'.
  const pagiFunc = async (page_value, searchTerm, limit_value) => {
    const data = await fetch("/api/infra_mon_find", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_number: page_value,
        search: searchTerm,
      }),
    }).then((res) => res.json());

    dispatch(initData(data?.data_list?.map((item) => JSON.parse(item))));
    setTotalRowsMainPage(data?.total_rows); // Set the total rows
    setTotalPagesMainPage(data?.total_pages); // Set the total pages
    setLoading(false);
  };

  // Fetch data from the '/api/infra_mon_trend' API endpoint
  const chartData = async () => {
    const data = await fetch("/api/infra_mon_trend").then((res) => res.json());
    setVulnCount(data["VULN_COUNT"]);
    let keys = Object?.keys(data["MONTH_COUNT"]);
    // keys = typeof(data) === 'object' && Object.keys(data).length > 1 && Object.keys(data['MONTH_COUNT'])
    // console.log(`Keys_Console: ${keys}`);
    let sortedMonths = keys?.sort((a, b) => new Date(a) - new Date(b)); // Sort months chronologically
    // console.log(`sortedMonths: ${sortedMonths}`);
    let last5Months = sortedMonths?.slice(-5); // Select the last 5 months
    console.log(`last5Months: ${last5Months}`);
    // console.log(last5Months);
    let values = last5Months?.map((month) => data["MONTH_COUNT"][month]);
    var obj = { keys: last5Months, values: values };
    setMonthCount(obj);
    // Set the total vulnerabilities state variable based on the 'TOTAL' key in the response.
    setTotalVuln(data["TOTAL"]);
    // Set the not info state variable based on the 'NOT_INFO' key in the response.
    setNotInfo(data["NOT_INFO"]);
    // Set the loading state to false once the data has been fetched and processed.
    setLoading(false);
  };

  // * Takes in an object of data and returns an array of the top 10 items sorted in descending order by their value.
  const sortChartData = (data) => {
    const chartData = Object.entries(data)?.map(([key, value]) => ({
      key,
      value,
    }));
    chartData.sort((a, b) => b.value - a.value);
    // Return the top 10 items in the sorted array.
    return chartData.slice(0, 10);
  };

  const chart_vuln_cat = async () => {
    const data = await fetch("/api/infra_chart_vuln").then((res) => res.json());
    setVulnChart(sortChartData(data?.data_list));
  };

  const openCount = async () => {
    const data = await fetch("/api/infra_open_count").then((res) => res.json());

    setOpenVuln(data["open_count"]);
  };

  // HandleSearch
  const handleSearch = () => {
    setLoading(true);
    OverviewSearchDate(overviewDate, filterOverviewOptions);
  };

  // HandlePageChange
  const handlePageChange = (dataKey) => {
    setPage(dataKey);
    pagiFunc(dataKey, searchTerm);
    // handleSearchChange(searchTerm, dataKey);
  };

  // This function will be called when the user selects a new limit in the limit dropdown,
  // and will update the page state to 1, the limit state to the selected limit, and call,
  // the pagiFunc function with page 1 and the new limit.

  const handleChangeLimit = (dataKey) => {
    setPage(1);
    setLimit(dataKey);
    pagiFunc(1, dataKey, searchTerm);
  };

  const downloadHandler = () => {
    console.log(1);
  };

  // Function to close the modal
  const closeModal = () => {
    setShowNewUser(false);
  };

  // Function to open Modal
  const openModal = () => {
    console.log(showNewUser);
    setShowNewUser(true);
  };

  // API Call: /api/infra_change_vuln_status
  const changeVulnStatus = async (id, status_new) => {
    const data = await fetch("/api/infra_change_vuln_status", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cellid: id,
        status: resolutionActionStatus,
      }),
    }).then((res) => res.json());

    // update status and button text
    if (resolutionActionStatus === 2) {
      setResolutionActionStatus(0);
    } else {
      setResolutionActionStatus(resolutionActionStatus + 1);
    }

    // If the status is successfully changed, it displays a success message using toast.
    if (data["msg"] == "Changed Status") {
      toast.success("Issue Status Change and Notified to Pinaca");
    } else {
      // If not, it displays an error message.
      toast.error("Please try again!");
    }

    // Finally, it updates the page and pagination and gets the latest issue count
    setPage(1);
    pagiFunc(1, searchTerm);
    openCount();
  };
  const handleModalPageChange = (dataKey) => {
    setModalPage(dataKey);
    otherModalCall(dataKey);
  };
  const handleChangeModalLimit = (dataKey) => {
    setModalPage(1);
    setModalLimit(dataKey);
    otherModalCall(1, dataKey);
  };

  const handleTakeDownModalCloseSecond = () => {
    setOpenTakeDownModalSecond(false);
  };

  const handleModalPageChangeSecond = (dataKey) => {
    modalPageSecondCurrent(1);
    setModalPageSecond(dataKey);
    modalCall(1, dataKey, modalLimitSecond); // Fetch data with the new page number
  };

  const handleChangeModalLimitSecond = (dataKey) => {
    setModalPageSecondCurrent(1);
    setModalLimitSecond(dataKey);
    modalCall(1, modalVuln, dataKey); // Update with the correct vuln value
  };

  const fetchData = async (page_value, month) => {
    setLoading(true);

    const response = await fetch("/api/infra_month_data", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_number: page_value,
        month: month,
      }),
    });

    const data = await response.json();
    setInfraLineModalData(data.data_list.map((item) => JSON.parse(item)));
    setTotalRowsSecondLineChart(data?.total_rows);
    setTotalPagesSecondLineChart(data?.total_pages);
    setPaginationMonth(month); // seted updated clicked month in this state.
    setLoading(false);
  };

  const handleVulnerabilityModalFirstopen = (page_value, month) => {
    setInfraOpen(true);
    setSelectedMonth(month);
    setPaginationMonth(month); // Set the pagination month
    fetchData(1, page_value, month); // Fetch data for the selected month
    setLinePage(1);
    setCurrentPage(1);
  };

  const handleModalPageChangeLine = (page_value, month) => {
    setSecondModalpage(page_value);
    fetchData(page_value, month); // Fetch data for paginationMonth
    setCurrentPage(page_value);
  };

  const handleLineModalCloseFunc = () => {
    setInfraOpen(false);
  };

  const handleMonthSelect = (value) => {
    setSelectedMonth(value);
    fetchData(1, value);
    setSecondModalpage(1);
    setCurrentPage(1);
  };

  const handleVulnerabilityModalSecondopen = () => {
    setInfraOpen(false);
  };

  const downloadReport = async (search) => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const response = await fetch("/api/export_infra", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          search: searchTerm,
        }),
      });

      if (response.ok) {
        // File download successful
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download =
          "infra_list" +
          new Date().toDateString().replaceAll(" ", "_") +
          ".xlsx";
        a.click();

        toast.success("File downloaded successfuly !", {
          position: "top-center",
          autoClose: 2000, // 3 seconds
        });
      } else {
        // File download failed
        toast.error(
          "Error while downloading the file. Please try again later.",
          {
            position: "top-center",
            autoClose: 2000, // 4 seconds
          }
        );
      }
    } catch (error) {
      // Error while making the API request
      toast.error("An error occurred while processing your request.", {
        position: "top-center",
        autoClose: 2000, // 4 seconds
      });
    }
  };

  const handleExport = async () => {
    setIsLoading(true);

    try {
      await downloadReport();
    } catch (error) {
      console.error("Error occurred while downloading the VPS export:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchChange = (value) => {
    setSearchTerm(value);
  };

  const handleSearchFunc = (page_value) => {
    pagiFunc(1, searchTerm, page_value);
    setPage(1);
  };

  // vulnerability main Table and Modal code start Here
  const MainErrorText = "Please Select Year..";

  const detailHistoryModalData = async (
    pageNumber,
    selectedRowMonth,
    mainTableSelectedYear,
    selectedSeverity
  ) => {
    setLoading(true);
    let selectedValues = [];
    if (selectedSeverity === "All") {
      selectedValues = ModalDetailSeverity.map((item) => item.value);
    } else {
      selectedValues.push(selectedSeverity);
    }

    try {
      const response = await fetch("/api/infra_history", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          page_number: pageNumber,
          month: selectedRowMonth,
          year: mainTableSelectedYear,
          severity: selectedSeverity,
        }),
      });
      const data = await response.json();
      setDetailModalData(data?.data?.map((item) => JSON.parse(item)));
      setTotalRowsDetailModal(data?.total_rows); // Set the total rows
      setTotalPagesDetailModal(data?.total_pages); // Set the total pages
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  const mainDownloadReport = async () => {
    setIsLoading(true);
    fetch("/api/export_infra_stats", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        year: mainTableSelectedYear,
      }),
    }).then(async (response) => {
      setIsLoading(false);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        const filename = `Vul_History_${mainTableSelectedYear}.xlsx`;
        a.href = url;
        a.download = filename;
        a.click();
        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
    setIsLoading(true);
  };

  const detailModalDownloadReport = async (
    pageNumber,
    selectedRowMonth,
    mainTableSelectedYear
  ) => {
    setIsLoading(true);
    fetch("/api/export_infra_history", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        page_number: pageNumber,
        month: selectedRowMonth,
        year: mainTableSelectedYear,
        severity: selectedSeverity,
      }),
    }).then(async (response) => {
      setIsLoading(false);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Vul_History_${new Date()
          .toDateString()
          .replaceAll(" ", "_")}+_.xlsx`;
        a.click();
        toast.success("File Download successfully");
      } else {
        toast.error("File download failed");
      }
    });
    setIsLoading(true);
  };

  const openModalDetail = (
    pageNumber,
    selectedRowMonth,
    mainTableSelectedYear,
    selectedSeverity
  ) => {
    setOpenDetailModal(true);
    setDetailModalCurrentPage(pageNumber);
    setSelectedRowMonth(selectedRowMonth);
    setMainTableSelectedYear(mainTableSelectedYear);
    // setSelectedSeverity([]);
    detailHistoryModalData(
      pageNumber,
      selectedRowMonth,
      mainTableSelectedYear,
      selectedSeverity
    );
  };

  const onCloseDetailModal = () => {
    setOpenDetailModal(false);
    setSelectedSeverity([]);
    setSelectedRowMonth(null);
  };

  const handleDetailModalPageChange = (
    pageNumber,
    selectedRowMonth,
    mainTableSelectedYear,
    selectedSeverity
  ) => {
    setDetailModalCurrentPage(pageNumber);
    setSelectedRowMonth(selectedRowMonth);
    setMainTableSelectedYear(mainTableSelectedYear);
    detailHistoryModalData(
      pageNumber,
      selectedRowMonth,
      mainTableSelectedYear,
      selectedSeverity
    );
  };

  const vulFetchData = async (mainTableSelectedYear) => {
    setMainPageLoader(true);
    const data = await fetch("/api/infra_stats", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        year: mainTableSelectedYear,
      }),
    }).then((res) => res.json());

    setMainTableData(data?.data?.map((item) => JSON.parse(item)));
    setTotalRowsMainPage(data?.total_rows); // Set the total rows
    setTotalPagesMainPage(data?.total_pages); // Set the total pages
    setMainPageLoader(false);
  };

  const handleSearchClick = async () => {
    if (mainTableSelectedYear) {
      setMainTableData([]);
      setMainPageLoader(true);
      await vulFetchData(mainTableSelectedYear);
      setMainPageLoader(false);
    } else {
      toast.error(MainErrorText);
    }
  };
  const handleDownloadFunc = async () => {
    if (mainTableSelectedYear) {
      setMainPageLoader(true);
      await mainDownloadReport(mainTableSelectedYear);
      setMainPageLoader(false);
    } else {
      toast.error(MainErrorText);
    }
  };

  const handleDetailSearchClick = async (
    pageNumber,
    selectedRowMonth,
    mainTableSelectedYear,
    selectedSeverity
  ) => {
    setDetailModalData([]);
    setLoading(true);
    setDetailModalCurrentPage(1);
    await detailHistoryModalData(
      1,
      selectedRowMonth,
      mainTableSelectedYear,
      selectedSeverity
    );
    setLoading(false);
  };

  const handleAllSeverityClick = () => {
    if (selectAllChecked) {
      // If 'All' is already selected, clear all selections
      setSelectedSeverity([]);
      setSelectAllChecked(false);
      console.log("All cleared");
    } else {
      // Select 'All' and all other options
      const allValuesExceptAll = ModalDetailSeverity.filter(
        (option) => option.value !== "All"
      ).map((option) => option.value);

      setSelectedSeverity(allValuesExceptAll);
      setSelectAllChecked(true);
      console.log("All selected");
    }
  };

  useEffect(() => {
    const currentYear = new Date().getFullYear();
    const yearsArray = [];
    for (let year = 2022; year <= currentYear; year++) {
      yearsArray.push({ label: year.toString(), value: year.toString() });
    }
    setYears(yearsArray);
    setMainTableSelectedYear(currentYear.toString());
    setMonthYear(`All ${currentYear}`);
    vulFetchData(currentYear.toString()); // Fetch data for the current year on page load
  }, []);

  useEffect(() => {
    if (mainTableSelectedYear === null) {
      setMainPageLoader(true);
      if (mainPageLoader) {
        setMainTableData([]);
      }
    }
    setMainTableData([]);
    setMainPageLoader(false);
  }, []);

  useEffect(() => {
    setMainPageLoader(true);
    pagiFunc(1, searchTerm);
    chartData();
    openCount();
    chart_vuln_cat();
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
      {/* UPLAOD - Modal */}
      {allowed_actions?.upload && (
        <Modal
          open={showNewUser}
          onClose={closeModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <h3>Upload Scan Results</h3>
          <Modal.Body>
            <DatePicker
              placeholder="Select Date"
              style={{ width: 200 }}
              value={modelValueDate}
              onChange={setModelValueDate}
              format="dd-MM-yyyy"
            />
            <hr />
            File Upload:
            <Uploader
              action="/api/upload-infra"
              fileList={fileList}
              autoUpload={false}
              onChange={setFileList}
              ref={uploader}
              data={[modelValueDate]}
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
            <Button onClick={closeModal} appearance="subtle">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* VUL BREAKDOWN/RISK - Modal */}
      {allowed_actions?.view && (
        <Modal
          keyboard={false}
          size="full"
          open={openTakeDownModal}
          onClose={handleTakeDownModalClose}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon
            onClick={() => handleTakeDownModalClose()}
            className={styles.clear}
          />
          <h3>Vulnerability Status</h3>
          <Modal.Body>
            <Table
              virtualized
              loading={loading}
              bordered
              autoHeight
              data={infraModalData}
            >
              <Column width={200}>
                <HeaderCell>Affected Subdomain</HeaderCell>
                <CompactCell dataKey="Subdomain" />
              </Column>
              <Column width={150} fullText>
                <HeaderCell>Month of Discovery</HeaderCell>
                <CompactCell dataKey="Month" />
              </Column>
              <Column width={300} fullText>
                <HeaderCell>Type</HeaderCell>
                <CompactCell dataKey="Type" />
              </Column>
              <Column width={100} fullText>
                <HeaderCell>Severity</HeaderCell>
                <CompactCell dataKey="Severity" />
              </Column>
              <Column width={200}>
                <HeaderCell>Service</HeaderCell>
                <CompactCell dataKey="Service" />
              </Column>
              <Column minwidth={200} flexGrow={1}>
                <HeaderCell>Status</HeaderCell>
                <Cell style={{ padding: "6px" }}>
                  {(rowData) => (rowData.Status == true ? "Open" : "Resolved")}
                </Cell>
              </Column>
            </Table>
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
                // limit={[10]}
                layout={["total", "-", "|", "pager", "skip"]}
                pages={totalPagesFirstPieChart}
                total={totalRowsFirstPieChart}
                activePage={PieApexFirstCurrentPage}
                limit={modalLimitFirst} // Current active page from URL
                // onChangePage={handleModalFirstPiePageChange}
                onChangePage={(page_number) =>
                  handleModalFirstPiePageChange(page_number, status)
                }
              />
            </div>
          </Modal.Body>
        </Modal>
      )}

      {/* VUL BREAKDOWN/RISK - Modal */}
      {allowed_actions?.view && infraModalData && (
        <Modal
          keyboard={false}
          size="full"
          open={openTakeDownModalSecond}
          onClose={handleTakeDownModalCloseSecond}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon
            onClick={() => handleTakeDownModalCloseSecond()}
            className={styles.clear}
          />
          <h3>Vulnerability Status</h3>
          <Modal.Body>
            <Table
              virtualized
              loading={loading}
              bordered
              autoHeight
              data={infraModalData}
            >
              <Column width={200}>
                <HeaderCell>Affected Subdomain</HeaderCell>
                <CompactCell dataKey="Subdomain" />
              </Column>
              <Column width={250} fullText>
                <HeaderCell>Month of Discovery</HeaderCell>
                <CompactCell dataKey="Month" />
              </Column>
              <Column width={300} fullText>
                <HeaderCell>Type</HeaderCell>
                <CompactCell dataKey="Type" />
              </Column>
              <Column width={150} fullText>
                <HeaderCell>Severity</HeaderCell>
                <CompactCell dataKey="Severity" />
              </Column>
              <Column width={300}>
                <HeaderCell>Service</HeaderCell>
                <CompactCell dataKey="Service" />
              </Column>
              <Column minwidth={300} flexGrow={1}>
                <HeaderCell>Status</HeaderCell>
                <Cell style={{ padding: "6px" }}>
                  {(rowData) => (rowData.Status == true ? "Open" : "Resolved")}
                </Cell>
              </Column>
            </Table>
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
                layout={["total", "-", "|", "pager", "skip"]}
                pages={totalPagesSecondPieChart}
                total={totalRowsSecondPieChart}
                activePage={modalPageSecondCurrent}
                onChangePage={(page_number) =>
                  handlePageModalChange(page_number)
                }
              />
            </div>
          </Modal.Body>
        </Modal>
      )}

      {/* VUL BY MONTH - Modal */}
      {allowed_actions?.view && (
        <Modal
          keyboard={false}
          size="full"
          open={infraOpen}
          onClose={handleLineModalCloseFunc}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon
            onClick={() => handleLineModalCloseFunc()}
            className={styles.clear}
          />
          <h3> Vulnerability Month Status</h3>
          <Modal.Body>
            <SelectPicker
              label="Filter by Month"
              searchable={false}
              data={monthOptions}
              value={selectedMonth}
              onChange={handleMonthSelect}
              className={styles.selectPicker}
            />
            <Table
              virtualized
              loading={loading}
              bordered
              autoHeight
              data={infraLineModalData}
            >
              <Column width={200}>
                <HeaderCell>Affected Subdomain</HeaderCell>
                <CompactCell dataKey="Subdomain" />
              </Column>
              <Column width={250} fullText>
                <HeaderCell>Month of Discovery</HeaderCell>
                <CompactCell dataKey="Month" />
              </Column>
              <Column width={300} fullText>
                <HeaderCell>Type</HeaderCell>
                <CompactCell dataKey="Type" />
              </Column>
              <Column width={150} fullText>
                <HeaderCell>Severity</HeaderCell>
                <CompactCell dataKey="Severity" />
              </Column>
              <Column width={300}>
                <HeaderCell>Service</HeaderCell>
                <CompactCell dataKey="Service" />
              </Column>
              <Column minwidth={300} flexGrow={1}>
                <HeaderCell>Status</HeaderCell>
                <Cell style={{ padding: "6px" }}>
                  {(rowData) => (rowData.Status == true ? "Open" : "Resolved")}
                </Cell>
              </Column>
            </Table>
            <div style={{ padding: 20 }}>
              <Pagination
                prev
                next
                first
                last
                ellipsis
                boundaryLinks
                size="xs"
                layout={["total", "-", "|", "pager", "skip"]}
                pages={totalPagesSecondLineChart}
                total={totalRowsSecondLineChart}
                maxButtons={5}
                activePage={currentPage}
                limit={modalLimitFirst}
                onChangePage={(page_value) =>
                  handleModalPageChangeLine(page_value, paginationMonth)
                }
                onGoTo={(page) => setCurrentPage(page)}
              ></Pagination>
            </div>
          </Modal.Body>
        </Modal>
      )}

      {/* Vulnerability Modal start */}
      {allowed_actions?.view && (
        <Modal
          keyboard={false}
          size="full"
          open={openDetailModal}
          onClose={onCloseDetailModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon
            onClick={() => onCloseDetailModal()}
            className={styles.clear}
          />
          <h3>Vulnerability Month Status</h3>
          <div className={styles.detailBody}>
            <Input
              type="text"
              value={`${selectedRowMonth} ${mainTableSelectedYear}`}
              onChange={(e) => setSelectedRowMonth(e.target.value)}
              placeholder="Selected Month"
              className={styles.monthInput}
              disabled
            />
            <CheckPicker
              label="Type"
              countable={true}
              data={ModalDetailSeverity}
              placeholder="Select Severity"
              searchable={false}
              value={selectedSeverity}
              onChange={(values) => setSelectedSeverity(values)}
              className={styles.detailSelectPicker}
            />
          </div>

          <div className={styles.buttonDiv}>
            <Button
              appearance="primary"
              className={styles.detailSearchBtn}
              onClick={() =>
                handleDetailSearchClick(
                  pageNumber,
                  selectedRowMonth,
                  mainTableSelectedYear,
                  selectedSeverity
                )
              }
            >
              Search
            </Button>
            {allowed_actions?.download && (
              <Button
                className={styles.detailExportBtn}
                appearance="primary"
                onClick={() =>
                  detailModalDownloadReport(
                    pageNumber,
                    selectedRowMonth,
                    mainTableSelectedYear,
                    selectedSeverity
                  )
                }
              >
                Export
              </Button>
            )}
          </div>
          <Modal.Body>
            <Table
              virtualized
              loading={loading}
              bordered
              autoHeight
              data={detailModalData}
              className={styles.detailModalTable}
            >
              <Column minWidth={150} flexGrow={1}>
                <HeaderCell className={styles.tableHeaders}>
                  Severity
                </HeaderCell>
                <CompactCell className={styles.tableCell} dataKey="Severity" />
              </Column>
              <Column minWidth={180} flexGrow={1.3} fullText>
                <HeaderCell className={styles.tableHeaders}>
                  Vulnerability Subdomain
                </HeaderCell>
                <CompactCell className={styles.tableCell} dataKey="Subdomain" />
              </Column>

              <Column minWidth={180} flexGrow={2} fullText>
                <HeaderCell className={styles.tableHeaders}>
                  Vulnerability Type
                </HeaderCell>
                <CompactCell dataKey="Type" />
              </Column>
              <Column minWidth={150} flexGrow={1} fullText>
                <HeaderCell className={styles.tableHeaders}>
                  Reported Month
                </HeaderCell>
                <CompactCell className={styles.tableCell} dataKey="Month" />
              </Column>
              <Column minWidth={150} flexGrow={1}>
                <HeaderCell className={styles.tableHeaders}>Service</HeaderCell>
                <CompactCell className={styles.tableCell} dataKey="Service" />
              </Column>
              <Column minWidth={150} flexGrow={1} fullText>
                <HeaderCell className={styles.tableCell}>
                  Present Status
                </HeaderCell>
                <Cell className={styles.tableCell}>
                  {(dataKey) => (dataKey.Status == true ? "Open" : "Fixed")}
                </Cell>
              </Column>
            </Table>
          </Modal.Body>
          <div style={{ padding: 10 }}>
            <Pagination
              prev
              next
              first
              last
              ellipsis
              boundaryLinks
              size="xs"
              layout={["total", "-", "|", "pager", "skip"]}
              pages={totalPagesDetailModal}
              total={totalRowsDetailModal}
              maxButtons={5}
              activePage={detailModalCurrentPage}
              onChangePage={(pageNumber) =>
                handleDetailModalPageChange(
                  pageNumber,
                  selectedRowMonth,
                  mainTableSelectedYear,
                  selectedSeverity
                )
              }
              onGoTo={(page) => setDetailModalCurrentPage(page)}
            ></Pagination>
          </div>
        </Modal>
      )}

      {/* MAIN CYBER THREAT - Page */}
      {allowed_page?.infrastructure_monitoring && allowed_actions?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            {userRole == "admin" ? (
              <Board
                heading="Cyber Threat Monitoring"
                router={Router}
                action={{ label: "Upload Scan Results", handler: openModal }}
              />
            ) : (
              <Board heading="Cyber Threat Monitoring" router={Router} />
            )}

            {vulnCount && Object.values(vulnCount).length > 0 ? (
              <>
                <div className={styles.sus_main_container}>
                  <div className={styles.cardsRow + " row mb-10 mx-1"}>
                    <div
                      className={
                        styles.cardContainer +
                        " card shadow-sm align-items-center"
                      }
                    >
                      <CustomComponent
                        placement="auto"
                        tooltip="Vulnerabilities Breakdown"
                      />
                      <PiApexChart
                        event_func={(page_value, status_up) =>
                          handleStatusCall(page_value, status_up)
                        }
                        title={"Vulnerabilities Breakdown"}
                        label={[
                          "Vulnerabilities Open",
                          "Vulnerabilities Resolved",
                        ]}
                        series={[openVuln, notInfo - openVuln]}
                        height={350}
                        width="100%"
                      />
                    </div>
                    <div
                      className={
                        styles.cardContainer +
                        " card shadow-sm align-items-center"
                      }
                    >
                      <CustomComponent
                        placement="auto"
                        tooltip="Risk Severity of Vulnerabilities"
                      />
                      <PiApexChart
                        event_func={handleTakeDownModalOpen}
                        title={"Risk Severity of Vulnerabilities"}
                        label={Object.keys(vulnCount)}
                        series={Object.values(vulnCount)}
                        height={350}
                        width="100%"
                      />
                    </div>
                    <div
                      className={
                        styles.cardContainerLong +
                        " card shadow-sm align-items-center"
                      }
                    >
                      <CustomComponent
                        placement="auto"
                        tooltip="Vulnerabilities Discovered"
                      />
                      <LineApexChart
                        event_func={(pageValue, month) =>
                          handleVulnerabilityModalSecondopen(pageValue, month)
                        }
                        title={"Vulnerabilites Type"}
                        label={vulnChart.map((data) => data.key)}
                        data={vulnChart.map((data) => data.value)}
                        height={350}
                        width="100%"
                      />
                    </div>
                    <div
                      className={
                        styles.cardContainerLong +
                        " card shadow-sm align-items-center"
                      }
                    >
                      <CustomComponent
                        placement="auto"
                        tooltip="Vulnerabilities Discovered"
                      />
                      <LineApexChart
                        event_func={(page_value, month) =>
                          handleVulnerabilityModalFirstopen(page_value, month)
                        }
                        title={"Vulnerabilities Discovered (By Month)"}
                        label={monthCount["keys"]}
                        data={monthCount["values"]}
                        height={350}
                        width="100%"
                      />
                    </div>
                  </div>
                  <div>
                    {/* Main Header Container */}

                    {/* PNR Table Data Container */}
                    {/* <div className={styles.susN_data_container}> */}
                    <div
                      className={`${styles.susN_data_container} ${
                        !mainTableSelectedYear || mainPageLoader
                          ? styles.blur
                          : ""
                      }`}
                    >
                      <div className={styles.sus_div_header}>
                        {/* <div className={styles.sus_div_sub_headers}> */}
                        <div className={styles.sus_div_sub_yearPicker}>
                          <SelectPicker
                            label="Filter by Year"
                            searchable={false}
                            data={years}
                            placeholder="Select Year"
                            value={mainTableSelectedYear}
                            onChange={(value) =>
                              setMainTableSelectedYear(value)
                            }
                            className={styles.yearSelectPicker}
                          />
                        </div>
                        <div className={styles.div_header_btn}>
                          <Button
                            appearance="primary"
                            className={styles.searchBtn}
                            onClick={() =>
                              handleSearchClick(mainTableSelectedYear)
                            }
                          >
                            Search
                          </Button>
                          {allowed_actions?.download && (
                            <Button
                              className={styles.exportBtn}
                              appearance="primary"
                              onClick={() =>
                                handleDownloadFunc(mainTableSelectedYear)
                              }
                            >
                              Export
                            </Button>
                          )}
                        </div>
                        {/* </div> */}
                      </div>
                      <table className={styles.data_table} data={mainTableData}>
                        <thead className={styles.susN_tables_head}>
                          <tr>
                            <th>Month</th>
                            <th>Critical</th>
                            <th>High</th>
                            <th>Medium</th>
                            <th>Low</th>
                            <th>Informative</th>
                            <th>Total</th>
                            {allowed_actions?.view && <th>Details</th>}
                          </tr>
                        </thead>
                        <tbody>
                          {!mainTableSelectedYear || mainPageLoader ? (
                            <tr>
                              <td colSpan="8">
                                <div className={styles.loader_container}>
                                  <div className={styles.loader} />
                                </div>
                              </td>
                            </tr>
                          ) : (
                            // mainTableData.length > 0 &&
                            mainTableData?.map((item, index) => (
                              <tr key={index}>
                                {/* <td>{index + 1}</td> */}
                                {/* <td>{susCurrentPage > 1 ? (susCurrentPage - 1) * itemsPerPage + index + 1 : index + 1}</td> */}
                                <td>{item?.Month}</td>
                                <td>{item?.Critical}</td>
                                <td>{item?.High}</td>
                                <td>{item?.Medium}</td>
                                <td>{item?.Low}</td>
                                <td>{item?.Informative}</td>
                                <td>{item?.VULN_COUNT}</td>
                                {allowed_actions?.view && (
                                  <td>
                                    <Button
                                      appearance="primary"
                                      onClick={() => {
                                        const extractedMonth =
                                          item?.Month.split(" ")[0];
                                        setSelectedRowMonth(extractedMonth);
                                        openModalDetail(
                                          pageNumber,
                                          extractedMonth,
                                          mainTableSelectedYear,
                                          selectedSeverity
                                        );
                                      }}
                                    >
                                      {" "}
                                      View Details{" "}
                                    </Button>
                                  </td>
                                )}
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              ""
            )}

            {/* <div className={styles.tableContainer +  ' col'}>
              <div className={styles.submaindiv}>
                <Input
                type='text'
                  value={searchTerm}
                  // onChange={handleSearchChange}
                  onChange={(event) => handleSearchChange(event)}
                  placeholder="Search (Multiple keywords supported)..."
                  className={styles.searchInput}
                  prefix={<Icon icon="search" />}
                />
                <IconButton
                onClick={() => handleSearchFunc()}
                  variant="outlined"
                  color="blue"
                  appearance="primary"
                  icon={<SearchIcon />}
                  style={{ minWidth: 100, height: "40px" }}
                  className={styles.searchBtn}
                >
                  Search
                </IconButton>
                <Button 
                onClick={() => handleExport()}
                className={styles.exportBtn} 
                appearance="primary"
                >
                  Export
                </Button>
              </div>

              <div className={styles.tableContainer}>
              <table className={styles.responsiveTable}>
                  <thead>
                    <tr>
                      <th style={{ whiteSpace:"nowrap"}}>Affected Subdomain</th>
                      <th style={{ whiteSpace:"nowrap"}}>Month of Discovery</th>
                      <th  style={{ whiteSpace:"nowrap"}}>Type</th>
                      <th>Severity</th>
                      <th>Service</th>
                      <th>Resolution Action</th>
                      <th  style={{ whiteSpace:"nowrap"}}>Vulnerability Status</th>
                    </tr>
                  </thead>
                  <tbody>

                    {infraData?.map((item)=>(
                    <tr key={item?.$oid}>
                    <td>{item?.Subdomain}</td>
                    <td  style={{ whiteSpace:"nowrap" }}>{item?.Month}</td>
                    <td  style={{ whiteSpace:"nowrap" }}>{item?.Type}</td>
                    <td>{item?.Severity}</td>
                    <td  style={{ whiteSpace:"nowrap" }}>{item?.Service}</td>
                  
                    <td>
                    <Button appearance="primary"
                        onClick={() => changeVulnStatus(item?._id.$oid)}
                        style={{ width: 150 }}>
                        {item?.Status == 0
                          ? "Assign to IRCTC"
                          : item?.Status == 1
                          ? "Assign to Pinaca"
                          : item?.Status == 2
                          ? "Mark as Resolved"
                          : { buttonText }}
                        </Button>
                    </td>
                    <td  style={{ whiteSpace:"nowrap" }} >{item?.Status == true
                        ? "Assigned to IRCTC for Resolution"
                        : "Resolved by IRCTC"
                    }</td>
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
                  layout={["total", "-", "|", "pager", "skip"]}
                  total={totalRowsMainPage}
                  pages={totalPagesMainPage}
                  limit={limit}
                  activePage={page}
                  onChangePage={handlePageChange}
                  onChangeLimit={handleChangeLimit}
                />
              </div>
            </div> */}
          </div>
        </div>
      )}
    </>
  );
};

export default InfrastructureMonitoring;

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res);
}
