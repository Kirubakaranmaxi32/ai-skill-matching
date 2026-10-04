import React, { useEffect, useState } from 'react';
import {
  getAdminOverview,
  getAdminStudentStats,
  getAdminProjectStats,
  getAdminProgressStats,
  getAdminFeedbackStats,
  getAdminAiMatchingStats,
  getAdminSystemStats,
} from '../services/admin';
import {
  AdminOverviewResponse,
  AdminStudentStats,
  AdminProjectStats,
  AdminProgressStats,
  AdminFeedbackStats,
  AdminAiMatchingStats,
  AdminSystemStats,
} from '../types/admin';
import {
  Users,
  FolderKanban,
  CheckCircle2,
  TrendingUp,
  Cpu,
  Server,
  Star,
  Clock,
  Layers,
  Award,
  AlertTriangle,
  Info,
  RefreshCw,
  Loader2,
  Shield,
  Activity,
  ListTodo,
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'students' | 'projects' | 'progress' | 'ai' | 'system'>('overview');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null);
  const [studentStats, setStudentStats] = useState<AdminStudentStats | null>(null);
  const [projectStats, setProjectStats] = useState<AdminProjectStats | null>(null);
  const [progressStats, setProgressStats] = useState<AdminProgressStats | null>(null);
  const [feedbackStats, setFeedbackStats] = useState<AdminFeedbackStats | null>(null);
  const [aiStats, setAiStats] = useState<AdminAiMatchingStats | null>(null);
  const [systemStats, setSystemStats] = useState<AdminSystemStats | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, st, pr, pg, fb, ai, sys] = await Promise.all([
        getAdminOverview(),
        getAdminStudentStats(),
        getAdminProjectStats(),
        getAdminProgressStats(),
        getAdminFeedbackStats(),
        getAdminAiMatchingStats(),
        getAdminSystemStats(),
      ]);
      setOverview(ov);
      setStudentStats(st);
      setProjectStats(pr);
      setProgressStats(pg);
      setFeedbackStats(fb);
      setAiStats(ai);
      setSystemStats(sys);
    } catch (err: any) {
      console.error('Failed to load admin dashboard:', err);
      setError(err?.response?.data?.detail || 'Failed to retrieve administrative analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const isDemo = overview?.demo_mode || systemStats?.demo_mode;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
        <p className="text-slate-600 font-medium">Aggregating platform & AI metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-4">
          <AlertTriangle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-900">Dashboard Loading Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchDashboardData}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors inline-flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Demo Mode Banner */}
      {isDemo && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl flex items-center space-x-3 text-amber-900 shadow-sm">
          <Info className="w-5 h-5 text-amber-600 shrink-0" />
          <div className="flex-1 text-sm">
            <span className="font-bold uppercase tracking-wider text-xs bg-amber-200 text-amber-800 px-2 py-0.5 rounded mr-2">
              Demo Mode
            </span>
            <span className="font-medium">
              Running with Synthetic Local Data. Statistics reflect isolated demonstration state with zero database mutations.
            </span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-600 text-white rounded-xl shadow-md shadow-indigo-100">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Admin Operations Console</h1>
              <p className="text-sm text-slate-500 font-medium">Platform analytics, AI recommendation readiness, and system health</p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchDashboardData}
          className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex overflow-x-auto space-x-2 border-b border-slate-200 pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'students', label: 'Students & Skills', icon: Users },
          { id: 'projects', label: 'Projects & Teams', icon: FolderKanban },
          { id: 'progress', label: 'Progress & Tasks', icon: ListTodo },
          { id: 'ai', label: 'AI Matching & Feedback', icon: Cpu },
          { id: 'system', label: 'System Health', icon: Server },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && overview && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Registered Students</span>
                <Users className="w-5 h-5 text-indigo-500" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{overview.total_students}</div>
              <p className="text-xs text-slate-500 mt-1">Platform user accounts</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Active Projects</span>
                <FolderKanban className="w-5 h-5 text-blue-500" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{overview.total_projects}</div>
              <p className="text-xs text-slate-500 mt-1">{overview.total_project_members} total team members</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Avg Progress</span>
                <TrendingUp className="w-5 h-5 text-emerald-500" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{overview.avg_project_progress}%</div>
              <p className="text-xs text-slate-500 mt-1">Across all project milestones</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Collaboration Rating</span>
                <Star className="w-5 h-5 text-amber-500" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">
                {overview.avg_feedback_rating ? `${overview.avg_feedback_rating} / 5` : 'N/A'}
              </div>
              <p className="text-xs text-slate-500 mt-1">{overview.total_feedback} feedback submissions</p>
            </div>
          </div>

          {/* Quick Subsystem Status Bar */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">Core Subsystem Telemetry</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg flex items-center justify-between border border-slate-100">
                <div>
                  <div className="text-xs text-slate-500 font-medium">Database Backend</div>
                  <div className="text-sm font-bold text-slate-900">
                    {overview.database_connected ? 'Supabase PostgreSQL' : 'Local In-Memory'}
                  </div>
                </div>
                <div className={`px-2.5 py-1 rounded-full text-xs font-bold ${overview.database_connected ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}`}>
                  {overview.database_connected ? 'Connected' : 'Offline'}
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-lg flex items-center justify-between border border-slate-100">
                <div>
                  <div className="text-xs text-slate-500 font-medium">PyTorch MLP Model</div>
                  <div className="text-sm font-bold text-slate-900">{overview.ai_model_version}</div>
                </div>
                <div className={`px-2.5 py-1 rounded-full text-xs font-bold ${overview.ai_model_loaded ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                  {overview.ai_model_loaded ? 'Model Online' : 'Unavailable'}
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-lg flex items-center justify-between border border-slate-100">
                <div>
                  <div className="text-xs text-slate-500 font-medium">Team Formation Invitations</div>
                  <div className="text-sm font-bold text-slate-900">{overview.total_invitations} Invitations</div>
                </div>
                <div className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
                  Phase 13 Active
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: STUDENTS & SKILLS */}
      {activeTab === 'students' && studentStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Department Breakdown */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Users className="w-5 h-5 text-indigo-600" />
                <span>Students by Department</span>
              </h3>
              <div className="space-y-3">
                {studentStats.students_by_department.length === 0 ? (
                  <p className="text-sm text-slate-500">No student department records available.</p>
                ) : (
                  studentStats.students_by_department.map((dept) => (
                    <div key={dept.department} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <span className="text-sm font-medium text-slate-700">{dept.department}</span>
                      <span className="text-sm font-bold bg-white px-2.5 py-1 rounded border border-slate-200 text-slate-900">
                        {dept.count}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Academic Year Distribution */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Layers className="w-5 h-5 text-blue-600" />
                <span>Academic Year Breakdown</span>
              </h3>
              <div className="grid grid-cols-5 gap-2 text-center">
                {['1', '2', '3', '4', '5'].map((yr) => (
                  <div key={yr} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs text-slate-500 font-semibold">Year {yr}</div>
                    <div className="text-xl font-extrabold text-slate-900 mt-1">
                      {studentStats.students_by_year[yr] || 0}
                    </div>
                  </div>
                ))}
              </div>

              {/* Profile Completeness */}
              <div className="mt-6 pt-6 border-t border-slate-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Profile Completeness</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-2.5 bg-slate-50 rounded">
                    <span className="text-slate-600">With Skills: </span>
                    <span className="font-bold text-slate-900">{studentStats.profile_completeness.with_skills}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded">
                    <span className="text-slate-600">With Interests: </span>
                    <span className="font-bold text-slate-900">{studentStats.profile_completeness.with_interests}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded">
                    <span className="text-slate-600">With Projects: </span>
                    <span className="font-bold text-slate-900">{studentStats.profile_completeness.with_previous_projects}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded">
                    <span className="text-slate-600">With Certs: </span>
                    <span className="font-bold text-slate-900">{studentStats.profile_completeness.with_certifications}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Common Skills & Proficiency */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Award className="w-5 h-5 text-amber-500" />
                <span>Most Common Student Skills</span>
              </h3>
              <div className="space-y-2">
                {studentStats.most_common_skills.length === 0 ? (
                  <p className="text-sm text-slate-500">No skill association records available.</p>
                ) : (
                  studentStats.most_common_skills.map((sk) => (
                    <div key={sk.skill_id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{sk.skill_name}</div>
                        <span className="text-xs text-slate-500">{sk.category}</span>
                      </div>
                      <span className="text-xs font-bold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full border border-indigo-200">
                        {sk.student_count} students
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Proficiency Distribution */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4">Student Proficiency Distribution</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded">
                  <span className="text-sm font-medium text-slate-700">Level 1 — Beginner</span>
                  <span className="font-bold text-slate-900">{studentStats.proficiency_distribution.beginner}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded">
                  <span className="text-sm font-medium text-slate-700">Level 2 — Intermediate</span>
                  <span className="font-bold text-slate-900">{studentStats.proficiency_distribution.intermediate}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded">
                  <span className="text-sm font-medium text-slate-700">Level 3 — Advanced</span>
                  <span className="font-bold text-slate-900">{studentStats.proficiency_distribution.advanced}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded">
                  <span className="text-sm font-medium text-slate-700">Level 4 — Expert</span>
                  <span className="font-bold text-slate-900">{studentStats.proficiency_distribution.expert}</span>
                </div>
              </div>

              {/* Project Skill Demand */}
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-6 mb-3">Project Skill Demand</h4>
              <div className="space-y-2">
                {studentStats.project_skill_demand.slice(0, 4).map((d) => (
                  <div key={d.skill_id} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded">
                    <span className="font-medium text-slate-800">{d.skill_name}</span>
                    <span className="font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">{d.project_count} projects</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: PROJECTS & TEAMS */}
      {activeTab === 'projects' && projectStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Projects</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{projectStats.total_projects}</div>
              <div className="flex gap-2 mt-3 flex-wrap">
                <span className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                  Open: {projectStats.projects_by_status.open || 0}
                </span>
                <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded border border-blue-200">
                  In Progress: {projectStats.projects_by_status.in_progress || 0}
                </span>
                <span className="text-xs px-2 py-1 bg-slate-100 text-slate-700 rounded border border-slate-200">
                  Completed: {projectStats.projects_by_status.completed || 0}
                </span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Team Size Statistics</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{projectStats.total_project_members} Members</div>
              <div className="text-xs text-slate-600 mt-2 space-y-1">
                <div>Average Team: <span className="font-bold">{projectStats.avg_team_size} members</span></div>
                <div>Max Team Size: <span className="font-bold">{projectStats.max_team_size} members</span></div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Invitations (Phase 13)</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{projectStats.invitation_stats.total_invitations} Total</div>
              <div className="text-xs text-slate-600 mt-2 space-y-1">
                <div>Accepted: <span className="font-bold text-emerald-600">{projectStats.invitation_stats.invitations_by_status.accepted || 0}</span></div>
                <div>Pending: <span className="font-bold text-amber-600">{projectStats.invitation_stats.invitations_by_status.pending || 0}</span></div>
                <div>Acceptance Rate: <span className="font-bold">{(projectStats.invitation_stats.acceptance_rate * 100).toFixed(0)}%</span></div>
              </div>
            </div>
          </div>

          {/* Recent Projects Feed */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Clock className="w-5 h-5 text-slate-600" />
              <span>Recent Projects</span>
            </h3>
            <div className="divide-y divide-slate-100">
              {projectStats.recent_projects.length === 0 ? (
                <p className="text-sm text-slate-500 py-3">No recent projects.</p>
              ) : (
                projectStats.recent_projects.map((p) => (
                  <div key={p.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-slate-900">{p.title}</div>
                      <div className="text-xs text-slate-500">ID: {p.id.slice(0, 8)}... • Created {new Date(p.created_at).toLocaleDateString()}</div>
                    </div>
                    <span className="text-xs font-medium uppercase px-2.5 py-1 bg-slate-100 rounded text-slate-700">
                      {p.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: PROGRESS & TASKS */}
      {activeTab === 'progress' && progressStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Progress</span>
              <div className="text-3xl font-extrabold text-indigo-600 mt-2">{progressStats.avg_project_progress}%</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tasks</span>
              <div className="text-3xl font-extrabold text-slate-900 mt-2">{progressStats.total_tasks}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completed Tasks</span>
              <div className="text-3xl font-extrabold text-emerald-600 mt-2">{progressStats.completed_tasks}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Blocked Tasks</span>
              <div className="text-3xl font-extrabold text-red-600 mt-2">{progressStats.blocked_tasks}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4">Tasks by Status</h3>
              <div className="space-y-3">
                {Object.entries(progressStats.tasks_by_status).map(([st, cnt]) => (
                  <div key={st} className="flex justify-between items-center p-3 bg-slate-50 rounded">
                    <span className="text-sm font-medium text-slate-700 capitalize">{st.replace('_', ' ')}</span>
                    <span className="text-sm font-bold text-slate-900">{cnt}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4">Tasks by Priority</h3>
              <div className="space-y-3">
                {Object.entries(progressStats.tasks_by_priority).map(([prio, cnt]) => (
                  <div key={prio} className="flex justify-between items-center p-3 bg-slate-50 rounded">
                    <span className="text-sm font-medium text-slate-700 capitalize">{prio}</span>
                    <span className="text-sm font-bold text-slate-900">{cnt}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: AI MATCHING & FEEDBACK */}
      {activeTab === 'ai' && aiStats && feedbackStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Model Architecture & Status */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-indigo-600" />
                <span>Deep Learning Architecture (MLP)</span>
              </h3>
              <div className="space-y-2.5 text-sm">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Model Type:</span>
                  <span className="font-semibold text-slate-900">{aiStats.model_type}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Version:</span>
                  <span className="font-semibold text-slate-900">{aiStats.model_version}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Input Feature Dimensions:</span>
                  <span className="font-semibold text-slate-900">{aiStats.input_features_count}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Hidden Layers:</span>
                  <span className="font-semibold text-slate-900">{aiStats.hidden_layers.join(' → ')}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Trainable Parameters:</span>
                  <span className="font-semibold text-slate-900">{aiStats.trainable_parameters.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500">Embedding Backbone:</span>
                  <span className="font-semibold text-slate-900">{aiStats.sentence_transformer_model.split('/').pop()}</span>
                </div>
              </div>
            </div>

            {/* Candidate Readiness Pool */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4">Recommendation Pool Readiness</h3>
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold">Eligible Candidate Pool</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{aiStats.recommendation_readiness.eligible_candidates_count} Students</div>
                  <p className="text-xs text-slate-500 mt-1">Students with structured skills eligible for ML inference</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold">Recommendation-Ready Projects</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{aiStats.recommendation_readiness.projects_with_skills_count} Projects</div>
                  <p className="text-xs text-slate-500 mt-1">Projects with required skill criteria defined</p>
                </div>

                {/* Transparency notice for historical metrics */}
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start space-x-2 text-xs text-blue-800">
                  <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Historical Audit Note: </span>
                    {aiStats.historical_tracking_notice}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feedback Statistics */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Star className="w-5 h-5 text-amber-500" />
              <span>Collaboration Feedback Distribution</span>
            </h3>
            <div className="grid grid-cols-5 gap-3 text-center mb-6">
              {[5, 4, 3, 2, 1].map((stars) => (
                <div key={stars} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-xs font-semibold text-slate-500">{stars} Stars</div>
                  <div className="text-xl font-bold text-slate-900 mt-1">{feedbackStats.rating_distribution[stars.toString()] || 0}</div>
                </div>
              ))}
            </div>

            {/* Recent Feedback Feed */}
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Recent Feedback Submissions</h4>
            <div className="divide-y divide-slate-100">
              {feedbackStats.recent_feedback.length === 0 ? (
                <p className="text-sm text-slate-500 py-3">No feedback records yet.</p>
              ) : (
                feedbackStats.recent_feedback.map((f) => (
                  <div key={f.id} className="py-3 flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          ★ {f.rating} / 5
                        </span>
                        <span className="text-xs text-slate-400">{new Date(f.created_at).toLocaleDateString()}</span>
                      </div>
                      <p className="text-sm text-slate-700 mt-1">{f.feedback_text || '(No comments provided)'}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: SYSTEM HEALTH */}
      {activeTab === 'system' && systemStats && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Server className="w-5 h-5 text-indigo-600" />
              <span>Infrastructure & Subsystem Verification</span>
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">FastAPI Backend Service</div>
                    <div className="text-xs text-slate-500">API Router {systemStats.api_version} operational</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
                  HEALTHY
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Database Connection</div>
                    <div className="text-xs text-slate-500">Mode: {systemStats.database_mode}</div>
                  </div>
                </div>
                <span className={`px-3 py-1 text-xs font-bold rounded-full ${systemStats.database_connected ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-800'}`}>
                  {systemStats.database_connected ? 'LIVE SUPABASE' : 'IN-MEMORY'}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">PyTorch MLP Checkpoint</div>
                    <div className="text-xs text-slate-500">best_matching_mlp.pt weights verified</div>
                  </div>
                </div>
                <span className={`px-3 py-1 text-xs font-bold rounded-full ${systemStats.checkpoint_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                  {systemStats.checkpoint_verified ? 'VERIFIED' : 'MISSING'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
