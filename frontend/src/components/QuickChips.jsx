import { Sparkles, Wallet, RefreshCcwDot, Lock, ArrowUpDown } from 'lucide-react'

const CHIPS = [
  { icon: <Sparkles />,     label: 'What can you do?',           prompt: 'What can you help me with?' },
  { icon: <Wallet />,       label: 'Check account balance',      prompt: 'What is the balance on my chequing account?' },
  { icon: <RefreshCcwDot />, label: 'Dispute a transaction',     prompt: 'I need to dispute a transaction on my account.' },
  { icon: <Lock />,         label: 'Report a lost card',         prompt: 'I lost my debit card. How do I report it as lost or stolen?' },
  { icon: <ArrowUpDown />,  label: 'Increase transfer limit',    prompt: 'I want to increase my daily transfer limit.' },
]

export default function QuickChips({ onSelect, disabled }) {
  return (
    <div className="quick-starters">
      {CHIPS.map(({ icon, label, prompt }) => (
        <button
          key={label}
          className="chip"
          onClick={() => onSelect(prompt)}
          disabled={disabled}
        >
          {icon}
          {label}
        </button>
      ))}
    </div>
  )
}
