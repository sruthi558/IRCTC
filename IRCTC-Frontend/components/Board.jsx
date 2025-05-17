// Import Libraries
import React, { useState } from "react";
import ReloadIcon from "@rsuite/icons/Reload";
import { IconButton, Button, DatePicker, Modal, Uploader } from "rsuite";

// Import Styles
import styles from "../styles/Board.module.scss";
import { useRouter } from "next/router";

// import { Button } from 'rsuite';
// Board Component
const Board = (props) => {
  const { pathname } = useRouter();

  const router = useRouter();
  const handleDateChange = (date) => {
    props.setSelectedDate(date);
  };

  const handleReload = (props) => {
    router.reload();
  };

  return (
    <div className={styles.board + " row"}>
      <div className="col mx-auto">
        <h3 className={styles.boardHeading + " mx-auto"}>{props.heading}</h3>
        {pathname === "/daily_status" && (
          <React.Fragment>
            <DatePicker
              className={styles.statusdate}
              defaultValue={props.selectedDate}
              value={props.selectedDate}
              onChange={(date) => {
                handleDateChange(date);
              }}
            />
            <div className={styles.captureDiv}>
              {/* <Button
                onClick={props.captureScreenshot}
                className={styles.screebShotBtn}
              >
                Take Screenshot
              </Button> */}
              <Button 
                onClick={props.saveImgAsPdf} 
                className={styles.screebShotBtn}
              >Save as pdf</Button>
            </div>
          </React.Fragment>
        )}
      </div>

      <div className="col mx-auto">
        <div className={styles.detailsContainer + " float-end"}>
          {props.action && (
            <div className={styles.action}>
              <Button
                className={styles.board_btn}
                appearance="primary"
                onClick={props.action.handler}
              >
                {props.action.label}
              </Button>
              {props.action.label1 ? (
                <Button
                  className={styles.board_btn}
                  appearance="primary"
                  onClick={props.action.handler1}
                >
                  {props.action.label1}
                </Button>
              ) : null}
              {/* <button className={styles.board_btn} onClick={props.action.handler}>
                {props.action.label}
              </button> */}
            </div>
          )}
          {pathname !== "/suspected-pnrs" && (
            <IconButton
              icon={<ReloadIcon />}
              color="blue"
              onClick={handleReload}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Board;