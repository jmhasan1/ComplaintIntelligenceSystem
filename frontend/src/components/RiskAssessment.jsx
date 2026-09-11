export default function RiskAssessment({ risk, priority, fieldConfidence = {}, changed }) {
  const confidenceEntries = Object.entries(fieldConfidence).filter(
    ([, value]) => typeof value === 'number' && Number.isFinite(value)
  )

  return (
    <section className="risk-assessment">
      <h2>
        <span className="shield-icon">🛡</span> Initial Assessment &amp; Priority
      </h2>
      <div className="field-row">
        <div className="field">
          <label>Initial Severity</label>
          <input
            readOnly
            value={risk?.severity ?? ''}
            placeholder="Awaiting AI classification..."
            className={changed.has('severity') ? 'field-highlighted' : ''}
          />
        </div>
        <div className="field">
          <label>Priority</label>
          <input
            readOnly
            value={priority ?? ''}
            placeholder="Awaiting AI prioritization..."
            className={changed.has('priority') ? 'field-highlighted' : ''}
          />
        </div>
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

      {confidenceEntries.length > 0 && (
        <div className="confidence-panel">
          <div className="confidence-title">AI Extraction Confidence</div>
          <div className="confidence-grid">
            {confidenceEntries.map(([field, score]) => (
              <div className="confidence-item" key={field}>
                <span>{field.replaceAll('_', ' ')}</span>
                <strong>{Math.round(score * 100)}%</strong>
              </div>
            ))}
          </div>
          <small>Confidence is an AI estimate and should be verified during human review.</small>
        </div>
      )}
    </section>
  )
}
