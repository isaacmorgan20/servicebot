import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatPanel from './components/ChatPanel.jsx'

// ── API helpers ────────────────────────────────────────────────────────────
const api = {
  session: () => fetch('/api/session'),
  chat:    (session_id, message) =>
    fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id, message }),
    }),
  reset: (session_id) =>
    fetch('/api/reset', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id }),
    }),
}

function makeId() {
  return Math.random().toString(36).slice(2, 10)
}

function timestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function makeMsg(role, content, toolCalls = []) {
  return { id: makeId(), role, content, time: timestamp(), toolCalls }
}

// ── App ────────────────────────────────────────────────────────────────────
export default function App() {
  const [sessionId,      setSessionId]      = useState(null)
  const [messages,       setMessages]       = useState([])
  const [loading,        setLoading]        = useState(false)
  const [status,         setStatus]         = useState('loading')   // loading | online | error
  const [model,          setModel]          = useState('')
  const [statusMessages, setStatusMessages] = useState([])
  const [sidebarOpen,    setSidebarOpen]    = useState(true)
  const [inputValue,     setInputValue]     = useState('')
  const [booted,         setBooted]         = useState(false)

  // ── Init session on first render ─────────────────────────────────────────
  const initSession = useCallback(async () => {
    setStatus('loading')
    setLoading(true)
    try {
      const res  = await api.session()
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Session init failed')

      setSessionId(data.session_id)
      setModel(data.model)
      setStatus('online')
      setMessages([makeMsg('bot', data.greeting)])
    } catch {
      setStatus('error')
      setMessages([makeMsg('bot',
        '⚠️ Could not connect to the server.\n\nMake sure the backend is running:\n```\nuv run python run_web.py\n```'
      )])
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-boot once
  if (!booted) {
    setBooted(true)
    initSession()
  }

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    const message = (text ?? inputValue).trim()
    if (!message || loading || !sessionId) return

    setInputValue('')
    setMessages(prev => [...prev, makeMsg('user', message)])
    setLoading(true)
    setStatusMessages([])

    try {
      const res  = await api.chat(sessionId, message)
      const data = await res.json()

      if (!res.ok) {
        setMessages(prev => [...prev, makeMsg('bot', `⚠️ Error: ${data.detail || 'Something went wrong.'}`)])
        return
      }

      setMessages(prev => [...prev, makeMsg('bot', data.reply, data.tool_calls || [])])
      setModel(data.model)
      if (data.status_messages?.length) {
        setStatusMessages(data.status_messages)
        setTimeout(() => setStatusMessages([]), 8000)
      }
    } catch {
      setMessages(prev => [...prev, makeMsg('bot', '⚠️ Could not reach the server. Is the backend running?')])
    } finally {
      setLoading(false)
    }
  }, [inputValue, loading, sessionId])

  // ── Reset conversation ───────────────────────────────────────────────────
  const resetConversation = useCallback(async () => {
    if (loading) return
    setLoading(true)
    setStatus('loading')
    setMessages([])
    setStatusMessages([])

    try {
      const res  = await api.reset(sessionId)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)

      setSessionId(data.session_id)
      setModel(data.model)
      setStatus('online')
      setMessages([makeMsg('bot', data.greeting)])
    } catch {
      setStatus('error')
      setMessages([makeMsg('bot', '⚠️ Could not reset the session. Please refresh the page.')])
    } finally {
      setLoading(false)
    }
  }, [loading, sessionId])

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <>
      {/* Animated background orbs */}
      <div className="bg-orbs" aria-hidden="true">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="app-shell">
        <Sidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          status={status}
          model={model}
          onChipSelect={sendMessage}
          onReset={resetConversation}
          loading={loading}
        />

        <ChatPanel
          sidebarOpen={sidebarOpen}
          onOpenSidebar={() => setSidebarOpen(true)}
          model={model}
          messages={messages}
          loading={loading}
          statusMessages={statusMessages}
          onSend={sendMessage}
          inputValue={inputValue}
          onInputChange={setInputValue}
        />
      </div>
    </>
  )
}
