import { createSlice } from "@reduxjs/toolkit"
import { startOfDay, subDays, endOfDay } from 'date-fns';

// Represents the default date range to display data for:
// [startOfDay(subDays(new Date(), 7))], it calculates the start of the day 7 days ago from the current date.
// [endOfDay(new Date())], it calculates the end of the current day.
// Combines the start and end dates to create the default date range array.
const defaultDate = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]

const options = [
  'ARP',
  'AC',
  'NON_AC',
 ]

export const overviewSlice = createSlice({
	name: "overview",
	initialState: {
		pageNumber: 1,
		data: [],
		bSubCount: 0,
		bIpCount: 0,
		countData: [],
		ticketCount: 0,
		pageCount: 1,
		totalPageCount: 1,
		searchDate: defaultDate,
		filterOption: options.map(ts => ts),
		searchValue: '',
		searchToggle: false,
		tableLength: 20,
	},
	reducers: {
		initializeOverviewData: (state, action) => {
			state.data = action.payload
		},
		initializeTicketCount: (state, action) => {
			state.ticketCount = action.payload
		},
		initializeSubnetCount: (state, action) => {
			state.bSubCount = action.payload
		},
		initalizeIpCount: (state, action) => {
			state.bIpCount = action.payload
		},
		addNewUserID: (state, action) => {
			action.payload.forEach((item) => state.data.push(item))
		},
		initChangePageNumber: (state, action) => {
			state.pageNumber = action.payload
		},
		initializeUserIDCount: (state, action) => {
			state.countData = action.payload 
		},
		initPageCount: (state, action) => {
			state.pageCount =  action.payload
		},
		initTotalPageCount: (state, action) => {
			state.totalPageCount = action.payload
		},
		changeOverviewFilterDate: (state, action) => {
			state.searchDate = action.payload
		},
		changeOverviewFilterOption: (state, action) => {
			state.filterOption = action.payload
		},
		changeSearchValue: (state, action) => {
			state.searchValue = action.payload
		},
		changeSearchToggle: (state, action) => {
			state.searchToggle = action.payload
		},
		changeTableLength: (state, action) => {
			state.tableLength = action.payload
		}
	},
})

export const { initializeTicketCount, initializeSubnetCount, initalizeIpCount , changeTableLength, changeSearchToggle, changeSearchValue, changeOverviewFilterOption, changeOverviewFilterDate, initTotalPageCount, initPageCount, addNewUserID, initializeOverviewData, initChangePageNumber, initializeUserIDCount } = overviewSlice.actions

export default overviewSlice.reducer