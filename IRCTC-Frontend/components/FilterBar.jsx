// Import Libraries
import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import {
  startOfDay,
  endOfDay,
  addDays,
  subDays,
  addMonths,
  endOfMonth,
  startOfMonth,
  endOfWeek,
  startOfWeek,
} from "date-fns";
import {
  CheckPicker,
  DateRangePicker,
  IconButton,
  SelectPicker,
  Input,
  Button,
} from "rsuite";
import CloseIcon from "@rsuite/icons/Close";
import SearchIcon from "@rsuite/icons/Search";
import { useSelector, useDispatch } from "react-redux";

// Import Styles
import styles from "../styles/FilterBar.module.scss";

// Initialise data parameters and boundaries for search functionality.

// To enforce limit on date selection in future.
const { afterToday } = DateRangePicker;

// Performs the search with appropriate filters set.
function handleSearch() {
  const dispatch = useDispatch();
  const { searchValue, handleSearchValue } = props;

  // Length check for keyword search.
  // if (useridSearchValue.length < 3 && useridSearchValue.length != 0) {
  //     toast.error("Please enter keyword search more than 2 characters")
  // } else {

  // Start the loader.
  dispatch(setLoadingTrue());

  // Check if any search parameters are present, and if so, honour the filters.
  // Otherwise, complete unfiltered data is displayed.
  // This check has to be maintained since original data is cached on first page load, so the logic needs to check whether a new query has to be made as per the filters or original cached data should be shown if no filters are active.
  dispatch(prop.changeSearchToggle(true));

  // Stop the loader.
  dispatch(setLoadingFalse());
  // }
}

const tableLengthOptions = [5, 10, 15, 20].map((item) => ({
  label: item,
  value: item,
}));

// Default dates to be set in datepicker when filters are reset.
const defaultDate = [startOfDay(new Date(0)), endOfDay(new Date())];

