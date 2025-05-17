// endpoint
const endPoint = process.env.API_ENDPOINT;

// Import Libraries
import React, { useEffect, useState, forwardRef, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  Table,
  Popover,
  Whisper,
  IconButton,
  Input,
  Dropdown,
  CheckPicker,
  Steps,
  Tab,
  Nav,
  InputGroup,
} from "rsuite";
const { Column, HeaderCell, Cell } = Table;
import { Button, Modal, SelectPicker } from "rsuite";

const { Step } = Steps;
// const { Item: NavItem, Panel: NavPanel } = Nav;
const { Item: NavItem } = Nav;

// Import Components
import Board from "../../components/Board";
import Sidebar from "../../components/Sidebar";
import { validateUserCookiesFromSSR } from "../../utils/userVerification";
import Router, { useRouter } from "next/router";

import MoreIcon from "@rsuite/icons/legacy/More";
// Import Styles
import styles from "./Admin.module.scss";

import CloseIcon from "@rsuite/icons/Close";
import EyeIcon from '@rsuite/icons/legacy/Eye';
import EyeSlashIcon from '@rsuite/icons/legacy/EyeSlash';
import AvatarIcon from '@rsuite/icons/legacy/Avatar';

// Import Store
import { initPageCount } from "../../store/slice/userid";

const Textarea = forwardRef((props, ref) => (
  <Input {...props} as="textarea" ref={ref} />
));

import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
// USER PERMISSIONS
import { current_pages, user_allowed_actions } from "@/utils/dashboard.pages";

// Dropdown select option with: admin and user option
const selectData = ["admin", "user"].map((item) => ({
  label: item,
  value: item,
}));

const selectDepartment = ["Board", "Irctc", "Pinaca", "IT"].map((item) => ({
  label: item,
  value: item,
}));

// Whisper: component that displays popover or toolip
const ActionCell = ({ rowData, dataKey, ...props }) => {
  return (
    <Cell {...props} className="link-group">
      <Whisper
        placement="autoVerticalStart"
        trigger="click"
        speaker={renderMenu}
      >
        <IconButton appearance="subtle" icon={<MoreIcon />} />
      </Whisper>
    </Cell>
  );
};

// Render Popover Menu: that contains Dropdown.Menu Component (List of Dropdown.Items)
const renderMenu = ({ left, top, className }, ref) => {
  const handleSelect = (eventKey) => {
    if (eventKey == 1) {
    } else if (eventKey == 2) {
    }
  };
  return (
    <Popover ref={ref} className={className} style={{ left, top }} full>
      <Dropdown.Menu onSelect={handleSelect}>
        <Dropdown.Item eventKey={1}>Edit</Dropdown.Item>
        <Dropdown.Item eventKey={2}>Delete</Dropdown.Item>
      </Dropdown.Menu>
    </Popover>
  );
};

