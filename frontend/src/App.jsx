import { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { v4 as uuidv4 } from 'uuid'
import ComplaintForm from './components/ComplaintForm'
import CopilotPanel from './components/CopilotPanel'
import { setSessionId } from './store/copilotSlice'
import './index.css'

export default function App() {
  const dispatch = useDispatch()

  useEffect(() => {
    // One session per browser tab load. A real deployment would tie this to
    // auth/user identity instead of a random UUID.
    dispatch(setSessionId(uuidv4()))
  }, [dispatch])

  return (
    <div className="app-shell">
      <div className="form-pane">
        <ComplaintForm />
      </div>
      <div className="copilot-pane">
        <CopilotPanel />
      </div>
    </div>
  )
}
