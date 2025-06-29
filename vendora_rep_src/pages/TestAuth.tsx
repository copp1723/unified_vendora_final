import { useState } from 'react';

export default function TestAuth() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const testMagicLink = async () => {
    setMessage('Sending request...');
    
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
      console.log('Response:', data);
      
      if (data.result) {
        setMessage(`Success: ${data.result.message} Token: ${data.result.token}`);
      } else {
        setMessage(`Error: ${JSON.stringify(data.error)}`);
      }
    } catch (error) {
      console.error('Request failed:', error);
      setMessage(`Failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Magic Link Test</h1>
      
      <div style={{ marginBottom: '10px' }}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter email"
          style={{ padding: '8px', width: '300px' }}
        />
      </div>
      
      <button onClick={testMagicLink} style={{ padding: '8px 16px' }}>
        Test Magic Link
      </button>
      
      {message && (
        <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0' }}>
          {message}
        </div>
      )}
    </div>
  );
}