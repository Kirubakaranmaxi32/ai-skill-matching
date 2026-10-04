import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ProjectTask,
  ProjectProgressOverview,
  ProjectMember,
  FeedbackSummary,
  TaskStatus,
  TaskPriority,
  ProgressStatus,
  CollaborationQuality,
} from '../types';
import {
  getProjectProgressOverview,
  createProjectTask,
  updateProjectTask,
  deleteProjectTask,
  createProjectProgress,
  getProjectFeedback,
  submitProjectFeedback,
} from '../services/api';
import {
  CheckCircle2,
  Plus,
  Trash2,
  Loader2,
  Star,
  MessageSquare,
  BarChart3,
  Calendar,
  User,
  CheckSquare,
  Sparkles,
  X,
  ShieldAlert,
} from 'lucide-react';

interface ProjectProgressFeedbackProps {
  projectId: string;
  isOwner: boolean;
  members: ProjectMember[];
  isDemo?: boolean;
}

export const ProjectProgressFeedback: React.FC<ProjectProgressFeedbackProps> = ({
  projectId,
  isOwner,
  members,
  isDemo = false,
}) => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'feedback'>('tasks');

  // Overview & Tasks state
  const [overview, setOverview] = useState<ProjectProgressOverview | null>(null);
  const [loadingOverview, setLoadingOverview] = useState<boolean>(true);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [taskFilter, setTaskFilter] = useState<TaskStatus | 'all'>('all');

  // Feedback state
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary | null>(null);
  const [loadingFeedback, setLoadingFeedback] = useState<boolean>(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  // Task creation modal
  const [showTaskModal, setShowTaskModal] = useState<boolean>(false);
  const [taskTitle, setTaskTitle] = useState<string>('');
  const [taskDescription, setTaskDescription] = useState<string>('');
  const [taskAssignee, setTaskAssignee] = useState<string>('');
  const [taskPriority, setTaskPriority] = useState<TaskPriority>('medium');
  const [taskDueDate, setTaskDueDate] = useState<string>('');
  const [submittingTask, setSubmittingTask] = useState<boolean>(false);
  const [taskFormError, setTaskFormError] = useState<string | null>(null);

  // Progress update modal
  const [showProgressModal, setShowProgressModal] = useState<boolean>(false);
  const [progressTitle, setProgressTitle] = useState<string>('');
  const [progressDescription, setProgressDescription] = useState<string>('');
  const [progressPercentage, setProgressPercentage] = useState<number>(50);
  const [progressStatus, setProgressStatus] = useState<ProgressStatus>('on_track');
  const [submittingProgress, setSubmittingProgress] = useState<boolean>(false);
  const [progressFormError, setProgressFormError] = useState<string | null>(null);

  // Feedback submission modal
  const [showFeedbackModal, setShowFeedbackModal] = useState<boolean>(false);
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackText, setFeedbackText] = useState<string>('');
  const [feedbackQuality, setFeedbackQuality] = useState<CollaborationQuality>('exceptional');
  const [skillsAligned, setSkillsAligned] = useState<boolean>(true);
  const [submittingFeedback, setSubmittingFeedback] = useState<boolean>(false);
  const [feedbackFormError, setFeedbackFormError] = useState<string | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);

  // Load Overview & Tasks
  const loadOverview = useCallback(async () => {
    setLoadingOverview(true);
    setOverviewError(null);
    try {
      const data = await getProjectProgressOverview(projectId, isDemo);
      setOverview(data);
    } catch (err: unknown) {
      const errorMsg =
        err && typeof err === 'object' && 'response' in err && (err as { response?: { status?: number; data?: { detail?: string } } }).response?.status === 403
          ? 'FORBIDDEN'
          : err instanceof Error
          ? err.message
          : 'Failed to load project progress';
      setOverviewError(errorMsg);
    } finally {
      setLoadingOverview(false);
    }
  }, [projectId, isDemo]);

  // Load Feedback Summary
  const loadFeedback = useCallback(async () => {
    setLoadingFeedback(true);
    setFeedbackError(null);
    try {
      const data = await getProjectFeedback(projectId, isDemo);
      setFeedbackSummary(data);
    } catch (err: unknown) {
      const errorMsg =
        err && typeof err === 'object' && 'response' in err && (err as { response?: { status?: number } }).response?.status === 403
          ? 'FORBIDDEN'
          : err instanceof Error
          ? err.message
          : 'Failed to load feedback';
      setFeedbackError(errorMsg);
    } finally {
      setLoadingFeedback(false);
    }
  }, [projectId, isDemo]);

  useEffect(() => {
    loadOverview();
    loadFeedback();
  }, [loadOverview, loadFeedback]);

  // Handle Task Creation
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) {
      setTaskFormError('Task title is required');
      return;
    }
    setSubmittingTask(true);
    setTaskFormError(null);
    try {
      await createProjectTask(
        projectId,
        {
          title: taskTitle.trim(),
          description: taskDescription.trim() || undefined,
          assigned_student_id: taskAssignee || undefined,
          priority: taskPriority,
          due_date: taskDueDate ? new Date(taskDueDate).toISOString() : undefined,
        },
        isDemo
      );
      setTaskTitle('');
      setTaskDescription('');
      setTaskAssignee('');
      setTaskPriority('medium');
      setTaskDueDate('');
      setShowTaskModal(false);
      loadOverview();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create task';
      setTaskFormError(msg);
    } finally {
      setSubmittingTask(false);
    }
  };

  // Handle Task Status Toggle
  const handleUpdateTaskStatus = async (task: ProjectTask, newStatus: TaskStatus) => {
    try {
      await updateProjectTask(projectId, task.id, { status: newStatus }, isDemo);
      loadOverview();
    } catch (err) {
      console.error('Failed to update task status:', err);
    }
  };

  // Handle Task Deletion
  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteProjectTask(projectId, taskId, isDemo);
      loadOverview();
    } catch (err) {
      console.error('Failed to delete task:', err);
    }
  };

  // Handle Progress Checkpoint Creation
  const handleCreateProgress = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!progressTitle.trim()) {
      setProgressFormError('Checkpoint title is required');
      return;
    }
    setSubmittingProgress(true);
    setProgressFormError(null);
    try {
      await createProjectProgress(
        projectId,
        {
          title: progressTitle.trim(),
          description: progressDescription.trim() || undefined,
          progress_percentage: Number(progressPercentage),
          status: progressStatus,
        },
        isDemo
      );
      setProgressTitle('');
      setProgressDescription('');
      setProgressPercentage(50);
      setProgressStatus('on_track');
      setShowProgressModal(false);
      loadOverview();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create progress checkpoint';
      setProgressFormError(msg);
    } finally {
      setSubmittingProgress(false);
    }
  };

  // Handle Feedback Submission
  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingFeedback(true);
    setFeedbackFormError(null);
    try {
      await submitProjectFeedback(
        projectId,
        {
          rating: feedbackRating,
          feedback_text: feedbackText.trim() || undefined,
          collaboration_quality: feedbackQuality,
          skills_aligned: skillsAligned,
        },
        isDemo
      );
      setFeedbackSubmitted(true);
      setShowFeedbackModal(false);
      loadFeedback();
    } catch (err: unknown) {
      const responseData = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
      if (responseData?.status === 409) {
        setFeedbackFormError('You have already submitted collaboration feedback for this project.');
      } else {
        setFeedbackFormError(responseData?.data?.detail || (err instanceof Error ? err.message : 'Failed to submit feedback'));
      }
    } finally {
      setSubmittingFeedback(false);
    }
  };

  // Filtered tasks
  const filteredTasks = useMemo(() => {
    if (!overview) return [];
    if (taskFilter === 'all') return overview.tasks;
    return overview.tasks.filter((t) => t.status === taskFilter);
  }, [overview, taskFilter]);

  // Priority color helper
  const getPriorityBadge = (priority: TaskPriority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'high':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  // Status color helper
  const getStatusBadge = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'in_progress':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'blocked':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'todo':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  // Check if non-member forbidden
  if (overviewError === 'FORBIDDEN') {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 sm:p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-slate-200 text-slate-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Team Progress & Feedback Restricted</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Task tracking, milestone management, and collaboration reviews are strictly confidential to accepted team members and the project owner.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Navigation Tabs */}
      <div className="border-b border-slate-200 bg-slate-50/60 px-6 pt-4 flex items-center justify-between">
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('tasks')}
            className={`pb-3.5 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === 'tasks'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <CheckSquare className="w-4 h-4" />
            <span>Progress & Tasks</span>
            {overview && (
              <span className="ml-1.5 px-2 py-0.5 rounded-full text-xs bg-slate-200 text-slate-700">
                {overview.tasks.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('feedback')}
            className={`pb-3.5 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === 'feedback'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Star className="w-4 h-4" />
            <span>Collaboration Feedback</span>
            {feedbackSummary && (
              <span className="ml-1.5 px-2 py-0.5 rounded-full text-xs bg-slate-200 text-slate-700">
                {feedbackSummary.total_feedback_count}
              </span>
            )}
          </button>
        </div>

        {isDemo && (
          <span className="hidden sm:inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Demo Mode (Local In-Memory)</span>
          </span>
        )}
      </div>

      <div className="p-6 sm:p-8 space-y-6">
        {/* ================================================================= */}
        {/* TAB 1: PROGRESS & TASKS */}
        {/* ================================================================= */}
        {activeTab === 'tasks' && (
          <div className="space-y-6">
            {loadingOverview && (
              <div className="flex items-center justify-center py-12 space-x-2 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                <span className="text-sm">Loading project progress...</span>
              </div>
            )}

            {!loadingOverview && overview && (
              <>
                {/* Progress Overview Card */}
                <div className="bg-gradient-to-r from-slate-50 to-indigo-50/30 rounded-2xl border border-slate-200 p-5 sm:p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                        Team Completion Milestone {isOwner ? '• Project Owner' : '• Team Member'}
                      </span>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className="text-2xl font-black text-slate-900">
                          {`${overview.overall_progress_percentage}%`}
                        </span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-bold capitalize border ${
                            overview.latest_milestone_status === 'completed'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : overview.latest_milestone_status === 'delayed'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : overview.latest_milestone_status === 'at_risk'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                          }`}
                        >
                          {overview.latest_milestone_status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setShowProgressModal(true)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-colors"
                      >
                        <BarChart3 className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Update Milestone</span>
                      </button>

                      <button
                        onClick={() => setShowTaskModal(true)}
                        className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add Task</span>
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-3 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${Math.min(100, Math.max(0, overview.overall_progress_percentage))}%` }}
                    />
                  </div>

                  {/* Task Metrics Chips */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                      <span className="text-slate-500 block text-[11px]">Total Tasks</span>
                      <span className="font-bold text-slate-800 text-sm">{overview.total_tasks}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                      <span className="text-emerald-600 block text-[11px] font-semibold">Completed</span>
                      <span className="font-bold text-emerald-700 text-sm">{overview.completed_tasks}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                      <span className="text-indigo-600 block text-[11px] font-semibold">In Progress</span>
                      <span className="font-bold text-indigo-700 text-sm">{overview.in_progress_tasks}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                      <span className="text-slate-600 block text-[11px] font-semibold">To Do</span>
                      <span className="font-bold text-slate-700 text-sm">{overview.todo_tasks}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                      <span className="text-rose-600 block text-[11px] font-semibold">Blocked</span>
                      <span className="font-bold text-rose-700 text-sm">{overview.blocked_tasks}</span>
                    </div>
                  </div>
                </div>

                {/* Task Filter Pills */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center space-x-1.5 overflow-x-auto text-xs">
                    {(['all', 'todo', 'in_progress', 'completed', 'blocked'] as const).map((status) => (
                      <button
                        key={status}
                        onClick={() => setTaskFilter(status)}
                        className={`px-3 py-1 rounded-lg font-semibold capitalize transition-colors ${
                          taskFilter === status
                            ? 'bg-slate-900 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {status.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                  <span className="text-xs text-slate-400">
                    Showing {filteredTasks.length} of {overview.tasks.length} tasks
                  </span>
                </div>

                {/* Tasks List */}
                {filteredTasks.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 space-y-2">
                    <CheckSquare className="w-8 h-8 text-slate-300 mx-auto" />
                    <p className="text-sm font-medium text-slate-600">No tasks in this category</p>
                    <p className="text-xs">Create tasks to track action items and delegate responsibilities.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredTasks.map((task) => (
                      <div
                        key={task.id}
                        className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-xs space-y-2.5"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-start space-x-3">
                            <span
                              className={`mt-0.5 px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border shrink-0 ${getPriorityBadge(
                                task.priority
                              )}`}
                            >
                              {task.priority}
                            </span>
                            <div>
                              <h4
                                className={`text-sm font-semibold ${
                                  task.status === 'completed'
                                    ? 'line-through text-slate-400'
                                    : 'text-slate-900'
                                }`}
                              >
                                {task.title}
                              </h4>
                              {task.description && (
                                <p className="text-xs text-slate-500 mt-0.5">{task.description}</p>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 shrink-0">
                            {/* Status Selector */}
                            <select
                              value={task.status}
                              onChange={(e) => handleUpdateTaskStatus(task, e.target.value as TaskStatus)}
                              className={`px-2.5 py-1 rounded-lg text-xs font-semibold border focus:outline-none focus:ring-1 focus:ring-indigo-500 ${getStatusBadge(
                                task.status
                              )}`}
                            >
                              <option value="todo">To Do</option>
                              <option value="in_progress">In Progress</option>
                              <option value="completed">Completed</option>
                              <option value="blocked">Blocked</option>
                            </select>

                            <button
                              onClick={() => handleDeleteTask(task.id)}
                              className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                              title="Delete task"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Task Metadata Footer */}
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 border-t border-slate-100 pt-2">
                          <span className="flex items-center space-x-1">
                            <User className="w-3 h-3 text-slate-400" />
                            <span>
                              {task.assigned_student_name ? `Assigned: ${task.assigned_student_name}` : 'Unassigned'}
                            </span>
                          </span>

                          {task.due_date && (
                            <span className="flex items-center space-x-1">
                              <Calendar className="w-3 h-3 text-slate-400" />
                              <span>Due {new Date(task.due_date).toLocaleDateString()}</span>
                            </span>
                          )}

                          {task.completed_at && (
                            <span className="flex items-center space-x-1 text-emerald-600 font-medium">
                              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                              <span>Done {new Date(task.completed_at).toLocaleDateString()}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Milestones / Updates Timeline */}
                {overview.updates.length > 0 && (
                  <div className="space-y-3 pt-4 border-t border-slate-100">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Milestone Checkpoint History ({overview.updates.length})
                    </h4>
                    <div className="space-y-2">
                      {overview.updates.map((up) => (
                        <div
                          key={up.id}
                          className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                        >
                          <div className="space-y-0.5">
                            <span className="font-semibold text-slate-800">{up.title}</span>
                            {up.description && <p className="text-slate-500 text-[11px]">{up.description}</p>}
                          </div>
                          <div className="flex items-center space-x-3 text-slate-500 shrink-0">
                            <span className="font-bold text-slate-900">{`${up.progress_percentage}%`}</span>
                            <span className="text-[11px]">{new Date(up.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: COLLABORATION FEEDBACK */}
        {/* ================================================================= */}
        {activeTab === 'feedback' && (
          <div className="space-y-6">
            {loadingFeedback && (
              <div className="flex items-center justify-center py-12 space-x-2 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                <span className="text-sm">Loading collaboration feedback...</span>
              </div>
            )}

            {!loadingFeedback && feedbackSummary && (
              <>
                {/* Aggregate Summary Card */}
                <div className="bg-gradient-to-r from-amber-50/40 via-white to-indigo-50/30 rounded-2xl border border-slate-200 p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-14 h-14 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center font-black text-2xl">
                        {feedbackSummary.average_rating > 0 ? feedbackSummary.average_rating.toFixed(1) : '—'}
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-slate-900">Collaboration Satisfaction</h4>
                        <div className="flex items-center space-x-1 mt-0.5">
                          {[1, 2, 3, 4, 5].map((s) => (
                            <Star
                              key={s}
                              className={`w-4 h-4 ${
                                s <= Math.round(feedbackSummary.average_rating)
                                  ? 'text-amber-500 fill-amber-500'
                                  : 'text-slate-300'
                              }`}
                            />
                          ))}
                          <span className="text-xs text-slate-500 ml-1.5">
                            ({feedbackSummary.total_feedback_count} reviews)
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <span className="text-[11px] text-slate-500 block">AI Match Alignment</span>
                        <span className="font-bold text-emerald-700 text-sm">
                          {feedbackSummary.skills_aligned_percentage}% Aligned
                        </span>
                      </div>

                      <button
                        onClick={() => setShowFeedbackModal(true)}
                        className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>Submit Feedback</span>
                      </button>
                    </div>
                  </div>
                </div>

                {feedbackError && feedbackError !== 'FORBIDDEN' && (
                  <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                    {feedbackError}
                  </div>
                )}

                {feedbackSubmitted && (
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Your collaboration review has been submitted successfully!</span>
                  </div>
                )}

                {/* Feedback List */}
                {feedbackSummary.feedback_list.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 space-y-2">
                    <MessageSquare className="w-8 h-8 text-slate-300 mx-auto" />
                    <p className="text-sm font-medium text-slate-600">No collaboration feedback submitted yet</p>
                    <p className="text-xs">
                      Team members and project owners can rate mutual collaboration and evaluate AI recommendation accuracy.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {feedbackSummary.feedback_list.map((fb) => (
                      <div
                        key={fb.id}
                        className="p-4 rounded-xl border border-slate-200 bg-white space-y-2.5 shadow-2xs"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2.5">
                            <div className="flex items-center space-x-0.5">
                              {[1, 2, 3, 4, 5].map((s) => (
                                <Star
                                  key={s}
                                  className={`w-3.5 h-3.5 ${
                                    s <= fb.rating ? 'text-amber-500 fill-amber-500' : 'text-slate-200'
                                  }`}
                                />
                              ))}
                            </div>
                            <span className="font-semibold text-slate-800 text-xs">
                              {fb.student_name || 'Team Collaborator'}
                            </span>
                          </div>

                          <div className="flex items-center space-x-2">
                            {fb.collaboration_quality && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold capitalize bg-slate-100 text-slate-700 border border-slate-200">
                                {fb.collaboration_quality}
                              </span>
                            )}
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                fb.skills_aligned
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : 'bg-rose-50 text-rose-700 border-rose-200'
                              }`}
                            >
                              {fb.skills_aligned ? 'Skills Aligned' : 'Skills Mismatched'}
                            </span>
                          </div>
                        </div>

                        {fb.feedback_text && (
                          <p className="text-xs text-slate-600 leading-relaxed pl-1">{fb.feedback_text}</p>
                        )}

                        <div className="text-[10px] text-slate-400 pl-1">
                          Submitted {new Date(fb.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* ================================================================= */}
      {/* MODAL 1: ADD TASK */}
      {/* ================================================================= */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <CheckSquare className="w-5 h-5 text-indigo-600" />
                <span>Create Team Task</span>
              </h3>
              <button onClick={() => setShowTaskModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {taskFormError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {taskFormError}
              </div>
            )}

            <form onSubmit={handleCreateTask} className="space-y-3.5">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Task Title *</label>
                <input
                  type="text"
                  required
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  placeholder="e.g. Implement Sentence Transformer Embedding Cache"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  placeholder="Provide context, acceptance criteria, or technical details..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Assignee</label>
                  <select
                    value={taskAssignee}
                    onChange={(e) => setTaskAssignee(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.student_id} value={m.student_id}>
                        {m.student_name || 'Member'} ({m.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={taskPriority}
                    onChange={(e) => setTaskPriority(e.target.value as TaskPriority)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Target Due Date (Optional)</label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowTaskModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingTask}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submittingTask && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Create Task</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* MODAL 2: UPDATE MILESTONE */}
      {/* ================================================================= */}
      {showProgressModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                <span>Post Progress Milestone</span>
              </h3>
              <button onClick={() => setShowProgressModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {progressFormError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {progressFormError}
              </div>
            )}

            <form onSubmit={handleCreateProgress} className="space-y-3.5">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Milestone Title *</label>
                <input
                  type="text"
                  required
                  value={progressTitle}
                  onChange={(e) => setProgressTitle(e.target.value)}
                  placeholder="e.g. Sprint 2 Feature Complete"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={2}
                  value={progressDescription}
                  onChange={(e) => setProgressDescription(e.target.value)}
                  placeholder="Summary of deliverables and milestone results..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Progress Percentage ({progressPercentage}%)
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={progressPercentage}
                    onChange={(e) => setProgressPercentage(Number(e.target.value))}
                    className="w-full mt-2 accent-indigo-600"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Status</label>
                  <select
                    value={progressStatus}
                    onChange={(e) => setProgressStatus(e.target.value as ProgressStatus)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  >
                    <option value="on_track">On Track</option>
                    <option value="at_risk">At Risk</option>
                    <option value="delayed">Delayed</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowProgressModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingProgress}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submittingProgress && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Milestone</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* MODAL 3: SUBMIT FEEDBACK */}
      {/* ================================================================= */}
      {showFeedbackModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
                <span>Collaboration & Recommendation Review</span>
              </h3>
              <button onClick={() => setShowFeedbackModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {feedbackFormError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {feedbackFormError}
              </div>
            )}

            <form onSubmit={handleSubmitFeedback} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-2">Overall Rating (1 to 5 Stars)</label>
                <div className="flex items-center space-x-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      type="button"
                      key={star}
                      onClick={() => setFeedbackRating(star)}
                      className="p-1 text-slate-300 hover:text-amber-500 transition-colors focus:outline-none"
                    >
                      <Star
                        className={`w-7 h-7 ${
                          star <= feedbackRating ? 'text-amber-500 fill-amber-500' : 'text-slate-200'
                        }`}
                      />
                    </button>
                  ))}
                  <span className="ml-2 font-bold text-slate-800 text-sm">{feedbackRating} of 5</span>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Collaboration Quality</label>
                <select
                  value={feedbackQuality}
                  onChange={(e) => setFeedbackQuality(e.target.value as CollaborationQuality)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="exceptional">Exceptional — Exceeded all expectations</option>
                  <option value="good">Good — Smooth and productive teamwork</option>
                  <option value="adequate">Adequate — Met baseline requirements</option>
                  <option value="challenging">Challenging — Encountered coordination hurdles</option>
                </select>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-800 block">AI Recommendation Alignment</span>
                  <span className="text-[11px] text-slate-500">
                    Did the AI skill matching model recommend candidates with accurate technical skills?
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={skillsAligned}
                  onChange={(e) => setSkillsAligned(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Written Feedback (Optional)</label>
                <textarea
                  rows={3}
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Share constructive insights on team dynamics, skill execution, and project milestones..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowFeedbackModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingFeedback}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submittingFeedback && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Submit Review</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
