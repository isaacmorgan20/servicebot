import { Search, RotateCcw, Ticket, UserPlus, BookOpen, CheckCircle, XCircle } from 'lucide-react'

const TOOL_CONFIG = {
  lookup_account:    { icon: Search,    label: 'Account Lookup',   color: '#06b6d4' },
  reverse_transaction: { icon: RotateCcw, label: 'Transaction Reversal', color: '#22c55e' },
  update_ticket:     { icon: Ticket,    label: 'Ticket Update',    color: '#8b5cf6' },
  escalate_to_human: { icon: UserPlus,  label: 'Escalation',       color: '#f59e0b' },
  search_faq:        { icon: BookOpen,  label: 'Knowledge Search', color: '#a78bfa' },
}

function formatArgs(name, args) {
  if (name === 'lookup_account') return `Account: ${args.account_id || '—'}`
  if (name === 'reverse_transaction') return `Transaction: ${args.transaction_id || '—'}`
  if (name === 'update_ticket') return `Ticket: ${args.ticket_id || '—'} → ${args.status || '—'}`
  if (name === 'escalate_to_human') return `Ticket: ${args.ticket_id || '—'}`
  if (name === 'search_faq') return `"${args.query || ''}"`
  return JSON.stringify(args)
}

function formatResult(tool) {
  if (tool.status === 'error') {
    return tool.result?.error || 'Action failed'
  }
  const r = tool.result?.data
  if (!r) return 'Done'
  if (r.message) return r.message
  if (r.balance !== undefined) return `${r.type} — Balance $${r.balance?.toLocaleString?.() ?? r.balance} (${r.status})`
  if (r.status === 'reversal_initiated' && r.transaction_id) return `Reversal of $${r.amount} initiated for ${r.transaction_id}`
  if (r.new_status) return `Status: ${r.previous_status} → ${r.new_status}`
  if (r.escalated) return 'Escalated to human agent'
  if (Array.isArray(r) && r.length === 0) return 'No results found'
  if (Array.isArray(r)) return `Found ${r.length} result(s)`
  return 'Completed'
}

export default function ToolCallCard({ tool }) {
  const config = TOOL_CONFIG[tool.name] || { icon: Search, label: tool.name, color: '#94a3b8' }
  const Icon = config.icon
  const isSuccess = tool.status === 'success'

  return (
    <div className={`tool-card ${isSuccess ? 'success' : 'error'}`}>
      <div className="tool-card-icon" style={{ background: `${config.color}22`, color: config.color }}>
        {isSuccess ? <CheckCircle /> : <XCircle />}
      </div>
      <div className="tool-card-body">
        <div className="tool-card-header">
          <span className="tool-card-name">{config.label}</span>
          <span className={`tool-card-badge ${isSuccess ? 'success' : 'error'}`}>
            {isSuccess ? 'Success' : 'Failed'}
          </span>
        </div>
        <div className="tool-card-action">{formatArgs(tool.name, tool.arguments)}</div>
        <div className="tool-card-result">{formatResult(tool)}</div>
      </div>
    </div>
  )
}
