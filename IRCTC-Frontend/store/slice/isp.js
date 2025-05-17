import { createSlice } from "@reduxjs/toolkit"
import { startOfDay, endOfDay, subDays } from 'date-fns';


export const ispSlice = createSlice({
	name: "isp",
	initialState: {
		pageNumber: 1,
		data: [],
		countData: [],
		pageCount: 1,
		totalPageCount: 1,
		searchValue: '',
		searchToggle: false
	},
	reducers: {
		initData: (state, action) => {
			state.data = action.payload
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
		changeIspDate: (state, action) => {
			state.searchDate = action.payload
		},
		changeISPFilterOption: (state, action) => {
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

export const { changeSearchToggle, changeSearchValue,  changeISPFilterOption, changeIspDate, initTotalPageCount, initPageCount, addNewUserID, initData, initChangePageNumber, initializeUserIDCount } = ispSlice.actions

export default ispSlice.reducer