import { getIdToken } from './firebase';

const getAuthToken = async (): Promise<string | null> => {
  return getIdToken();
};

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  private async makeRequest<T>(method: string, path: string, body?: any): Promise<T> {
    const token = await getAuthToken();

    if (!token) {
      // Or handle this scenario differently, e.g., by redirecting to login
      // or allowing certain requests to proceed without a token.
      throw new Error('Authentication token not available. Please log in.');
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };

    const config: RequestInit = {
      method,
      headers,
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${path}`, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }

    if (response.status === 204) { // No content
      return null as T;
    }

    return response.json() as Promise<T>;
  }

  async submitQuery(query: string, sources?: string[], options?: Record<string, any>) {
    return this.makeRequest<{ task_id: string }>('POST', '/query', { query, sources, options });
  }

  async getTaskStatus(taskId: string) {
    // Matching TaskStatusResponse in DealerPortal.tsx, though result is still any
    return this.makeRequest<{ status: string, result?: any, taskId?: string }>('GET', `/task/${taskId}/status`);
  }

  async submitFeedback(taskId: string, feedback: { rating: number; comment?: string }) {
    return this.makeRequest<void>('POST', `/task/${taskId}/feedback`, feedback);
  }

  // Example of keeping an existing function, assuming it will be adapted or removed later
  async getAvailableModels() {
    // This might need to be updated or removed if not part of the new FastAPI backend
    return this.makeRequest('GET', '/models'); // Assuming a /models endpoint
  }

  async healthCheck() {
    const response = await fetch('/api/health'); // Assuming this doesn't need auth and isn't under /api/v1
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }
}

export const api = new ApiClient();
