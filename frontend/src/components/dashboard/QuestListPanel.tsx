import PanelDark from '../../components/PanelDark'
import GoldRule from '../../components/GoldRule'
import type { QuestItem } from './types'
import './QuestListPanel.css'

type QuestListPanelProps = {
  title: string
  items: QuestItem[]
  className?: string
}

export default function QuestListPanel({ title, items, className = '' }: QuestListPanelProps) {
  return (
    <PanelDark className={`dash-panel dash-panel-list ${className}`} showCorners={false}>
      <div className="dash-panel-title">{title}</div>
      <GoldRule />
      <div className="quest-list">
        {items.map((item) => (
          <div key={item.course + item.title} className="quest-row">
            <span className={`quest-kind quest-kind-${item.kind}`} />
            <div className="quest-info">
              <span className="mono quest-course">{item.course}</span>
              <span className="quest-title">{item.title}</span>
            </div>
            <span className="mono quest-due">{item.due}</span>
          </div>
        ))}
      </div>
    </PanelDark>
  )
}
