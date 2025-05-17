import { createSlice, current } from "@reduxjs/toolkit";
import { current_pages, user_allowed_actions } from "@/utils/dashboard.pages"; 

export const userSlice = createSlice({
  name: "user",
  initialState: {
    email: "",
    bookmarks: [
    ],
    monitors: [],
    role: "",
    dept: "",
    user_pages:{
      overview:1,
      suspected_pnr:0,
      suspected_ip:0,
      suspected_users:0,
      ip_history:0,
      infrastructure_monitoring:0,
      brand_monitoring:0,
      daily_log_analysis:0,
      user_regidtration:0,
      booking_logs:0,
      blacklists:0,
      daily_status:0,
      reports:0,
      about_us:1,
      admin_panel:0,
    },
    user_actions: {
      view: 0,
      download: 0, 
      upload: 0,
      delete: 0
    }
  },
  reducers: {
    setRole: (state, action) => {
      state.role = action.payload;
    },
    setDept: (state, action) => {
      state.dept = action.payload;
    },
    setEmail: (state, action) => {
      state.email = action.payload;
    },
    setAllBookmarks: (state, action) => {
      state.bookmarks = [...action.payload];
    },
    addBookmark: (state, action) => {
      state.bookmarks.push(action.payload);
    },
    removeBookmark: (state, action) => {
      const allBookmarks = current(state.bookmarks);
      const filteredBookmark = allBookmarks.filter(
        (item) => item.domain != action.payload
      );
      state.bookmarks = [...filteredBookmark];
    },
    addUserPages: (state, action) => {
      state.user_pages = action.payload;
    },
    addUserActions: (state, action) => {
      state.user_actions = action.payload; 
    } 
  },
});

export const { setRole, setDept, setAllBookmarks, setEmail, addBookmark, removeBookmark, addUserPages, addUserActions} = userSlice.actions;

export default userSlice.reducer;
