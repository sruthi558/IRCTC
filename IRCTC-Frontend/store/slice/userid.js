import { createSlice } from "@reduxjs/toolkit"
import { startOfDay, subDays, endOfDay } from 'date-fns';


const defaultDate = [startOfDay(subDays(new Date(), 7)), endOfDay(new Date())]

const options = [
  'Blocked',
  'Ignored',
  'Pending',
]

export const useridSlice = createSlice({
	name: "userid",
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
		initializeUserID: (state, action) => {
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
		changeUserIDdate: (state, action) => {
			state.searchDate = action.payload
		},
		changeUserIDFilterOption: (state, action) => {
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

export const { changeSearchToggle, changeSearchValue, changeUserIDFilterOption, changeUserIDdate, initTotalPageCount, initPageCount, addNewUserID, initializeUserID, initChangePageNumber, initializeUserIDCount } = useridSlice.actions

export default useridSlice.reducer