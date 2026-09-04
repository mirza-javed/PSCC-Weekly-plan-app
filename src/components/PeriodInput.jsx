import React from 'react';
import { detectScript, isRtlScript } from '../utils/scriptDetector';

const PDF_SAFE_LIMIT = 100;

export function PeriodInput({
  slot,
  value = '',
  onChange,
  onBlur,
  disabled = false,
  isDraft = false,
  isSaved = false,
}) {
  const isRtl = isRtlScript(value, slot.Subject);
  const script = detectScript(value, slot.Subject);
  const charCount = value.length;
  const isOverLimit = charCount > PDF_SAFE_LIMIT;

  const getStatus = () => {
    if (isDraft) return { label: '✎ Draft', class: 'draft' };
    if (isSaved || (value && value.trim())) return { label: '✓ Saved', class: 'saved' };
    return { label: '— Empty', class: 'empty' };
  };

  const status = getStatus();

  const getScriptClass = () => {
    if (script === 'sindhi') return 'font-sindhi';
    if (script === 'urdu') return 'font-urdu';
    return '';
  };

  const getPlaceholder = () => {
    if (script === 'sindhi') return 'هفتيوار سبق جو عنوان داخل ڪريو...';
    if (script === 'urdu') return 'ہفتہ وار سبق کا عنوان درج کریں...';
    return 'Enter lesson topic...';
  };

  return (
    <div className={`period-card ${isDraft ? 'has-draft' : ''}`}>
      <div className="period-header">
        <div className="period-meta">
          <span className="period-pill">P{slot.Period}</span>
          <span style={{ color: 'var(--color-primary)' }}>{slot.Class_Section}</span>
          <span style={{ color: 'var(--color-text-muted)', fontWeight: 400 }}>·</span>
          <span>{slot.Subject}</span>
        </div>

        <span className={`status-badge ${status.class}`}>
          {status.label}
        </span>
      </div>

      <textarea
        dir={isRtl ? 'rtl' : 'ltr'}
        className={`smart-textarea ${getScriptClass()} ${isOverLimit ? 'over-limit' : ''}`}
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        onBlur={() => onBlur && onBlur(value)}
        placeholder={getPlaceholder()}
        disabled={disabled}
        rows={2}
      />

      <div className="period-footer">
        <span>
          {script === 'urdu' && 'اردو نستعلیق (Urdu - Nastaliq)'}
          {script === 'sindhi' && 'سنڌي لطيفي (Sindhi - Lateefi)'}
          {script === 'latin' && 'English / Latin'}
        </span>

        <span style={{ color: isOverLimit ? 'var(--color-status-empty)' : 'inherit', fontWeight: isOverLimit ? 700 : 400 }}>
          {charCount}/{PDF_SAFE_LIMIT} chars {isOverLimit && '⚠️ (May wrap)'}
        </span>
      </div>
    </div>
  );
}
