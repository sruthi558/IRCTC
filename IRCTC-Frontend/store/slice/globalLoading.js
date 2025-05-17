import { createSlice } from "@reduxjs/toolkit"

export const globalLoadingSlice = createSlice({
  name: "globalLoading",
  initialState: {
    status: false,
  },
  reducers: {
    setLoadingTrue: (state) => {
      state.status = true
    },
    setLoadingFalse: (state) => {
      state.status = false
    },
  },
})

export const { setLoadingTrue, setLoadingFalse } = globalLoadingSlice.actions

export default globalLoadingSlice.reducer