import { Bot, PanelLeftClose, Cpu, RotateCcw } from 'lucide-react'
import QuickChips from './QuickChips.jsx'

export default function Sidebar({ open, onClose, status, model, onChipSelect, onReset, loading }) {
  const dotClass = `status-dot ${status}`
  const statusText = { loading: 'Connecting…', online: 'Online', error: 'Connection Error' }

  return (
    <aside className={`sidebar${open ? '' : ' closed'}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon"><Bot /></div>
          <div className="logo-text">
            <span className="logo-title">NexSupport</span>
            <span className="logo-sub">AI Assistant</span>
          </div>
        </div>
        <button className="icon-btn" onClick={onClose} aria-label="Close sidebar">
          <PanelLeftClose />
        </button>
      </div>

      {/* Status */}
      <div className="status-bar">
        <span className={dotClass} />
        <span className="status-label">{statusText[status] ?? status}</span>
      </div>

      {/* Model */}
      <div className="model-card">
        <div className="model-card-label">
          <Cpu /> Active Model
        </div>
        <div className="model-name">{model || 'Loading…'}</div>
      </div>

      {/* Quick Starters */}
      <div className="section-label">Quick Start</div>
      <QuickChips onSelect={onChipSelect} disabled={loading} />

      {/* Footer */}
      <div className="sidebar-footer">
        <button className="btn-reset" onClick={onReset} disabled={loading}>
          <RotateCcw /> New Conversation
        </button>
      </div>
    </aside>
  )
}
