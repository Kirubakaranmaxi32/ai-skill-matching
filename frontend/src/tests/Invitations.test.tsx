import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { InvitationsPage } from '../pages/InvitationsPage';
import { ProtectedRoute } from '../components/ProtectedRoute';
import * as AuthContextModule from '../context/AuthContext';
import * as ApiModule from '../services/api';
import { InvitationResponse } from '../types';

vi.mock('../services/api');

describe('Phase 13: Voluntary Team Formation & Invitations Frontend Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = {
    id: 'user-cand-123',
    email: 'candidate@college.edu',
  } as any;

  const mockReceivedInvitations: InvitationResponse[] = [
    {
      id: 'inv-1',
      project_id: 'proj-1',
      inviter_id: 'stud-owner-1',
      invited_student_id: 'stud-cand-1',
      status: 'pending',
      created_at: '2026-10-04T10:00:00Z',
      project: {
        id: 'proj-1',
        title: 'Autonomous Drone Navigation',
        description: 'Building vision models for real-time quadcopter navigation.',
        status: 'open',
        owner_id: 'stud-owner-1',
      },
      inviter: {
        id: 'stud-owner-1',
        full_name: 'Sarah Connor',
        academic_year: 4,
        department: 'Robotics',
      },
      invited_student: {
        id: 'stud-cand-1',
        full_name: 'John Doe',
        academic_year: 3,
        department: 'Computer Science',
      },
    },
    {
      id: 'inv-2',
      project_id: 'proj-2',
      inviter_id: 'stud-owner-2',
      invited_student_id: 'stud-cand-1',
      status: 'accepted',
      created_at: '2026-10-03T09:00:00Z',
      project: {
        id: 'proj-2',
        title: 'Healthcare AI Analytics',
        description: 'Predictive patient diagnostics.',
        status: 'open',
        owner_id: 'stud-owner-2',
      },
      inviter: {
        id: 'stud-owner-2',
        full_name: 'Dr. Gregory House',
      },
      invited_student: {
        id: 'stud-cand-1',
        full_name: 'John Doe',
      },
    },
  ];

  const mockSentInvitations: InvitationResponse[] = [
    {
      id: 'inv-sent-1',
      project_id: 'proj-my-1',
      inviter_id: 'stud-cand-1',
      invited_student_id: 'stud-target-1',
      status: 'pending',
      created_at: '2026-10-04T11:00:00Z',
      project: {
        id: 'proj-my-1',
        title: 'My Custom Compiler',
        description: 'LLVM based compiler project.',
        status: 'open',
        owner_id: 'stud-cand-1',
      },
      inviter: {
        id: 'stud-cand-1',
        full_name: 'John Doe',
      },
      invited_student: {
        id: 'stud-target-1',
        full_name: 'Ada Lovelace',
        academic_year: 4,
      },
    },
  ];

  it('1. redirects unauthenticated users from /invitations to /login', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <Routes>
          <Route
            path="/invitations"
            element={
              <ProtectedRoute>
                <InvitationsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Screen Mock</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Login Screen Mock')).toBeTruthy();
  });

  it('2. renders empty state when user has no invitations', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    vi.mocked(ApiModule.getMyInvitations).mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <InvitationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No Received Invitations')).toBeTruthy();
    });
  });

  it('3. renders received invitations with project title, inviter info, and status', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    vi.mocked(ApiModule.getMyInvitations).mockResolvedValue(mockReceivedInvitations);

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <InvitationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Autonomous Drone Navigation')).toBeTruthy();
      expect(screen.getByText(/Invited by Sarah Connor/i)).toBeTruthy();
      expect(screen.getByText('Pending Response')).toBeTruthy();
      expect(screen.getByText('Healthcare AI Analytics')).toBeTruthy();
      expect(screen.getByText('Accepted')).toBeTruthy();
    });
  });

  it('4. accepts invitation voluntarily and updates UI', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    vi.mocked(ApiModule.getMyInvitations).mockResolvedValue(mockReceivedInvitations);
    vi.mocked(ApiModule.acceptInvitation).mockResolvedValue({
      ...mockReceivedInvitations[0],
      status: 'accepted',
    });

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <InvitationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Autonomous Drone Navigation')).toBeTruthy();
    });

    const acceptBtn = screen.getByRole('button', { name: /Accept & Join Team/i });
    fireEvent.click(acceptBtn);

    await waitFor(() => {
      expect(ApiModule.acceptInvitation).toHaveBeenCalledWith('inv-1');
      expect(screen.getByText(/You voluntarily joined "Autonomous Drone Navigation"!/i)).toBeTruthy();
    });
  });

  it('5. declines invitation voluntarily and shows confirmation', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    vi.mocked(ApiModule.getMyInvitations).mockResolvedValue(mockReceivedInvitations);
    vi.mocked(ApiModule.rejectInvitation).mockResolvedValue({
      ...mockReceivedInvitations[0],
      status: 'rejected',
    });

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <InvitationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Autonomous Drone Navigation')).toBeTruthy();
    });

    const declineBtn = screen.getByRole('button', { name: /Decline/i });
    fireEvent.click(declineBtn);

    await waitFor(() => {
      expect(ApiModule.rejectInvitation).toHaveBeenCalledWith('inv-1');
      expect(screen.getByText(/Declined invitation for "Autonomous Drone Navigation"/i)).toBeTruthy();
    });
  });

  it('6. switches to Sent Invitations tab and allows cancelling a pending invitation', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    vi.mocked(ApiModule.getMyInvitations).mockImplementation(async (_, role) => {
      if (role === 'sent') return mockSentInvitations;
      return mockReceivedInvitations;
    });
    vi.mocked(ApiModule.cancelInvitation).mockResolvedValue({
      ...mockSentInvitations[0],
      status: 'cancelled',
    });

    render(
      <MemoryRouter initialEntries={['/invitations']}>
        <InvitationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Received Invitations')).toBeTruthy();
    });

    // Click Sent Invitations tab
    const sentTab = screen.getByRole('button', { name: /Sent Invitations/i });
    fireEvent.click(sentTab);

    await waitFor(() => {
      expect(screen.getByText('My Custom Compiler')).toBeTruthy();
      expect(screen.getByText(/Sent to Ada Lovelace/i)).toBeTruthy();
      expect(screen.getByRole('button', { name: /Cancel Invitation/i })).toBeTruthy();
    });

    // Click cancel button
    const cancelBtn = screen.getByRole('button', { name: /Cancel Invitation/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(ApiModule.cancelInvitation).toHaveBeenCalledWith('inv-sent-1');
      expect(screen.getByText(/Pending invitation was cancelled successfully/i)).toBeTruthy();
    });
  });

  it('7. allows project owner to invite recommended candidate on RecommendationsPage', async () => {
    const { RecommendationsPage } = await import('../pages/RecommendationsPage');

    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isConfigured: true,
      session: null,
    });

    const mockProject = {
      id: 'proj-rec-1',
      title: 'Robotics Rover',
      description: 'Autonomous exploration rover',
      status: 'open',
      owner_id: 'user-cand-123',
      created_at: '2026-03-01T00:00:00Z',
      updated_at: '2026-03-01T00:00:00Z',
      required_skills: [],
      members: [],
    };

    const mockRecs = {
      project_id: 'proj-rec-1',
      project_title: 'Robotics Rover',
      total_eligible_candidates: 1,
      returned_recommendations_count: 1,
      min_score_threshold: 0.0,
      model_version: 'v1.0.0-cpu',
      recommendations: [
        {
          rank: 1,
          student_id: 'cand-target-99',
          student_name: 'Grace Hopper',
          academic_year: 4,
          compatibility_score: 0.95,
          matched_skill_count: 3,
          required_skill_count: 3,
          skill_coverage_ratio: 1.0,
          mean_proficiency_matched: 0.8,
          proficiency_deficit_ratio: 0.0,
          interest_domain_overlap: 1.0,
          prior_project_experience_norm: 0.8,
          certification_count_norm: 0.5,
          explanation: {
            matched_skills: [],
            missing_skills: [],
            skill_coverage_ratio: 1.0,
            proficiency_alignment: 1.0,
            interest_overlap: 1.0,
            experience_signal: 0.8,
          },
          invitation_status: null,
        },
      ],
    };

    vi.mocked(ApiModule.getMyProjects).mockResolvedValue([mockProject as any]);
    vi.mocked(ApiModule.getProjectById).mockResolvedValue(mockProject as any);
    vi.mocked(ApiModule.getProjectRecommendations).mockResolvedValue(mockRecs as any);
    vi.mocked(ApiModule.sendProjectInvitation).mockResolvedValue({
      id: 'new-inv-1',
      project_id: 'proj-rec-1',
      inviter_id: 'user-cand-123',
      invited_student_id: 'cand-target-99',
      status: 'pending',
      created_at: '2026-10-04T12:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/recommendations?projectId=proj-rec-1']}>
        <RecommendationsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Grace Hopper')).toBeTruthy();
      expect(screen.getByRole('button', { name: /Invite to Team/i })).toBeTruthy();
    });

    // Click Invite to Team
    const inviteBtn = screen.getByRole('button', { name: /Invite to Team/i });
    fireEvent.click(inviteBtn);

    await waitFor(() => {
      expect(ApiModule.sendProjectInvitation).toHaveBeenCalledWith('proj-rec-1', 'cand-target-99');
      expect(screen.getByText(/Invitation successfully sent to Grace Hopper!/i)).toBeTruthy();
      expect(screen.getByText('Invitation Sent')).toBeTruthy();
    });
  });
});
