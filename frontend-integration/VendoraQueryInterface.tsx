import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Send, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// WebSocket for real-time updates
let ws = null;

interface QueryResponse {
  summary?: string;
  detailed_insight?: any;
  data_visualization?: {
    type: string;
    config: any;
  };
  confidence_level?: string;
  metadata?: {
    task_id: string;
    complexity: string;
    processing_time_ms: number;
    revision_count: number;
  };
  error?: string;
}

interface TaskStatus {
  status: string;
  current_level: number;
  complexity: string;
  duration_ms: number;
  has_validated_insight: boolean;
}

export function VendoraQueryInterface({ dealershipId }: { dealershipId: string }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      ws = new WebSocket('ws://localhost:8765');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'operation' && taskStatus?.task_id) {
          // Update task status based on real-time updates
          console.log('Real-time update:', data);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setResponse(null);
    setTaskStatus(null);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          dealership_id: dealershipId,
          context: {
            user_role: 'manager',
            interface: 'web'
          }
        }),
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || 'Query processing failed');
      }
      
      setResponse(data);
      
      // Poll for task status if we have a task ID
      if (data.metadata?.task_id) {
        pollTaskStatus(data.metadata.task_id);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/task/${taskId}/status`);
      if (res.ok) {
        const status = await res.json();
        setTaskStatus(status);
      }
    } catch (err) {
      console.error('Failed to fetch task status:', err);
    }
  };

  const renderVisualization = () => {
    if (!response?.data_visualization || !response.detailed_insight) return null;
    
    const { type, config } = response.data_visualization;
    const data = response.detailed_insight.data || [];
    
    switch (type) {
      case 'line_chart':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="y" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar_chart':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="y" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      default:
        return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'revision_needed':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin" />;
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Ask VENDORA</CardTitle>
          <CardDescription>
            Get AI-powered insights about your dealership performance
            {wsConnected && (
              <Badge variant="outline" className="ml-2">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
                Live
              </Badge>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Textarea
              placeholder="What would you like to know? For example: 'What were my top selling vehicles last month?' or 'Forecast next quarter's revenue'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="min-h-[100px]"
              disabled={loading}
            />
            <Button 
              onClick={handleSubmit} 
              disabled={loading || !query.trim()}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Submit Query
                </>
              )}
            </Button>
          </div>

          {/* Task Status */}
          {taskStatus && (
            <Alert>
              <AlertDescription className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(taskStatus.status)}
                  <span>Status: {taskStatus.status}</span>
                  <Badge variant="outline">{taskStatus.complexity}</Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  Level {taskStatus.current_level} • {taskStatus.duration_ms}ms
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Response Display */}
          {response && !error && (
            <div className="space-y-4">
              {/* Summary */}
              {response.summary && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Summary</CardTitle>
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <span>Confidence: {response.confidence_level}</span>
                      {response.metadata && (
                        <>
                          <span>•</span>
                          <span>{response.metadata.processing_time_ms}ms</span>
                          {response.metadata.revision_count > 0 && (
                            <>
                              <span>•</span>
                              <span>{response.metadata.revision_count} revisions</span>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{response.summary}</p>
                  </CardContent>
                </Card>
              )}

              {/* Visualization */}
              {response.data_visualization && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      {response.data_visualization.config?.title || 'Data Visualization'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {renderVisualization()}
                  </CardContent>
                </Card>
              )}

              {/* Detailed Insights */}
              {response.detailed_insight && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Detailed Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Key Metrics */}
                      {response.detailed_insight.key_metrics && (
                        <div>
                          <h4 className="font-medium mb-2">Key Metrics</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {Object.entries(response.detailed_insight.key_metrics).map(([key, value]) => (
                              <div key={key} className="bg-muted p-2 rounded">
                                <div className="text-xs text-muted-foreground">{key}</div>
                                <div className="font-medium">{String(value)}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Insights */}
                      {response.detailed_insight.insights && response.detailed_insight.insights.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Key Insights</h4>
                          <ul className="list-disc list-inside space-y-1">
                            {response.detailed_insight.insights.map((insight: string, idx: number) => (
                              <li key={idx} className="text-sm">{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Recommendations */}
                      {response.detailed_insight.recommendations && response.detailed_insight.recommendations.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Recommendations</h4>
                          <div className="space-y-2">
                            {response.detailed_insight.recommendations.map((rec: any, idx: number) => (
                              <div key={idx} className="flex items-start space-x-2">
                                <Badge variant={
                                  rec.priority === 'high' ? 'destructive' : 
                                  rec.priority === 'medium' ? 'default' : 'secondary'
                                }>
                                  {rec.priority}
                                </Badge>
                                <p className="text-sm flex-1">
                                  {typeof rec === 'string' ? rec : rec.action}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Example usage in a page
export function DealerDashboard() {
  const dealershipId = 'dealer_123'; // This would come from auth/context
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Dealer Dashboard</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <VendoraQueryInterface dealershipId={dealershipId} />
        </div>
        <div>
          {/* Other dashboard widgets */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Quick stats content */}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
