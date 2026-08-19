import { useSelector } from 'react-redux'
import RiskAssessment from './RiskAssessment'

// Assignment rule: "you must not fill the left form manually; instead, use
// the AI assistant on the right." Fields are therefore read-only inputs
// (not disabled -- disabled inputs often can't be styled/selected for
// copy-paste, which QA reviewers may want to do -- readOnly keeps text
// selectable while still blocking manual edits).
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
  const form = useSelector((s) => s.form)
  // Match the reference demo: the record becomes ready once the core
  // complaint identity/description exists. Completeness is surfaced as a
  // warning rather than silently blocking the demo workflow.
  const isReadyToCommit = Boolean(form.product_name && form.complaint_description)
  const changed = new Set(form.lastUpdatedFields || [])

  return (
    <div className="complaint-form">
      <div className="form-header">
        <div>
          <h1>Log Customer Complaint</h1>
          <p className="subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className={`status-badge ${isReadyToCommit ? 'ready' : 'pending'}`}>
          {isReadyToCommit ? 'Ready to Commit' : 'Pending Triage'}
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
          {form.missing_fields?.length > 0 && (
            <> · Missing: {form.missing_fields.join(', ')}</>
          )}
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
        <h2>3. Facility &amp; Material Impact</h2>
        <div className="field-row">
          <Field label="Originating Site Block" value={form.originating_site_block} highlighted={changed.has('originating_site_block')} />
          <Field label="Impacted Non-Product Materials (NPM)" value={form.impacted_npm} highlighted={changed.has('impacted_npm')} />
        </div>
      </section>

      <section>
        <h2>4. Defect Analysis</h2>
        <div className="field-row">
          <Field label="Complaint Category" value={form.complaint_category} highlighted={changed.has('complaint_category')} />
        </div>
        <div className="field">
          <label>Complaint Description</label>
          <textarea
            readOnly
            value={form.complaint_description ?? ''}
            placeholder="AI will synthesize the complaint into a formal QMS description..."
            className={changed.has('complaint_description') ? 'field-highlighted' : ''}
          />
        </div>
      </section>

      <RiskAssessment risk={form.risk_assessment} changed={changed} />
    </div>
  )
}
