import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  sessionId: null,
  messages: [
    {
      role: 'assistant',
      content:
        'Ready to process new complaints. You can paste the raw email from the customer, or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.',
    },
  ],
  isProcessing: false,
}

const copilotSlice = createSlice({
  name: 'copilot',
  initialState,
  reducers: {
    setSessionId(state, action) {
      state.sessionId = action.payload
    },
    addUserMessage(state, action) {
      state.messages.push({ role: 'user', content: action.payload })
    },
    addUserFileMessage(state, action) {
      state.messages.push({ role: 'user', content: '', file: action.payload })
    },
    addAssistantMessage(state, action) {
      state.messages.push({ role: 'assistant', content: action.payload })
    },
    setProcessing(state, action) {
      state.isProcessing = action.payload
    },
  },
})

export const {
  setSessionId,
  addUserMessage,
  addUserFileMessage,
  addAssistantMessage,
  setProcessing,
} = copilotSlice.actions
export default copilotSlice.reducer
