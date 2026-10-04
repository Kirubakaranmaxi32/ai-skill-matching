import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { ProfilePage } from '../pages/ProfilePage';
import * as AuthContextModule from '../context/AuthContext';
import * as ApiModule from '../services/api';

// Mock dependencies
vi.mock('../services/api');

describe('Profile Route and Protection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects unauthenticated users from /profile to /login', () => {
    // Mock unauthenticated user state
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
      <MemoryRouter initialEntries={['/profile']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Mock Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Expect to be redirected to login
    expect(screen.getByText('Mock Login Page')).toBeTruthy();
    expect(screen.queryByText('Student Profile')).toBeNull();
  });

  it('renders ProfilePage for authenticated user with all tabs and sections', async () => {
    // Mock authenticated user state
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 'test-user-id', email: 'student@college.edu' } as any,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    // Mock API responses
    vi.spyOn(ApiModule, 'getDepartments').mockResolvedValue([
      { id: 'dept-1', name: 'Computer Science & Engineering' },
    ]);
    vi.spyOn(ApiModule, 'getSkills').mockResolvedValue([
      { id: 'skill-1', name: 'Python', category: 'ai_ml' },
    ]);
    vi.spyOn(ApiModule, 'getInterests').mockResolvedValue([
      { id: 'int-1', name: 'Deep Learning' },
    ]);
    vi.spyOn(ApiModule, 'getStudentProfile').mockResolvedValue({
      id: 'student-1',
      user_id: 'test-user-id',
      full_name: 'Kirubakaran S',
      department_id: 'dept-1',
      academic_year: 3,
      hours_per_week: 15,
      bio: 'Enthusiastic engineer',
    });
    vi.spyOn(ApiModule, 'getStudentSkills').mockResolvedValue([
      {
        id: 'ss-1',
        student_id: 'student-1',
        skill_id: 'skill-1',
        proficiency: 3,
        skill_name: 'Python',
        category: 'ai_ml',
      },
    ]);
    vi.spyOn(ApiModule, 'getStudentInterests').mockResolvedValue([
      {
        id: 'si-1',
        student_id: 'student-1',
        interest_id: 'int-1',
        interest_name: 'Deep Learning',
      },
    ]);
    vi.spyOn(ApiModule, 'getStudentCertifications').mockResolvedValue([
      {
        id: 'cert-1',
        student_id: 'student-1',
        name: 'AWS Cloud Practitioner',
        issuing_organization: 'Amazon Web Services',
        issue_date: '2026-05-01',
      },
    ]);
    vi.spyOn(ApiModule, 'getStudentProjects').mockResolvedValue([
      {
        id: 'proj-1',
        student_id: 'student-1',
        title: 'Drone Path Planner',
        description: 'Autonomous ROS2 system',
        technologies: ['Python', 'OpenCV'],
      },
    ]);

    render(
      <MemoryRouter initialEntries={['/profile']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    // Await profile to load
    await waitFor(() => {
      expect(screen.getByText('Student Profile')).toBeTruthy();
      expect(screen.getByText('student@college.edu')).toBeTruthy();
    });

    // Check tabs rendered
    expect(screen.getByText('Basic Profile')).toBeTruthy();
    expect(screen.getByText(/Skills/)).toBeTruthy();
    expect(screen.getByText(/Interests/)).toBeTruthy();
    expect(screen.getByText(/Certifications/)).toBeTruthy();
    expect(screen.getByText(/Projects/)).toBeTruthy();

    // Check pre-populated field
    expect(screen.getByDisplayValue('Kirubakaran S')).toBeTruthy();
  });
});
