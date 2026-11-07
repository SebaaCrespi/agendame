// Auth Context for managing authentication state

import { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from 'react';
import type { User } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; nombre: string; rol: 'CLIENTE' | 'PROVEEDOR' }) => Promise<void>;
  logout: () => void;
  /** true si el usuario cerró sesión a propósito (no por sesión vencida). */
  cerroSesion: boolean;
  updateUser: (data: { nombre?: string; password?: string }) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cerroSesion, setCerroSesion] = useState(false);

  const refreshUser = useCallback(async () => {
    if (!api.isAuthenticated()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      setUser(null);
      api.logout();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    setCerroSesion(false);
    setUser(data.user);
  };

  const register = async (data: { email: string; password: string; nombre: string; rol: 'CLIENTE' | 'PROVEEDOR' }) => {
    const result = await api.register(data);
    setCerroSesion(false);
    setUser(result.user);
  };

  const logout = () => {
    api.logout();
    setCerroSesion(true);
    setUser(null);
  };

  const updateUser = async (data: { nombre?: string; password?: string }) => {
    const updatedUser = await api.updateMe(data);
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, cerroSesion, updateUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}