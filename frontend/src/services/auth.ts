import { User, Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from './supabase';

export interface AuthResponse<T> {
  data: T | null;
  error: string | null;
}

export interface RegisterParams {
  name: string;
  email: string;
  password: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export const register = async ({
  name,
  email,
  password,
}: RegisterParams): Promise<AuthResponse<{ user: User | null; session: Session | null }>> => {
  if (!isSupabaseConfigured()) {
    return {
      data: null,
      error: 'Supabase credentials are not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env',
    };
  }

  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: name,
        },
      },
    });

    if (error) {
      return { data: null, error: error.message };
    }

    // If user registration succeeded and session exists, create basic student record in students table
    if (data.user) {
      try {
        await supabase.from('students').upsert({
          user_id: data.user.id,
          full_name: name,
          academic_year: 1,
        });
      } catch (dbErr) {
        console.warn('Initial student record will be created upon database sync:', dbErr);
      }
    }

    return { data, error: null };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown registration error';
    return { data: null, error: errorMsg };
  }
};

export const login = async ({
  email,
  password,
}: LoginParams): Promise<AuthResponse<{ user: User | null; session: Session | null }>> => {
  if (!isSupabaseConfigured()) {
    return {
      data: null,
      error: 'Supabase credentials are not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env',
    };
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return { data: null, error: error.message };
    }

    return { data, error: null };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown login error';
    return { data: null, error: errorMsg };
  }
};

export const logout = async (): Promise<{ error: string | null }> => {
  if (!isSupabaseConfigured()) {
    return { error: null };
  }

  try {
    const { error } = await supabase.auth.signOut();
    if (error) {
      return { error: error.message };
    }
    return { error: null };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown logout error';
    return { error: errorMsg };
  }
};

export const getCurrentSession = async (): Promise<Session | null> => {
  if (!isSupabaseConfigured()) {
    return null;
  }
  try {
    const { data } = await supabase.auth.getSession();
    return data.session;
  } catch {
    return null;
  }
};

export const getCurrentUser = async (): Promise<User | null> => {
  if (!isSupabaseConfigured()) {
    return null;
  }
  try {
    const { data } = await supabase.auth.getUser();
    return data.user;
  } catch {
    return null;
  }
};
