import { Sparkles, Package, RefreshCcwDot, Lock, Briefcase } from 'lucide-react'

const CHIPS = [
  { icon: <Sparkles />, label: 'What can you do?',       prompt: 'What can you help me with?' },
  { icon: <Package />,  label: 'Order issue',            prompt: 'I have an issue with my order. Can you help?' },
  { icon: <RefreshCcwDot />, label: 'Request a refund',  prompt: "I'd like to request a refund. What's the process?" },
  { icon: <Lock />,     label: 'Account access',         prompt: 'I am having trouble logging into my account.' },
  { icon: <Briefcase />, label: 'SME business support',  prompt: 'I need support for my small business operations.' },
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
