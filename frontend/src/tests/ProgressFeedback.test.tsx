import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ProjectProgressFeedback } from '../components/ProjectProgressFeedback';
import * as ApiModule from '../services/api';
import { ProjectProgressOverview, FeedbackSummary, ProjectMember } from '../types';

vi.mock('../services/api');

describe('Phase 14: Project Progress & Collaboration Feedback Frontend Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockMembers: ProjectMember[] = [
    {
      id: 'mem-1',
      project_id: 'proj-100',
      student_id: 'stud-1',
      role: 'owner',
      joined_at: '2026-10-01T10:00:00Z',
      student_name: 'Alice Johnson',
    },
    {
      id: 'mem-2',
      project_id: 'proj-100',
      student_id: 'stud-2',
      role: 'member',
      joined_at: '2026-10-02T12:00:00Z',
      student_name: 'Bob Smith',
    },
  ];

  const mockOverview: ProjectProgressOverview = {
    project_id: 'proj-100',
    overall_progress_percentage: 50,
    total_tasks: 2,
    completed_tasks: 1,
    in_progress_tasks: 1,
    blocked_tasks: 0,
    todo_tasks: 0,
    latest_milestone_status: 'on_track',
    tasks: [
      {
        id: 'task-1',
        project_id: 'proj-100',
        title: 'Train PyTorch Neural Network',
        description: 'Fine-tune on project embeddings dataset',
        assigned_student_id: 'stud-2',
        assigned_student_name: 'Bob Smith',
        status: 'completed',
        priority: 'high',
        due_date: '2026-10-10T00:00:00Z',
        completed_at: '2026-10-04T12:00:00Z',
        created_by: 'stud-1',
        created_by_name: 'Alice Johnson',
        created_at: '2026-10-02T10:00:00Z',
        updated_at: '2026-10-04T12:00:00Z',
      },
      {
        id: 'task-2',
        project_id: 'proj-100',
        title: 'Build Frontend Dashboard',
        description: 'Connect React components to FastAPI endpoints',
        assigned_student_id: 'stud-1',
        assigned_student_name: 'Alice Johnson',
        status: 'in_progress',
        priority: 'medium',
        due_date: '2026-10-12T00:00:00Z',
        completed_at: null,
        created_by: 'stud-1',
        created_by_name: 'Alice Johnson',
        created_at: '2026-10-03T10:00:00Z',
        updated_at: '2026-10-03T10:00:00Z',
      },
    ],
    updates: [
      {
        id: 'up-1',
        project_id: 'proj-100',
        title: 'Sprint 1 Completion',
        description: 'Completed model architecture checkpoint',
        progress_percentage: 50,
        status: 'on_track',
        created_by: 'stud-1',
        created_by_name: 'Alice Johnson',
        created_at: '2026-10-04T10:00:00Z',
        updated_at: '2026-10-04T10:00:00Z',
        completed_at: null,
      },
    ],
  };

  const mockFeedbackSummary: FeedbackSummary = {
    project_id: 'proj-100',
    average_rating: 4.5,
    total_feedback_count: 2,
    skills_aligned_percentage: 100.0,
    feedback_list: [
      {
        id: 'fb-1',
        project_id: 'proj-100',
        student_id: 'stud-2',
        student_name: 'Bob Smith',
        rating: 5,
        feedback_text: 'Great teamwork and excellent AI skill alignment.',
        collaboration_quality: 'exceptional',
        skills_aligned: true,
        created_at: '2026-10-04T11:00:00Z',
        updated_at: '2026-10-04T11:00:00Z',
      },
    ],
  };

  it('renders progress overview percentage, milestone status, and task list', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText('50%').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Train PyTorch Neural Network')).toBeTruthy();
      expect(screen.getByText('Build Frontend Dashboard')).toBeTruthy();
      expect(screen.getByText('Sprint 1 Completion')).toBeTruthy();
    });
  });

  it('switches to Collaboration Feedback tab and renders satisfaction metrics', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Progress & Tasks')).toBeTruthy();
    });

    const feedbackTab = screen.getByText('Collaboration Feedback');
    fireEvent.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText('4.5')).toBeTruthy();
      expect(screen.getByText('(2 reviews)')).toBeTruthy();
      expect(screen.getByText('100% Aligned')).toBeTruthy();
      expect(screen.getByText('Great teamwork and excellent AI skill alignment.')).toBeTruthy();
    });
  });

  it('filters tasks by workflow status', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Train PyTorch Neural Network')).toBeTruthy();
    });

    // Click 'in progress' filter button
    const inProgressFilterBtn = screen.getByRole('button', { name: /^in progress$/i });
    fireEvent.click(inProgressFilterBtn);

    await waitFor(() => {
      expect(screen.getByText('Build Frontend Dashboard')).toBeTruthy();
      expect(screen.queryByText('Train PyTorch Neural Network')).toBeNull();
    });
  });

  it('handles task status updates via select dropdown', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);
    vi.mocked(ApiModule.updateProjectTask).mockResolvedValue({
      ...mockOverview.tasks[1],
      status: 'completed',
    });

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Build Frontend Dashboard')).toBeTruthy();
    });

    const selectElements = screen.getAllByRole('combobox');
    const taskSelect = selectElements.find(
      (sel) => (sel as HTMLSelectElement).value === 'in_progress'
    );
    expect(taskSelect).toBeDefined();

    if (taskSelect) {
      fireEvent.change(taskSelect, { target: { value: 'completed' } });
      await waitFor(() => {
        expect(ApiModule.updateProjectTask).toHaveBeenCalledWith(
          'proj-100',
          'task-2',
          { status: 'completed' },
          false
        );
      });
    }
  });

  it('renders restricted notice when access is forbidden (403)', async () => {
    const forbiddenError = { response: { status: 403 } };
    vi.mocked(ApiModule.getProjectProgressOverview).mockRejectedValue(forbiddenError);
    vi.mocked(ApiModule.getProjectFeedback).mockRejectedValue(forbiddenError);

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={false}
        members={[]}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Team Progress & Feedback Restricted')).toBeTruthy();
      expect(
        screen.getByText(/Task tracking, milestone management, and collaboration reviews are strictly confidential/i)
      ).toBeTruthy();
    });
  });

  it('allows opening task creation modal and creating a new task', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);
    vi.mocked(ApiModule.createProjectTask).mockResolvedValue({
      id: 'task-3',
      project_id: 'proj-100',
      title: 'Run Integration Tests',
      status: 'todo',
      priority: 'high',
      created_by: 'stud-1',
      created_at: '2026-10-04T12:30:00Z',
    });

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Add Task')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('Add Task'));

    await waitFor(() => {
      expect(screen.getByText('Create Team Task')).toBeTruthy();
    });

    const titleInput = screen.getByPlaceholderText(/Implement Sentence Transformer/i);
    fireEvent.change(titleInput, { target: { value: 'Run Integration Tests' } });

    const submitBtn = screen.getByRole('button', { name: /^Create Task$/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(ApiModule.createProjectTask).toHaveBeenCalledWith(
        'proj-100',
        expect.objectContaining({
          title: 'Run Integration Tests',
          priority: 'medium',
        }),
        false
      );
    });
  });

  it('allows submitting collaboration review in feedback tab', async () => {
    vi.mocked(ApiModule.getProjectProgressOverview).mockResolvedValue(mockOverview);
    vi.mocked(ApiModule.getProjectFeedback).mockResolvedValue(mockFeedbackSummary);
    vi.mocked(ApiModule.submitProjectFeedback).mockResolvedValue({
      id: 'fb-2',
      project_id: 'proj-100',
      student_id: 'stud-1',
      rating: 5,
      collaboration_quality: 'exceptional',
      skills_aligned: true,
      created_at: '2026-10-04T12:45:00Z',
    });

    render(
      <ProjectProgressFeedback
        projectId="proj-100"
        isOwner={true}
        members={mockMembers}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Collaboration Feedback')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('Collaboration Feedback'));

    await waitFor(() => {
      expect(screen.getByText('Submit Feedback')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('Submit Feedback'));

    await waitFor(() => {
      expect(screen.getByText('Collaboration & Recommendation Review')).toBeTruthy();
    });

    const submitReviewBtn = screen.getByRole('button', { name: /^Submit Review$/i });
    fireEvent.click(submitReviewBtn);

    await waitFor(() => {
      expect(ApiModule.submitProjectFeedback).toHaveBeenCalledWith(
        'proj-100',
        expect.objectContaining({
          rating: 5,
          collaboration_quality: 'exceptional',
          skills_aligned: true,
        }),
        false
      );
    });
  });
});
