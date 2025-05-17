// Import Libraries
import { Sidenav, Nav } from 'rsuite'
import { router, useRouter } from 'next/router'
import React, { useEffect, useState } from 'react'
import Image from 'next/image'
import { useSelector } from 'react-redux'

// Import Assets
import AdminIcon from '@rsuite/icons/Admin'
import CharacterLockIcon from '@rsuite/icons/CharacterLock'
import DeviceIcon from '@rsuite/icons/Device'
import GridIcon from '@rsuite/icons/Grid'
import ListIcon from '@rsuite/icons/List'
import ReviewRefuseIcon from '@rsuite/icons/ReviewRefuse'
import TreeIcon from '@rsuite/icons/Tree'
import TrendIcon from '@rsuite/icons/Trend'
import ExitIcon from '@rsuite/icons/Exit'
import GlobalIcon from '@rsuite/icons/Global'
import SingleSourceIcon from '@rsuite/icons/SingleSource'
import PeoplesIcon from '@rsuite/icons/Peoples'
import logo from '../public/static/images/logo.png'
import DataAuthorizeIcon from '@rsuite/icons/DataAuthorize';
import HistoryIcon from '@rsuite/icons/History';

import MoveUpIcon from '@rsuite/icons/MoveUp';
import MobileIcon from '@rsuite/icons/Mobile';
import TreemapIcon from '@rsuite/icons/Treemap';
import StorageIcon from '@rsuite/icons/Storage';
import OperatePeopleIcon from '@rsuite/icons/OperatePeople';
import UserBadgeIcon from '@rsuite/icons/UserBadge';


import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

// Import Styles
import styles from '../styles/Sidebar.module.scss'

import InfoRoundIcon from '@rsuite/icons/InfoRound';
import InfoOutlineIcon from '@rsuite/icons/InfoOutline';
import BranchIcon from '@rsuite/icons/Branch';
import RemindOutlineIcon from '@rsuite/icons/RemindOutline';
import DetailIcon from '@rsuite/icons/Detail';
import AttachmentIcon from '@rsuite/icons/Attachment';
import PageIcon from '@rsuite/icons/Page';
import AppSelectIcon from '@rsuite/icons/AppSelect';
import ShieldIcon from '@rsuite/icons/Shield';

