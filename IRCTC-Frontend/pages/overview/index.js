// Import Libraries
import Image from "next/image";
import { useEffect, useState } from "react";
// import { useSelector, useDispatch } from "react-redux";
import { Button, Loader, Modal, Table, Tooltip, Whisper } from "rsuite";
// import { startOfDay, subDays, endOfDay } from "date-fns";
import Router, { useRouter } from "next/router";
// import dynamic from "next/dynamic";

// Import Components
import BarApexChart from "@/components/BarApexChart";
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
// import FilterBar from "../../components/FilterBar";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";

// Import Assets
import ipAddress from "../../public/static/images/ip-address.svg";
import vulnerability from "../../public/static/images/vulnerability.svg";
import pnrAnalyzed from "../../public/static/images/pnr-analyzed.svg";
import questionMark from "../../public/static/images/questionmark.svg";
import software from "../../public/static/images/software.svg";
import takedownConducted from "../../public/static/images/takedown-conducted.svg";
import users from "../../public/static/images/users.svg";

// Import Styles
import styles from "./Overview.module.scss";
import { join } from "lodash";
import { toast } from "react-toastify";
import { useSelector } from "react-redux";

// import no. formatter
import { formatNumber } from "@/utils/formatNumbers";

// // Import Store
// import {
//   changeOverviewFilterDate
// } from "../../store/slice/overview";

// Destructure the Table component import.
const { Column, HeaderCell, Cell } = Table;

// Renders an Image component with a tooltip when hovered over.
const CustomComponent = ({ placement, tooltip }) => (
  <Whisper
    trigger="hover"
    placement={placement}
    controlId={`control-id-${placement}`}
    speaker={<Tooltip arrow={false}>{tooltip}</Tooltip>}
  >
    {/* Render an Image component with a question mark icon and specified class */}
    <Image
      src={questionMark}
      className={styles.questionmark}
      alt="Explanation"
    ></Image>
  </Whisper>
);

