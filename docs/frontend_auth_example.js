/**
 * Frontend Authentication Example for VENDORA
 * This shows how to authenticate with Firebase and call the protected API
 */

import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  sendEmailVerification,
  onAuthStateChanged 
} from 'firebase/auth';

// Firebase configuration
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "vendora-analytics.firebaseapp.com",
  projectId: "vendora-analytics",
  storageBucket: "vendora-analytics.appspot.com",
  messagingSenderId: "your-sender-id",
  appId: "your-app-id"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * VendoraAPI class for authenticated API calls
 */
class VendoraAPI {
  constructor() {
    this.auth = auth;
    this.baseURL = API_BASE_URL;
    this.token = null;
  }

  /**
   * Get current ID token, refreshing if necessary
   */
  async getToken() {
    const user = this.auth.currentUser;
    if (!user) {
      throw new Error('No authenticated user');
    }
    
    // Get token, forcing refresh if needed
    this.token = await user.getIdToken();
    return this.token;
  }

  /**
   * Make authenticated API request
   */
  async request(endpoint, options = {}) {
    const token = await this.getToken();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || error.detail || 'API request failed');
    }

    return response.json();
  }

  /**
   * Process an analytical query
   */
  async processQuery(query, dealershipId, context = {}) {
    return this.request('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        dealership_id: dealershipId,
        context
      })
    });
  }

  /**
   * Get task status
   */
  async getTaskStatus(taskId) {
    return this.request(`/api/v1/task/${taskId}/status`);
  }

  /**
   * Get current user info
   */
  async getCurrentUser() {
    return this.request('/api/v1/auth/me');
  }

  /**
   * Get system metrics (admin/analyst only)
   */
  async getSystemMetrics() {
    return this.request('/api/v1/system/metrics');
  }
}

// Create API instance
const vendoraAPI = new VendoraAPI();

/**
 * Authentication functions
 */

// Sign up new user
export async function signUp(email, password, displayName) {
  try {
    // Create user account
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Send verification email
    await sendEmailVerification(user);
    
    // Update profile with display name
    if (displayName) {
      await user.updateProfile({ displayName });
    }
    
    return {
      success: true,
      user: {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        emailVerified: user.emailVerified
      },
      message: 'Account created! Please check your email to verify your account.'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Sign in existing user
export async function signIn(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Check if email is verified
    if (!user.emailVerified) {
      return {
        success: false,
        error: 'Please verify your email before signing in.',
        needsVerification: true
      };
    }
    
    // Get user info from backend
    const userInfo = await vendoraAPI.getCurrentUser();
    
    return {
      success: true,
      user: userInfo
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Sign out
export async function signOut() {
  try {
    await auth.signOut();
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Listen for auth state changes
export function onAuthChange(callback) {
  return onAuthStateChanged(auth, async (user) => {
    if (user) {
      try {
        // Get full user info from backend
        const userInfo = await vendoraAPI.getCurrentUser();
        callback({ authenticated: true, user: userInfo });
      } catch (error) {
        // User is authenticated but backend call failed
        callback({ 
          authenticated: true, 
          user: {
            uid: user.uid,
            email: user.email,
            emailVerified: user.emailVerified,
            displayName: user.displayName
          },
          error: error.message 
        });
      }
    } else {
      callback({ authenticated: false, user: null });
    }
  });
}

/**
 * Example usage in React component
 */
export function ExampleComponent() {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [queryResult, setQueryResult] = React.useState(null);

  React.useEffect(() => {
    // Listen for auth changes
    const unsubscribe = onAuthChange(({ authenticated, user }) => {
      setUser(authenticated ? user : null);
    });

    return unsubscribe;
  }, []);

  const handleQuery = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const result = await vendoraAPI.processQuery(
        "What were my top selling vehicles last month?",
        user.dealership_id || "dealer_123"
      );
      setQueryResult(result);
    } catch (error) {
      console.error('Query failed:', error);
      alert(`Query failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div>Please sign in to continue</div>;
  }

  return (
    <div>
      <h2>Welcome, {user.display_name || user.email}</h2>
      <p>Dealership: {user.dealership_id || 'Not assigned'}</p>
      
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Processing...' : 'Run Test Query'}
      </button>
      
      {queryResult && (
        <pre>{JSON.stringify(queryResult, null, 2)}</pre>
      )}
    </div>
  );
}

// Export API instance
export { vendoraAPI };