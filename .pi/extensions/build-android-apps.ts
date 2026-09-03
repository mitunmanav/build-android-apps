import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let _cache = undefined;
let _injected = false;

const strip = (c) => { const m = c.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/); return m ? m[1] : c; };

const getBootstrap = () => {
  if (_cache !== undefined) return _cache;
  const p = path.resolve(__dirname, '../../skills/build-android-apps/SKILL.md');
  if (!fs.existsSync(p)) { _cache = null; return null; }
  const body = strip(fs.readFileSync(p, 'utf8'));
  const map = 'Invoke a skill → `skill` tool; Read → `read`; Edit → `apply_patch`; Run → `bash`; Search → `grep`,`glob`; Subagent → `task` general; Todos → `todowrite`.';
  _cache = `<EXTREMELY_IMPORTANT>\nYou have build-android-apps.\n\n${body}\n\n${map}\n</EXTREMELY_IMPORTANT>`;
  return _cache;
};

const resetInjection = () => { _injected = false; };

export const BuildAndroidAppsExtension = async () => ({
  session_start: async () => { resetInjection(); },
  session_compact: async () => { resetInjection(); },
  context: async (messages) => {
    const b = getBootstrap(); if (!b || !messages.length) return messages;
    if (_injected) return messages;
    const first = messages.find((m) => m.role === 'user'); if (!first || !first.content.length) return messages;
    if (first.content.some((p) => p.type === 'text' && p.text.includes('EXTREMELY_IMPORTANT'))) return messages;
    _injected = true;
    first.content.unshift({ type: 'text', text: b, timestamp: Date.now() });
    return messages;
  }
});

export { getBootstrap, resetInjection };
