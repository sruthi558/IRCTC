import { createSlice } from "@reduxjs/toolkit"
import { startOfDay, subDays, endOfDay } from 'date-fns';


const defaultDate = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]

const options = [
    'Open',
    'Closed',
    'All',
]

export const booklogSlice = createSlice({
	name: "bookLog",
	initialState: {
		pageNumber: 1,
		data: [],
		countData: [],
		totalRowsCount: 1,
		totalPageCount: 1,
		searchDate: defaultDate,
		filterOption: options.map(ts => ts),
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
		initCount: (state, action) => {
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

export const { changeSearchToggle, changeSearchValue, changeFilterOption, changeDate, initTotalPageCount, initPageCount, initData, initChangePageNumber, initCount } = booklogSlice.actions

export default booklogSlice.reducer