import { ChatResponse, HealthResponse, ConversationContextState } from '../types';

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim();
const API_BASE = RAW_BASE ? `${RAW_BASE.replace(/\/+$/, '')}/api/v1` : '/api/v1';
const HEALTH_TIMEOUT_MS = 10000;
const CHAT_TIMEOUT_MS = 75000;

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    if (!res.ok) {
      throw new Error(`Health check returned HTTP ${res.status}`);
    }
    return res.json();
  } catch (err: any) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      throw new Error(`Health check timed out after ${HEALTH_TIMEOUT_MS / 1000}s.`);
    }
    throw new Error(`Backend unavailable at ${API_BASE}/health (${err.message})`);
  }
}

export async function sendChatMessage(
  message: string,
  preferred_language: string = 'auto',
  context_state?: ConversationContextState | null,
  session_id?: string
): Promise<ChatResponse> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        preferred_language,
        context_state: context_state || undefined,
        session_id: session_id || undefined,
      }),
      signal: AbortSignal.timeout(CHAT_TIMEOUT_MS),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Backend returned HTTP ${res.status}`);
    }

    return res.json();
  } catch (err: any) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      throw new Error(
        `Request timed out after ${CHAT_TIMEOUT_MS / 1000}s. The retrieval service may be warming up or busy.`
      );
    }
    throw new Error(err.message || 'Failed to connect to backend retrieval service.');
  }
}
