import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export function Toast({ message, type = 'success', onClose }) {
  if (!message) return null;

  return (
    <div className="toast-container">
      <div className={`toast toast-${type}`} role="alert">
        {type === 'success' && <CheckCircle2 size={18} />}
        {type === 'error' && <AlertCircle size={18} />}
        {type === 'warning' && <AlertCircle size={18} />}
        {type === 'info' && <Info size={18} />}
        <span>{message}</span>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#FFF', cursor: 'pointer', marginLeft: '8px' }}
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
