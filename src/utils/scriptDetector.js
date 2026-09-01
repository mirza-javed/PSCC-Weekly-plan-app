const SINDHI_ONLY_CHARS = new Set("ٻڀٺٽٿڃڄڇڏڊڍڦڱڳڙڪڻڌ");
const ARABIC_SCRIPT_RANGE = /[\u0600-\u06FF]/;

export function detectScript(text = '', subject = '') {
  if (!text || typeof text !== 'string' || !text.trim()) {
    const sub = (subject || '').trim().toLowerCase();
    if (sub.includes('sindhi')) return 'sindhi';
    if (sub.includes('urdu') || sub.includes('islamiat')) return 'urdu';
    return 'latin';
  }

  for (const ch of text) {
    if (SINDHI_ONLY_CHARS.has(ch)) return 'sindhi';
  }

  if (!ARABIC_SCRIPT_RANGE.test(text)) {
    return 'latin';
  }

  const sub = (subject || '').trim().toLowerCase();
  if (sub.includes('sindhi')) return 'sindhi';
  if (sub.includes('urdu')) return 'urdu';

  return 'urdu';
}

export function isRtlScript(text = '', subject = '') {
  const script = detectScript(text, subject);
  return script === 'urdu' || script === 'sindhi';
}
