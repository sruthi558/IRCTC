import { combineReducers } from "redux";
import session from "redux-persist/lib/storage/session";
import userSlice from "./user.js";
import useridSlice from "./userid";
import globalLoadingSlice from "./globalLoading";
import brandmonSlice from "./brandMonitoring"
import analysisSlice from "./analysis"
import ispSlice from "./isp"
import dashSlice from "./overview"
import ModalPopupSlice from "./ModalPopup"
import thunk from 'redux-thunk';
import storage from 'redux-persist/lib/storage';
import { persistReducer, persistStore } from 'redux-persist';
// import toggleReducer from "./toggleSlice"
import { configureStore } from "@reduxjs/toolkit";
import { reportSlice } from "./report";
// WHITELIST
const persistConfig = {
  key: "root",
  // storage: new CookieStorage(Cookies), //session,
  storage: session,
 // only card will be persisted
};



export const store = configureStore({
  reducer: {
    userid: useridSlice,
    loading: globalLoadingSlice,
    brandmon: brandmonSlice,
    analysis: analysisSlice,
    isp: ispSlice,
    dashboard: dashSlice,
    modalPopup: ModalPopupSlice,
    report: reportSlice,
    user: userSlice
  },
  middleware: [thunk]
})

export const persistor = persistStore(store)