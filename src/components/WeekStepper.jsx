import React from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import {
  formatWeekRange,
  isWeekLocked,
  getMondayOf,
  toIsoDate,
  getRelativeWeekMonday,
} from '../utils/dateHelpers';

export function WeekStepper({ selectedWeek, onWeekChange }) {
  const isLocked = isWeekLocked(selectedWeek);
  const formattedRange = formatWeekRange(selectedWeek);

  const handlePrev = () => {
    const [y, m, d] = selectedWeek.split('-').map(Number);
    const prevMon = new Date(y, m - 1, d - 7);
    onWeekChange(toIsoDate(prevMon));
  };

  const handleNext = () => {
    const [y, m, d] = selectedWeek.split('-').map(Number);
    const nextMon = new Date(y, m - 1, d + 7);
    onWeekChange(toIsoDate(nextMon));
  };

  const handleDatePick = (e) => {
    const val = e.target.value;
    if (val) {
      const mon = getMondayOf(new Date(val));
      onWeekChange(toIsoDate(mon));
    }
  };

  const lastWeekIso = getRelativeWeekMonday(-1);
  const thisWeekIso = getRelativeWeekMonday(0);
  const nextWeekIso = getRelativeWeekMonday(1);

  return (
    <section className="week-stepper-card" aria-label="Week Selector">
      <div className="stepper-row">
        <button
          type="button"
          className="stepper-btn"
          onClick={handlePrev}
          aria-label="Previous Week"
          title="Previous Week"
        >
          <ChevronLeft size={20} />
        </button>

        <div className="stepper-info">
          <div className="stepper-range">{formattedRange}</div>
          <span
            className={`stepper-badge ${isLocked ? 'badge-locked' : 'badge-editable'}`}
          >
            {isLocked ? '🔒 Locked (Read-Only)' : '● Editable'}
          </span>
        </div>

        <button
          type="button"
          className="stepper-btn"
          onClick={handleNext}
          aria-label="Next Week"
          title="Next Week"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      <div className="quick-week-pills">
        <button
          type="button"
          className={`pill-btn ${selectedWeek === lastWeekIso ? 'active' : ''}`}
          onClick={() => onWeekChange(lastWeekIso)}
        >
          Last Week
        </button>
        <button
          type="button"
          className={`pill-btn ${selectedWeek === thisWeekIso ? 'active' : ''}`}
          onClick={() => onWeekChange(thisWeekIso)}
        >
          This Week
        </button>
        <button
          type="button"
          className={`pill-btn ${selectedWeek === nextWeekIso ? 'active' : ''}`}
          onClick={() => onWeekChange(nextWeekIso)}
        >
          Next Week
        </button>
        
        <label className="pill-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
          <CalendarIcon size={14} />
          <span>Pick Date</span>
          <input
            type="date"
            onChange={handleDatePick}
            style={{ opacity: 0, position: 'absolute', width: '1px', height: '1px' }}
          />
        </label>
      </div>
    </section>
  );
}
