import React, { useState, useMemo } from 'react';
import { Search, Download, Users, School } from 'lucide-react';

const DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export function TimetableView({ timetable = [], teachers = [], classes = [], classSections = [], onPreviewPdf }) {
  const [viewMode, setViewMode] = useState('class'); // 'class' or 'teacher'
  const [selectedClass, setSelectedClass] = useState(classes[0] || '8');
  const [selectedSection, setSelectedSection] = useState('A');
  const [selectedTeacher, setSelectedTeacher] = useState(teachers[0] || '');
  const [searchQuery, setSearchQuery] = useState('');

  // Available sections for chosen class
  const availableSections = useMemo(() => {
    const secs = timetable
      .filter((r) => String(r.Class) === String(selectedClass))
      .map((r) => r.Section)
      .filter(Boolean);
    return Array.from(new Set(secs)).sort();
  }, [timetable, selectedClass]);

  // Filtered and chronologically sorted rows (Monday -> Saturday, P1 -> P7)
  const filteredRows = useMemo(() => {
    let list = [];
    if (viewMode === 'class') {
      list = timetable.filter(
        (r) =>
          String(r.Class) === String(selectedClass) &&
          String(r.Section) === String(selectedSection)
      );
    } else {
      list = timetable.filter((r) => r.Teacher === selectedTeacher);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (r) =>
          (r.Subject && r.Subject.toLowerCase().includes(q)) ||
          (r.Teacher && r.Teacher.toLowerCase().includes(q)) ||
          (r.Class_Section && r.Class_Section.toLowerCase().includes(q)) ||
          (r.Day && r.Day.toLowerCase().includes(q))
      );
    }

    const dayIdx = (d) => {
      const idx = DAY_ORDER.indexOf(d);
      return idx === -1 ? 999 : idx;
    };

    return list.sort((a, b) => {
      const dayDiff = dayIdx(a.Day) - dayIdx(b.Day);
      if (dayDiff !== 0) return dayDiff;
      return (Number(a.Period) || 0) - (Number(b.Period) || 0);
    });
  }, [timetable, viewMode, selectedClass, selectedSection, selectedTeacher, searchQuery]);

  // Today's day name for highlight
  const todayDayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });

  // Group sorted rows by day so all periods of a single day are displayed together
  const groupedByDay = useMemo(() => {
    const map = {};
    DAY_ORDER.forEach((d) => { map[d] = []; });
    filteredRows.forEach((row) => {
      if (!map[row.Day]) map[row.Day] = [];
      map[row.Day].push(row);
    });
    return DAY_ORDER.map((day) => ({
      day,
      rows: map[day],
      isToday: day.toLowerCase() === todayDayName.toLowerCase(),
    })).filter((g) => g.rows.length > 0);
  }, [filteredRows, todayDayName]);

  const handleDownloadPdf = () => {
    if (viewMode === 'class') {
      const classSec = `${selectedClass}-${selectedSection}`;
      const url = `/api/pdf/class-timetable?class_section=${encodeURIComponent(classSec)}`;
      onPreviewPdf(url, `Timetable - Class ${classSec}`);
    } else {
      const url = `/api/pdf/teacher-timetable?teacher=${encodeURIComponent(selectedTeacher)}`;
      onPreviewPdf(url, `Timetable - ${selectedTeacher}`);
    }
  };

  return (
    <div>
      <div className="controls-card">
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className={`btn ${viewMode === 'class' ? 'btn-primary' : 'btn-outline'}`}
            style={{ flex: 1, minHeight: '40px' }}
            onClick={() => setViewMode('class')}
          >
            <School size={16} /> Class & Section
          </button>
          <button
            type="button"
            className={`btn ${viewMode === 'teacher' ? 'btn-primary' : 'btn-outline'}`}
            style={{ flex: 1, minHeight: '40px' }}
            onClick={() => setViewMode('teacher')}
          >
            <Users size={16} /> Teacher
          </button>
        </div>

        {viewMode === 'class' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="select-class">Class</label>
              <select
                id="select-class"
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
              <label className="form-label" htmlFor="select-section">Section</label>
              <select
                id="select-section"
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
        ) : (
          <div className="form-group">
            <label className="form-label" htmlFor="select-teacher">Teacher Name</label>
            <select
              id="select-teacher"
              className="form-select"
              value={selectedTeacher}
              onChange={(e) => setSelectedTeacher(e.target.value)}
            >
              {teachers.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--color-text-muted)' }} />
            <input
              type="search"
              className="form-input"
              style={{ paddingLeft: '36px', width: '100%' }}
              placeholder="Search by subject, teacher, day..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <button
            type="button"
            className="btn btn-outline"
            style={{ minHeight: '44px', whiteSpace: 'nowrap' }}
            onClick={handleDownloadPdf}
          >
            <Download size={16} /> PDF
          </button>
        </div>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto 20px', padding: '0 16px' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
          Showing <strong>{filteredRows.length}</strong> scheduled periods
        </div>

        <div className="timetable-table-wrapper">
          <table className="timetable-table">
            <thead>
              <tr>
                <th>Day</th>
                <th>Period</th>
                {viewMode === 'teacher' && <th>Class-Sec</th>}
                <th>Subject</th>
                {viewMode === 'class' && <th>Teacher</th>}
              </tr>
            </thead>
            <tbody>
              {groupedByDay.map(({ day, rows, isToday }) => (
                <React.Fragment key={day}>
                  <tr className={`day-separator-row ${isToday ? 'is-today' : ''}`}>
                    <td colSpan={viewMode === 'teacher' ? 4 : 4}>
                      <div className="day-separator-content">
                        <span className="day-separator-name">{day}</span>
                        <span className="day-separator-badge">
                          {rows.length} {rows.length === 1 ? 'period' : 'periods'}
                        </span>
                        {isToday && <span className="day-separator-today">● Today</span>}
                      </div>
                    </td>
                  </tr>
                  {rows.map((r, i) => (
                    <tr key={`${day}-${r.Period}-${i}`} className={isToday ? 'today-highlight' : ''}>
                      <td style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                        {r.Day}
                      </td>
                      <td>
                        <span className="period-pill">P{r.Period}</span>
                      </td>
                      {viewMode === 'teacher' && (
                        <td>
                          <strong>{r.Class_Section}</strong>
                        </td>
                      )}
                      <td>{r.Subject}</td>
                      {viewMode === 'class' && <td>{r.Teacher}</td>}
                    </tr>
                  ))}
                </React.Fragment>
              ))}
              {filteredRows.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-muted)' }}>
                    No periods match your selection.
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
