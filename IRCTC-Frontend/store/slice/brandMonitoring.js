import { createSlice } from '@reduxjs/toolkit'
import { startOfDay, subDays, endOfDay } from 'date-fns'

const defaultDate = [startOfDay(subDays(new Date(), 300)), endOfDay(new Date())]

const options = [
  'Youtube',
  'FB',
  'Domain',
  'Telegram',
  'Instagram',
  'Twitter',
  'Mobile',
]

export const brandMonitoringSlice = createSlice({
  name: 'brandMonitoring',
  initialState: {
    pageNumber: 1,
    data: [],
    countData: [],
    pageCount: 1,
    totalPageCount: 1,
    searchDate: defaultDate,
    filterOption: options.map((ts) => ts),
    searchValue: '',
    searchToggle: false,
  },
  reducers: {
    initalizeData: (state, action) => {
      state.data = action.payload
    },
    addNewUserID: (state, action) => {
      action.payload.forEach((item) => state.data.push(item))
    },
    initChangePageNumber: (state, action) => {
      state.pageNumber = action.payload
    },
    deleteDataIndex: (state, action) => {
      delete state.data[action.payload]
    },
    initializeUserIDCount: (state, action) => {
      state.countData = action.payload
    },
    initPageCount: (state, action) => {
      state.pageCount = action.payload
    },
    initTotalPageCount: (state, action) => {
      state.totalPageCount = action.payload
    },
    changeSearchDate: (state, action) => {
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
    },
  },
})

export const {
  changeSearchToggle,
  deleteDataIndex,
  changeSearchValue,
  changeFilterOption,
  changeSearchDate,
  initTotalPageCount,
  initPageCount,
  addNewUserID,
  initalizeData,
  initChangePageNumber,
  initializeUserIDCount,
} = brandMonitoringSlice.actions

export default brandMonitoringSlice.reducer
