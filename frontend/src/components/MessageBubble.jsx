import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function MessageBubble({ role, content, time }) {
  const isBot = role === 'bot'

  return (
    <div className={`msg ${role}`}>
      <div className="msg-avatar">
        {isBot ? <Bot /> : <User />}
      </div>
      <div className="msg-col">
        <div className="msg-bubble">
          {isBot ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          ) : (
            content
          )}
        </div>
        <div className="msg-time">{time || formatTime()}</div>
      </div>
    </div>
  )
}
