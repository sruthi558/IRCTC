import React, { useState } from "react";
import { useSelector } from "react-redux";
import { Toggle, Dropdown, Button, IconButton } from "rsuite";
import { toast } from "react-toastify";
import styles from "../styles/BrandMonitoringResult.module.scss";
// Import Stores
import { setImgUrl } from "../store/slice/ModalPopup";
import {deleteDataIndex} from '../store/slice/brandMonitoring'
import Link from "next/link";
import { useRouter } from "next/router";

const BrandMonitoringResult = (data) => {  
  // Define all the actions that the user can request for regarding takedown.
  const td_drop = {
    0: 'Take Action',
    1: 'Initiate Takedown',
    2: 'Takedown Initiated',
    3: 'Takedown Completed',
    4: 'Takedown Rejected',
    5: 'Cease and Desist Required'
  }

  const noimages = {
    'Mobile Application': '/static/images/circular-graphic.svg',
    'Facebook':'/static/images/facebook.svg',
    'Twitter':'/static/images/twitter.svg',
    'Youtube':'/static/images/youtube.svg',
    'Telegram':'/static/images/telegram.svg',
    'Instagram':'/static/images/instagram.svg',
    'Domain':'/static/images/domain.svg',
    'Website':'/static/images/domain.svg',
    'Social Media':'/static/images/Social_media_ico.svg.png'
  }

  // Set state for loader.
  const [keyActive, setKeyActive] = useState(data.data.td_status);

  const [visibleState, setVisibleState] = useState(data.data.visible);

  const userRole = useSelector((state) => state.persistedReducer.role);

  const imageLink =
    data.data.Snapshot && data.data.Snapshot.length > 0
      ? data.data.Snapshot
      : data.data.ProfileImage;
  let severityClass = "low";
  function truncate(str, n) {
    if (str) {
      if (typeof str != "string") {
        str = str.join(" ");
      }
      str = str.replace("\n", " ");
      return str.length > n ? str.slice(0, n - 1) + "..." : str;
    } else {
      return null;
    }
  }
  

  const handleTakedown = eventKey => {
    setTakedownfunc(eventKey, data.data._id.$oid);
    setKeyActive(eventKey);
  }

  const handleImageClick = (e) => {
    e.preventDefault();
    data.dispatch(deleteDataIndex(data.index));
    setVisibility(false, data.data._id.$oid);
    toast.error("Data deleted");
  }

  return (
    <div index={data.index} className={styles.brandMonitoringCardWrapper}>
    <img onClick={handleImageClick} className={styles.xbutton}></img>
    {/* <img onClick={handleImageClick} className={styles.xbutton} src="/static/images/cancel-icon.svg"></img> */}
      <div className={styles.header}>
        <div className={styles.titleWrapper}>
          <h5 className="card-title">{data.data.title}</h5>
        </div>
        <div className="d-flex">
        {/* <div className={styles.showImage+ " me-auto p-2"}>
        {imageLink.length > 0 ? 
          <Button appearance="primary" onClick={handleShowImage} >Show Image</Button> : null }
            {loading && <div>Loading...</div>}
        </div> */}

        {/* <div className={styles.buttonContainer+ " p-2"}>
          <Dropdown appearance="primary" activeKey={keyActive} title={td_drop[keyActive]} disabled = {data.data.td_status > 1 && userRole == 'user' ? true : false} onSelect={eventKey => handleTakedown(eventKey)}>
            <Dropdown.Item eventKey={0}>Request Pending</Dropdown.Item>
            <Dropdown.Item eventKey={1}>Initiate TakeDown</Dropdown.Item>
            { userRole == "admin" ? <Dropdown.Item eventKey={2}>Takedown Initiated</Dropdown.Item>: null }
            { userRole == "admin" ? <Dropdown.Item eventKey={3}>Takedown Completed</Dropdown.Item>: null }
            { userRole == "admin" ? <Dropdown.Item eventKey={4}>Takedown Rejected</Dropdown.Item> : null }
          </Dropdown>
        </div> */}
        </div>
      </div>
      {/* {userRole == "admin" ? (
            <div className={styles.display}>
              Display{" "}
              <Toggle
                checked={visibleState}
                loading={loading}
                arial-label="Switch"
                onChange={(newData) => handleVisibltyIrctc(newData)}
              />
            </div>
          ) : null} */}

      <div className={styles.brandMonitoringCard}>

      {
        false ?

        <div className={styles.imageContainer}>
          <div className={styles.screenshot + " shadow"}>
            <img
              src={imageLink}
              onClick={handleShowImage}
              alt="Image"
            ></img>
          </div>
        </div> : 

        <div className={styles.imageContainer}>
          <div className={styles.noImage}>
            <img
              src={noimages[data.data.threatSource]}
              alt="No Image"
              className={styles.noImage}
            ></img>
          </div>
        </div> 
      }
      <div className={styles.body}>
        <table className="table" >
          <tbody>
            {data.data.Severity && (
              <tr data-toggle="tooltip" title={data.data.Severity}>
                  <td className={styles.label}><b>Severity:</b></td>
                <td><div className={severityClass}>{truncate(data.data.Severity, 30)}</div></td>
              </tr>
            )}
            {data.data.threatSource && (
              <tr data-toggle="tooltip" title={data.data.threatSource}>
                <td className={styles.label}><b>Source:</b></td>
                <td>{truncate(data.data.threatSource, 40)} {data.index}</td>
              </tr>
            )}
            {data.data.requestedDate && (
              <tr data-toggle="tooltip" title={data.data.requestedDate}>
                <td className={styles.label}><b>Requested Date:</b></td>
                <td>{truncate(new Date(data.data.requestedDate?.$date).toDateString(), 30)}</td>
              </tr>
            )}
            {data.data.Link && (
              <tr data-toggle="tooltip" title={data.data.Link}>
                <td className={styles.label}><b>Link:</b></td>
                <td>
                  <a 
                    href={`http://${data.data?.Link}`}
                    className={styles.link}
                    target="_blank"
                  >
                  {truncate(`http://${data.data?.Link}`, 30)}
                  </a>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      </div>
    </div>
  );
};

export default BrandMonitoringResult;