// FilterBar Component
function FilterBar(prop) {
  const { handleDateRangeChange } = prop;
  function handleSearch() {
    // Length check for keyword search.
    // if (useridSearchValue.length < 3 && useridSearchValue.length != 0) {
    //     toast.error("Please enter keyword search more than 2 characters")
    // } else {

    // Start the loader.
    dispatch(setLoadingTrue());

    // Check if any search parameters are present, and if so, honour the filters.
    // Otherwise, complete unfiltered data is displayed.
    // This check has to be maintained since original data is cached on first page load, so the logic needs to check whether a new query has to be made as per the filters or original cached data should be shown if no filters are active.
    dispatch(prop.changeSearchToggle(true));

    // Stop the loader.
    dispatch(setLoadingFalse());
    // }
  }

  // Reset all the applied filters and display the complete unfiltered data.
  function handleClear() {
    // Set no search flag, that is, no filters have been applied and therefore complete unfiltered data is to be displayed.
    dispatch(prop.changeSearchToggle(false));

    onclear();
  }

  // Change options in the filter for booking type.
  function handleBookingTypeFilterChange(event) {
    prop.dispatch(prop.changeOptions(event));
  }

  const { asPath } = useRouter();
  const handleDateChange = (ranges) => {
    console.log(ranges);
    handleDateRangeChange(prop.dateRange); // pass dateRange as argument here
  };

  const handleFilterReport = (value) => {
    prop.setFilterOption(value);
  };

  const handleSearchValues = (value) => {
    prop.setSearchValue(value);
  };
  const hnadleBrandSearchValues = (value) => {
    prop.setSearchValue(value);
  };

  const eraseHandler = () => {
    prop.setSearchValue("");
    prop.setDateRange("");
  };

  const handleSearchChange = (value) => {
    prop?.setSearchInputText(value);
  };
  return (
    <>
      <div className={styles.filterBar + " d-flex"}>
        <div style={{ display: "flex" }}>
          {asPath === "/brand-monitoring" && (
            <DateRangePicker
              format={prop.format}
              hoverRange={prop.hoverange}
              value={prop.searchDate}
              onChange={prop.setSearchDate}
              disabledDate={afterToday()}
            />
          )}
          {asPath === "/brand-monitoring" && (
            <Input
              label="Keyword Search"
              placeholder="Keyword Search"
              value={prop.searchValue}
              onChange={hnadleBrandSearchValues}
              className={styles.brandMonSearchStyle}
            />
          )}

          {asPath === "/reports" && (
            <div className="m-auto ">
              <CheckPicker
                label="Type"
                value={prop.selectedFilterOptions}
                data={prop.availableFilterOptions}
                onChange={handleFilterReport}
                style={{ width: 230 }}
              />

              <DateRangePicker
                className={styles.reportDatePicker}
                style={{ margin: "10px" }}
                onChange={prop.handleDateRangeChange}
                value={prop.dateRange}
              />
            </div>
          )}

          <div className={styles.softwareProBoardButs_main_div}>
            <div className={styles.softwareProBoardButs_sub_div}>
              {asPath === "/software-procurement" && (
                <DateRangePicker
                  onChange={prop.handleDateRangeChange}
                  value={prop.dateRange}
                />
              )}

              {asPath == "/software-procurement" && (
                <Input
                  label="Keyword Search"
                  placeholder="Keyword Search"
                  value={prop.searchValue}
                  onChange={handleSearchValues}
                  className={styles.softwareSearchInput}
                />
              )}
            </div>
          </div>
        </div>

        <div style={{ display: "flex" }}>
          {prop.tableLength ? (
            <div className="p-2">
              <SelectPicker
                label="No. of Entries"
                data={tableLengthOptions}
                value={prop.tableLength}
                onChange={(newvalue) =>
                  prop.dispatch(prop.changeBarLength(newvalue))
                }
                style={{ minWidth: 120 }}
              />
            </div>
          ) : null}

          {/* </div> */}
        </div>

        <div className={styles.reportBoardButs_main_div}>
          <div className={styles.reportBoardButs_sub_div}>
            {asPath === "/reports" && (
              <IconButton
                onClick={prop.onsearch}
                variant="outlined"
                color="blue"
                appearance="primary"
                icon={<SearchIcon style={{ height: "40px" }} />}
                style={{ minWidth: 100, height: "40px" }}
              >
                Search
              </IconButton>
            )}

            {asPath === "/reports" && (
              <IconButton
                onClick={prop.onclear}
                variant="outlined"
                color="red"
                appearance="primary"
                icon={<CloseIcon style={{ height: "40px" }} />}
                style={{ minWidth: 100, height: "40px" }}
              >
                Clear
              </IconButton>
            )}
          </div>

          <div className={styles.softwareProBoardButs_three_btn_div}>
            {asPath === "/software-procurement" && (
              <IconButton
                onClick={prop.onsearch}
                variant="outlined"
                color="blue"
                appearance="primary"
                className={styles.softwareBtns}
                icon={<SearchIcon style={{ height: "38px" }} />}
                style={{ minWidth: 100, height: "38px" }}
              >
                Search
              </IconButton>
            )}

            {asPath === "/software-procurement" && (
              <Button
                onClick={prop.handleVPSExport}
                // className={styles.exportbtn}
                appearance="primary"
                style={{ minWidth: 100, height: "38px" }}
              >
                Export
              </Button>
              // {prop.exportDataFunction}
            )}
            {asPath === "/software-procurement" && (
              <IconButton
                onClick={eraseHandler}
                variant="outlined"
                color="red"
                appearance="primary"
                // className={styles.softwareBtns}
                icon={<CloseIcon style={{ height: "38px" }} />}
                style={{ minWidth: 100, height: "38px" }}
              >
                Clear
              </IconButton>
            )}
          </div>

          <div className={styles.brandMonBoardButs_main_div}>
            <div className={styles.brandMonBoardButs_sub_div}>
              {asPath === "/brand-monitoring" && (
                <IconButton
                  pageLoading={prop.pageLoading}
                  onClick={() => {
                    prop.onsearch();
                    prop.setIsSearch(true);
                  }}
                  variant="outlined"
                  color="blue"
                  appearance="primary"
                  icon={<SearchIcon style={{ height: "40px" }} />}
                  style={{ minWidth: 100, height: "40px" }}
                >
                  Search
                </IconButton>
              )}

              {asPath === "/brand-monitoring" && (
                <IconButton
                  onClick={prop.onclear}
                  variant="outlined"
                  color="red"
                  appearance="primary"
                  icon={<CloseIcon style={{ height: "40px" }} />}
                  style={{ minWidth: 100, height: "40px" }}
                >
                  Clear
                </IconButton>
              )}
            </div>
          </div>
        </div>
      </div>
      <div className={styles.toutsBut_main_div}>
        <div className={styles.toutsBut_sub_div}>
          {asPath === "/touts_details" && (
            <>
              <Input
                value={prop?.searchInputText}
                onChange={handleSearchChange}
                label="Keyword Search"
                placeholder="Keyword Search"
                className={styles.toutsSearchInput}
              />
              {/* <Button onClick={handleSearchClick}>Search</Button> */}

              <IconButton
                onClick={prop?.searchFilter}
                variant="outlined"
                color="blue"
                appearance="primary"
                className={styles.toutssearchBtn}
                icon={
                  <SearchIcon style={{ height: "38px", textAlign: "center" }} />
                }
                style={{ minWidth: 120, height: "38px" }}
              >
                Search
              </IconButton>
              <Button appearance="primary" 
              style={{ minWidth: 100, height: "38px" }}
              onClick={prop?.handleExportBtn}> Export </Button>
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default FilterBar;
