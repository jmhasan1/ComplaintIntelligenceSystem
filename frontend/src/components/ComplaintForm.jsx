import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import RiskAssessment from './RiskAssessment'
import { commitComplaint, markComplaintReviewed, resetComplaint } from '../api/client'
import { resetForm, setReviewState } from '../store/formSlice'
import { addAssistantMessage } from '../store/copilotSlice'

function Field({ label, value, highlighted }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input
        type="text"
        readOnly
        value={value ?? ''}
        placeholder="Awaiting AI extraction..."
        className={highlighted ? 'field-highlighted' : ''}
      />
    </div>
  )
}

export default function ComplaintForm() {
  const dispatch = useDispatch()
  const form = useSelector((s) => s.form)
  const sessionId = useSelector((s) => s.copilot.sessionId)
  const [saving, setSaving] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const isReadyToCommit = Boolean(form.product_name && form.complaint_description)
  const canMarkReviewed = isReadyToCommit && !(form.validation_errors?.length > 0)
  const isReviewed = form.review_status === 'reviewed'
  const changed = new Set(form.lastUpdatedFields || [])

  const handleSave = async () => {
    if (!sessionId || !isReadyToCommit || !isReviewed || saving) return
    setSaving(true)
    try {
      const res = await commitComplaint(sessionId)
      dispatch(resetForm())
      dispatch(addAssistantMessage(`Complaint ${res.complaint_id} committed to the QMS ledger. Ready for the next complaint.`))
    } catch (err) {
      console.error(err)
      dispatch(addAssistantMessage('Could not save the complaint. Please review the form and try again.'))
    } finally {
      setSaving(false)
    }
  }

  const handleMarkReviewed = async () => {
    if (!sessionId || !canMarkReviewed || reviewing || isReviewed) return
    setReviewing(true)
    try {
      await markComplaintReviewed(sessionId)
      // Refresh the local state through the existing form response shape.
      dispatch(setReviewState({ review_status: 'reviewed', review_required: false }))
      dispatch(addAssistantMessage('Human review completed. The complaint is ready to save.'))
    } catch (err) {
      console.error(err)
      dispatch(addAssistantMessage(err.response?.data?.detail || 'Could not mark the complaint as reviewed.'))
    } finally {
      setReviewing(false)
    }
  }

  const handleReset = async () => {
    if (!sessionId || resetting) return
    setResetting(true)
    try {
      await resetComplaint(sessionId)
      dispatch(resetForm())
      dispatch(addAssistantMessage('Form reset. Ready for a new complaint.'))
    } catch (err) {
      console.error(err)
      dispatch(addAssistantMessage('Could not reset the complaint session.'))
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="complaint-form">
      <div className="form-header">
        <div>
          <h1>Log Customer Complaint</h1>
          <p className="subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className={`status-badge ${isReviewed ? 'ready' : isReadyToCommit ? 'review' : 'pending'}`}>
          {isReviewed ? 'Ready to Save' : isReadyToCommit ? 'Review Required' : 'Pending Triage'}
        </span>
      </div>

      {form.duplicate_flag && (
        <div className="duplicate-banner">
          ⚠ Possible duplicate complaint detected. {form.duplicate_notes}
        </div>
      )}
      {form.completeness_score > 0 && (
        <div className="completeness-banner">
          <strong>Complaint completeness:</strong> {Math.round(form.completeness_score * 100)}%
          {form.missing_fields?.length > 0 && <> · Missing: {form.missing_fields.join(', ')}</>}
        </div>
      )}

      <section>
        <h2>1. Origin &amp; Customer Details</h2>
        <div className="field-row">
          <Field label="Complaint Source" value={form.complaint_source} highlighted={changed.has('complaint_source')} />
          <Field label="Customer Name" value={form.customer_name} highlighted={changed.has('customer_name')} />
        </div>
      </section>

      <section>
        <h2>2. Product &amp; Batch Identification</h2>
        <div className="field-row">
          <Field label="Product Name" value={form.product_name} highlighted={changed.has('product_name')} />
          <Field label="Product Strength / Grade" value={form.product_strength} highlighted={changed.has('product_strength')} />
        </div>
        <div className="field-row">
          <Field label="Batch / Lot Number" value={form.batch_number} highlighted={changed.has('batch_number')} />
          <Field label="Affected Quantity" value={form.affected_quantity} highlighted={changed.has('affected_quantity')} />
        </div>
        <div className="field-row">
          <Field label="Manufacturing Date" value={form.manufacturing_date} highlighted={changed.has('manufacturing_date')} />
          <Field label="Expiry Date" value={form.expiry_date} highlighted={changed.has('expiry_date')} />
        </div>
      </section>

      <section>
        <h2>3. Complaint Details</h2>
        <div className="field-row">
          <Field label="Complaint Type" value={form.complaint_type} highlighted={changed.has('complaint_type')} />
          <Field label="Complaint Date" value={form.complaint_date} highlighted={changed.has('complaint_date')} />
        </div>
        <div className="field">
          <label>Detailed Complaint Description</label>
          <textarea
            readOnly
            value={form.complaint_description ?? ''}
            placeholder="AI will synthesize the complaint into a formal QMS description..."
            className={changed.has('complaint_description') ? 'field-highlighted' : ''}
          />
        </div>
      </section>

      <RiskAssessment risk={form.risk_assessment} priority={form.priority} fieldConfidence={form.field_confidence} changed={changed} />

      {form.validation_errors?.length > 0 && (
        <div className="validation-banner">
          <strong>Validation requires attention:</strong>
          <ul>
            {form.validation_errors.map((error) => <li key={error}>{error}</li>)}
          </ul>
        </div>
      )}

      <div className={`review-banner ${isReviewed ? 'reviewed' : ''}`}>
        <div>
          <strong>{isReviewed ? '✓ Human Review Complete' : 'Human Review Required'}</strong>
          <span>{isReviewed ? 'This complaint is ready to save.' : 'Review the AI-extracted fields and recommendations before saving.'}</span>
        </div>
        {!isReviewed && (
          <button className="review-btn" onClick={handleMarkReviewed} disabled={!canMarkReviewed || reviewing}>
            {reviewing ? 'Reviewing...' : 'Mark Reviewed'}
          </button>
        )}
      </div>

      <div className="form-actions">
        <button className="reset-btn" onClick={handleReset} disabled={resetting}>
          {resetting ? 'Resetting...' : '↺ Reset Form'}
        </button>
        <button className="commit-btn" onClick={handleSave} disabled={!isReadyToCommit || !isReviewed || saving}>
          {saving ? 'Saving...' : 'Save Complaint'}
        </button>
      </div>
    </div>
  )
}
