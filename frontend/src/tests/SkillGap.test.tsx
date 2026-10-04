import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { SkillGapView } from '../components/SkillGapView';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { ProtectedRoute } from '../components/ProtectedRoute';
import * as AuthContextModule from '../context/AuthContext';
import * as ApiModule from '../services/api';
import {
  SkillGapResponse,
  Project,
  ProjectDetail,
  ProjectRecommendationResponse,
} from '../types';

vi.mock('../services/api');

describe('Phase 6: Skill-Gap Analysis Frontend Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = {
    id: 'test-user-id',
    email: 'student@college.edu',
  } as any;

  const mockSkillGapData: SkillGapResponse = {
    project_id: 'proj-123',
    project_title: 'Autonomous Rover System',
    student_id: 'stud-456',
    student_name: 'Alice Johnson',
    summary: {
      total_required_skills: 3,
      matched_count: 1,
      partial_count: 1,
      missing_count: 1,
      skill_coverage_ratio: 0.3333,
      proficiency_gap_count: 1,
      overall_gap_summary: 'Candidate fully matches 1 of 3 required skills (33% coverage), with 1 partial proficiency gap(s) and 1 missing skill(s).',
    },
    skills: [
      {
        skill_id: 'sk-1',
        skill_name: 'Python',
        category: 'ai_ml',
        required_proficiency: 3,
        student_proficiency: 4,
        status: 'matched',
        proficiency_gap: null,
      },
      {
        skill_id: 'sk-2',
        skill_name: 'PyTorch',
        category: 'ai_ml',
        required_proficiency: 3,
        student_proficiency: 2,
        status: 'partial',
        proficiency_gap: 1,
      },
      {
        skill_id: 'sk-3',
        skill_name: 'ROS2',
        category: 'robotics',
        required_proficiency: 2,
        student_proficiency: null,
        status: 'missing',
        proficiency_gap: null,
      },
    ],
  };

  // 1. Loading state
  it('1. renders loading state with spinner and text', () => {
    render(<SkillGapView data={null} loading={true} />);
    expect(
      screen.getByText('Calculating skill alignment & proficiency gaps...')
    ).toBeTruthy();
  });

  // 2. API error handling
  it('2. renders API error alert cleanly', () => {
    render(
      <SkillGapView
        data={null}
        loading={false}
        error="Unable to fetch skill gap from backend"
      />
    );
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText('Unable to load skill gap analysis')).toBeTruthy();
    expect(
      screen.getByText('Unable to fetch skill gap from backend')
    ).toBeTruthy();
  });

  // 3. Empty state (no required skills)
  it('3. renders empty state when project has no required skills', () => {
    const emptyData: SkillGapResponse = {
      project_id: 'proj-0',
      student_id: 'stud-0',
      summary: {
        total_required_skills: 0,
        matched_count: 0,
        partial_count: 0,
        missing_count: 0,
        skill_coverage_ratio: 1.0,
        proficiency_gap_count: 0,
        overall_gap_summary: 'Project specifies no required skills. Full coverage.',
      },
      skills: [],
    };

    render(<SkillGapView data={emptyData} />);
    expect(
      screen.getByText('This project specifies no required skills.')
    ).toBeTruthy();
    expect(screen.getByText('100%')).toBeTruthy();
  });

  // 4. Successful skill-gap display: matched, partial, and missing skills
  it('4. displays coverage ratio, matched, partial proficiency gap, and missing skills', () => {
    render(<SkillGapView data={mockSkillGapData} />);

    // Coverage percentage
    expect(screen.getByText('33%')).toBeTruthy();

    // Summary KPIs and badges
    expect(screen.getAllByText('Matched').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Partial Gap')).toBeTruthy();
    expect(screen.getAllByText('Missing').length).toBeGreaterThanOrEqual(1);

    // Matched skill
    expect(screen.getByText('Python')).toBeTruthy();

    // Partial skill with gap
    expect(screen.getByText('PyTorch')).toBeTruthy();
    expect(screen.getByText('Proficiency Gap (1)')).toBeTruthy();
    expect(screen.getByText('Gap: 1 level')).toBeTruthy();

    // Missing skill
    expect(screen.getByText('ROS2')).toBeTruthy();
    expect(screen.getByText('Your level: Not available')).toBeTruthy();
  });

  // 5. Demo-mode indicator
  it('5. renders demo mode indicator badge when isDemo is true', () => {
    render(<SkillGapView data={mockSkillGapData} isDemo={true} />);
    expect(screen.getByText('Demo Data')).toBeTruthy();
  });

  // 6. RecommendationsPage integration: drilldown into candidate skill gap
  it('6. toggles candidate skill gap drilldown on RecommendationsPage', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      session: { access_token: 'fake-jwt' } as any,
      loading: false,
      isConfigured: true,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    });

    const mockProject: Project = {
      id: 'proj-123',
      owner_id: 'test-user-id',
      title: 'Autonomous Rover System',
      description: 'Robotics project',
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

    const mockRecs: ProjectRecommendationResponse = {
      project_id: 'proj-123',
      project_title: 'Autonomous Rover System',
      total_eligible_candidates: 1,
      returned_recommendations_count: 1,
      min_score_threshold: 0.0,
      model_version: 'v1.0.0-cpu',
      recommendations: [
        {
          rank: 1,
          student_id: 'stud-456',
          student_name: 'Alice Johnson',
          academic_year: 4,
          compatibility_score: 0.88,
          matched_skill_count: 1,
          required_skill_count: 1,
          skill_coverage_ratio: 1.0,
          mean_proficiency_matched: 1.0,
          proficiency_deficit_ratio: 0.0,
          interest_domain_overlap: 1.0,
          prior_project_experience_norm: 0.5,
          certification_count_norm: 0.3,
          explanation: {
            matched_skills: [],
            missing_skills: [],
            skill_coverage_ratio: 1.0,
            proficiency_alignment: 1.0,
            interest_overlap: 1.0,
            experience_signal: 0.5,
          },
        },
      ],
    };

    vi.spyOn(ApiModule, 'getMyProjects').mockResolvedValue([mockProject]);
    vi.spyOn(ApiModule, 'getProjectById').mockResolvedValue(mockProjectDetail);
    vi.spyOn(ApiModule, 'getProjectRecommendations').mockResolvedValue(mockRecs);
    vi.spyOn(ApiModule, 'getProjectSkillGap').mockResolvedValue(mockSkillGapData);

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

    // Wait for candidate card to render
    await waitFor(() => {
      expect(screen.getByText('Alice Johnson')).toBeTruthy();
      expect(screen.getByText('View Skill Gap Analysis')).toBeTruthy();
    });

    // Click "View Skill Gap Analysis"
    fireEvent.click(screen.getByText('View Skill Gap Analysis'));

    // Wait for skill gap breakdown to render
    await waitFor(() => {
      expect(
        screen.getByText('Alice Johnson — Skill Gap Analysis')
      ).toBeTruthy();
      expect(screen.getAllByText('Python').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('PyTorch').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('ROS2')).toBeTruthy();
      expect(screen.getByText('Hide Skill Gap Analysis')).toBeTruthy();
    });
  });
});
