import React, { createContext, useContext, useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const AuthContext = createContext({});

const SUPABASE_URL = 'https://ewtaaomkzwcbcfummwdb.supabase.co';
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_NSZpDVKbjoOHhxxhpdVANA_ceqXcWI4';
const ADMIN_EMAIL = 'umerazizgujjar009@gmail.com';

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const normalizeRole = (rawRole) => {
    if (!rawRole) return '';
    return String(rawRole).toLowerCase().trim();
  };

  const getIsAdmin = (authUser) => {
    if (!authUser) return false;
    const email = String(authUser.email || '').toLowerCase().trim();
    const metaRole = normalizeRole(authUser.user_metadata?.role || authUser.app_metadata?.role);
    return email === ADMIN_EMAIL || metaRole === 'admin';
  };

  // Initialize session on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) throw sessionError;
        
        if (session) {
          setSession(session);
          setUser(session.user);
        }
        
        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            setSession(session);
            setUser(session?.user || null);
          }
        );

        return () => {
          subscription?.unsubscribe();
        };
      } catch (err) {
        setError(err.message);
        console.error('Auth initialization error:', err);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) throw signInError;

      // Best-effort metadata seed for the configured admin identity.
      if (String(email || '').toLowerCase().trim() === ADMIN_EMAIL && normalizeRole(data.user?.user_metadata?.role) !== 'admin') {
        try {
          await supabase.auth.updateUser({
            data: {
              ...(data.user?.user_metadata || {}),
              role: 'admin',
            },
          });
        } catch (metaError) {
          console.warn('Could not set admin metadata automatically:', metaError?.message || metaError);
        }
      }

      setSession(data.session);
      setUser(data.user);
      return { success: true, data };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      setError(null);
      setLoading(true);

      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            role: String(email || '').toLowerCase().trim() === ADMIN_EMAIL ? 'admin' : 'user',
          },
        },
      });

      if (signUpError) throw signUpError;

      setSession(data.session);
      setUser(data.user);
      return { success: true, data };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      const { error: signOutError } = await supabase.auth.signOut();
      
      if (signOutError) throw signOutError;

      setSession(null);
      setUser(null);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const loginWithGoogle = async () => {
    try {
      setError(null);
      const { data, error: googleError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      });

      if (googleError) throw googleError;

      return { success: true, data };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const value = {
    user,
    session,
    loading,
    error,
    login,
    signup,
    logout,
    loginWithGoogle,
    isAuthenticated: !!session,
    isAdmin: getIsAdmin(user),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
