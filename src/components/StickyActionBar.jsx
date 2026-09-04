import React from 'react';
import { Save, Download, CheckCircle2 } from 'lucide-react';

export function StickyActionBar({
  totalSlots,
  filledSlots,
  unsavedCount,
  onSaveAll,
  onExportPdf,
  isSaving,
  isLocked,
}) {
  const percentage = totalSlots > 0 ? Math.round((filledSlots / totalSlots) * 100) : 0;

  return (
    <aside className="sticky-action-bar" aria-label="Action Bar">
      <div className="action-bar-content">
        <div className="progress-row">
          <span>Weekly Plan Progress</span>
          <span>
            {filledSlots} of {totalSlots} Periods ({percentage}%)
          </span>
        </div>

        <div className="progress-track" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
          <div className="progress-fill" style={{ width: `${percentage}%` }} />
        </div>

        <div className="action-buttons">
          {!isLocked ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={onSaveAll}
              disabled={isSaving}
            >
              <Save size={18} />
              {isSaving ? 'Saving Plans...' : 'Save All Plan'}
            </button>
          ) : (
            <button type="button" className="btn btn-secondary" disabled>
              🔒 Week Locked (Read-Only)
            </button>
          )}

          <button
            type="button"
            className="btn btn-outline"
            onClick={onExportPdf}
          >
            <Download size={18} /> Download PDF
          </button>
        </div>
      </div>
    </aside>
  );
}
