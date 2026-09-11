import { createSlice } from '@reduxjs/toolkit'

// Mirrors backend ComplaintState / ComplaintStateUpdate field names exactly
// so the API response can be spread directly into state without mapping.
const initialState = {
  complaint_source: null,
  customer_name: null,
  product_name: null,
  product_strength: null,
  batch_number: null,
  affected_quantity: null,
  manufacturing_date: null,
  expiry_date: null,
  complaint_type: null,
  complaint_date: null,
  complaint_description: null,
  priority: null,
  risk_assessment: {
    severity: null,
    suggested_next_action: null,
    initial_risk_assessment: null,
    capa_recommendation: null,
  },
  duplicate_flag: null,
  duplicate_notes: null,
  missing_fields: [],
  completeness_score: 0,
  field_confidence: {},
  validation_errors: [],
  review_status: 'draft',
  review_required: false,
  // UI-only, not sent to backend
  lastUpdatedFields: [],
}

const formSlice = createSlice({
  name: 'form',
  initialState,
  reducers: {
    // Applied whenever /api/chat or /api/upload returns a new form_state.
    // We intentionally REPLACE with the server's full form_state (server is
    // the source of truth for the merge), but keep lastUpdatedFields
    // separately so the UI can highlight only what changed.
    setFormState(state, action) {
      const { form_state, updated_fields } = action.payload
      Object.assign(state, form_state)
      state.lastUpdatedFields = updated_fields || []
    },
    resetForm() {
      return initialState
    },
    setReviewState(state, action) {
      state.review_status = action.payload.review_status
      state.review_required = action.payload.review_required
    },
  },
})

export const { setFormState, resetForm, setReviewState } = formSlice.actions
export default formSlice.reducer
