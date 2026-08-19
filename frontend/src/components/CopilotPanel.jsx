import { useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  addUserMessage,
  addUserFileMessage,
  addAssistantMessage,
  setProcessing,
} from '../store/copilotSlice'
import { setFormState } from '../store/formSlice'
import { sendChatMessage, uploadComplaintDocument } from '../api/client'

export default function CopilotPanel() {
  const dispatch = useDispatch()
  const { sessionId, messages, isProcessing } = useSelector((s) => s.copilot)
  const [input, setInput] = useState('')
  const fileInputRef = useRef(null)

  const applyResponse = (res) => {
    dispatch(setFormState({ form_state: res.form_state, updated_fields: res.updated_fields }))
    dispatch(addAssistantMessage(res.reply))
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isProcessing) return
    dispatch(addUserMessage(text))
    setInput('')
    dispatch(setProcessing(true))
    try {
      // Powers log_complaint (first message) and edit_complaint
      // (subsequent corrections) -- decided server-side by the graph.
      const res = await sendChatMessage(sessionId, text)
      applyResponse(res)
    } catch (err) {
      dispatch(addAssistantMessage('Something went wrong processing that. Please try again.'))
      console.error(err)
    } finally {
      dispatch(setProcessing(false))
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    dispatch(addUserFileMessage({ name: file.name, type: 'PDF Document' }))
    dispatch(setProcessing(true))
    try {
      const res = await uploadComplaintDocument(sessionId, file)
      applyResponse(res)
    } catch (err) {
      dispatch(addAssistantMessage('Could not process that document. Please try another file.'))
      console.error(err)
    } finally {
      dispatch(setProcessing(false))
      e.target.value = ''
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="copilot-panel">
      <div className="copilot-header">
        <h2>🧪 AIVOA Copilot</h2>
        <p>Drop complaint files or paste text below.</p>
      </div>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message message-${m.role}`}>
            {m.file ? (
              <div className="file-chip">
                📄 <span>{m.file.name}</span>
                <small>{m.file.type}</small>
              </div>
            ) : (
              m.content
            )}
          </div>
        ))}
        {isProcessing && (
          <div className="message message-assistant message-loading">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}
      </div>

      <div className="input-bar">
        <button
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Upload complaint PDF/email"
        >
          📎
        </button>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.txt,.eml"
          onChange={handleFileChange}
        />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message or paste a complaint..."
          disabled={isProcessing}
        />
        <button className="send-btn" onClick={handleSend} disabled={isProcessing}>
          ✓
        </button>
      </div>
      <p className="powered-by">POWERED BY LANGGRAPH</p>
    </div>
  )
}
