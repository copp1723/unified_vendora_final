import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth } from '@/lib/firebase';
import { api } from '@/lib/api';
import { onAuthStateChanged, User } from 'firebase/auth';
import { UserInfoResponse } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  userInfo: UserInfoResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  userInfo: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfoResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      try {
        setError(null);
        
        if (firebaseUser) {
          setUser(firebaseUser);
          
          // Only fetch user info if email is verified
          if (firebaseUser.emailVerified) {
            try {
              const info = await api.getCurrentUser();
              setUserInfo(info);
            } catch (err) {
              console.error('Failed to fetch user info:', err);
              setError('Failed to fetch user information');
              // User is authenticated but we couldn't get their info
              // This might happen if the backend is down
            }
          } else {
            setUserInfo(null);
          }
        } else {
          setUser(null);
          setUserInfo(null);
        }
      } catch (err) {
        console.error('Auth state change error:', err);
        setError('Authentication error occurred');
      } finally {
        setIsLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const value = {
    user,
    userInfo,
    isLoading,
    isAuthenticated: !!user && user.emailVerified,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
