import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, Save } from 'lucide-react';
import { PeriodInput } from './PeriodInput';

export function DayAccordion({
  day,
  slots = [],
  topicsByRowId = {},
  draftsByRowId = {},
  savedRowIds = new Set(),
  onTopicChange,
  onTopicBlur,
  onSaveDay,
  isLocked = false,
  defaultOpen = false,
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const filledCount = slots.filter((slot) => {
    const topic = (topicsByRowId[slot.RowID] || '').trim();
    return topic.length > 0;
  }).length;

  const totalCount = slots.length;
  const isComplete = totalCount > 0 && filledCount === totalCount;

  return (
    <article className={`day-card ${isComplete ? 'complete' : ''}`}>
      <button
        type="button"
        className="day-accordion-header"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className="day-title-group">
          {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          <h3>{day}</h3>
          <span className="day-slots-count">
            {filledCount}/{totalCount} filled
          </span>
        </div>

        <div>
          {isComplete ? (
            <span className="status-badge saved" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={13} /> Complete
            </span>
          ) : (
            <span className="status-badge draft">
              {totalCount - filledCount} remaining
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="day-body">
          {slots.map((slot) => {
            const currentTopic = topicsByRowId[slot.RowID] || '';
            const isDraft = slot.RowID in draftsByRowId;
            const isSaved = savedRowIds.has(slot.RowID);

            return (
              <PeriodInput
                key={slot.RowID}
                slot={slot}
                value={currentTopic}
                onChange={(newVal) => onTopicChange(slot.RowID, newVal)}
                onBlur={(newVal) => onTopicBlur && onTopicBlur(slot.RowID, newVal)}
                disabled={isLocked}
                isDraft={isDraft}
                isSaved={isSaved}
              />
            );
          })}

          {!isLocked && onSaveDay && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ minHeight: '38px', fontSize: '0.85rem' }}
                onClick={() => onSaveDay(day)}
              >
                <Save size={15} /> Save {day}'s Plans
              </button>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
