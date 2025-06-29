import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Building, MessageSquare, TrendingUp, FileText, DollarSign, Users, BarChart3, LogOut, ThumbsUp, ThumbsDown } from 'lucide-react';
import { auth } from '@/lib/firebase'; // Import Firebase auth
import { signInWithEmailAndPassword, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { api } from '@/lib/api'; // Import the new api client
import { useToast } from "@/hooks/use-toast";
import { FeedbackForm } from '@/components/FeedbackForm'; // Import the FeedbackForm component


// Define interfaces for API responses (based on Pydantic models)
// These should match the actual structures from your FastAPI backend
interface QueryResponse {
  task_id: string;
}

interface TaskStatusResponse {
  status: string;
  result?: any; // Define more specific type if result structure is known
  taskId?: string; // Added to carry taskId through mutations
}

interface FeedbackRequest {
  // Define feedback structure, e.g.
  rating: number;
  comment?: string;
}

// Example: Define a more specific type for dealer data if available from an endpoint
interface DealerData {
  dealerName: string; // Example field
  // ... other dealer specific data
  files?: Array<{ // Assuming files might be part of dealer data or a separate endpoint
    id: string;
    filename: string;
    uploadDate: string;
    size: number;
    type: string;
  }>;
  analysis?: { // Assuming analysis might be part of dealer data or a separate endpoint
    metrics: {
      totalRevenue: number;
      totalUnits: number;
      avgProfitMargin: number;
    };
    insights: {
      topPerformer: string;
      bestLeadSource: string;
      coachingRecommendation: string;
      leadOptimization: string;
    };
  };
}


export default function DealerPortal() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true); // To handle initial auth state loading

  const [message, setMessage] = useState('');
  // Update chat history to include optional taskId for assistant messages
  const [chatHistory, setChatHistory] = useState<Array<{role: string, content: string, taskId?: string}>>([]);
  const { toast } = useToast();
  const queryClientHook = useQueryClient();


  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user);
      setIsLoadingAuth(false);
      if (user) {
        // Optionally, fetch initial data or invalidate queries on login
        queryClientHook.invalidateQueries(['dealerData']); // Example
      }
    });
    return () => unsubscribe();
  }, [queryClientHook]);

  const handleLogin = async () => {
    if (!email || !password) {
      toast({ title: "Login Error", description: "Email and password are required.", variant: "destructive" });
      return;
    }
    try {
      await signInWithEmailAndPassword(auth, email, password);
      toast({ title: "Login Successful", description: `Welcome back!` });
    } catch (error: any) {
      console.error('Login failed:', error);
      toast({ title: "Login Failed", description: error.message, variant: "destructive" });
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      setChatHistory([]); // Clear chat history on logout
      toast({ title: "Logged Out", description: "You have been successfully logged out." });
    } catch (error: any) {
      console.error('Logout failed:', error);
      toast({ title: "Logout Failed", description: error.message, variant: "destructive" });
    }
  };

  // Example: Fetching some generic dealer data (adapt to your actual endpoint)
  // Replace 'getDealerData' with an actual method in api.ts if you have one
  // For now, this is a placeholder.
  const { data: dealerData, isLoading: isLoadingDealerData, error: dealerDataError } = useQuery<DealerData, Error>(
    ['dealerData', currentUser?.uid], // Query key includes user ID to refetch on user change
    async () => {
      // This is a placeholder. You'll need an API endpoint to get dealer-specific data.
      // For example: return await api.makeRequest<DealerData>('GET', `/dealer/${currentUser.uid}/profile`);
      // If no such specific endpoint, you might be querying tasks or other data instead.
      // This example simulates fetching some data that might be displayed on the portal.
      // If your app doesn't have a "dealer profile" endpoint, adjust or remove this.
      if (!currentUser) throw new Error("User not authenticated");
      // Simulate fetching data or replace with actual API call like:
      // return api.getSomeUserData();
      // For demonstration, returning mock data:
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
      return {
        dealerName: currentUser.email || "Valued Dealer",
        files: [],
        analysis: {
          metrics: { totalRevenue: 120000, totalUnits: 50, avgProfitMargin: 15 },
          insights: { topPerformer: "Model X", bestLeadSource: "Website", coachingRecommendation: "Focus on follow-ups", leadOptimization: "Target local ads" }
        }
      };
    },
    {
      enabled: !!currentUser && !isLoadingAuth, // Only run if user is logged in
    }
  );

  // Mutation for submitting a query
  const submitQueryMutation = useMutation<QueryResponse, Error, { query: string }>(
    ({ query }) => api.submitQuery(query),
    {
      onSuccess: (data) => {
        toast({ title: "Query Submitted", description: `Task ID: ${data.task_id}. Checking status...` });
        // Optionally, start polling for task status or navigate
        // For example, poll for status:
        // pollTaskStatus(data.task_id);
      },
      onError: (error) => {
        toast({ title: "Query Error", description: error.message, variant: "destructive" });
      }
    }
  );

  // Mutation for sending a chat message (which might internally use submitQuery)
  const sendMessageMutation = useMutation<TaskStatusResponse, Error, { content: string }>(
    async ({ content }) => {
      // This is a simplified chat interaction.
      // A real chat might involve creating a message in a conversation thread,
      // then the backend processes it and returns AI response.
      // Here, we'll simulate sending a message as a query and getting a direct result or task ID.
      const queryResponse = await api.submitQuery(content); // Use the actual query submission
      // Poll for the result or handle as per your backend's chat/query flow
      let taskStatus = await api.getTaskStatus(queryResponse.task_id);
      let retries = 0;
      const maxRetries = 10; // Poll for ~20 seconds
      let currentTaskStatus = await api.getTaskStatus(queryResponse.task_id);
      while (currentTaskStatus.status === 'PENDING' && retries < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
          currentTaskStatus = await api.getTaskStatus(queryResponse.task_id);
          retries++;
      }
      if (currentTaskStatus.status === 'FAILURE') throw new Error(currentTaskStatus.result?.error || "Task failed");
      if (currentTaskStatus.status !== 'SUCCESS') throw new Error("Task did not complete in time.");

      // Return both the status and the original task_id
      return { ...currentTaskStatus, taskId: queryResponse.task_id };
    },
    {
      onSuccess: (data) => { // `data` here is now { ...currentTaskStatus, taskId: queryResponse.task_id }
        // Assuming 'data' is TaskStatusResponse and it has 'result' and 'task_id' (from the initial query)
        // We need to ensure the original task_id that generated this response is available.
        // The `data` from onSuccess here is the final TaskStatusResponse.
        // The `variables` for this mutation was { content: string }.
        // We need the task_id that was part of the `api.submitQuery` response.
        // Let's adjust the mutation function to return the task_id along with the status.

        // Let's refine the mutation function to return { ...taskStatus, taskId: queryResponse.task_id }
        const agentMessage = {
          role: 'assistant',
          content: data.result?.response || data.result?.content || JSON.stringify(data.result) || 'Received response.',
          taskId: data.taskId // We'll ensure taskId is passed through
        };
        setChatHistory(prev => [...prev, agentMessage]);
      },
      onError: (error) => {
        const errorMessage = { role: 'assistant', content: `Error: ${error.message}` };
        setChatHistory(prev => [...prev, errorMessage]);
        toast({ title: "Chat Error", description: error.message, variant: "destructive" });
      }
    }
  );

  const handleSendMessage = async () => {
    if (!message.trim() || !currentUser) return;

    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setMessage('');
    sendMessageMutation.mutate({ content: message });
  };

  if (isLoadingAuth) {
    return ( // Basic loading state while checking auth
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Building className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">VENDORA</span>
            </div>
            <CardTitle>Dealer Portal Login</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </div>
            <Button onClick={handleLogin} className="w-full">
              Login
            </Button>
            {/* TODO: Add Sign Up / Forgot Password links if needed */}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main portal content shown when user is authenticated
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Building className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">VENDORA</h1>
              <p className="text-sm text-gray-600">{currentUser?.email || 'Dealer Portal'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              Connected
            </Badge>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" /> Logout
            </Button>
          </div>
        </div>

        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="chat">AI Analysis</TabsTrigger>
            <TabsTrigger value="upload">Data Upload</TabsTrigger>
            <TabsTrigger value="files">Files</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {isLoadingDealerData && <p>Loading dashboard data...</p>}
            {dealerDataError && <p className="text-red-500">Error loading dashboard: {dealerDataError.message}</p>}
            {dealerData?.analysis && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${dealerData.analysis.metrics.totalRevenue.toLocaleString()}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Units Sold</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {dealerData.analysis.metrics.totalUnits}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Profit Margin</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {dealerData.analysis.metrics.avgProfitMargin}%
                    </div>
                  </CardContent>
                </Card>

                <Card className="md:col-span-2 lg:col-span-3">
                  <CardHeader>
                    <CardTitle>Key Insights</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-green-700">Top Performer</h4>
                        <p className="text-sm text-gray-600">{dealerData.analysis.insights.topPerformer}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-blue-700">Best Lead Source</h4>
                        <p className="text-sm text-gray-600">{dealerData.analysis.insights.bestLeadSource}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-orange-700">Coaching Recommendation</h4>
                        <p className="text-sm text-gray-600">{dealerData.analysis.insights.coachingRecommendation}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-purple-700">Lead Optimization</h4>
                        <p className="text-sm text-gray-600">{dealerData.analysis.insights.leadOptimization}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <Card className="h-[600px] flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  AI Data Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-2 border rounded-md">
                  {chatHistory.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] p-3 rounded-lg shadow-sm ${
                        msg.role === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <p className="text-sm">{msg.content}</p>
                      </div>
                    </div>
                    {msg.role === 'assistant' && msg.taskId && (
                      <div className="flex justify-start pl-4">
                        <FeedbackForm
                          taskId={msg.taskId}
                          onSubmitSuccess={() => {
                            // Optionally, provide visual feedback or hide form upon successful submission
                            toast({ title: "Feedback Recorded", description: `For task ${msg.taskId}`});
                          }}
                        />
                      </div>
                    )}
                  </React.Fragment>
                  ))}
                  {sendMessageMutation.isLoading && (
                     <div className="flex justify-start">
                        <div className="max-w-[80%] p-3 rounded-lg bg-gray-100 text-gray-900 shadow-sm">
                            <p className="text-sm italic">AI is thinking...</p>
                        </div>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Ask about your dealership data..."
                    onKeyPress={(e) => e.key === 'Enter' && !sendMessageMutation.isLoading && handleSendMessage()}
                    disabled={sendMessageMutation.isLoading}
                  />
                  <Button onClick={handleSendMessage} disabled={sendMessageMutation.isLoading}>
                    {sendMessageMutation.isLoading ? "Sending..." : "Send"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload">
            <Card>
              <CardHeader>
                <CardTitle>Upload Data Files</CardTitle>
              </CardHeader>
              <CardContent>
                {/* TODO: Implement file upload UI and logic */}
                <p className="text-gray-600">File upload functionality will be implemented here.</p>
                <p className="text-gray-500 text-sm mt-2">This will connect to an endpoint like /api/v1/upload and show task status.</p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Files Tab */}
          <TabsContent value="files">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Uploaded Files
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingDealerData && <p>Loading files...</p>}
                {/* Assuming dealerData.files is the correct path after API integration */}
                {dealerData?.files && dealerData.files.length > 0 ? (
                  <div className="space-y-2">
                    {dealerData.files.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <h4 className="font-medium">{file.filename}</h4>
                          <p className="text-sm text-gray-600">
                            {new Date(file.uploadDate).toLocaleDateString()} • {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                        <Badge variant="outline">{file.type}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  !isLoadingDealerData && <p className="text-gray-600">No files uploaded yet or unable to load files.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}