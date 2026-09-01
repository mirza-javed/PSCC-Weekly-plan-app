import React from 'react';
import { Calendar, RefreshCw } from 'lucide-react';

export function Header({ onRefresh, isRefreshing }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <img
          src="/pscc-logo.jpg"
          alt="PSCC Crest"
          className="header-logo"
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
        <div className="header-title-group">
          <h1>Pakistan Steel Cadet College</h1>
          <p>Weekly Teaching Plan & Schedule System</p>
        </div>
      </div>

      <button
        type="button"
        className="stepper-btn"
        onClick={onRefresh}
        disabled={isRefreshing}
        title="Refresh Data from Google Sheets"
        aria-label="Refresh timetable data"
        style={{ width: '38px', height: '38px', minWidth: '38px', minHeight: '38px' }}
      >
        <RefreshCw size={16} className={isRefreshing ? 'spin-animation' : ''} />
      </button>
    </header>
  );
}
