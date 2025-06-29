import { JsonRpcRequest, JsonRpcResponse, ChatResponse } from './types';

class ApiClient {
  private idCounter = 1;

  private async makeRequest<T>(method: string, params?: any): Promise<T> {
    const request: JsonRpcRequest = {
      jsonrpc: '2.0',
      id: this.idCounter++,
      method,
      params
    };

    const response = await fetch('/api/rpc', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }

    const jsonResponse: JsonRpcResponse<T> = await response.json();

    if (jsonResponse.error) {
      throw new Error(`${jsonResponse.error.message} (Code: ${jsonResponse.error.code})`);
    }

    if (!jsonResponse.result) {
      throw new Error('No result returned from server');
    }

    return jsonResponse.result as T;
  }

  async sendMessage(conversationId: number, content: string, agentType?: string, model?: string, coordination?: boolean) {
    const response = await this.makeRequest<ChatResponse>('send_message', {
      conversationId,
      content,
      agentType,
      model,
      coordination
    });

    return response;
  }

  async getAvailableModels() {
    return this.makeRequest('available_models', {});
  }

  async searchMemories(query: string, similarity?: number) {
    return this.makeRequest('memory_search', {
      query,
      similarity
    });
  }

  async storeMemory(content: string, metadata?: any) {
    return this.makeRequest('memory_store', {
      content,
      metadata
    });
  }

  async listFiles() {
    return this.makeRequest('file_list');
  }

  async readFile(path: string) {
    return this.makeRequest('file_read', { path });
  }

  async writeFile(path: string, content: string) {
    return this.makeRequest('file_write', { path, content });
  }



  // MCP Integration
  async getMCPServers() {
    return await this.makeRequest('mcp_servers', {});
  }

  async getMCPServerStatus() {
    return await this.makeRequest('mcp_server_status', {});
  }

  async executeMCPOperation(server: string, operation: string, params: any) {
    return await this.makeRequest('mcp_operation', {
      server,
      operation,
      params
    });
  }

  async getConversations() {
    return this.makeRequest('get_conversations');
  }

  async createConversation(title?: string) {
    return this.makeRequest('create_conversation', { title });
  }

  async getMessages(conversationId: number) {
    return this.makeRequest('get_messages', { conversationId });
  }

  async getAgents(): Promise<{ agents: any[] }> {
    return this.makeRequest<{ agents: any[] }>('get_agents');
  }

  async getServiceStatus() {
    return this.makeRequest('service_status');
  }

  async getUserFiles() {
    return this.makeRequest('get_user_files');
  }

  async getFileData(fileId: number) {
    return this.makeRequest('get_file_data', { fileId });
  }

  async validateDataQuality(fileId: number) {
    return this.makeRequest('validate_data_quality', { fileId });
  }

  async healthCheck() {
    const response = await fetch('/api/health');
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }
}

export const api = new ApiClient();
