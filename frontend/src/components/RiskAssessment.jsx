import { useDispatch, useSelector } from 'react-redux'
import { useState } from 'react'
import { commitComplaint } from '../api/client'
import { resetForm } from '../store/formSlice'
import { addAssistantMessage } from '../store/copilotSlice'

export default function RiskAssessment({ risk, changed }) {
  const dispatch = useDispatch()
  const sessionId = useSelector((s) => s.copilot.sessionId)
  const [committing, setCommitting] = useState(false)

  const handleCommit = async () => {
    if (!sessionId) return
    setCommitting(true)
    try {
      const res = await commitComplaint(sessionId)
      dispatch(resetForm())
      dispatch(
        addAssistantMessage(
          `Complaint ${res.complaint_id} committed to the QMS ledger. Ready for the next complaint.`
        )
      )
    } finally {
      setCommitting(false)
    }
  }

  return (
    <section className="risk-assessment">
      <h2>
        <span className="shield-icon">🛡</span> AI Copilot Risk Assessment
      </h2>
      <div className="field-row">
        <div className="field">
          <label>Severity (Suggested)</label>
          <input
            readOnly
            value={risk?.severity ?? ''}
            placeholder="Awaiting AI classification..."
            className={changed.has('severity') ? 'field-highlighted' : ''}
          />
        </div>
        <div className="field">
          <label>Suggested Next Action</label>
          <input
            readOnly
            value={risk?.suggested_next_action ?? ''}
            placeholder="Awaiting AI recommendation..."
            className={changed.has('suggested_next_action') ? 'field-highlighted' : ''}
          />
        </div>
      </div>
      <div className="field">
        <label>Initial Risk Assessment</label>
        <textarea
          readOnly
          value={risk?.initial_risk_assessment ?? ''}
          placeholder="AI reasoning will appear here..."
          className={changed.has('initial_risk_assessment') ? 'field-highlighted' : ''}
        />
      </div>
      {risk?.capa_recommendation && (
        <div className="field">
          <label>CAPA Recommendation (bonus)</label>
          <textarea
            readOnly
            value={risk.capa_recommendation}
            className={changed.has('capa_recommendation') ? 'field-highlighted' : ''}
          />
        </div>
      )}

      <button className="commit-btn" onClick={handleCommit} disabled={committing}>
        {committing ? 'Committing...' : 'Commit to QMS Ledger'}
      </button>
    </section>
  )
}
