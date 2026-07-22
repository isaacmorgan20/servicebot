import { Bot } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="msg bot">
      <div className="msg-avatar">
        <Bot />
      </div>
      <div className="msg-col">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  )
}
