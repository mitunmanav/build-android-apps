import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
let _cache = undefined;
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
export const BuildAndroidAppsPlugin = async () => ({
  config: async (config) => {
    config.skills = config.skills || {}; config.skills.paths = config.skills.paths || [];
    const dir = path.resolve(__dirname, '../../skills');
    if (!config.skills.paths.includes(dir)) config.skills.paths.push(dir);
  },
  'experimental.chat.messages.transform': async (_input, output) => {
    const b = getBootstrap(); if (!b || !output.messages.length) return;
    const first = output.messages.find(m => m.info.role === 'user'); if (!first || !first.parts.length) return;
    if (first.parts.some(p => p.type === 'text' && p.text.includes('EXTREMELY_IMPORTANT'))) return;
    const ref = first.parts[0]; first.parts.unshift({ ...ref, type: 'text', text: b });
  }
});
