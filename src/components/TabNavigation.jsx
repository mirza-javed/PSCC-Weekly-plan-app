import React from 'react';
import { Calendar, Edit3, Eye } from 'lucide-react';

export function TabNavigation({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'timetable', label: 'Timetable View', icon: Calendar },
    { id: 'data_entry', label: 'Data Entry', icon: Edit3 },
    { id: 'weekly_plan', label: 'Weekly Plan View', icon: Eye },
  ];

  return (
    <nav className="tabs-container" role="tablist" aria-label="Main Navigation">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            className={`tab-button ${isActive ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <Icon size={18} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
