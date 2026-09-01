import React, { useState, useEffect, useMemo } from 'react';
import { WeekStepper } from './WeekStepper';
import { DayAccordion } from './DayAccordion';
import { StickyActionBar } from './StickyActionBar';
import { Copy, Sparkles, CheckCircle2 } from 'lucide-react';
import { isWeekLocked, getRelativeWeekMonday } from '../utils/dateHelpers';

const DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export function DataEntryView({
  timetable = [],
  teachers = [],
  plans = [],
  selectedWeek,
  onWeekChange,
  onSavePlans,
  onPreviewPdf,
  isSaving,
}) {
  // Remember selected teacher in localStorage
  const [selectedTeacher, setSelectedTeacher] = useState(() => {
    return localStorage.getItem('pscc_selected_teacher') || teachers[0] || '';
  });

  // Local draft cache stored by entry_id
  const [draftTopics, setDraftTopics] = useState({});
  const [persistedTopics, setPersistedTopics] = useState({});
  const [savedRowIds, setSavedRowIds] = useState(new Set());

  useEffect(() => {
    if (selectedTeacher) {
      localStorage.setItem('pscc_selected_teacher', selectedTeacher);
    }
  }, [selectedTeacher]);

  // Teacher's timetable slots sorted by DAY_ORDER and Period
  const teacherSlots = useMemo(() => {
    const slots = timetable.filter((r) => r.Teacher === selectedTeacher);
    const dayIdx = (d) => {
      const idx = DAY_ORDER.indexOf(d);
      return idx === -1 ? 999 : idx;
    };
    return slots.sort((a, b) => {
      const diff = dayIdx(a.Day) - dayIdx(b.Day);
      if (diff !== 0) return diff;
      return (Number(a.Period) || 0) - (Number(b.Period) || 0);
    });
  }, [timetable, selectedTeacher]);

  // Sync incoming plans from server
  useEffect(() => {
    const loaded = {};
    const saved = new Set();
    plans.forEach((p) => {
      if (p.TimetableRowID) {
        loaded[p.TimetableRowID] = p.Topic || '';
        if (p.Topic && p.Topic.trim()) {
          saved.add(p.TimetableRowID);
        }
      }
    });
    setPersistedTopics(loaded);
    setSavedRowIds(saved);
    setDraftTopics({}); // Clear drafts on fresh week load
  }, [plans, selectedWeek]);

  // Merge persisted topics + local unsaved drafts
  const activeTopics = useMemo(() => {
    return { ...persistedTopics, ...draftTopics };
  }, [persistedTopics, draftTopics]);

  // Group teacher's slots by Day
  const groupedDays = useMemo(() => {
    const map = {};
    DAY_ORDER.forEach((d) => { map[d] = []; });
    teacherSlots.forEach((slot) => {
      if (map[slot.Day]) {
        map[slot.Day].push(slot);
      }
    });
    return DAY_ORDER.map((day) => ({
      day,
      slots: map[day].sort((a, b) => Number(a.Period) - Number(b.Period)),
    })).filter((group) => group.slots.length > 0);
  }, [teacherSlots]);

  const isLocked = isWeekLocked(selectedWeek);

  const handleTopicChange = (rowId, newTopic) => {
    setDraftTopics((prev) => ({
      ...prev,
      [rowId]: newTopic,
    }));
  };

  const unsavedCount = Object.keys(draftTopics).length;

  const totalSlots = teacherSlots.length;
  const filledSlots = teacherSlots.filter((s) => {
    const topic = (activeTopics[s.RowID] || '').trim();
    return topic.length > 0;
  }).length;

  // Save All handler
  const handleSaveAll = () => {
    const rowsToSave = teacherSlots.map((slot) => {
      const entryId = `${slot.RowID}_${selectedWeek}`;
      const topic = activeTopics[slot.RowID] || '';
      return {
        EntryID: entryId,
        TimetableRowID: slot.RowID,
        WeekStartDate: selectedWeek,
        Topic: topic,
        SubmittedBy: selectedTeacher,
      };
    });

    onSavePlans(rowsToSave, () => {
      // On success, promote drafts to persisted
      setPersistedTopics(activeTopics);
      setDraftTopics({});
      const newSaved = new Set(savedRowIds);
      rowsToSave.forEach((r) => {
        if (r.Topic.trim()) newSaved.add(r.TimetableRowID);
      });
      setSavedRowIds(newSaved);
    });
  };

  // Save single day handler
  const handleSaveDay = (dayName) => {
    const dayGroup = groupedDays.find((g) => g.day === dayName);
    if (!dayGroup) return;

    const rowsToSave = dayGroup.slots.map((slot) => {
      const entryId = `${slot.RowID}_${selectedWeek}`;
      const topic = activeTopics[slot.RowID] || '';
      return {
        EntryID: entryId,
        TimetableRowID: slot.RowID,
        WeekStartDate: selectedWeek,
        Topic: topic,
        SubmittedBy: selectedTeacher,
      };
    });

    onSavePlans(rowsToSave, () => {
      setPersistedTopics((prev) => ({ ...prev, ...draftTopics }));
      // Clear saved day from drafts
      setDraftTopics((prev) => {
        const next = { ...prev };
        dayGroup.slots.forEach((s) => { delete next[s.RowID]; });
        return next;
      });
    });
  };

  // Copy last week topics
  const handleCopyPreviousWeek = async () => {
    if (!window.confirm('Copy submitted topics from the previous week into empty slots?')) return;
    try {
      const [y, m, d] = selectedWeek.split('-').map(Number);
      const prevMon = new Date(y, m - 1, d - 7);
      const prevMonIso = prevMon.toISOString().split('T')[0];

      const res = await fetch(`/api/plans?week_start=${prevMonIso}`);
      const data = await res.json();
      if (data.entries && data.entries.length > 0) {
        const newDrafts = { ...draftTopics };
        let copied = 0;
        data.entries.forEach((e) => {
          if (e.Topic && !activeTopics[e.TimetableRowID]) {
            newDrafts[e.TimetableRowID] = e.Topic;
            copied++;
          }
        });
        setDraftTopics(newDrafts);
        alert(`Successfully copied ${copied} lesson topics from last week into your draft!`);
      } else {
        alert('No plans found for the previous week.');
      }
    } catch (err) {
      alert('Could not load previous week plans: ' + err.message);
    }
  };

  const handleExportPdf = () => {
    const url = `/api/pdf/teacher-plan?teacher=${encodeURIComponent(selectedTeacher)}&week_start=${selectedWeek}`;
    onPreviewPdf(url, `Weekly Plan - ${selectedTeacher} (${selectedWeek})`);
  };

  return (
    <div>
      <WeekStepper selectedWeek={selectedWeek} onWeekChange={onWeekChange} />

      <div className="controls-card">
        <div className="form-group">
          <label className="form-label" htmlFor="entry-teacher-select">Your Name (Teacher)</label>
          <select
            id="entry-teacher-select"
            className="form-select"
            value={selectedTeacher}
            onChange={(e) => setSelectedTeacher(e.target.value)}
          >
            {teachers.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {!isLocked && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ flex: 1, minHeight: '40px', fontSize: '0.85rem' }}
              onClick={handleCopyPreviousWeek}
            >
              <Copy size={15} /> Copy Previous Week Topics
            </button>
          </div>
        )}
      </div>

      {teacherSlots.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>
          No scheduled periods found for <strong>{selectedTeacher}</strong>.
        </div>
      ) : (
        <>
          <div className="day-cards-list">
            {groupedDays.map(({ day, slots }, index) => (
              <DayAccordion
                key={day}
                day={day}
                slots={slots}
                topicsByRowId={activeTopics}
                draftsByRowId={draftTopics}
                savedRowIds={savedRowIds}
                onTopicChange={handleTopicChange}
                onSaveDay={handleSaveDay}
                isLocked={isLocked}
                defaultOpen={index === 0} // Open Monday by default
              />
            ))}
          </div>
          <div className="action-bar-spacer" aria-hidden="true" />
        </>
      )}

      {teacherSlots.length > 0 && (
        <StickyActionBar
          totalSlots={totalSlots}
          filledSlots={filledSlots}
          unsavedCount={unsavedCount}
          onSaveAll={handleSaveAll}
          onExportPdf={handleExportPdf}
          isSaving={isSaving}
          isLocked={isLocked}
        />
      )}
    </div>
  );
}
