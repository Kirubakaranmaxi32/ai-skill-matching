import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import * as AuthContextModule from '../context/AuthContext';
import * as ApiModule from '../services/api';
import { Project, ProjectDetail, ProjectRecommendationResponse } from '../types';

vi.mock('../services/api');

describe('Phase 5 Step 5: Recommendations Frontend UI Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = {
    id: 'test-user-id',
    email: 'student@college.edu',
  } as any;

  const mockProject: Project = {
    id: 'proj-123',
    owner_id: 'test-student-id',
    title: 'Autonomous Rover System',
    description: 'Robotics and Computer Vision Project with ROS2 and PyTorch',
    status: 'open',
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-01T00:00:00Z',
  };

  const mockProjectDetail: ProjectDetail = {
    ...mockProject,
    required_skills: [
      {
        id: 'ps-1',
        project_id: 'proj-123',
        skill_id: 'sk-1',
        skill_name: 'Python',
        required_proficiency: 3,
        created_at: '2026-03-01T00:00:00Z',
      },
    ],
    members: [],
  };

  const mockRecResponse: ProjectRecommendationResponse = {
    project_id: 'proj-123',
    project_title: 'Autonomous Rover System',
    total_eligible_candidates: 2,
    returned_recommendations_count: 2,
    min_score_threshold: 0.0,
    model_version: 'v1.0.0-cpu',
    recommendations: [
      {
        rank: 1,
        student_id: 'cand-1',
        student_name: 'Alice Johnson',
        academic_year: 4,
        compatibility_score: 0.884,
        matched_skill_count: 1,
        required_skill_count: 1,
        skill_coverage_ratio: 1.0,
        mean_proficiency_matched: 0.75,
        proficiency_deficit_ratio: 0.0,
        interest_domain_overlap: 1.0,
        prior_project_experience_norm: 0.5,
        certification_count_norm: 0.25,
        explanation: {
          matched_skills: [
            {
              skill_id: 'sk-1',
              skill_name: 'Python',
              student_proficiency: 4,
              required_proficiency: 3,
            },
          ],
          missing_skills: [],
          skill_coverage_ratio: 1.0,
          proficiency_alignment: 1.0,
          interest_overlap: 1.0,
          experience_signal: 0.5,
        },
      },
      {
        rank: 2,
        student_id: 'cand-2',
        student_name: 'Bob Smith',
        academic_year: 2,
        compatibility_score: 0.421,
        matched_skill_count: 0,
        required_skill_count: 1,
        skill_coverage_ratio: 0.0,
        mean_proficiency_matched: 0.0,
        proficiency_deficit_ratio: 0.75,
        interest_domain_overlap: 0.0,
        prior_project_experience_norm: 0.0,
        certification_count_norm: 0.0,
        explanation: {
          matched_skills: [],
          missing_skills: [
            {
              skill_id: 'sk-1',
              skill_name: 'Python',
              required_proficiency: 3,
            },
          ],
          skill_coverage_ratio: 0.0,
          proficiency_alignment: 0.25,
          interest_overlap: 0.0,
          experience_signal: 0.0,
        },
      },
    ],
  };

  // 1. Protected Route: redirects unauthenticated users to /login
  it('1. redirects unauthenticated users from /recommendations to /login', () => {
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
      <MemoryRouter initialEntries={['/recommendations']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Mock Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Mock Login Page')).toBeTruthy();
    expect(screen.queryByText('Project Recommendations')).toBeNull();
  });

  // 2. Loading State: displays loading indicator while fetching
  it('2. displays loading state while retrieving user projects and recommendations', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    // Induce pending promise
    vi.spyOn(ApiModule, 'getMyProjects').mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter initialEntries={['/recommendations']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Loading your projects...')).toBeTruthy();
  });

  // 3. Successful Recommendation Rendering: renders candidate student cards
  it('3. successfully renders candidate recommendation cards for an authenticated owner project', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockResolvedValue(mockRecResponse);

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Project Recommendations')).toBeTruthy();
      expect(screen.getAllByText('Autonomous Rover System').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Alice Johnson')).toBeTruthy();
      expect(screen.getByText('Bob Smith')).toBeTruthy();
    });
  });

  // 4. Compatibility Score Rendering: verifies exact continuous score display
  it('4. displays continuous compatibility score directly from backend recommendation result', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockResolvedValue(mockRecResponse);

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      // 0.884 * 100 = 88%
      expect(screen.getByText('88% Compatibility')).toBeTruthy();
      // 0.421 * 100 = 42%
      expect(screen.getByText('42% Compatibility')).toBeTruthy();
    });
  });

  // 5. Rank Rendering: preserves rank order (#1, #2)
  it('5. preserves deterministic rank ordering (#1, #2) exactly as returned by backend', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockResolvedValue(mockRecResponse);

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeTruthy();
      expect(screen.getByText('#2')).toBeTruthy();
    });
  });

  // 6. Empty Recommendation State: displays message when no candidates match
  it('6. displays empty state when project has zero eligible candidate recommendations', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const emptyRecResponse: ProjectRecommendationResponse = {
      project_id: 'proj-123',
      project_title: 'Autonomous Rover System',
      total_eligible_candidates: 0,
      returned_recommendations_count: 0,
      min_score_threshold: 0.0,
      model_version: 'v1.0.0-cpu',
      recommendations: [],
    };

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockResolvedValue(emptyRecResponse);

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No Candidate Recommendations Found')).toBeTruthy();
    });
  });

  // 7. API Error State: displays clear error message when recommendation API fails
  it('7. renders clear error notification when recommendation API returns error', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockRejectedValue(new Error('Project not found or archived'));
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockRejectedValue(new Error('Project not found or archived'));

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeTruthy();
      expect(screen.getByText('Unable to load recommendations')).toBeTruthy();
      expect(screen.getByText('Project not found or archived')).toBeTruthy();
    });
  });

  // 8. Authentication Error Handling: unauthorized / non-owner handled
  it('8. handles unauthorized non-owner 403 error cleanly', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockRejectedValue(
      new Error('You do not have permission to view recommendations for this project')
    );

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-123']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeTruthy();
      expect(screen.getByText('You do not have permission to view recommendations for this project')).toBeTruthy();
    });
  });

  // 9. Demo Mode: Renders demo banner and synthetic candidate badges when in demo mode
  it('9. renders demo mode banner and demo candidate indicators', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const mockDemoProj: Project = {
      id: 'demo-proj-1',
      owner_id: 'demo-student-a',
      title: 'AI Sign Language Translator (Demo)',
      description: 'Demo project using PyTorch and OpenCV',
      status: 'open',
      created_at: '2026-03-01T00:00:00Z',
      updated_at: '2026-03-01T00:00:00Z',
    };

    const mockDemoProjDetail: ProjectDetail = {
      ...mockDemoProj,
      required_skills: [
        {
          id: 'ps-demo-1',
          project_id: 'demo-proj-1',
          skill_id: 'sk-1',
          skill_name: 'PyTorch',
          required_proficiency: 3,
          created_at: '2026-03-01T00:00:00Z',
        },
      ],
      members: [],
    };

    const mockDemoRecs: ProjectRecommendationResponse = {
      project_id: 'demo-proj-1',
      project_title: 'AI Sign Language Translator (Demo)',
      total_eligible_candidates: 1,
      returned_recommendations_count: 1,
      min_score_threshold: 0.0,
      model_version: 'v1.0.0-cpu-demo',
      recommendations: [
        {
          rank: 1,
          student_id: 'demo-cand-b',
          student_name: 'Student B (Demo)',
          academic_year: 3,
          compatibility_score: 0.912,
          matched_skill_count: 1,
          required_skill_count: 1,
          skill_coverage_ratio: 1.0,
          mean_proficiency_matched: 0.75,
          proficiency_deficit_ratio: 0.0,
          interest_domain_overlap: 1.0,
          prior_project_experience_norm: 0.5,
          certification_count_norm: 0.33,
          explanation: {
            matched_skills: [
              {
                skill_id: 'sk-1',
                skill_name: 'PyTorch',
                student_proficiency: 3,
                required_proficiency: 3,
              },
            ],
            missing_skills: [],
            skill_coverage_ratio: 1.0,
            proficiency_alignment: 1.0,
            interest_overlap: 1.0,
            experience_signal: 0.5,
          },
        },
      ],
    };

    vi.spyOn(ApiModule, 'getDemoProjects').mockResolvedValue([mockDemoProj]);
    vi.spyOn(ApiModule, 'getDemoProject').mockResolvedValue(mockDemoProjDetail);
    vi.spyOn(ApiModule, 'getDemoRecommendations').mockResolvedValue(mockDemoRecs);

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=demo-proj-1&demo=true']}>
        <Routes>
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('DEMO MODE — Synthetic Local Data')).toBeTruthy();
      expect(screen.getByText('Demo Candidate')).toBeTruthy();
      expect(screen.getByText('Student B (Demo)')).toBeTruthy();
      expect(screen.getByText('91% Compatibility')).toBeTruthy();
    });
  });
});
