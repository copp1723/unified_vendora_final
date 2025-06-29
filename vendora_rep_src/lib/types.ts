export interface Agent {
  id: number;
  name: string;
  description: string;
  systemPrompt: string;
  isActive: boolean;
  capabilities: string[];
  createdAt: Date;
}

export interface Message {
  id: number;
  conversationId: number;
  userId?: number;
  agentType?: string;
  content: string;
  metadata?: any;
  tokenCount?: number;
  createdAt: Date;
}

export interface Conversation {
  id: number;
  userId: number;
  title?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Memory {
  id: number;
  userId: number;
  content: string;
  metadata?: any;
  similarity?: number;
  createdAt: Date;
}

export interface ServiceStatus {
  status: 'active' | 'limited' | 'error';
  message: string;
}

export interface ServiceStatuses {
  openrouter: ServiceStatus;
  supermemory: ServiceStatus;
  supabase: ServiceStatus;
  file_access: ServiceStatus;
  email: ServiceStatus;
}

export interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: any;
}

export interface JsonRpcResponse<T = any> {
  jsonrpc: '2.0';
  id: string | number;
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

export interface AgentResponse {
  content: string;
  agentType: string;
  tokenUsage: number;
  metadata?: any;
  error?: boolean;
}

export interface ChatResponse {
  responses: AgentResponse[];
  totalTokens: number;
}
