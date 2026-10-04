import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AdminRoute } from '../components/AdminRoute';
import { AdminDashboardPage } from '../pages/AdminDashboardPage';
import * as AuthContextModule from '../context/AuthContext';
import * as AdminApiModule from '../services/admin';
import {
  AdminOverviewResponse,
  AdminStudentStats,
  AdminProjectStats,
  AdminProgressStats,
  AdminFeedbackStats,
  AdminAiMatchingStats,
  AdminSystemStats,
} from '../types/admin';

// Mock the admin API module
vi.mock('../services/admin');

describe('Phase 15: Admin Dashboard Frontend Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockOverview: AdminOverviewResponse = {
    total_students: 42,
    total_projects: 7,
    total_project_members: 18,
    total_invitations: 12,
    avg_project_progress: 68.5,
    total_feedback: 9,
    avg_feedback_rating: 4.67,
    ai_model_loaded: true,
    ai_model_version: 'PyTorch MLP v1.0',
    database_connected: true,
    demo_mode: false,
  };

  const mockStudents: AdminStudentStats = {
    total_students: 42,
    students_by_department: [
      { department: 'Computer Science', count: 28 },
      { department: 'Information Technology', count: 14 },
    ],
    students_by_year: {
      '1': 0,
      '2': 0,
      '3': 22,
      '4': 20,
      '5': 0,
    },
    profile_completeness: {
      with_skills: 35,
      with_interests: 30,
      with_previous_projects: 15,
      with_certifications: 10,
      completion_rate_percentage: 83.3,
    },
    total_skills: 18,
    skills_by_category: {
      Programming: 8,
      Frameworks: 6,
      Tools: 4,
    },
    most_common_skills: [
      { skill_id: 'sk-1', skill_name: 'Python', category: 'Programming', student_count: 25 },
      { skill_id: 'sk-2', skill_name: 'React', category: 'Frameworks', student_count: 18 },
    ],
    proficiency_distribution: {
      beginner: 10,
      intermediate: 20,
      advanced: 12,
      expert: 5,
    },
    project_skill_demand: [
      { skill_id: 'sk-1', skill_name: 'Python', category: 'Programming', project_count: 5 },
    ],
    demo_mode: false,
  };

  const mockProjects: AdminProjectStats = {
    total_projects: 7,
    projects_by_status: {
      open: 3,
      in_progress: 3,
      completed: 1,
      archived: 0,
    },
    recent_projects: [
      {
        id: 'proj-1',
        title: 'AI Healthcare Diagnostics',
        status: 'open',
        owner_id: 'stud-1',
        created_at: '2026-10-01T00:00:00Z',
      },
    ],
    total_project_members: 18,
    avg_team_size: 2.6,
    max_team_size: 5,
    invitation_stats: {
      total_invitations: 12,
      invitations_by_status: { accepted: 8, pending: 3, declined: 1 },
      acceptance_rate: 66.7,
    },
    demo_mode: false,
  };

  const mockProgress: AdminProgressStats = {
    avg_project_progress: 68.5,
    projects_by_progress_status: {
      not_started: 1,
      in_progress: 4,
      completed: 2,
      blocked: 0,
    },
    total_tasks: 15,
    tasks_by_status: {
      todo: 4,
      in_progress: 5,
      completed: 6,
    },
    completed_tasks: 6,
    pending_tasks: 9,
    blocked_tasks: 0,
    tasks_by_priority: {
      low: 3,
      medium: 7,
      high: 5,
    },
    demo_mode: false,
  };

  const mockFeedback: AdminFeedbackStats = {
    total_feedback: 9,
    avg_rating: 4.67,
    rating_distribution: {
      '5': 6,
      '4': 3,
    },
    recent_feedback: [
      {
        id: 'fb-1',
        project_id: 'proj-1',
        student_id: 'stud-2',
        rating: 5,
        feedback_text: 'Excellent teamwork and skill distribution.',
        created_at: '2026-10-03T10:00:00Z',
      },
    ],
    demo_mode: false,
  };

  const mockAiMatching: AdminAiMatchingStats = {
    model_loaded: true,
    model_type: 'MLP (PyTorch Matching Model)',
    model_version: 'v1.0',
    input_features_count: 10,
    hidden_layers: [64, 32],
    trainable_parameters: 2817,
    checkpoint_present: true,
    sentence_transformer_available: true,
    sentence_transformer_model: 'sentence-transformers/all-MiniLM-L6-v2',
    recommendation_readiness: {
      eligible_candidates_count: 35,
      projects_with_skills_count: 7,
    },
    feedback_satisfaction_avg: 4.67,
    feedback_total_count: 9,
    historical_tracking_available: false,
    historical_tracking_notice: 'Individual recommendation session logs are not persisted to database. Real-time inference telemetry and checkpoint verification shown above.',
    demo_mode: false,
  };

  const mockSystem: AdminSystemStats = {
    status: 'healthy',
    database_connected: true,
    database_mode: 'Supabase PostgreSQL',
    demo_mode: false,
    api_version: 'v1',
    ai_subsystem_healthy: true,
    checkpoint_verified: true,
  };

  const setupDefaultMocks = () => {
    vi.mocked(AdminApiModule.checkAdminStatus).mockResolvedValue({
      is_admin: true,
      user_id: 'admin-uid-1',
      email: 'admin@university.edu',
    });
    vi.mocked(AdminApiModule.getAdminOverview).mockResolvedValue(mockOverview);
    vi.mocked(AdminApiModule.getAdminStudentStats).mockResolvedValue(mockStudents);
    vi.mocked(AdminApiModule.getAdminProjectStats).mockResolvedValue(mockProjects);
    vi.mocked(AdminApiModule.getAdminProgressStats).mockResolvedValue(mockProgress);
    vi.mocked(AdminApiModule.getAdminFeedbackStats).mockResolvedValue(mockFeedback);
    vi.mocked(AdminApiModule.getAdminAiMatchingStats).mockResolvedValue(mockAiMatching);
    vi.mocked(AdminApiModule.getAdminSystemStats).mockResolvedValue(mockSystem);
  };

  describe('Route Protection & Authorization', () => {
    it('redirects unauthenticated users to /login', async () => {
      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isConfigured: true,
        register: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
            <Route path="/login" element={<div>Mock Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Mock Login Page')).toBeTruthy();
        expect(screen.queryByText('Admin Operations Console')).toBeNull();
      });
    });

    it('denies access to non-admin authenticated users with 403 Access Denied UI', async () => {
      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: {
          id: 'student-uid-1',
          email: 'student@university.edu',
          app_metadata: {},
          user_metadata: {},
          aud: 'authenticated',
          created_at: '2026-10-01T00:00:00Z',
        } as any,
        session: { access_token: 'fake-jwt' } as any,
        loading: false,
        isConfigured: true,
        register: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
      });

      vi.mocked(AdminApiModule.checkAdminStatus).mockResolvedValue({
        is_admin: false,
        user_id: 'student-uid-1',
        email: 'student@university.edu',
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
            <Route path="/dashboard" element={<div>Student Dashboard Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Access Denied')).toBeTruthy();
        expect(screen.getByText(/Administrative privileges are required/i)).toBeTruthy();
        expect(screen.getByText('Return to Student Dashboard')).toBeTruthy();
      });
    });

    it('grants access to authorized administrator', async () => {
      setupDefaultMocks();

      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: {
          id: 'admin-uid-1',
          email: 'admin@university.edu',
          app_metadata: { role: 'admin' },
          user_metadata: {},
          aud: 'authenticated',
          created_at: '2026-10-01T00:00:00Z',
        } as any,
        session: { access_token: 'admin-jwt' } as any,
        loading: false,
        isConfigured: true,
        register: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Admin Operations Console')).toBeTruthy();
        expect(screen.getByText('Overview')).toBeTruthy();
      });
    });
  });

  describe('Admin Dashboard Data Rendering', () => {
    beforeEach(() => {
      setupDefaultMocks();

      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: {
          id: 'admin-uid-1',
          email: 'admin@university.edu',
          app_metadata: { role: 'admin' },
          user_metadata: {},
          aud: 'authenticated',
          created_at: '2026-10-01T00:00:00Z',
        } as any,
        session: { access_token: 'admin-jwt' } as any,
        loading: false,
        isConfigured: true,
        register: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
      });
    });

    it('renders Overview tab metrics correctly', async () => {
      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Registered Students')).toBeTruthy();
        expect(screen.getByText('42')).toBeTruthy();
        expect(screen.getByText('Active Projects')).toBeTruthy();
        expect(screen.getByText('7')).toBeTruthy();
        expect(screen.getByText('Avg Progress')).toBeTruthy();
        expect(screen.getByText('68.5%')).toBeTruthy();
        expect(screen.getByText('Collaboration Rating')).toBeTruthy();
        expect(screen.getByText('4.67 / 5')).toBeTruthy();
      });
    });

    it('switches to Students & Skills tab and displays statistics', async () => {
      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeTruthy();
      });

      // Click on Students & Skills tab
      const studentTab = screen.getByRole('button', { name: /Students & Skills/i });
      fireEvent.click(studentTab);

      await waitFor(() => {
        expect(screen.getByText('Students by Department')).toBeTruthy();
        expect(screen.getByText('Computer Science')).toBeTruthy();
        expect(screen.getByText('Information Technology')).toBeTruthy();
        expect(screen.getByText('Most Common Student Skills')).toBeTruthy();
        expect(screen.getAllByText('Python').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('React')).toBeTruthy();
      });
    });

    it('switches to AI Matching & Feedback tab and displays MLP parameters and notice', async () => {
      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeTruthy();
      });

      // Click on AI Matching & Feedback tab
      const aiTab = screen.getByText('AI Matching & Feedback');
      fireEvent.click(aiTab);

      await waitFor(() => {
        expect(screen.getByText('Deep Learning Architecture (MLP)')).toBeTruthy();
        expect(screen.getByText('2,817')).toBeTruthy(); // Trainable parameters
        expect(screen.getByText('64 → 32')).toBeTruthy(); // Hidden layers
        expect(screen.getByText('Recommendation Pool Readiness')).toBeTruthy();
        expect(screen.getByText(/Historical Audit Note:/i)).toBeTruthy();
      });
    });

    it('displays Demo Mode banner when demo mode is active', async () => {
      vi.mocked(AdminApiModule.getAdminOverview).mockResolvedValue({
        ...mockOverview,
        demo_mode: true,
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboardPage />
                </AdminRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Demo Mode')).toBeTruthy();
        expect(screen.getByText(/Running with Synthetic Local Data/i)).toBeTruthy();
      });
    });
  });
});