// Dashboard Component
const SusUsers = () => {
  const dispatch = useDispatch();
  const useridData = useSelector((state) => state.userid.data); // userId info from Redux
  const [showNewUser, setShowNewUser] = useState(false); // create new user

  const [editUserModal, setEditUserModal] = useState(false);

  // GET USER - allowed page permission and allowed page action
  const allowed_page = useSelector(
    (state) => state.persistedReducer.user_pages
  );
  const allowed_action = useSelector(
    (state) => state.persistedReducer.user_actions
  );

  const allowedPages = [];
  const allowedActions = [];

  if (allowed_page && allowed_action) {
    allowedPages.push(allowed_page);
    allowedActions.push(allowed_action);
  }

  // Initialize the router to get the routing info of the page
  const router = useRouter();

  useEffect(() => {
    if (!allowed_page?.admin) {
      router.push("/overview");
    }
  }, []);

  const [loading, setLoading] = useState(false);
  const [limit, setLimit] = useState(10); // no. of items displaed/page
  const [page, setPage] = useState(1); // currently displayed page
  const [softMainLoading, setSoftMainLoading] = useState(false);
  const [tableData, setTableData] = useState([]);

  //CompactCell is a functional component that returns a custom Cell with blue color styling.
  const CompactCell = (props) => <Cell {...props} style={{ color: "blue" }} />;

  // Initialise the date to be searched through the data.
  const overviewDate = useSelector((state) => state.dashboard.searchDate);

  // Initialise the filters to be used while searching through the data.
  // Default is all: ARP, Tatkal AC and Tatkal Non-AC.
  const filterOverviewOptions = useSelector(
    (state) => state.dashboard.filterOption
  );

  const [selectedPages, setSelectedPages] = useState({});
  const [selectedAction, setSelectedAction] = useState({});
  const [currentStep, setCurrentStep] = useState(0);

  // new View Modal states----------
  const [userViewData, setUserViewData] = useState(false);
  const [selectedActions, setSelectedActions] = useState({});
  const [viewEmail, setViewEmail] = useState("");

  const [allInputs, setAllInputs] = useState({
    username: "",
    name: "",
    email: "",
    password: "",
    department: "",
    departmentrole: "",
    role: "",
    user_pages: [],
    user_actions: [],
  });

  const [inputValidity, setInputValidity] = useState({});
  const [editUserData, setEditUserData] = useState(null);
  const [editUserRole, setEditUserRole] = useState("");
  const [editUserPages, setEditUserPages] = useState({});
  const [editUserActions, setEditUserActions] = useState({});
  const [modalId, setModalId] = useState();
  const [selectedUserRole, setSelectedUserRole] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");

  const [editFormData, setEditFormData] = useState({
    username: "",
    name: "",
    email: "",
    password: "",
    department: "",
    departmentrole: "",
    role: "",
  });

  const userPages = current_pages.map((item) => ({
    label: item.page,
    value: item.page,
  }));

  let userActionsVal = [];
  Object.keys(user_allowed_actions[0]).map((x) => {
    userActionsVal.push({
      label: x,
      value: x,
      selected: selectedActions[x] || false, // Track selected state
    });
  });

  // API Call /api/brandmon_list_all
  const pagiFunc = async (page_value, table_length) => {
    try {
      setSoftMainLoading(true);
      const response = await fetch("/api/admin_panel", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      });
      const res_data = await response.json();
      setTableData(res_data).catch((err) =>
        console.error(`Error getting the data: ${err}`)
      );
    } catch (error) {
      console.error("Error fetching table data:", error);
    }
    setSoftMainLoading(false);
  };

  const handleUserRoleChange = (val) => {
    setSelectedUserRole(val);
    allInputs.role = val;
    setAllInputs(allInputs);
  };
  const handleDepartmentChange = (val) => {
    setSelectedDepartment(val);
    allInputs.departmentrole = val;
    setAllInputs(allInputs);
  };

  // This useEffect hook will be executed only once when the component mounts,
  // and will set the loading state to true and call the pagiFunc function with page 1 and limit 10.
  useEffect(() => {
    setLoading(true);
    pagiFunc(1, 10);
  }, []);

  // Handle Search
  const handleSearch = () => {
    setLoading(true);
    pagiFunc(overviewDate, filterOverviewOptions);
  };

  // Handle Pagination Change
  const handlePageChange = (dataKey) => {
    setPage(dataKey);
    pagiFunc(dataKey, limit);
  };

  // This function will be called when the user selects a new limit in the limit dropdown,
  // and will update the page state to 1, the limit state to the selected limit, and call,
  // the pagiFunc function with page 1 and the new limit.
  const handleChangeLimit = (dataKey) => {
    setPage(1);
    setLimit(dataKey);
    pagiFunc(1, dataKey);
  };

  const downloadHandler = () => {
    console.log(1);
  };

  const closeModal = () => {
    setUserViewData(false);
    setEditUserModal(false);
  };

  const closeAddUserModal = () =>{
    setShowNewUser(false);
  }
  const openViewModal = (email) => {
    setUserViewData(true);
    setCurrentStep(0);
    setViewEmail(email);
  };

  const handleEditInputChange = (e) => {
    const { name, value } = e.target;
    setEditUserData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  // Function to open Modal
  const openModal = () => {
    setShowNewUser(true);
  };

  // API Call to Delete User '/api/delete_user?email', .
  const deleteUser = async (email) => {
    const data = await fetch("/api/delete_user?email=" + email).then((res) =>
      res.json()
    );
    toast.success(data["detail"]);
    setTimeout(function () {
      Router.reload();
    }, 4000);
  };

  const handleSelect = (eventKey) => {
    console.log(eventKey);
  };

  // Handle Submit
  const formSubmit = async (e) => {
    e.preventDefault();
    // Signup API Call '/api/signup'
    if (!allInputs) {
      console.error('all', allInputs);
      return;
    }
    const emptyFields = Object.keys(allInputs).filter((key) => !allInputs[key]);

    if (emptyFields.length > 0) {
      toast.error(`Please fill the ${emptyFields.join(", ")} field(s)`);
      return;
    }

    if (
      !Object.values(allInputs.user_pages).some((selected) => selected) &&
      allInputs.user_actions.length === 0
    ) {
      toast.error("Please select at least one user page or user action");
      return;
    }

    if (!Object.values(allInputs.user_pages).some((selected) => selected)) {
      toast.error("Please select at least one user page");
      return;
    }
    if (!Object.values(allInputs.user_actions).some((selected) => selected)) {
      toast.error("Please select at least one user action");
      return;
    }

    try {
      const data = await fetch("/api/signup", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...allInputs,
        }),
      });
      const responseData = await data.json();

      if (!data.ok) {
        const err_msg = responseData.message || "Unknown error occured";
        toast.error(`Error: ${err_msg}`);
      } else {
        toast.success("User created successfully!!");
        setTimeout(function () {
          Router.reload();
        }, 4000);
        // setShowNewUser(false);
      }
      console.log(`Data status: ${data.ok}`);
    } catch (error) {
      console.error(`Error: ${error}`);
      console.log("An error occured, please try again.");
    }
  };

  const editFormSUbmitObject = (array) => {
    return array.reduce((obj, item) => {
      obj[item] = true;
      return obj;
    }, {});
  };

  const EditFormSubmit = async (e) => {
    closeModal();
    e.preventDefault();
    const userPagesObject = editFormSUbmitObject(editUserPages);
    const userActionsObject = editFormSUbmitObject(editUserActions);
    try {
      const data = await fetch("/api/edit_user", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...editFormData,
          user_pages: userPagesObject,
          user_actions: userActionsObject,
          id: modalId,
        }),
      });
      const responseData = await data.json();

      if (!data.ok) {
        const err_msg = responseData.message || "Unknown error occured";
        toast.error(`Error: ${err_msg}`);
      } else {
        toast.success("User Edited successfully!!");
        setTimeout(function () {
          Router.reload();
        }, 4000);
        // setShowNewUser(false);
      }
      console.log(`Data status: ${data.ok}`);
    } catch (error) {
      console.error(`Error: ${error}`);
      console.log("An error occured, please try again.");
    }
  };

  const handleUserPagesCheckboxClick = (checkedValues) => {
    setAllInputs((prev) => {
      const updatedPages = userPages.reduce((acc, page) => {
        acc[page.value] = checkedValues.includes(page.value);
        return acc;
      }, {});

      return {
        ...prev,
        user_pages: updatedPages,
      };
    });
  };

  const handleUserActionsCheckboxClick = (checkedValues) => {
    setAllInputs((prev) => {
      const updatedAction = userActionsVal.reduce((acc, page) => {
        acc[page.value] = checkedValues.includes(page.value);
        return acc;
      }, {});

      return {
        ...prev,
        user_actions: updatedAction,
      };
    });
  };

  const handleColumnNameChange = (value, name) => {
    setAllInputs((prev) => ({
      ...prev,
      [name]: value ?? "",
    }));

    // Update input validity
    setInputValidity((prev) => ({
      ...prev,
      [name]: !!value?.trim(),
    }));
  };

  const handleTabChange = (eventKey) => {
    setCurrentStep(Number(eventKey));
  };

  const openEditModal = (userData) => {
    setEditUserData(userData);
    setEditUserRole(userData.role || "");
    // let allowedPagesArr = Object.fromEntries(current_pages.map(x => [x.page, userData.user_pages[x.page]?true:false]));

    // let allowedActionArr = Object.keys(user_allowed_actions).filter(
    //   (key) => userData.user_actions[key]?true:false
    // )
    let allowedPagesArr = Object.keys(userData.user_pages).filter(
      (key) => userData.user_pages[key]
    );
    let allowedActionArr = Object.keys(userData.user_actions).filter(
      (key) => userData.user_actions[key]
    );

    setEditUserPages(allowedPagesArr);
    setEditUserActions(allowedActionArr);
    setEditFormData(userData);
    setEditUserModal(true);
  };
  const [visible, setVisible] = useState(false);

  const handleChange = () => {
    setVisible(!visible);
  };

  return (
    <>
      {/* ADD USER MODAL */}
      {allowed_page?.admin && allowed_action.upload && (
        <Modal
          open={showNewUser}
          onClose={closeAddUserModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon onClick={() => closeAddUserModal()} className={styles.clear} />
          <h3> User Registration </h3>
          <Modal.Body>
          <InputGroup  className={`${styles.inputBoxes} ${
                !inputValidity.username ? styles.invalid : ""
              }`}>
          <InputGroup.Addon className={styles.inputAddons}>Username</InputGroup.Addon>
            <Input
              name="username"
              autoComplete="off" 
              // type="text"
              // value={`Username: ${allInputs.username|| ''}`}
              onChange={(value) => {
                handleColumnNameChange(value, "username");
                setInputValidity((prev) => ({
                  ...prev,
                  username: !!value.trim(),
                }));
              }}
            />
            </InputGroup>
            {/* {!allInputs.username && <span className={`${styles.requiredstar} ${!inputValidity.username ? styles.invalid : ''}`}></span>} */}
            <InputGroup  className={`${styles.inputBoxes} ${
                !inputValidity.name ? styles.invalid : ""
              }`}>
            <InputGroup.Addon className={styles.inputAddons}>Full Name</InputGroup.Addon>
            <Input
              name="name"
              type="text"
              // value={allInputs.name}
              onChange={(value) => {
                handleColumnNameChange(value, "name");
                setInputValidity((prev) => ({
                  ...prev,
                  name: !!value.trim(),
                }));
              }}
             
            />
            </InputGroup>
            {/* {!allInputs.name && <span className={`${styles.requiredstar} ${!inputValidity.name ? styles.invalid : ''}`}></span>} */}
            <InputGroup  className={`${styles.inputBoxes} ${
                !inputValidity.email ? styles.invalid : ""
              }`}>
            <InputGroup.Addon className={styles.inputAddons}> Email </InputGroup.Addon>
            <Input
              name="email"
              // type="text"
              autoComplete="off" // Disable autofill
              onChange={(value) => {
                handleColumnNameChange(value, "email");
                setInputValidity((prev) => ({
                  ...prev,
                  email: !!value.trim(),
                }));
              }}             
            />
             </InputGroup>
            
             <InputGroup className={`${styles.inputBoxes} ${
                !inputValidity.password ? styles.invalid : ""
              }`}>
            <InputGroup.Addon className={styles.inputAddons}>Password</InputGroup.Addon>
            <Input
              name="password"
              // type="password"
              // autoComplete="off" // Disable autofill but not working
              autoComplete="new-password"
              type={visible ? 'text' : 'password'}  
              onChange={(value) => {
                handleColumnNameChange(value, "password");
                setInputValidity((prev) => ({
                  ...prev,
                  password: !!value.trim(),
                }));
              }}              
            />
            {/* code for hide unHide password with icon. */}
             <InputGroup.Button onClick={handleChange}> 
              {visible ? <EyeIcon /> : <EyeSlashIcon />}
            </InputGroup.Button>
            </InputGroup>
            
            <InputGroup  className={`${styles.inputBoxes} ${
                !inputValidity.department ? styles.invalid : ""
              }`}>
            <InputGroup.Addon className={styles.inputAddons}>Department</InputGroup.Addon>
            <Input
              name="department"
              type="text"
              onChange={(value) => {
                handleColumnNameChange(value, "department");
                setInputValidity((prev) => ({
                  ...prev,
                  department: !!value.trim(),
                }));
              }}             
            />
            </InputGroup>

            {/* <InputGroup  className={`${styles.inputBoxes} ${
                !inputValidity.departmentrole ? styles.invalid : ""
              }`}>
            <InputGroup.Addon>Department Role</InputGroup.Addon>
            <Input
              name="departmentrole"
              type="text"
              onChange={(value) => {
                handleColumnNameChange(value, "departmentrole");
                setInputValidity((prev) => ({
                  ...prev,
                  departmentrole: !!value.trim(),
                }));
              }}             
            />
            </InputGroup> */}
            <br />
            <SelectPicker
              label="Department Role"
              className={styles.selectpickers}
              data={selectDepartment}
              onChange={(newValue) => handleDepartmentChange(newValue)}
              searchable={false}
            />
            <br />
            <SelectPicker
              label="Role"
              searchable={false}
              className={styles.selectpickers}
              data={selectData}
              onChange={(newValue) => handleUserRoleChange(newValue)}
            />
            <br />
            <div>
              <CheckPicker
                data={userPages}
                label="Access Pages"
                searchable={false}
                onChange={handleUserPagesCheckboxClick}
                className={styles.selectpickers}
                placement="topStart"
                disabledItemValues={selectedUserRole === "user" ? ["admin"] : []}
                />
            </div>
            <div>
              <CheckPicker
                data={userActionsVal}
                label="Allowed Actions"
                onChange={handleUserActionsCheckboxClick}
                className={styles.selectpickers}
                placement="topStart"
                searchable={false}
              />
            </div>
            <br />
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={formSubmit} appearance="primary">
              Submit
            </Button>
            <Button onClick={closeAddUserModal} appearance="subtle">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* EDIT MODAL */}
      {allowed_page?.admin && allowed_action.edit && (
        <Modal
          open={editUserModal}
          onClose={closeModal}
          className={styles.modal}
          backdrop="static"
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <h3>Edit User Registration</h3>
          <Modal.Body>
            <Input
              name="username"
              type="text"
              value={`Username: ${editUserData?.username || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Username"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <Input
              name="name"
              type="text"
              value={`Fullname: ${editUserData?.name || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Full Name"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <Input
              name="email"
              type="text"
              value={`Email: ${editUserData?.email || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Email"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <Input
              name="password"
              type="password"
              value={`Password: ${editUserData?.password || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Password"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <Input
              name="department"
              type="text"
              value={`Department: ${editUserData?.department || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Department"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <Input
              name="departmentrole"
              type="text"
              value={`Department Role: ${editUserData?.department_role || ""}`}
              onChange={(e) => handleEditInputChange(e)}
              placeholder="Department Role"
              className={styles.editInputBoxes}
              disabled
            />
            <br />
            <SelectPicker
              label="Role"
              className={styles.editInputRole}
              data={selectData}
              value={editUserRole}
              onChange={(newValue) => handleUserRoleChange(newValue)}
              disabled={true}
            />
            <br />
            <div>
              <CheckPicker
                data={userPages}
                label="Access Pages"
                value={editUserPages}
                onChange={(value) => setEditUserPages(value)}
                className={styles.editInputBoxes}
                placement="topStart"
                disabledItemValues={editUserRole === "user" ? ["admin"] : []}
              />
            </div>
            <br />
            <div>
              <CheckPicker
                data={userActionsVal}
                label="Allowed Actions"
                value={editUserActions}
                onChange={(value) => setEditUserActions(value)}
                className={styles.editInputBoxes}
                placement="topStart"
              />
            </div>
            <br />
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={EditFormSubmit} appearance="primary">
              Submit
            </Button>
            <Button onClick={closeModal} appearance="default">
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* VIEW MODAL */}
      {allowed_page?.admin && allowed_action.view && (
        <Modal
          open={userViewData}
          onClose={closeModal}
          size="sm"
          backdrop="static"
        >
          <CloseIcon onClick={() => closeModal()} className={styles.clear} />
          <h4>User Allowed Pages & Actions</h4>
          <Modal.Body className={styles.viewBody}>
            <Nav
              appearance="tabs"
              activeKey={currentStep.toString()}
              onSelect={handleTabChange}
              className={styles.navstyle}
            >
              <NavItem eventKey="0" className={styles.textStyle}>
                Allowed Pages
              </NavItem>
              <NavItem eventKey="1" className={styles.textStyle}>
                Allowed Action
              </NavItem>
            </Nav>
            <div style={{ marginTop: 10 }}>
              {currentStep === 0 && (
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Pages</th>
                      <th>Access</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(selectedPages).map((page, index) => {
                      return (
                        <tr key={page[0]}>
                          <td className={styles.tdstyle}>{page[0]}</td>
                          <td className={styles.tdAccessCol}>
                            {page[1] ? "True" : "False"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
              {currentStep === 1 && (
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Action Buttons</th>
                      <th>Access</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(selectedAction).map((page, index) => {
                      return (
                        <tr key={page[0]}>
                          <td className={styles.tdstyle}>{page[0]}</td>
                          <td className={styles.tdAccessCol}>
                            {page[1] ? "True" : "False"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button
              onClick={closeModal}
              appearance="ghost"
              style={{ marginTop: "15px" }}
            >
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* MAIN ADMIN - Page */}
      {allowed_page?.admin && allowed_action?.view && (
        <div className={styles.dashboard}>
          <div className={styles.sidebar}>
            <Sidebar />
          </div>
          <div className={styles.page}>
            <Board
              heading="Admin Panel"
              action={{ label: "Add New User", handler: openModal }}
              // action={{ label: 'Edit User', handler: openModal }}
              router={Router}
            />
            <div className={styles.pnr_main_container}>
              {/* ADMIN Table Data Container */}
              <div className={styles.admin_main_container}>
                <div className={styles.admin_data_container}>
                  <table className={styles.data_table}>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Department</th>
                        <th>Department Role</th>
                        {allowed_action?.view && allowed_action?.edit && allowed_action?.delete && <th>Action</th>}
                        {/* {allowed_action?.edit && <th>Edit</th>}
                        {allowed_action?.delete && <th>Delete</th>} */}
                      </tr>
                    </thead>
                    <tbody>
                      {tableData?.map((item) => (
                        <tr key={item?.id}>
                          <td>{item?.id}</td>
                          <td>{item?.username}</td>
                          <td>{item?.name}</td>
                          <td>{item?.email}</td>
                          <td>{item?.role}</td>
                          <td>{item?.department}</td>
                          <td>{item?.department_role}</td>
                          {allowed_action?.view && (
                            <td className={styles.actionColumn}>
                              <Button
                                appearance="primary"
                                color="blue"
                                size="md"
                                className={styles.buttonCustom}
                                onClick={() => {
                                  setViewEmail(item?.email);
                                  setSelectedPages(item?.user_pages);
                                  setSelectedAction(item?.user_actions);
                                  openViewModal(item?.email);
                                }}
                              >
                                View
                              </Button>
                              {allowed_action?.edit && (
                              <Button
                                className={styles.editbutton}
                                appearance="primary"
                                color="cyan"
                                onClick={() => {
                                  openEditModal(item);
                                  setModalId(item?.id);
                                  // console.log("Item data for edit:", item);
                                }}
                              >
                                Edit
                              </Button>
                               )}
                              {allowed_action?.delete && (
                              <Button
                                appearance="primary"
                                className={styles.button}
                                color="red"
                                onClick={() => deleteUser(item.email)}
                              >
                                Delete
                              </Button>
                              )}
                            </td>
                          )}
                        </tr>
                      ))}
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

export default SusUsers;

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res);
}