// Overview Page
const OverviewPage = ({ rowData, userPagesObject = {}, checkboxes = [] }) => {
  // Initialising the router
  const router = useRouter();

  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_actions = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  // ------------------------------ Page Setup ------------------------------ //

  // This is another piece of data from the Redux store that contains information about which users are
  //  currently displayed on each page in the table on the dashboard. It's likely used to keep track of
  //  which users are currently displayed and to update the UI when the page changes.
  // This state variable also uses the persisted state, which means the data will be stored and
  // retrieved from browser storage even after the browser is refreshed or closed.
  const pages = useSelector((state) => state.persistedReducer.user_pages);

  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [pnrModalDisplayToggle, setPNRModalDisplayToggle] = useState(false);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [
    userRegistrationsModalDisplayToggle,
    setUserRegistrationsModalDisplayToggle,
  ] = useState(false);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [
    vulnerabilitiesModalDisplayToggle,
    setVulnerabilitiesModalDisplayToggle,
  ] = useState(false);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [ipBlacklistModalDisplayToggle, setIPBlacklistModalDisplayToggle] =
    useState(false);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [takedownModalDisplayToggle, setTakedownModalDisplayToggle] =
    useState(false);
  // uploadModalDisplayToggle toggles the state of modal to be displayed.
  const [
    softwareAnalysisModalDisplayToggle,
    setSoftwareAnalysisModalDisplayToggle,
  ] = useState(false);

  const [takedownConductedCount, setTakedownConductedCount] = useState(0);
  const [takedownCompletedCount, setTakedownCompletedCount] = useState(0);

  // openModal displays the modal.
  const openModal = (toggleFunction) => {
    toggleFunction(true);
  };

  // closeModal removes the modal.
  const closeModal = (toggleFunction) => {
    toggleFunction(false);
  };

  // vulnCount is a state variable that holds the "totalPnr" value for the month Count in pi-chart.
  const [totalPnr, setTotalPnr] = useState(0);
  // vulnCount is a state variable that holds the 'pnrFlag' value for the PNR count.
  const [pnrFlag, setPnrFlag] = useState(0);
  // vulnCount is a state variable that holds the 'totalUser' value for the month Count in pi-chart.
  const [totalUser, setTotalUser] = useState(0);
  // vulnCount is a state variable that holds the 'userFlag' value for the month Count.
  const [userFlag, setUserFlagged] = useState(0);
  // vulnCount is a state variable that holds the blackSub value for the blacklist subnet.
  const [blackSub, setBlackSub] = useState(0);
  // vulnCount is a state variable that holds the blackIp value for the blacklist ip.
  const [blackIp, setBlackIp] = useState(0);
  // vulnCount is a state variable that holds the vulnCount value for the month Count in pi-chart.
  const [vulnCount, setVulnCount] = useState(0);
  //This state defines a new state variable named "pnrTrend" and sets its initial value to an empty object.
  const [pnrTrend, setPnrTrend] = useState({});
  //This state defines a new state variable named "userTrend" and sets its initial value to an empty object.
  const [userTrend, setUserTrend] = useState({});
  //This state defines a new state variable named "vpsTrend" and sets its initial value to an empty object.
  const [vpsTrend, setVpsTrend] = useState({});
  //This state defines a new state variable named "vpsTrendPercentage" and sets its initial value to an empty object.
  const [vpsTrendPercentage, setVpsTrendPercentage] = useState([]);
  //This state defines a new state variable named "vulnChart" and sets its initial value to an empty array.
  const [vulnChart, setVulnChart] = useState({});
  //This state defines a new state variable named "keyLabel" and sets its initial value to an empty array.
  const [keyLabel, setKeyLabel] = useState({});

  // state for software data and website and app data 
  
  const [websiteTakedowns, setWebsiteTakedowns] = useState([]);
  const [appTakedowns, setAppTakedowns] = useState([]);

  // we state for website and mobile apps
  const [softwareApplications, setSoftwareApplications] = useState([]);

  // API Call: '/api/fetch-over-data'
  const fetchOverData = async () => {
    const data = await fetch("/api/fetch-over-data").then((response) =>
      response.json()
    );

    let fp = data?.data[0];

    // Set the total PNR count state variable based on the 'PNR_COUNT' key in the response.
    setTotalPnr(data?.data[0]["PNR_COUNT"]);
    // Set the total user count state variable based on the 'USER_COUNT' key in the response.
    setTotalUser(data?.data[0]["USER_COUNT"]);
    // Set the blacklisted subnet state variable based on the 'BLACKLIST_SUBNET' key in the response.
    setBlackSub(data?.data[0]["BLACKLIST_SUBNET"]);
    // Set the blacklisted IP state variable based on the 'BLACKLIST_IP' key in the response.
    setBlackIp(data?.data[0]["BLACKLIST_IP"]);
    // Set the vulnerability count state variable based on the 'VULN_REPORTED' key in the response.
    setVulnCount(data?.data[0]["VULN_REPORTED"]);
    // Set the PNR trend state variable based on the 'PNR_TOTAL_TREND' key in the response.
    setPnrTrend(
      JSON.parse(data?.data[0]["PNR_TOTAL_TREND"]?.replace(/'/g, '"'))
    );
    // Set the user trend state variable based on the 'USER_TOTAL_TREND' key in the response.
    setUserTrend(
      JSON.parse(data?.data[0]["USER_TOTAL_TREND"]?.replace(/'/g, '"'))
    );
    // Set the VPS trend state variable based on the 'PNR_VPS_TREND' key in the response.
    setVpsTrend(JSON.parse(data?.data[0]["PNR_VPS_TREND"]?.replace(/'/g, '"')));
    // Set the PNR flagged count state variable based on the 'SUS_PNR_COUNT' key in the response.
    setPnrFlag(data?.data[0]["SUS_PNR_COUNT"]);
    // Set the flagged user count state variable based on the 'SUS_USER_COUNT' key in the response.
    setUserFlagged(data?.data[0]["SUS_USER_COUNT"]);
    // Set the vulnerability chart state variable based on the 'VULN_TYPE' key in the response.
    setVulnChart(JSON.parse(data?.data[0]["VULN_TYPE"]?.replace(/'/g, '"')));
    setKeyLabel(JSON.parse(data?.data[0]["PNR_VPS_TREND"]?.replace(/'/g, '"')));
    setTakedownConductedCount(data?.data[0]["TAKEDOWN_INITIATED"]);
    setTakedownCompletedCount(data?.data[0]["TAKEDOWN_COMPLETED"]);

    // Calculate the VPS trend percentage and set the state variable.
    // Calculate the percentage of VPS counts compared to total counts for each month,
    // and add them to an array, starting with a hardcoded value for the first month
    let jp = [];
    // Extract keys and values for PNR and VPS trends from fetched data
    let keys = Object.keys(
      JSON.parse(data?.data[0]["PNR_TOTAL_TREND"]?.replace(/'/g, '"'))
    );
    let totalCountValues = Object.values(
      JSON.parse(data?.data[0]["PNR_TOTAL_TREND"]?.replace(/'/g, '"'))
    );
    let vpsCountValues = Object.values(
      JSON.parse(data?.data[0]["PNR_VPS_TREND"]?.replace(/'/g, '"'))
    );
    // for (let i = 0; i < keys.length; i++) {
    for (let i = 0; i < Math.min(keys.length, 12); i++) {
      if (i == 0) {
        jp.push(71);
      }
      jp.push(parseInt((vpsCountValues[i] / totalCountValues[i]) * 100));
    }
    setVpsTrendPercentage(jp.slice(-12));
  };

  useEffect(() => {
    fetchOverData();
  }, []);

  const allChecked = Object.values(userPagesObject).every(
    (isChecked) => isChecked
  );
  // downloadReport function takes two parameter f_name and f_hash.
  const downloadReport = (f_name, f_hash) => {
    // Check if all checkboxes are checked
    const allChecked = checkboxes.every((value) => value === 1);

    // Show a toast message if not all checkboxes are checked
    if (!allChecked) {
      toast.error("Please check all checkboxes before downloading");
      return;
    }

    // It first creates a URL object from the blob, then creates a new anchor element
    fetch("/api/archive-download?f_hash=" + f_hash)
      .then((response) => {
        // This code creates a downloadable file from the response blob.
        response.blob().then((blob) => {
          let url = window.URL.createObjectURL(blob);
          let a = document.createElement("a");
          a.href = url;
          // and sets the download attribute with the file name.
          a.download = f_name;
          // Finally, it triggers a click
          // event on the anchor element to initiate the download.
          a.click();
        });
      })
      .catch((error) => {
        console.log(error);
      });
    // };
  };

  const filterDomainAndAppsData = async () => {
    try {
      const response = await fetch("/api/overview_top_web", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      const data = await response.json();

      // Filter data based on threatSource
      const websiteData = data?.data_list?.filter(
        (item) => JSON.parse(item)?.threatSource === "Website"
      );
      const appData = data?.data_list?.filter(
        (item) => JSON.parse(item)?.threatSource === "Mobile Application"
      );
      // Update state variables
      setWebsiteTakedowns(websiteData?.map((item) => JSON.parse(item)));
      setAppTakedowns(appData?.map((item) => JSON.parse(item)));
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const AnalyzedSoftwares = async (pageNumber) => {
    // setMainPageLoading(true);
    try {
      const response = await fetch("/api/overview_top_software", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      const data = await response.json();
      setSoftwareApplications(data?.data_list?.map((item) => JSON.parse(item)));
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  useEffect(() => {
    fetchOverData();
    filterDomainAndAppsData();
    AnalyzedSoftwares();
  }, []);

  return (
    <>
      {allowed_page?.overview && allowed_actions?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>
            <div className={styles.header}>
              <Board heading="Overview" router={Router} />
            </div>

            <div className={styles.content}>
              {/* ############### FIRST CARD ############### */}
              <div className={styles.cardsRow}>
                {/* New Combined PNR Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* main Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={pnrAnalyzed}
                          className={styles.pnrAnalyzed}
                          alt="PNRs Analyzed"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {totalPnr ? formatNumber(totalPnr) : ""}
                        </p>
                        <h4>PNRs Analyzed</h4>
                        <p>Since 1st January 2023</p>
                      </div>
                      <div className={styles.verticalRule}></div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {pnrFlag ? formatNumber(pnrFlag) : ""}
                        </p>
                        <h4>PNRs Flagged</h4>
                        <p>Since 1st January 2023</p>
                      </div>
                    </div>
                    {/* Graphical Content */}
                    <div className={styles.modalStyles}>
                      {Object.keys(pnrTrend).length > 0 ? (
                        <div className={styles.chartContainer}>
                          <BarApexChart
                            labels={Object.keys(pnrTrend).slice(-12)}
                            series={Object.values(pnrTrend).slice(-12)}
                            title="Monthly Average of PNRs Analyzed"
                            height={350}
                            width="100%"
                          />
                        </div>
                      ) : null}
                      <p className={styles.modalDescription}>
                        We are flagging PNRs on a daily basis based on the
                        following factors:
                      </p>
                      <ul>
                        <li>
                          PNR has been booked from an IP Address that has
                          exhibited suspicious behavior.
                        </li>
                        <li>
                          PNR has been booked by a user that has exhibited
                          suspicious behavior.
                        </li>
                      </ul>
                      <br />
                      <br />
                    </div>
                  </div>
                </div>

                {/* New Combined USER REg. Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* Main Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={users}
                          className={styles.users}
                          alt="User Registrations Analyzed"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {totalUser ? formatNumber(totalUser) : ""}
                        </p>
                        {/* <p className={styles.head}>User Registrations Analyzed</p> */}
                        <h5>User Registrations Analyzed</h5>
                        <p>Since 1st January 2023</p>
                      </div>
                      <div className={styles.verticalRule}></div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {userFlag ? formatNumber(userFlag) : ""}
                        </p>
                        <h4>User IDs Flagged</h4>
                        <p>Since 1st January 2023</p>
                      </div>
                    </div>
                    {/* Graphical Content */}
                    <div className={styles.modalStyles}>
                      {Object.keys(pnrTrend).length > 0 ? (
                        <div className={styles.chartContainer}>
                          <BarApexChart
                            labels={Object.keys(userTrend).slice(-12)}
                            series={Object.values(userTrend).slice(-12)}
                            title="Monthly Average of User Registrations Analyzed"
                            height={350}
                            width="100%"
                          />
                        </div>
                      ) : null}
                      <p className={styles.modalDescription}>
                        We are flagging USERIDs on a daily basis based on the
                        following factors:
                      </p>
                      <ul>
                        <li>
                          User has booked tickets on the same day from multiple
                          IP Addresses.
                        </li>
                        <li>
                          User ID has been created as part of a series such as
                          axb123, axb124, axb125 and so on.
                        </li>
                        <li>
                          Multiple user IDs belonging to a series have booked
                          tickets on the same day.
                        </li>
                        <li>User ID has been registered from a VPS.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* ############### SECOND CARD ############### */}
              <div className={styles.cardsRow}>
                {/* New Ip Analysis Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={ipAddress}
                          className={styles.ipAddress}
                          alt="IP Addresses"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {blackIp ? formatNumber(blackIp) : ""}
                        </p>
                        <h5>IP Addresses Flagged from Touts Infrastructure </h5>
                      </div>
                      <div className={styles.verticalRule}></div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p
                          style={{
                            fontSize: "0.9rem",
                            fontWeight: "bold",
                            letterSpacing: "0.8px",
                            marginTop: "20px",
                            marginBottom: "10px",
                          }}
                        >
                          ITAF may please consider to confirm count.
                        </p>
                        <h5>IP Addresses Blacklisted</h5>
                      </div>
                    </div>
                    {/* Graphical */}
                    <div className={styles.modalStyles}>
                      {Object.keys(keyLabel).length > 0 ? (
                        <div className={styles.chartContainer}>
                          <BarApexChart
                            labels={Object.keys(keyLabel).slice(-12)}
                            series={Object.values(vpsTrendPercentage).slice(
                              -12
                            )}
                            title="Trend of VPS Booked Tickets (Percentage %)"
                            dataLabels={true}
                            height={300}
                            width="100%"
                          />
                        </div>
                      ) : null}
                      <p
                        style={{
                          fontSize: "1rem",
                          fontWeight: "bold",
                          letterSpacing: "0.8px",
                        }}
                      >
                        ITAF whitelisted the 11Cr. IP Addresses that Pinaca has
                        Flagged until Mar. 28, 2023.{" "}
                      </p>
                      <p className={styles.modalDescription}>
                        Blacklisting of IP Addresses from Virtual Private
                        Servers display a decreasing trend. This indicates that
                        the touts have moved from using servers back to home
                        networks, thus removing their advantage of faster
                        internet.
                      </p>
                      <p className={styles.modalDescription}>
                        Blacklisting is based on the following factors:
                      </p>
                      <ul>
                        <li>
                          More than 20 PNRs have been booked by a single IP
                          Address in a single day.
                        </li>
                        <li>
                          IP Address belongs to a subnet that has been allocated
                          for Virtual Private Servers, and has been observed
                          booking a ticket.
                        </li>
                        <li>
                          IP Address belongs to a subnet that has been allocated
                          for Virtual Private Servers, and has been observed
                          registering a user.
                        </li>
                        <li>
                          More than 5 users have registered by a single IP
                          Address in a single day.
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* New Vulnerability Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={vulnerability}
                          className={styles.vulnerability}
                          alt="Location"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>{vulnCount}</p>
                        <h5>Vulnerabilities Flagged</h5>
                        {/* <p>Excluding Informative</p> */}
                      </div>
                      <div className={styles.verticalRule}></div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p
                          style={{
                            fontSize: "0.9rem",
                            fontWeight: "bold",
                            letterSpacing: "0.8px",
                            marginTop: "20px",
                            marginBottom: "10px",
                          }}
                        >
                          ITAF may please consider to confirm count.
                        </p>
                        <h5>Vulnerabilities Fixed</h5>
                        {/* <p>Since 15th January 2023</p> */}
                      </div>
                    </div>
                    {/* Graphical */}
                    <div className={styles.modalStyles}>
                      {Object.keys(vulnChart).length > 0 ? (
                        <div className={styles.chartContainer}>
                          <BarApexChart
                            labels={Object.keys(vulnChart)}
                            series={Object.values(vulnChart)}
                            title="Severity-Wise Count of Reported Vulnerabilities"
                            height={300}
                            width="100%"
                          />
                        </div>
                      ) : null}
                      <p className={styles.modalDescriptionFourth}>
                        Severity of vulnerabilities is classified as follows:
                        <ul className={styles.FourthModalUl}>
                          <li className={styles.FourthModalLi}>
                            <b>Critical Vulnerability:</b> Exploitation of the
                            vulnerability likely results in root-level
                            compromise of servers or infrastructure devices.
                          </li>
                          <li className={styles.FourthModalLi}>
                            <b>High Vulnerability:</b>The vulnerability is
                            difficult to exploit and exploitation could result
                            in elevated privileges.
                          </li>
                          <li className={styles.FourthModalLi}>
                            <b>Medium Vulnerability:</b> Vulnerabilities that
                            require the attacker to reside on the same local
                            network as the victim and provide only limited
                            access.
                          </li>
                          <li className={styles.FourthModalLi}>
                            <b>Low Vulnerability:</b> Vulnerabilities in the low
                            range typically have very little impact on an
                            organisation's business.
                          </li>
                          <li className={styles.FourthModalLi}>
                            <b>Informative Vulnerability:</b> Vulnerabilities
                            that are not directly harmful and are mainly just
                            violations of good practice as per security
                            guidelines.
                          </li>
                        </ul>
                      </p>
                    </div>
                  </div>
                </div>

                {/* New Takedown Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={takedownConducted}
                          className={styles.takedownConducted}
                          alt="Takedowns"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {" "}
                          {takedownConductedCount
                            ? takedownConductedCount
                            : 300}{" "}
                        </p>
                        <h5>Takedowns Conducted</h5>
                        <p>Since 1st January 2023</p>
                      </div>
                      <div className={styles.verticalRule}></div>
                      <div className={styles.cardBody + " card border-0"}>
                        <p className={styles.count}>
                          {takedownCompletedCount
                            ? takedownCompletedCount
                            : 250}
                        </p>
                        <h5>Takedowns Completed</h5>
                        <p>Since 1st January 2023</p>
                      </div>
                    </div>
                    {/* Graphical */}
                    <div className={styles.modalStyles}>
                      <p className={styles.modalDescription}>
                        We conduct takedowns to stop the distribution of
                        software, to disrupt its functionality, stop the touts
                        from misleading the customers through clever usage of
                        the IRCTC name or by impersonating IRCTC officials.
                        <br />
                        <br />
                        {/* Website Takedown List */}
                        <p className={styles.table_content_head}>
                          Five latest websites takedown
                        </p>
                        <div className={styles.table_div}>
                          <table className={styles.table_sec}>
                            {/* table head */}
                            <thead className={styles.table_head}>
                              <tr>
                                <th>S. No</th>
                                <th>Website</th>
                                <th>Status</th>
                              </tr>
                            </thead>
                            {/* table data */}
                            <tbody>
                              {websiteTakedowns?.map((data, index) => (
                                <tr>
                                  <td>{index + 1}</td>
                                  <td>
                                    <a
                                      href={data?.Link}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      {" "}
                                      {data.Link}{" "}
                                    </a>
                                  </td>
                                  <td>{data?.presentStatus}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <br />
                        {/* Phone App Takedown */}
                        <p className={styles.table_content_head}>
                          Five latest Mobile Apps takedown
                        </p>
                        <div className={styles.table_div}>
                          <table className={styles.table_sec}>
                            {/* table head */}
                            <thead className={styles.table_head}>
                              <tr>
                                <th>S. No</th>
                                <th>App Name</th>
                                <th>Status</th>
                              </tr>
                            </thead>
                            {/* table data */}
                            <tbody>
                              {appTakedowns?.map((data, index) => (
                                <tr>
                                  <td>{index + 1}</td>
                                  <td>
                                    <a
                                      href={data.Link}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      {data.Link}
                                    </a>
                                  </td>
                                  <td>{data.presentStatus}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </p>
                    </div>
                  </div>
                </div>

                {/* New Software Analysed Section */}
                <div className={styles.parent}>
                  <div className={styles.child}>
                    {/* Content */}
                    <div className={styles.card}>
                      <div className={styles.imageWrapper}>
                        <Image
                          src={software}
                          className={styles.software}
                          alt="Tatkal Booking Software"
                        ></Image>
                      </div>
                      <div className={styles.cardBody + " card border-0"}>
                        {/* <p className={styles.count}>{softwareData.length}</p> */}
                        <p className={styles.count}>
                          {softwareApplications.software_count
                            ? softwareApplications.software_count
                            : 12}
                        </p>
                        <h4>Touting Softwares Analyzed</h4>
                        <p>Since 1st January 2023</p>
                      </div>
                    </div>
                    {/* Graphical */}
                    <div className={styles.modalStyles}>
                      <p className={styles.modalDescription}>
                        Tatkal Booking Software are analzyed to:
                        <ul>
                          <li>Understand the modus operandi of touts.</li>
                          <li>
                            Check if any vulnerabilities are being exploited in
                            the IRCTC infrastructure.
                          </li>
                          <li>
                            Understand how the touts are bypassing checks on the
                            IRCTC web portal.
                          </li>
                          <li>
                            Draw out the mitigations to be put in-place to
                            counter the software.
                          </li>
                        </ul>
                        <br />
                        The following software have been analyzed thus far:
                      </p>
                      <br />
                      <div className={styles.software_table_div}>
                        <table className={styles.software_table_sec}>
                          {/* table head */}
                          <thead className={styles.software_table_head}>
                            <tr>
                              <th>S. No</th>
                              <th>Name of Softwares</th>
                              <th>Status</th>
                              <th>Details</th>
                            </tr>
                          </thead>
                          {/* table data */}
                          <tbody className={styles.tableBody}>
                            {softwareApplications?.map((data, index) => (
                              <tr key={index}>
                                <td>{index + 1}</td>
                                <td>{data?.software_name}</td>
                                <td>{data?.current_status}</td>
                                <td>
                                  <Button
                                    appearance={"primary"}
                                    href="software-procurement"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    View History
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default OverviewPage;

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res);
}
