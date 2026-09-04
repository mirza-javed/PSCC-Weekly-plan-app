import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { TabNavigation } from './components/TabNavigation';
import { TimetableView } from './components/TimetableView';
import { DataEntryView } from './components/DataEntryView';
import { WeeklyPlanAdminView } from './components/WeeklyPlanAdminView';
import { PdfModal } from './components/PdfModal';
import { Toast } from './components/Toast';
import { getRelativeWeekMonday } from './utils/dateHelpers';

export function App() {
  const [activeTab, setActiveTab] = useState('data_entry');
  const [selectedWeek, setSelectedWeek] = useState(() => getRelativeWeekMonday(0));
  
  // Data states
  const [staticData, setStaticData] = useState({
    timetable: [],
    subjects: [],
    teachers: [],
    classes: [],
    class_sections: [],
  });
  const [plans, setPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Modal and Toast state
  const [pdfModal, setPdfModal] = useState({ isOpen: false, url: '', title: '' });
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast({ message: '', type: 'success' });
    }, 4000);
  };

  // Fetch Static Timetable
  const fetchTimetable = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) setIsRefreshing(true);
      const res = await fetch(`/api/timetable${forceRefresh ? '?refresh=true' : ''}`);
      if (!res.ok) throw new Error(`Failed to load timetable: ${res.statusText}`);
      const data = await res.json();
      setStaticData(data);
      if (forceRefresh) showToast('Timetable data reloaded successfully.');
    } catch (err) {
      console.error(err);
      showToast(`Error connecting to server: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Fetch Weekly Plans for selected week
  const fetchPlans = useCallback(async (weekIso) => {
    try {
      const res = await fetch(`/api/plans?week_start=${weekIso}`);
      if (!res.ok) throw new Error(`Failed to load plans: ${res.statusText}`);
      const data = await res.json();
      setPlans(data.entries || []);
    } catch (err) {
      console.error(err);
      showToast(`Error loading weekly plans: ${err.message}`, 'warning');
    }
  }, []);

  useEffect(() => {
    fetchTimetable();
  }, [fetchTimetable]);

  useEffect(() => {
    if (selectedWeek) {
      fetchPlans(selectedWeek);
    }
  }, [selectedWeek, fetchPlans]);

  // Save Plans Handler
  const handleSavePlans = async (rowsToSave, onSuccess) => {
    setIsSaving(true);
    try {
      const res = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: rowsToSave }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${res.status}): ${res.statusText}`);
      }

      const result = await res.json();

      if (result.failed && result.failed.length > 0) {
        showToast(
          `Saved ${result.saved.length} of ${result.total} periods. ${result.failed.length} failed. Please try saving again.`,
          'warning'
        );
      } else {
        showToast('All plans saved successfully!');
        if (onSuccess) onSuccess(result.rows || rowsToSave);
        // Refresh plans from server
        fetchPlans(selectedWeek);
      }
    } catch (err) {
      console.error(err);
      showToast(`Failed to save plans: ${err.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreviewPdf = (url, title) => {
    setPdfModal({
      isOpen: true,
      url,
      title,
    });
  };

  return (
    <div className="app-container">
      <Header
        onRefresh={() => fetchTimetable(true)}
        isRefreshing={isRefreshing}
      />

      <TabNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-text-muted)' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Loading Pakistan Steel Cadet College Schedule...
          </div>
          <p style={{ fontSize: '0.85rem', marginTop: '8px' }}>
            Fetching verified timetable data from Google Sheets.
          </p>
        </div>
      ) : (
        <main>
          {activeTab === 'timetable' && (
            <TimetableView
              timetable={staticData.timetable}
              teachers={staticData.teachers}
              classes={staticData.classes}
              classSections={staticData.class_sections}
              onPreviewPdf={handlePreviewPdf}
            />
          )}

          {activeTab === 'data_entry' && (
            <DataEntryView
              timetable={staticData.timetable}
              teachers={staticData.teachers}
              plans={plans}
              selectedWeek={selectedWeek}
              onWeekChange={setSelectedWeek}
              onSavePlans={handleSavePlans}
              onPreviewPdf={handlePreviewPdf}
              isSaving={isSaving}
            />
          )}

          {activeTab === 'weekly_plan' && (
            <WeeklyPlanAdminView
              timetable={staticData.timetable}
              classes={staticData.classes}
              plans={plans}
              selectedWeek={selectedWeek}
              onWeekChange={setSelectedWeek}
              onPreviewPdf={handlePreviewPdf}
            />
          )}
        </main>
      )}

      <PdfModal
        isOpen={pdfModal.isOpen}
        onClose={() => setPdfModal({ isOpen: false, url: '', title: '' })}
        pdfUrl={pdfModal.url}
        title={pdfModal.title}
      />

      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />
    </div>
  );
}
