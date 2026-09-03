import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { BuildAndroidAppsExtension } = await import(path.resolve(__dirname, '../../.pi/extensions/build-android-apps.ts'));

const userMsg = (text) => ({ role: 'user', content: [{ type: 'text', text }], timestamp: Date.now() });

test('context injects bootstrap once per session', async () => {
  const ext = await BuildAndroidAppsExtension();
  await ext.session_start();
  const messages = [userMsg('hi')];
  await ext.context(messages);
  assert.equal(messages[0].content.length, 2);
  assert.ok(messages[0].content[0].text.includes('EXTREMELY_IMPORTANT'));
  await ext.context(messages);
  assert.equal(messages[0].content.length, 2);
});

test('session_compact re-arms injection', async () => {
  const ext = await BuildAndroidAppsExtension();
  await ext.session_start();
  const first = [userMsg('hi')];
  await ext.context(first);
  assert.equal(first[0].content.length, 2);
  await ext.session_compact();
  const second = [userMsg('follow-up')];
  await ext.context(second);
  assert.equal(second[0].content.length, 2);
  assert.ok(second[0].content[0].text.includes('EXTREMELY_IMPORTANT'));
});
