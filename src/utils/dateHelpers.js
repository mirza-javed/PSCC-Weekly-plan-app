export function getMondayOf(dateInput = new Date()) {
  const d = new Date(dateInput);
  const day = d.getDay(); // 0 is Sunday, 1 is Monday, ...
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is Sunday
  const monday = new Date(d.setDate(diff));
  monday.setHours(0, 0, 0, 0);
  return monday;
}

export function toIsoDate(dateObj) {
  const d = new Date(dateObj);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatWeekRange(mondayIsoString) {
  if (!mondayIsoString) return '';
  const [y, m, d] = mondayIsoString.split('-').map(Number);
  const mon = new Date(y, m - 1, d);
  const sat = new Date(y, m - 1, d + 5);

  const monStr = mon.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  const satStr = sat.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  return `${monStr} — ${satStr}`;
}

export function isWeekLocked(mondayIsoString) {
  if (!mondayIsoString) return false;
  const todayIso = toIsoDate(new Date());
  // Editable if mondayIsoString > todayIso (future weeks only)
  return mondayIsoString <= todayIso;
}

export function getRelativeWeekMonday(offsetWeeks = 0) {
  const mon = getMondayOf(new Date());
  mon.setDate(mon.getDate() + offsetWeeks * 7);
  return toIsoDate(mon);
}
