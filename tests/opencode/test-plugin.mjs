import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { BuildAndroidAppsPlugin } = await import(path.resolve(__dirname, '../../.opencode/plugins/build-android-apps.js'));

test('config registers skills dir', async () => {
  const plugin = await BuildAndroidAppsPlugin();
  const config = { skills: { paths: [] } };
  await plugin.config(config);
  assert.equal(config.skills.paths.length, 1);
  assert.ok(config.skills.paths[0].endsWith('skills'));
});

test('transform injects bootstrap once per session', async () => {
  const plugin = await BuildAndroidAppsPlugin();
  const output = { messages: [{ info: { role: 'user' }, parts: [{ type: 'text', text: 'hi' }] }] };
  await plugin['experimental.chat.messages.transform']({}, output);
  assert.equal(output.messages[0].parts.length, 2);
  assert.ok(output.messages[0].parts[0].text.includes('EXTREMELY_IMPORTANT'));
  await plugin['experimental.chat.messages.transform']({}, output);
  assert.equal(output.messages[0].parts.length, 2);
});
