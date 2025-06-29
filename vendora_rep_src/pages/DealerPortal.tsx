import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Building, MessageSquare, TrendingUp, FileText, DollarSign, Users, BarChart3 } from 'lucide-react';

interface DealerData {
  dealer: string;
  authenticated: boolean;
  data: {
    files: {
      fileCount: number;
      files: Array<{
        id: number;
        filename: string;
        uploadDate: string;
        size: number;
        type: string;
      }>;
    };
    analysis: {
      dealer: string;
      filename: string;
      receivedDate: string;
      qualityScore: number;
      metrics: {
        totalRevenue: number;
        totalUnits: number;
        avgProfitMargin: number;
        conversionRate: number;
        costPerLead: number;
      };
      insights: {
        topPerformer: string;
        bestLeadSource: string;
        coachingRecommendation: string;
        leadOptimization: string;
        inventoryStrategy: string;
        profitOptimization: string;
      };
    };
  };
}

export default function DealerPortal() {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [dealerEmail, setDealerEmail] = useState('');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{role: string, content: string}>>([]);

  // Check for token in URL on load
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    if (urlToken) {
      setToken(urlToken);
      verifyToken(urlToken);
    }
  }, []);

  const verifyToken = async (tokenToVerify: string) => {
    try {
      const response = await fetch('/api/jsonrpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'verify_magic_link',
          params: { token: tokenToVerify }
        })
      });

      const data = await response.json();
      if (data.result?.authenticated) {
        setIsAuthenticated(true);
        setDealerEmail(data.result.dealerEmail);
      }
    } catch (error) {
      console.error('Token verification failed:', error);
    }
  };

  const requestMagicLink = async () => {
    try {
      const response = await fetch('/api/jsonrpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'request_magic_link',
          params: { email }
        })
      });

      const data = await response.json();
      alert(data.result?.message || 'Magic link sent!');
    } catch (error) {
      alert('Failed to send magic link');
    }
  };

  const { data: dealerData } = useQuery<DealerData>({
    queryKey: ['dealer-data', dealerEmail],
    queryFn: async () => {
      const response = await fetch('/api/jsonrpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'get_dealer_data',
          params: { dealerEmail }
        })
      });
      const data = await response.json();
      return data.result;
    },
    enabled: isAuthenticated && !!dealerEmail
  });

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setMessage('');

    try {
      const response = await fetch('/api/jsonrpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'send_message',
          params: { message }
        })
      });

      const data = await response.json();
      const agentMessage = { role: 'assistant', content: data.result?.content || 'Error processing request' };
      setChatHistory(prev => [...prev, agentMessage]);
    } catch (error) {
      const errorMessage = { role: 'assistant', content: 'Failed to process your message. Please try again.' };
      setChatHistory(prev => [...prev, errorMessage]);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Building className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">VENDORA</span>
            </div>
            <CardTitle>Dealer Portal Access</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="email">Dealer Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your dealer email"
              />
            </div>
            <Button onClick={requestMagicLink} className="w-full">
              Request Access Link
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Building className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">VENDORA</h1>
              <p className="text-sm text-gray-600">{dealerEmail}</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            Connected
          </Badge>
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
            {dealerData?.data.analysis && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${dealerData.data.analysis.metrics.totalRevenue.toLocaleString()}
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
                      {dealerData.data.analysis.metrics.totalUnits}
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
                      {dealerData.data.analysis.metrics.avgProfitMargin}%
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
                        <p className="text-sm text-gray-600">{dealerData.data.analysis.insights.topPerformer}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-blue-700">Best Lead Source</h4>
                        <p className="text-sm text-gray-600">{dealerData.data.analysis.insights.bestLeadSource}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-orange-700">Coaching Recommendation</h4>
                        <p className="text-sm text-gray-600">{dealerData.data.analysis.insights.coachingRecommendation}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-purple-700">Lead Optimization</h4>
                        <p className="text-sm text-gray-600">{dealerData.data.analysis.insights.leadOptimization}</p>
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
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                  {chatHistory.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] p-3 rounded-lg ${
                        msg.role === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <p className="text-sm">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Ask about your dealership data..."
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  />
                  <Button onClick={sendMessage}>Send</Button>
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
                <p className="text-gray-600">File upload functionality will be available soon.</p>
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
                {dealerData?.data.files.files.length ? (
                  <div className="space-y-2">
                    {dealerData.data.files.files.map((file) => (
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
                  <p className="text-gray-600">No files uploaded yet.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}