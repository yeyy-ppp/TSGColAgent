import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchRuntime, selectedExperiment, sendConversationMessage, startExperiment } from './api';

describe('dashboard API client', () => {
  afterEach(() => vi.restoreAllMocks());

  it('reads the experiment id from the URL', () => {
    window.history.replaceState({}, '', '/?experiment=java-run');
    expect(selectedExperiment()).toBe('java-run');
  });

  it('requests the selected runtime snapshot', async () => {
    const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ schema_version: 1 }), { status: 200 }));
    await fetchRuntime('run-1');
    expect(mock).toHaveBeenCalledWith('/api/runtime?experiment=run-1', { cache: 'no-store' });
  });

  it('sends a persistent conversation to the test knowledge agent', async () => {
    const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ conversation: {}, message: {}, answer: {} }), { status: 200 }));
    await sendConversationMessage('chat-1', 'Calculator任务的覆盖率？');
    expect(mock).toHaveBeenCalledWith('/api/chats/chat-1/messages', expect.objectContaining({ method: 'POST' }));
  });

  it('starts the existing terminal runner through the backend', async () => {
    const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ experiment: { id: 'run-1' }, process_id: 8 }), { status: 201 }));
    await startExperiment({ mode: 'single', source: 'D:\\Calculator.java', output: 'D:\\runs\\calculator', language: 'java', llm: true });
    expect(mock).toHaveBeenCalledWith('/api/experiments/start', expect.objectContaining({ method: 'POST' }));
  });
});
