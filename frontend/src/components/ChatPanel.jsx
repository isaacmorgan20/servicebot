import { useEffect, useRef, useCallback } from 'react'
import { MessageCircleHeart, PanelLeftOpen, Zap, Send, AlertTriangle } from 'lucide-react'
import MessageBubble from './MessageBubble.jsx'
import ToolCallCard from './ToolCallCard.jsx'
import TypingIndicator from './TypingIndicator.jsx'

export default function ChatPanel({
  sidebarOpen,
  onOpenSidebar,
  model,
  messages,
  loading,
  statusMessages,
  onSend,
  inputValue,
  onInputChange,
}) {
  const messagesEndRef  = useRef(null)
  const textareaRef     = useRef(null)

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [inputValue])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const canSend = inputValue.trim().length > 0 && !loading

  return (
    <main className="chat-panel">
      {/* Top Bar */}
      <header className="topbar">
        {!sidebarOpen && (
          <button className="icon-btn" onClick={onOpenSidebar} aria-label="Open sidebar">
            <PanelLeftOpen />
          </button>
        )}
        <div className="topbar-title">
          <MessageCircleHeart /> NexSupport Chat
        </div>
        <div className="topbar-model">
          <Zap />
          <span>{model || '—'}</span>
        </div>
      </header>

      {/* Messages */}
      <div className="messages-wrap">
        <div className="messages" role="log" aria-live="polite" aria-label="Chat messages">
          {messages.length === 0 && !loading ? (
            <div className="empty-state">
              <div className="empty-icon"><MessageCircleHeart /></div>
              <div className="empty-title">How can I help you?</div>
              <p className="empty-sub">
                Ask me anything — from order issues and refunds to business support. I'm here for you.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id}>
                <MessageBubble
                  role={msg.role}
                  content={msg.content}
                  time={msg.time}
                />
                {msg.toolCalls?.length > 0 && (
                  <div className="tool-calls-group">
                    {msg.toolCalls.map((tc, i) => (
                      <ToolCallCard key={`${msg.id}-tc-${i}`} tool={tc} />
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          {loading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Fallback / Status Strip */}
      {statusMessages.length > 0 && (
        <div className="status-strip">
          <AlertTriangle />
          <span>{statusMessages.join(' — ')}</span>
        </div>
      )}

      {/* Input */}
      <footer className="input-area">
        <div className="input-box">
          <textarea
            ref={textareaRef}
            className="user-input"
            placeholder="Type your message…"
            rows={1}
            maxLength={4000}
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            aria-label="Message input"
            autoFocus
          />
          <button
            className="send-btn"
            onClick={onSend}
            disabled={!canSend}
            aria-label="Send message"
          >
            <Send />
          </button>
        </div>
        <p className="input-hint">
          Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
        </p>
      </footer>
    </main>
  )
}
