import { ChatResponse, HealthResponse } from '../types';

const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      throw new Error(`Health check returned HTTP ${res.status}`);
    }
    return res.json();
  } catch (err: any) {
    throw new Error(`Backend unavailable at ${API_BASE}/health (${err.message})`);
  }
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Backend returned HTTP ${res.status}`);
    }

    return res.json();
  } catch (err: any) {
    throw new Error(err.message || 'Failed to connect to backend retrieval service.');
  }
}
