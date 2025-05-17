import { configureStore } from "@reduxjs/toolkit";
import userSlice from "./slice/user";
import useridSlice from "./slice/userid";
import globalLoadingSlice from "./slice/globalLoading";
import brandMonitoringSlice from "./slice/brandMonitoring"
import analysisSlice from "./slice/analysis"
import ispSlice from "./slice/isp"
import overviewSlice from "./slice/overview"
import ModalPopupSlice from "./slice/ModalPopup"
import reportSlice from './slice/report'
import infraSlice from './slice/inframon'
import userregSlice from './slice/userreg'
import booklogSlice from './slice/bookingLogs'
import sususerSlice from './slice/sususer'
import thunk from 'redux-thunk';
import storage from 'redux-persist/lib/storage';
import { persistReducer, persistStore } from 'redux-persist';

const persistConfig = {
  key: 'root',
  storage,
}
const persistedReducer = persistReducer(persistConfig, userSlice)

export const store = configureStore({
  reducer: {
    persistedReducer,
    sususer: sususerSlice,
    userid: useridSlice,
    userreg: userregSlice,
    bookingLogs: booklogSlice,
    loading: globalLoadingSlice,
    inframon: infraSlice,
    brandMonitoring: brandMonitoringSlice,
    analysis: analysisSlice,
    isp: ispSlice,
    overview: overviewSlice,
    dashboard: overviewSlice,
    modalPopup: ModalPopupSlice,
    report: reportSlice
  },
  middleware: [thunk],
	devtools: false,
})

export const persistor = persistStore(store)
