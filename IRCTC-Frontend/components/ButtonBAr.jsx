// Import Libraries
import React from 'react'
import { startOfDay, endOfDay, addDays, subDays, addMonths, endOfMonth, startOfMonth, endOfWeek, startOfWeek } from 'date-fns';
import { CheckPicker, DateRangePicker, IconButton, SelectPicker, Input, Button } from 'rsuite';
import CloseIcon from '@rsuite/icons/Close';
import SearchIcon from '@rsuite/icons/Search';

// Import Styles
import styles from '../styles/ButtonBar.module.scss';

// Initialise data parameters and boundaries for search functionality.

// To enforce limit on date selection in future.
const { afterToday } = DateRangePicker;

// Predefined most used date ranges to apply filters in period of time to improve UX.
const predefinedRanges = [
  {
    label: 'Today',
    value: [new Date(), new Date()],
    placement: 'left'
  },
  {
    label: 'Yesterday',
    value: [addDays(new Date(), -1), addDays(new Date(), -1)],
    placement: 'left'
  },
  {
    label: 'This week',
    value: [startOfWeek(new Date()), endOfWeek(new Date())],
    placement: 'left'
  },
  {
    label: 'Last 7 days',
    value: [subDays(new Date(), 6), new Date()],
    placement: 'left'
  },
  {
    label: 'Last 30 days',
    value: [subDays(new Date(), 29), new Date()],
    placement: 'left'
  },
  {
    label: 'This month',
    value: [startOfMonth(new Date()), new Date()],
    placement: 'left'
  },
  {
    label: 'Last month',
    value: [startOfMonth(addMonths(new Date(), -1)), endOfMonth(addMonths(new Date(), -1))],
    placement: 'left'
  },
  {
    label: 'This year',
    value: [new Date(new Date().getFullYear(), 0, 1), new Date()],
    placement: 'left'
  },
  {
    label: 'Last year',
    value: [new Date(new Date().getFullYear() - 1, 0, 1), new Date(new Date().getFullYear(), 0, 0)],
    placement: 'left'
  },
  {
    label: 'All time',
    value: [new Date(new Date().getFullYear() - 1, 0, 1), new Date()],
    placement: 'left'
  },
  {
    label: 'Last week',
    closeOverlay: false,
    value: value => {
      const [start = new Date()] = value || [];
      return [
        addDays(startOfWeek(start, { weekStartsOn: 0 }), -7),
        addDays(endOfWeek(start, { weekStartsOn: 0 }), -7)
      ];
    },
    appearance: 'default'
  },
  {
    label: 'Next week',
    closeOverlay: false,
    value: value => {
      const [start = new Date()] = value || [];
      return [
        addDays(startOfWeek(start, { weekStartsOn: 0 }), 7),
        addDays(endOfWeek(start, { weekStartsOn: 0 }), 7)
      ];
    },
    appearance: 'default'
  }
];

// Performs the search with appropriate filters set.
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

const tableLengthOptions = [
  5,10,15,20
].map(
  item => ({ label: item, value: item })
);

// Default dates to be set in datepicker when filters are reset.
const defaultDate = [startOfDay(new Date(0)), endOfDay(new Date())]

// FilterBar Component
function ButtonBar(prop) {

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
  
  // Prepare data to inject options in filter on the page.
  // const injectableFilterOptions = prop.availableFilterOptions.map(
  //   item => ({ label: item, value: item })
  // );

  // Change options in the filter for booking type.
  function handleBookingTypeFilterChange(event) {
    prop.dispatch(prop.changeOptions(event))
  }

  // // Reset all filter options.
  // function handleClear() {
  //   // Reset booking type filter options to all values.
  //   dispatch(changeOptions(prop.availableFilterOptions.map(ts => ts)));
  //   // Reset date filter to default date.
  //   dispatch(changeDate(defaultDate));
  // };

  // Render
  return (
    
    <div className={styles.buttonBar + " row mx-auto"}>

      <div className="col-md-auto">
        <IconButton onClick={prop.onsearch} variant="outlined" color="blue" appearance="primary" icon={<SearchIcon />}  >Search</IconButton>
      </div>
      
      <div className="col-md-auto">
        <IconButton className="float-end" onClick={prop.onclear} variant="outlined" color="red" appearance="primary" icon={<CloseIcon />} >Clear</IconButton>
      </div>
    </div>
  )
}

export default ButtonBar;