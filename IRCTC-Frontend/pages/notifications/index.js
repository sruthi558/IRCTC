// endpoint
const endPoint = 'http://127.0.0.1:8000'

// Import Libraries
import { useEffect, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Table, Popover, Dropdown, Pagination } from 'rsuite'
const { Column, HeaderCell, Cell } = Table
import { Button, Modal, Uploader, Nav } from 'rsuite'
import { validateUserCookiesFromSSR } from '../../utils/userVerification'

// Import Components
import Board from '../../components/Board'
import FilterBar from '../../components/FilterBar'

// Import Styles
import styles from './Notification.module.scss'

// Import Store
import userid, {
  changeOverviewFilterDate,
  changeOverviewFilterOption,
  changeTableLength,
} from '../../store/slice/analysis'

// ActionCell: Custom Component, likely renders a clickable cell in a table
const ActionCell = ({ rowData, dataKey, onClick, ...props }) => {
  return (
    <Cell {...props} style={{ padding: '6px' }}>
      <Button
        appearance="primary"
        onClick={() => {
          onClick(rowData.id)
        }}
      >
        {rowData.status === 'Processed' ? 'Download' : 'Processing'}
      </Button>
    </Cell>
  )
}

// The renderMenu function renders a Popover component that contains a Dropdown.Menu component,
const renderMenu = ({ onClose, left, top, className }, ref) => {
  const handleSelect = (eventKey) => {
    onClose()
    console.log(eventKey)
  }
  return (
    <Popover ref={ref} className={className} style={{ left, top }} full>
      <Dropdown.Menu onSelect={handleSelect}>
        <Dropdown.Item eventKey={1}>Edit</Dropdown.Item>
        <Dropdown.Item eventKey={2}>Delete</Dropdown.Item>
      </Dropdown.Menu>
    </Popover>
  )
}

// Dashboard Component
const SusUsers = () => {
  // Initialise the dispatcher.
  const dispatch = useDispatch()
  // userRole contains the role of the user currently logged in for role-based restrictions.
  const userRole = useSelector((state) => state.persistedReducer.role)
  const useridData = useSelector((state) => state.analysis.data)
  // This state variable is used to determine whether to show a form or UI for creating a new user.
  const [showNewUser, setShowNewUser] = useState(false)
  // This is another piece of data from the Redux store that contains the total number of pages for the user IDs.
  const useridPageCount = useSelector((state) => state.analysis.pageCount)
  // active is a state variable that holds the active item in navbar.
  const [active, setActive] = useState('home')
  // This state variable is used to indicate whether some asynchronous operation is currently loading or not.
  const [loading, setLoading] = useState(false)
  // This state variable determines the number of items to display per page.
  const [limit, setLimit] = useState(10)
  // This state variable determines the current page of users being displayed.
  const [page, setPage] = useState(1)
  //   CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: 'blue' }} />
  // Initialise the date to be searched through the data.
  const overviewDate = useSelector((state) => state.dashboard.searchDate)
  // This is a piece of data from the Redux store that contains information used to display charts on a dashboard.
  const chartsData = useSelector((state) => state.dashboard.data)
  // This state variable contains the number of items to display in a table on the dashboard.
  const displayCount = useSelector((state) => state.dashboard.tableLength)
  // Initialise the filters to be used while searching through the data.
  const filterOverviewOptions = useSelector((state) => state.dashboard.filterOption)
  // Available filter options for this page.
  const options = ['ARP', 'Tatkal AC', 'Tatkal Non-AC', ' User Registration']

  // API Call: /api/brandmon_list_all.
  const pagiFunc = async (page_value, table_length) => {
    const data = await fetch('/api/analysis_list_all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_id: page_value,
      }),
    })
      .then((res) => res.json())
      .then(() => setLoading(false))
  }

  // API Call'/api/userid_pagecount_all'
  const initTotalPageCount = async (value) => {
    const data = await fetch('/api/userid_pagecount_all', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    }).then((res) => res.json())
    // dispatch(initPageCount(data.page_count));
  }

  useEffect(() => {
    setLoading(true)
    pagiFunc(1, 10)
    //initTotalPageCount();
  }, [])

  // Handle Search 
  const handleSearch = () => {
    setLoading(true)
    OverviewSearchDate(overviewDate, filterOverviewOptions)
  }

  // Handle Page Change 
  const handlePageChange = (dataKey) => {
    setPage(dataKey)
    pagiFunc(dataKey, limit)
  }

  // This function will be called when the user selects a new limit in the limit dropdown,
  // and will update the page state to 1, the limit state to the selected limit, and call,
  // the pagiFunc function with page 1 and the new limit.
  const handleChangeLimit = (dataKey) => {
    setPage(1)
    setLimit(dataKey)
    pagiFunc(1, dataKey)
  }

  const downloadHandler = () => {
    console.log(1)
  }

  // close or remove the opened modal
  const closeModal = () => {
    setShowNewUser(false)
  }

  // Function to close Modal
  const openModal = () => {
    setShowNewUser(true)
  }

  // This is a Navbar component that displays navigation items based on the user's role.
  const Navbar = ({ active, onSelect, ...props }) => {
    return (
      <Nav
        {...props}
        activeKey={active}
        onSelect={onSelect}
        style={{ marginBottom: 50 }}
      >
        <Nav.Item eventKey="news">All Notifications</Nav.Item>
        <Nav.Item eventKey="solutions">Brand-Monitoring</Nav.Item>
        <Nav.Item eventKey="products">File Upload</Nav.Item>
        {userRole == 'admin' ? (
          <Nav.Item eventKey="about">User Monitoring</Nav.Item>
        ) : null}
      </Nav>
    )
  }

  // Render
  return (
    <>
      {/* Modal Starts */}
      <Modal open={showNewUser} onClose={closeModal} className={styles.modal}>
        <Modal.Header as="h1">
          <Modal.Title as="h1">File Upload</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Uploader action="//jsonplaceholder.typicode.com/posts/" multiple />
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={closeModal} appearance="primary">
            Submit
          </Button>
          <Button onClick={closeModal} appearance="subtle">
            Cancel
          </Button>
        </Modal.Footer>
      </Modal>
      {/* Modal Ends*/}
      <div className={styles.dashboard}>
        <div className={styles.sidebar}>
          <Sidebar />
        </div>

        <div className={styles.page}>
          <Board heading="Notifications" />

          <FilterBar
            selectedFilterOptions={filterOverviewOptions}
            availableFilterOptions={options}
            tableLength={displayCount}
            changeOptions={changeOverviewFilterOption}
            pageSource="Overview"
            changeDate={changeOverviewFilterDate}
            valuedate={overviewDate}
            onsearch={handleSearch}
            changeBarLength={changeTableLength}
            dispatch={dispatch}
          />

          <div
            className="col mx-auto"
            style={{
              display: 'block',
              paddingLeft: 30,
              marginTop: 20,
            }}
          >
            <Navbar appearance="tabs" active={active} onSelect={setActive} />
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
                layout={['total', '-', 'limit', '|', 'pager', 'skip']}
                total={useridPageCount}
                limit={limit}
                activePage={page}
                onChangePage={handlePageChange}
                onChangeLimit={handleChangeLimit}
              />
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default SusUsers

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res)
}
