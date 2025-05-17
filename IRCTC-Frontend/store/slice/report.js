import { createSlice } from "@reduxjs/toolkit"
import { startOfDay, subDays, endOfDay } from 'date-fns';


const defaultDate = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]

const options = ['Infrastructure Monitoring', 'Brand Monitoring', 'Special Logs', 'Monthly Logs','Software Analysis','Osint Reports', "Others"]

export const reportSlice = createSlice({
	name: "report",
	initialState: {
		pageNumber: 1,
		data: [],
		countData: [],
		pageCount: 1,
		totalPageCount: 1,
		searchDate: defaultDate,
		filterOption: options.map(ts => ts),
		searchValue: '',
		searchToggle: false
	},
	reducers: {
		initReportData: (state, action) => {
			state.data = action.payload
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
		changeDate: (state, action) => {
			state.searchDate = action.payload
		},
		changeFilterOption: (state, action) => {
			state.filterOption = action.payload
		},
		changeSearchValue: (state, action) => {
			state.searchValue = action.payload
		},
		changeSearchToggle: (state, action) => {
			state.searchToggle = action.payload
		}
	},
})

export const { changeSearchToggle, changeSearchValue, changeFilterOption, changeDate, initTotalPageCount, initPageCount, addNewUserID, initReportData, initChangePageNumber, initializeUserIDCount } = reportSlice.actions

export default reportSlice.reducer