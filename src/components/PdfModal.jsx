import React from 'react';
import { X, Download } from 'lucide-react';

export function PdfModal({ isOpen, onClose, pdfUrl, title = 'PDF Document Preview' }) {
  if (!isOpen || !pdfUrl) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-content">
        <div className="modal-header">
          <h2 id="modal-title" style={{ fontSize: '1.05rem', fontWeight: 600 }}>{title}</h2>
          <button
            type="button"
            className="stepper-btn"
            onClick={onClose}
            style={{ width: '32px', height: '32px', minWidth: '32px', minHeight: '32px', background: 'transparent', color: '#FFF', border: 'none' }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body" style={{ padding: 0, height: '70vh' }}>
          <iframe
            src={pdfUrl}
            title={title}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
          />
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <a
            href={pdfUrl}
            download
            className="btn btn-primary"
            style={{ textDecoration: 'none' }}
          >
            <Download size={18} /> Download File
          </a>
        </div>
      </div>
    </div>
  );
}
