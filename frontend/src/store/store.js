import { configureStore } from '@reduxjs/toolkit'
import formReducer from './formSlice'
import copilotReducer from './copilotSlice'

export const store = configureStore({
  reducer: {
    form: formReducer,
    copilot: copilotReducer,
  },
})
