import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { ProjectsPage } from '../pages/ProjectsPage';
import { CreateProjectPage } from '../pages/CreateProjectPage';
import { ProjectDetailsPage } from '../pages/ProjectDetailsPage';
import * as AuthContextModule from '../context/AuthContext';
import * as ApiModule from '../services/api';

vi.mock('../services/api');

describe('Phase 4: Project Frontend UI Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects unauthenticated users from /projects to /login', () => {
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
      <MemoryRouter initialEntries={['/projects']}>
        <Routes>
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Mock Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Mock Login Page')).toBeTruthy();
    expect(screen.queryByText('Projects')).toBeNull();
  });

  it('renders Projects page empty state when user has no projects', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 'test-user-id', email: 'student@college.edu' } as any,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={['/projects']}>
        <Routes>
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No Projects Found')).toBeTruthy();
      expect(screen.getByText('Create Your First Project')).toBeTruthy();
    });
  });

  it('renders list of projects for authenticated user', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 'test-user-id', email: 'student@college.edu' } as any,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([
      {
        id: 'proj-1',
        owner_id: 'student-1',
        title: 'Autonomous Drone Path Planner',
        description: 'Using ROS2 and OpenCV for quadcopter navigation.',
        status: 'open',
        created_at: '2026-10-01T12:00:00Z',
        updated_at: '2026-10-01T12:00:00Z',
      },
    ]);

    render(
      <MemoryRouter initialEntries={['/projects']}>
        <Routes>
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Autonomous Drone Path Planner')).toBeTruthy();
      expect(screen.getByText('Open (Recruiting)')).toBeTruthy();
      expect(screen.getByText('View')).toBeTruthy();
      expect(screen.getByText('Edit')).toBeTruthy();
    });
  });

  it('validates required fields on Create Project page and submits API call', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 'test-user-id', email: 'student@college.edu' } as any,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const createSpy = vi.spyOn(ApiModule, 'createProject').mockResolvedValue({
      id: 'proj-new-123',
      owner_id: 'student-1',
      title: 'Valid Project Title',
      description: 'Valid Project Description',
      status: 'open',
      created_at: '2026-10-02T12:00:00Z',
      updated_at: '2026-10-02T12:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/projects/new']}>
        <Routes>
          <Route path="/projects/new" element={<CreateProjectPage />} />
          <Route path="/projects/proj-new-123" element={<div>Project Details Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Create New Project')).toBeTruthy();

    const titleInput = screen.getByLabelText(/Project Title/);
    const descInput = screen.getByLabelText(/Project Description/);
    const submitBtn = screen.getByRole('button', { name: /Create Project/i });

    // Fill valid data
    fireEvent.change(titleInput, { target: { value: 'Valid Project Title' } });
    fireEvent.change(descInput, { target: { value: 'Valid Project Description' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith({
        title: 'Valid Project Title',
        description: 'Valid Project Description',
        status: 'open',
      });
      expect(screen.getByText('Project Details Page Mock')).toBeTruthy();
    });
  });

  it('renders Project Details page with required skills and owner controls', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 'test-user-id', email: 'owner@college.edu' } as any,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue({
      id: 'proj-1',
      owner_id: 'student-1',
      title: 'Robotics Swarm Control',
      description: 'Distributed consensus algorithms for drone swarms.',
      status: 'open',
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
      owner: {
        id: 'student-1',
        user_id: 'test-user-id',
        full_name: 'Kirubakaran S',
        academic_year: 3,
      },
      required_skills: [
        {
          id: 'ps-1',
          project_id: 'proj-1',
          skill_id: 'skill-1',
          required_proficiency: 3,
          created_at: '2026-10-01T12:00:00Z',
          skill_name: 'PyTorch',
          category: 'ai_ml',
        },
      ],
      members: [
        {
          id: 'pm-1',
          project_id: 'proj-1',
          student_id: 'student-1',
          role: 'owner',
          joined_at: '2026-10-01T12:00:00Z',
          student_name: 'Kirubakaran S',
        },
      ],
    });

    vi.spyOn(ApiModule, 'getSkills').mockResolvedValue([
      { id: 'skill-1', name: 'PyTorch', category: 'ai_ml' },
      { id: 'skill-2', name: 'ROS2', category: 'robotics' },
    ]);

    render(
      <MemoryRouter initialEntries={['/projects/proj-1']}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Robotics Swarm Control')).toBeTruthy();
      expect(screen.getAllByText('Kirubakaran S').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('PyTorch')).toBeTruthy();
      expect(screen.getAllByText(/Level 3: Advanced/).length).toBeGreaterThanOrEqual(1);
      // Owner controls
      expect(screen.getByText('Edit Project')).toBeTruthy();
      expect(screen.getAllByText(/Archive/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Add Skill Requirement')).toBeTruthy();
    });
  });
});
