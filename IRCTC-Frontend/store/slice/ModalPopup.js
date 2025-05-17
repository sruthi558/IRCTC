import { createSlice } from "@reduxjs/toolkit"

export const modalPopup = createSlice({
  name: "modalPopup",
  initialState: {
    imgUrl: "",
    showImageModal: false,
  },
  reducers: {
    setImgUrl: (state, action) => {
      state.imgUrl = action.payload
    },
    enableImageModal: (state) => {
      state.showImageModal = true
    },
    disableImageModal: (state) => {
      state.showImageModal = false
    },
  },
})

export const { setImgUrl, enableImageModal, disableImageModal } =
  modalPopup.actions

export default modalPopup.reducer