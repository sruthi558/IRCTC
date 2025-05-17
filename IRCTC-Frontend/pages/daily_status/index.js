
import Board from "@/components/Board";
import Sidebar from "@/components/Sidebar";
import React, { useEffect, useState, useRef } from "react";
import Router, { useRouter } from "next/router"; 
import styles from "./DailyStats.module.scss";
import { Table } from "rsuite";
import html2canvas from 'html2canvas';
import { saveAs } from 'file-saver';
import { object } from "sharp/lib/is";

import jsPDF from 'jspdf';
import 'jspdf-autotable';

import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; 

import { useSelector } from 'react-redux'


const daily_status = () => {

  // router initializing 
  const router = useRouter()

  const allowed_page = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  useEffect(() => {
    if(!allowed_page?.daily_status) {
      router.push("/overview")
    }
  }, [])

  const [selectedDate, setSelectedDate] = useState(new Date());

  const [mockData, setMockData] = useState({})

  // Save page as image 
  const captureScreenshot = () => {
    const body = document.querySelector('body');
    html2canvas(body).then(canvas => {
      canvas.toBlob(blob => {
        saveAs(blob, 'screenshot.png');
      });
    });
  };

  const contentRef = useRef(null);

  const saveImgAsPdf = async () => {
    const content = contentRef.current;

    // window.alert("Starting Download..")
    toast.info('Starting Download..', {
      position: toast.POSITION.TOP_CENTER,
      toastId: 'downloadToast',
      className: 'custom-toast',
      bodyClassName: 'custom-toast-body',
    });

    html2canvas(content, { scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      pdf.addImage(imgData, 'PNG', 0, 0, 210, 0);
      pdf.save(`daily-status-${JSON.stringify(new Date())}.pdf`);
    });

    // window.alert("Download Complete!!")
    // toast.success('Download Complete!', {
    //   position: toast.POSITION.TOP_CENTER,
    //   toastId: 'downloadCompleteToast',
    //   className: 'custom-toast',
    //   bodyClassName: 'custom-toast-body',
    // });
  };


  const getDataApiCall = async() => {
    
    const currentDate = new Date(`${selectedDate}`);
    const formattedDate = (selectedDate != null || selectedDate != undefined) && currentDate.toISOString().slice(0, 10) + "T00:00:00Z";

    try {
      const response = await fetch("/api/fetch-user-reg-logs", {
        method: 'POST',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          searchDate: formattedDate,
        }),
        timeout: 10 * 60 * 1000, // Set for 10 min
      })
  
      const res_data = await response.json(); 
      setMockData(res_data); 
      // console.log(`API Res Data: ${res_data}`);
      // console.log(res_data);

    } catch (error) {
      console.error(`Error getting DailyLogs API Data: ${error}`);
    }
  }; 

  useEffect(() => {
    // console.log(`Making API Call!!`);

    getDataApiCall(); 
  }, [selectedDate])

  // console.log(`Date: ${selectedDate}`);

  // Render Date 
  const formattedDateToRender = (selectedDate) => {
    if (!selectedDate) return "";
    const date = new Date(selectedDate);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
  };

  return (
    <>
      {(allowed_page?.daily_status && allowed_actions?.view) && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>

          <div className={styles.page}>        
            <div className={styles.header}>
              <Board heading="Daily Status" router={Router}
                selectedDate={selectedDate}
                setSelectedDate={setSelectedDate}
                value={selectedDate}
                captureScreenshot={captureScreenshot}
                saveImgAsPdf={saveImgAsPdf}
              />
            </div>

            <div ref={contentRef}>

              {/* New Overall Section */}
              <div className={styles.user_reg_container}>
                {/* Main Header */}
                <div className={styles.user_reg_header}>
                  <p className={styles.user_reg_title}>{selectedDate ? formattedDateToRender(selectedDate) : ""}</p>
                </div>
                {/* Child Container */}
                <div className={styles.user_reg_child_container}>
                  {/* IP */}
                  <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Count of IP Addresses</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_IP !== undefined ? mockData.TOTAL_IP : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div>
                  {/* Users Reg. */}
                  <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Count of Users Registered</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_PNR?.TOTAL !== undefined ? mockData.TOTAL_USER.TOTAL : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div>
                  {/* PNRs */}
                  <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Count of PNRs Booked</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_USER?.TOTAL !== undefined ? mockData.TOTAL_PNR.TOTAL : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* User Reg. Statistics */}
              <div className={styles.user_reg_container}>
                {/* Main Header */}
                <div className={styles.user_reg_header}>
                  <p className={styles.user_reg_title}>User Registration Statistics</p>
                </div>
                {/* Child Container */}
                <div className={styles.user_reg_child_container}>
                  {/* Total Reg. */}
                  {/* <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Total Users Registered</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_USER?.TOTAL !== undefined ? mockData?.TOTAL_USER?.TOTAL : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div> */}
                  {/* VPS Reg. */}
                  <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Users Registered using VPS</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_USER?.USER_REG?.VPS !== undefined ? mockData?.TOTAL_USER?.USER_REG?.VPS : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div>
                  {/* Non VPS Reg. */}
                  <div className={styles.user_reg_child}>
                    <p className={styles.user_reg_child_header}>Users Registered using Non VPS</p>
                    <p className={styles.user_reg_child_number}>
                      {mockData?.TOTAL_USER?.USER_REG?.NON_VPS !== undefined ? mockData?.TOTAL_USER?.USER_REG?.NON_VPS : (
                        <div className={styles.loader_container}>
                          <div className={styles.loader} />
                        </div> 
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Total PNR Booking Statistics: Main Header Div */}
              <div className={styles.pnr_main_container}>

                {/* Main Header Container */}
                <div className={styles.pnr_div_header}>
                  <p className={styles.pnr_header_title}>PNR Booking Statistics</p>
                </div>

                {/* PNR Table Data Container */}
                <div className={styles.pnr_data_container}>
                  <table className={styles.data_table}>
                    <thead className={styles.pnr_tables_head}>
                      <tr>
                        <th>Classification</th>
                        <th>Category</th>
                        <th>1 min</th>
                        <th>3 min</th>
                        <th>5 min</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td>ARP</td>
                        <td>Non VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_NON_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_NON_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_NON_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_NON_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                      <tr>
                        <td>ARP</td>
                        <td>VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.ARP_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                      <tr>
                        <td>Tatkal AC</td>
                        <td>Non VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_NON_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_NON_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_NON_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_NON_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                      <tr>
                        <td>Tatkal AC</td>
                        <td>VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.AC_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                      <tr>
                        <td>Tatkal NON AC</td>
                        <td>Non VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_NON_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_NON_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_NON_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_NON_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                      <tr>
                        <td>Tatkal NON AC</td>
                        <td>VPS</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_VPS?.BREAKDOWN[0].min_1}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_VPS?.BREAKDOWN[0].min_3}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_VPS?.BREAKDOWN[0].min_5}</td>
                        <td>{mockData?.TOTAL_PNR?.PNR_BOOKING?.NON_AC_VPS?.BREAKDOWN[0].min_5}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}
    </>
  );
};

export default daily_status;
