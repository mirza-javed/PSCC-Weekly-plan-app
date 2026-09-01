import React, { useState, useMemo } from 'react';
import { WeekStepper } from './WeekStepper';
import { Download, AlertTriangle, CheckCircle, Search } from 'lucide-react';
import { isRtlScript, detectScript } from '../utils/scriptDetector';

const DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export function WeeklyPlanAdminView({
  timetable = [],
  classes = [],
  plans = [],
  selectedWeek,
  onWeekChange,
  onPreviewPdf,
}) {
  const [selectedClass, setSelectedClass] = useState(classes[0] || '8');
  const [selectedSection, setSelectedSection] = useState('A');
  const [filterMissingOnly, setFilterMissingOnly] = useState(false);

  // Available sections for chosen class
  const availableSections = useMemo(() => {
    const secs = timetable
      .filter((r) => String(r.Class) === String(selectedClass))
      .map((r) => r.Section)
      .filter(Boolean);
    return Array.from(new Set(secs)).sort();
  }, [timetable, selectedClass]);

  // Merge timetable slots with loaded week's plan topics
  const mergedRows = useMemo(() => {
    const classSecSlots = timetable.filter(
      (r) =>
        String(r.Class) === String(selectedClass) &&
        String(r.Section) === String(selectedSection)
    );

    const plansMap = {};
    plans.forEach((p) => {
      if (p.TimetableRowID) {
        plansMap[p.TimetableRowID] = p.Topic || '';
      }
    });

    const dayIdx = (d) => {
      const idx = DAY_ORDER.indexOf(d);
      return idx === -1 ? 999 : idx;
    };

    const rows = classSecSlots.map((slot) => {
      const topic = plansMap[slot.RowID] || '';
      return {
        ...slot,
        Topic: topic,
        hasTopic: Boolean(topic && topic.trim()),
      };
    });

    return rows.sort((a, b) => {
      const dayDiff = dayIdx(a.Day) - dayIdx(b.Day);
      if (dayDiff !== 0) return dayDiff;
      return (Number(a.Period) || 0) - (Number(b.Period) || 0);
    });
  }, [timetable, selectedClass, selectedSection, plans]);

  // Metrics
  const totalSlots = mergedRows.length;
  const filledSlots = mergedRows.filter((r) => r.hasTopic).length;
  const missingSlots = totalSlots - filledSlots;
  const percentage = totalSlots > 0 ? Math.round((filledSlots / totalSlots) * 100) : 0;

  // Filtered rows
  const displayRows = useMemo(() => {
    if (filterMissingOnly) {
      return mergedRows.filter((r) => !r.hasTopic);
    }
    return mergedRows;
  }, [mergedRows, filterMissingOnly]);

  const handleExportPdf = () => {
    const classSec = `${selectedClass}-${selectedSection}`;
    const url = `/api/pdf/weekly-plan?class_section=${encodeURIComponent(classSec)}&week_start=${selectedWeek}`;
    onPreviewPdf(url, `Weekly Plan - Class ${classSec} (${selectedWeek})`);
  };

  return (
    <div>
      <WeekStepper selectedWeek={selectedWeek} onWeekChange={onWeekChange} />

      <div className="controls-card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="admin-select-class">Class</label>
            <select
              id="admin-select-class"
              className="form-select"
              value={selectedClass}
              onChange={(e) => {
                setSelectedClass(e.target.value);
                const firstSec = timetable
                  .filter((r) => String(r.Class) === e.target.value)
                  .map((r) => r.Section)[0] || 'A';
                setSelectedSection(firstSec);
              }}
            >
              {classes.map((c) => (
                <option key={c} value={c}>Class {c}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="admin-select-section">Section</label>
            <select
              id="admin-select-section"
              className="form-select"
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
            >
              {availableSections.map((s) => (
                <option key={s} value={s}>Section {s}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={filterMissingOnly}
              onChange={(e) => setFilterMissingOnly(e.target.checked)}
            />
            <span>Show missing periods only</span>
          </label>

          <button
            type="button"
            className="btn btn-primary"
            style={{ minHeight: '42px' }}
            onClick={handleExportPdf}
          >
            <Download size={16} /> Export Class Weekly PDF
          </button>
        </div>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto 20px', padding: '0 16px' }}>
        {/* Status banner */}
        <div
          style={{
            background: missingSlots > 0 ? '#FEF2F2' : '#ECFDF5',
            border: `1px solid ${missingSlots > 0 ? '#FECACA' : '#A7F3D0'}`,
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {missingSlots > 0 ? (
              <AlertTriangle size={20} color="#DC2626" />
            ) : (
              <CheckCircle size={20} color="#059669" />
            )}
            <span style={{ fontWeight: 600, fontSize: '0.9rem', color: missingSlots > 0 ? '#991B1B' : '#065F46' }}>
              Class {selectedClass}-{selectedSection}: {filledSlots} of {totalSlots} Planned ({percentage}%)
            </span>
          </div>

          {missingSlots > 0 && (
            <span style={{ fontSize: '0.8rem', color: '#DC2626', fontWeight: 700 }}>
              {missingSlots} period(s) missing
            </span>
          )}
        </div>

        {/* Merged table */}
        <div className="timetable-table-wrapper">
          <table className="timetable-table">
            <thead>
              <tr>
                <th>Day</th>
                <th>Period</th>
                <th>Subject</th>
                <th>Teacher</th>
                <th>Topic / Lesson Plan</th>
              </tr>
            </thead>
            <tbody>
              {displayRows.map((r, i) => {
                const isRtl = isRtlScript(r.Topic, r.Subject);
                const script = detectScript(r.Topic, r.Subject);
                const scriptClass = script === 'sindhi' ? 'font-sindhi' : script === 'urdu' ? 'font-urdu' : '';
                return (
                  <tr key={i} style={{ background: !r.hasTopic ? '#FFF9F9' : 'transparent' }}>
                    <td style={{ fontWeight: 600 }}>{r.Day}</td>
                    <td>P{r.Period}</td>
                    <td>{r.Subject}</td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>{r.Teacher}</td>
                    <td>
                      {r.hasTopic ? (
                        <span
                          dir={isRtl ? 'rtl' : 'ltr'}
                          className={scriptClass}
                          style={{ display: 'block', maxWidth: '380px' }}
                        >
                          {r.Topic}
                        </span>
                      ) : (
                        <span style={{ color: '#DC2626', fontStyle: 'italic', fontSize: '0.82rem' }}>
                          (No plan submitted)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {displayRows.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-muted)' }}>
                    No missing periods! All plans for this week are complete.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