// CustomSidenav Component
const CustomSidenav = ({
  appearance,
  openKeys,
  expanded,
  onOpenChange,
  onExpand,
  selectedRole,
  ...navProps
}) => {
  // Initialise react router for routing after a successful sign-in.
  const router = useRouter()

  // Trigger user signout.
  const handleSignOut = async () => {
    // Sign out the user from the backend.
    fetch('/api/signout', {
      method: 'GET',
      credentials: 'include',
    }).then(() => router.push('/signin'))

    // Sign out the user from the frontend.
    // Clear out the local storage of the browser to delete the cookie.
    localStorage.clear()
  }

  // Fetch the user role from the reducer.
  const userRole = useSelector((state) => state.persistedReducer.role)
  const userDept = useSelector((state) => state.persistedReducer.dept)

  // Render the component.
  const user_pages = useSelector((state) => state.persistedReducer.user_pages)

  // Getting allowed pages and allowed actions for the user 
  const allowed_pages = useSelector((state) => state.persistedReducer.user_pages)
  const allowed_actions = useSelector((state) => state.persistedReducer.user_actions)

  // Redux Data; user related 
  const redux_usr = useSelector((state) => state.persistedReducer)

  // console.log(redux_usr);
  // console.log('allowed actions', allowed_actions);
  // console.log('allowed_pages', allowed_pages);

  return (
    <div className={styles.sidebar}>
      <Sidenav
        appearance={appearance}
        expanded={expanded}
        openKeys={openKeys}
        onOpenChange={onOpenChange}
        className={styles.sidenav}
      >
        <Sidenav.Header>
          <div className={ styles.logoContainer + ' d-flex justify-content-center align-items-center p-5' }>
            <Image src={logo} className={styles.logo} alt="IRCTC"></Image>
          </div>
        </Sidenav.Header>

        <Sidenav.Body>

          <Nav {...navProps}>

            {/* OVERVIEW - Page */}
            {allowed_pages?.overview && allowed_actions?.view && (
              <Nav.Item
                eventKey="0"
                icon={<GridIcon />}
                href={'/overview'}
                active={router.pathname == '/overview' ? true : false}
              >
                Overview
              </Nav.Item>
            )}

            {/* SUS PNR - Page */}
            {(allowed_pages?.suspected_pnrs && allowed_actions?.view) && (
              <Nav.Item
                eventKey="1"
                icon={<InfoOutlineIcon />}
                href={'/suspected-pnrs'}
                active={router.pathname == '/suspected-pnrs' ? true : false}
              >
                Suspected PNRs
              </Nav.Item>
            )}

            {/* SUS IP ADD - Page */}
            {/* {(allowed_pages?.suspected_ip_addresses && allowed_actions?.view) && (
              <Nav.Item
                eventKey="2"
                icon={<ReviewRefuseIcon />}
                href={'/suspected-ip-addresses'}
                active={
                  router.pathname == '/suspected-ip-addresses' ? true : false
                }
              >
                Suspected IP Addresses
              </Nav.Item>
            )} */}

            {/* SUS USR - Page */}
            {(allowed_pages?.suspected_users && allowed_actions?.view) && (
              <Nav.Item
                eventKey="3"
                icon={<InfoOutlineIcon />}
                href={'/suspected-users'}
                active={router.pathname == '/suspected-users' ? true : false}
              >
                Suspected Users
              </Nav.Item>
            )}

            {/* SUS IP HIST - Page */}
            {(allowed_pages?.ip_history && allowed_actions?.view) && (
              <Nav.Item
                eventKey="5"
                icon={<InfoOutlineIcon />}
                href={'/ip-history'}
                active={router.pathname == '/ip-history' ? true : false}
              >
                Suspected IP Addresses
              </Nav.Item>
            )}

            {/* SUS NO - Page */}
            {(allowed_pages?.suspected_number && allowed_actions?.view) && (
              <Nav.Item
                eventKey="4"
                icon={<InfoOutlineIcon />}
                href={'/suspected-number'}
                active={router.pathname == '/suspected-number' ? true : false}
              >
                Suspected Numbers
              </Nav.Item>
            )}

            {/* SUS USR HIST - Page */}
            {/* {(allowed_pages?.suspected_user_history && allowed_actions?.view) && (
              <Nav.Item
                eventKey="6"
                icon={<OperatePeopleIcon />}
                href={'/suspected-user-history'}
                active={router.pathname == '/suspected-user-history' ? true : false}
              >
                Suspected User History
              </Nav.Item>
            )} */}

            {/* CASE MANAGEMENT - Group */}
            {(allowed_pages?.casemanagement_user || allowed_pages?.casemanagement_pnr) ? (
              <Nav.Menu
                eventKey='7'
                icon={<ListIcon/>}
                title="Case Management"
              >
                {/* Overview */}
                {(allowed_pages?.casemanagement_overview && allowed_actions?.view) && (
                  <Nav.Item
                    eventKey='7-0'
                    icon={<UserBadgeIcon/>}
                    href='/casemanagement/overview'
                    active={router.pathname === '/casemanagement/overview' ? true : false}
                  >
                    Overview
                  </Nav.Item>
                )}

                {/* USER Case Management */}
                {(allowed_pages?.casemanagement_user && allowed_actions?.view) && (
                  <Nav.Item
                    eventKey='7-1'
                    icon={<UserBadgeIcon/>}
                    href='/casemanagement/user'
                    active={router.pathname === '/casemanagement/user' ? true : false}
                  >
                    User Case
                  </Nav.Item>
                )}

                {/* PNR Case Management */}
                {allowed_pages?.casemanagement_pnr && allowed_actions?.view && (
                  <Nav.Item
                    eventKey='7-2'
                    icon={<DataAuthorizeIcon/>}
                    href='/casemanagement/pnr'
                    active={router.pathname === '/casemanagement/pnr' ? true : false}
                  >
                    Pnr Case
                  </Nav.Item>
                )}
                {/* IP Case Management */}
                {allowed_pages?.casemanagement_ip && allowed_actions?.view && (
                  <Nav.Item
                    eventKey='7-3'
                    icon={<ShieldIcon/>}
                    href='/casemanagement/ip'
                    active={router.pathname === '/casemanagement/ip' ? true : false}
                  >
                    IP Case
                  </Nav.Item>
                )}
              </Nav.Menu>
            ) : ("")
          }

            {(allowed_pages?.touts_details && allowed_actions?.view) && (
              <Nav.Item
                eventKey="15"
                icon={<CharacterLockIcon />}
                href={'/touts_details'}
                active={router.pathname == '/touts_details' ? true : false}
              >
                Touts Details
              </Nav.Item>
            )}

            {/* INFRA (CYBER) - Page */}
            {(allowed_pages?.infrastructure_monitoring && allowed_actions?.view) && (
              <Nav.Item
                eventKey="8"
                icon={<BranchIcon />}
                active={ router.pathname == '/infrastructure-monitoring' ? true : false }
                href={'/infrastructure-monitoring'}
              >
                Cyber Threat Monitoring
              </Nav.Item>
            )}

            {/* BRAND MON - Page */}
            {(allowed_pages?.brand_monitoring && allowed_actions?.view) && (
              <Nav.Item
                eventKey="9"
                icon={<DeviceIcon />}
                href={'/brand-monitoring'}
                active={router.pathname == '/brand-monitoring' ? true : false}
              >
                Brand Monitoring
              </Nav.Item>
            )}

            {/* STATISTICS TAB - Group */}
            {(allowed_pages?.booking_logs || allowed_pages?.user_registration_logs || allowed_pages?.blacklist || allowed_pages?.daily_status) ? 
              (
                <Nav.Menu eventKey="10" icon={<ListIcon />} title="Statistics">

                  {/* DAILY LOG - Page */}
                  {(allowed_pages?.booking_logs && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="10-1"
                      icon={<TrendIcon />}
                      href={'/booking-logs'}
                      active={router.pathname == '/booking-logs' ? true : false}
                    >
                      Daily Log Analysis
                    </Nav.Item>
                  )}

                  {/* USR REG - Page */}
                  {(allowed_pages?.user_registration_logs && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="10-2"
                      icon={<CharacterLockIcon />}
                      href={'/user-registration-logs'}
                      active={router.pathname == '/user-registration-logs' ? true : false}
                    >
                      User Registration
                    </Nav.Item>
                  )}

                  {/* BLACKLIST - Page */}
                  {(allowed_pages?.blacklist && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="10-3"
                      icon={<RemindOutlineIcon />}
                      href={'/blacklist'}
                      active={router.pathname == '/blacklist' ? true : false}
                    >
                      Blacklists
                    </Nav.Item>
                  )}

                  {/* DAILY STAT - Page */}
                  {(allowed_pages?.daily_status && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="10-4"
                      icon={<DetailIcon />}
                      href={'/daily_status'}
                      active={router.pathname == '/daily_status' ? true : false}
                    >
                      Daily Status
                    </Nav.Item>
                  )}

                </Nav.Menu>
              ) : ""     
            }

            {/* REPORTS TAB - Group */}
            {(allowed_pages?.reports || allowed_pages?.software_procurement) ? 
              (
                <Nav.Menu eventKey="11"  icon={<ListIcon />} title={'Reports'}>

                  {/* REPORTS - Page */}
                  {(allowed_pages?.reports && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="11-1"
                      icon={<PageIcon />}
                      href={'/reports'}
                      active={router.pathname == '/reports' ? true : false}
                    >
                      Report Archive
                    </Nav.Item>
                  )}

                  {/* SOFTWARE PROC - Page */}
                  {(allowed_pages?.software_procurement && allowed_actions?.view) && (
                    <Nav.Item
                      eventKey="11-2"
                      icon={<AppSelectIcon />}
                      href={'/software-procurement'}
                      active={router.pathname == '/software-procurement' ? true : false}
                    >
                      Software Procurement
                    </Nav.Item>
                  )}

                </Nav.Menu>
              ) : ""
            }

            {/* ABOUT - Page */}
            <Nav.Item 
              eventKey="12" 
              icon={<PeoplesIcon />} 
              href={'/about-us'}
              active={router.pathname === '/about-us' ? true : false}
            >
              About Us
            </Nav.Item>

            {/* ADMIN - Page */}
            {(allowed_pages?.admin && allowed_actions?.view) && (
              <Nav.Item
                eventKey="13"
                icon={<AdminIcon />}
                href={'/admin'}
                active={router.pathname === '/admin' ? true : false}
              >
                Admin Panel
              </Nav.Item>
            )}
            
            <Nav.Item
              eventKey="14"
              icon={<ExitIcon />}
              className={styles.signout}
              onClick={handleSignOut}
            >
              Sign Out
            </Nav.Item>
           
          </Nav>
        </Sidenav.Body>
        
        <Sidenav.Toggle onToggle={onExpand} className={styles.closeBtn} />
        {expanded && <div className={styles.Footer}>
        <h4>
          Powered by <img src={'/static/images/pinaca-re-logo.png'} alt='Pinaca Logo' />
        </h4>
      </div>}
      </Sidenav>
    </div>
  )
}
// Sidebar Component
const Sidebar = (props) => {
  // Set the state for open menu, corresponding to Dropdown eventkey (controlled).
  const [openKeys, setOpenKeys] = React.useState(['2', '3', '4'])

  // Set the state for whether to expand the Sidenav.
  const [expanded, setExpand] = React.useState(true)
  // Render the component.
  return (
    <CustomSidenav
      openKeys={openKeys}
      onOpenChange={setOpenKeys}
      expanded={expanded}
      onExpand={setExpand}
      appearance="default"
    />
  )
}

export default Sidebar
