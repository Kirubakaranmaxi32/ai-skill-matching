import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  getMyProjects,
  getProjectById,
  getProjectRecommendations,
  getDemoProjects,
  getDemoProject,
  getDemoRecommendations,
  getProjectSkillGap,
  getDemoProjectSkillGap,
  sendProjectInvitation,
} from '../services/api';
import {
  Project,
  ProjectDetail,
  ProjectRecommendationResponse,
  SkillGapResponse,
} from '../types';
import {
  Users,
  Award,
  Sparkles,
  AlertCircle,
  Loader2,
  CheckCircle2,
  FolderKanban,
  ArrowLeft,
  ChevronDown,
  Target,
  Send,
  Clock,
  X,
} from 'lucide-react';
import { SkillGapView } from '../components/SkillGapView';

export const RecommendationsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlProjectId = searchParams.get('projectId');
  const urlDemo = searchParams.get('demo') === 'true';

  const [isDemoMode, setIsDemoMode] = useState<boolean>(urlDemo);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(urlProjectId || '');
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [recommendationsData, setRecommendationsData] = useState<ProjectRecommendationResponse | null>(null);

  const [loadingProjects, setLoadingProjects] = useState<boolean>(true);
  const [loadingRecs, setLoadingRecs] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Skill Gap state per candidate
  const [expandedGapStudentId, setExpandedGapStudentId] = useState<string | null>(null);
  const [gapDataMap, setGapDataMap] = useState<Record<string, SkillGapResponse>>({});
  const [loadingGapMap, setLoadingGapMap] = useState<Record<string, boolean>>({});
  const [gapErrorMap, setGapErrorMap] = useState<Record<string, string | null>>({});

  // Invitation state per candidate
  const [invitingStudentId, setInvitingStudentId] = useState<string | null>(null);
  const [inviteNotice, setInviteNotice] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  const handleInviteCandidate = async (studentId: string, studentName: string) => {
    if (!selectedProjectId) return;
    setInvitingStudentId(studentId);
    setInviteNotice(null);
    try {
      await sendProjectInvitation(selectedProjectId, studentId);
      setInviteNotice({
        type: 'success',
        message: `Invitation successfully sent to ${studentName}!`,
      });
      if (recommendationsData) {
        setRecommendationsData({
          ...recommendationsData,
          recommendations: recommendationsData.recommendations.map((r) =>
            r.student_id === studentId
              ? { ...r, invitation_status: 'pending' }
              : r
          ),
        });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to send invitation';
      setInviteNotice({
        type: 'error',
        message: msg,
      });
    } finally {
      setInvitingStudentId(null);
    }
  };

  const toggleSkillGap = async (studentId: string) => {
    if (expandedGapStudentId === studentId) {
      setExpandedGapStudentId(null);
      return;
    }
    setExpandedGapStudentId(studentId);
    if (!gapDataMap[studentId]) {
      setLoadingGapMap((prev) => ({ ...prev, [studentId]: true }));
      setGapErrorMap((prev) => ({ ...prev, [studentId]: null }));
      try {
        const data = isDemoMode
          ? await getDemoProjectSkillGap(selectedProjectId, studentId)
          : await getProjectSkillGap(selectedProjectId, studentId);
        setGapDataMap((prev) => ({ ...prev, [studentId]: data }));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load skill gap';
        setGapErrorMap((prev) => ({ ...prev, [studentId]: msg }));
      } finally {
        setLoadingGapMap((prev) => ({ ...prev, [studentId]: false }));
      }
    }
  };

  // 1. Load projects on mount or when mode toggles
  useEffect(() => {
    let isMounted = true;
    const loadProjects = async () => {
      setLoadingProjects(true);
      setError(null);
      try {
        let projs: Project[] = [];
        if (isDemoMode) {
          projs = await getDemoProjects();
        } else {
          projs = await getMyProjects();
        }

        if (isMounted) {
          setProjects(projs);
          if (projs.length > 0) {
            // If current selectedProjectId is in the loaded list, keep it; otherwise select first
            if (urlProjectId && projs.some((p) => p.id === urlProjectId)) {
              setSelectedProjectId(urlProjectId);
            } else {
              setSelectedProjectId(projs[0].id);
              setSearchParams(
                isDemoMode
                  ? { projectId: projs[0].id, demo: 'true' }
                  : { projectId: projs[0].id },
                { replace: true }
              );
            }
          } else {
            setSelectedProjectId('');
            setSelectedProject(null);
            setRecommendationsData(null);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load projects';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoadingProjects(false);
        }
      }
    };

    loadProjects();
    return () => {
      isMounted = false;
    };
  }, [isDemoMode]);

  // 2. Load recommendations & project details whenever selectedProjectId changes
  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null);
      setRecommendationsData(null);
      return;
    }

    let isMounted = true;
    const loadProjectRecommendations = async () => {
      setLoadingRecs(true);
      setError(null);
      try {
        let projDetails: ProjectDetail;
        let recs: ProjectRecommendationResponse;

        if (isDemoMode) {
          [projDetails, recs] = await Promise.all([
            getDemoProject(selectedProjectId),
            getDemoRecommendations(selectedProjectId, 10, 0.0),
          ]);
        } else {
          [projDetails, recs] = await Promise.all([
            getProjectById(selectedProjectId),
            getProjectRecommendations(selectedProjectId, 10, 0.0),
          ]);
        }

        if (isMounted) {
          setSelectedProject(projDetails);
          setRecommendationsData(recs);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error ? err.message : 'Failed to retrieve recommendations for this project';
          setError(msg);
          setSelectedProject(null);
          setRecommendationsData(null);
        }
      } finally {
        if (isMounted) {
          setLoadingRecs(false);
        }
      }
    };

    loadProjectRecommendations();
    return () => {
      isMounted = false;
    };
  }, [selectedProjectId, isDemoMode]);

  const handleSelectProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setExpandedGapStudentId(null);
    setGapDataMap({});
    setSearchParams(
      isDemoMode ? { projectId, demo: 'true' } : { projectId }
    );
  };

  const handleToggleDemoMode = (enableDemo: boolean) => {
    setIsDemoMode(enableDemo);
    setSelectedProjectId('');
    setSelectedProject(null);
    setRecommendationsData(null);
    setExpandedGapStudentId(null);
    setGapDataMap({});
    setSearchParams(enableDemo ? { demo: 'true' } : {});
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      {/* Header, Mode Toggle, and Explanation */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>AI-Driven Team Recommendation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Project Recommendations
          </h1>
          <p className="text-sm text-slate-600 max-w-2xl leading-relaxed">
            Candidate students are evaluated using a trained PyTorch Multi-Layer Perceptron (MLP)
            compatibility model. The continuous compatibility score (0–100%) represents multidimensional
            alignment across skill coverage, proficiency, domain interests, and previous project experience.
          </p>
        </div>

        {/* Mode Switcher Toggle */}
        <div className="shrink-0 flex items-center space-x-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
          <button
            onClick={() => handleToggleDemoMode(false)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              !isDemoMode
                ? 'bg-white text-slate-900 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Live Database
          </button>
          <button
            onClick={() => handleToggleDemoMode(true)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 ${
              isDemoMode
                ? 'bg-amber-500 text-white shadow-xs'
                : 'text-amber-800 hover:text-amber-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Demo Mode</span>
          </button>
        </div>
      </div>

      {/* Prominent Demo Mode Banner */}
      {isDemoMode && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start space-x-3 shadow-xs">
          <Sparkles className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-bold text-sm">DEMO MODE — Synthetic Local Data</h4>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                Offline Synthetic
              </span>
            </div>
            <p className="text-xs text-amber-800 leading-relaxed">
              Viewing local synthetic demonstration dataset from <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">data/demo/</code>.
              No records are queried from or written to the remote Supabase database.
              Compatibility scores and rankings are dynamically computed by the real trained PyTorch MLP model on CPU.
            </p>
          </div>
        </div>
      )}

      {/* Global Error Banner */}
      {error && (
        <div
          role="alert"
          className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3"
        >
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm">
            <p className="font-semibold">Unable to load recommendations</p>
            <p className="text-rose-700">{error}</p>
          </div>
        </div>
      )}

      {/* Initial Project Loading */}
      {loadingProjects && (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
          <p className="text-sm font-medium text-slate-600">
            {isDemoMode ? 'Loading demo projects...' : 'Loading your projects...'}
          </p>
        </div>
      )}

      {/* Empty State: No Projects Created Yet (Live Mode) */}
      {!loadingProjects && projects.length === 0 && !error && !isDemoMode && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 sm:p-12 text-center space-y-4 shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
            <FolderKanban className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900">No Projects Found</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              You must own at least one project in Supabase to generate student candidate recommendations.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              to="/projects/new"
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition-colors shadow-sm"
            >
              <span>Create Your First Project</span>
            </Link>
            <button
              onClick={() => handleToggleDemoMode(true)}
              className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 text-sm font-semibold border border-amber-200 transition-colors"
            >
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span>Explore Demo Mode</span>
            </button>
          </div>
        </div>
      )}

      {/* Project Selector & Overview when projects exist */}
      {!loadingProjects && projects.length > 0 && (
        <div className="space-y-6">
          {/* Project Switcher Bar */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <label htmlFor="project-select" className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                <span>Select Project</span>
                {isDemoMode && (
                  <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded">
                    Demo
                  </span>
                )}
              </label>
              <div className="relative">
                <select
                  id="project-select"
                  value={selectedProjectId}
                  onChange={(e) => handleSelectProject(e.target.value)}
                  className="w-full sm:w-96 appearance-none bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 pr-9 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            {selectedProjectId && !isDemoMode && (
              <div className="flex items-center space-x-2">
                <Link
                  to={`/projects/${selectedProjectId}`}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>View Project Details</span>
                </Link>
              </div>
            )}
          </div>

          {/* Selected Project Summary Card */}
          {selectedProject && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-xl font-bold text-slate-900">{selectedProject.title}</h2>
                    {isDemoMode && (
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                        Demo Project
                      </span>
                    )}
                  </div>
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 mt-1 rounded-full text-xs font-semibold capitalize bg-slate-100 text-slate-700 border border-slate-200">
                    Status: {selectedProject.status}
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  <span>{selectedProject.required_skills.length} Required Skills Specified</span>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Project Summary</h4>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {selectedProject.description}
                </p>
              </div>

              {/* Required Skills */}
              {selectedProject.required_skills.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                    <Award className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Target Skills Needed</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedProject.required_skills.map((s) => (
                      <span
                        key={s.skill_id}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-50 text-slate-700 border border-slate-200"
                      >
                        <span className="font-medium">{s.skill_name}</span>
                        <span className="text-[10px] text-slate-500 font-semibold">
                          (Req Lvl {s.required_proficiency})
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recommendations Content */}
          {loadingRecs && (
            <div className="py-16 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
              <p className="text-sm font-semibold text-slate-800">
                Evaluating candidate students with PyTorch MLP...
              </p>
              <p className="text-xs text-slate-500">
                Computing 10-dimensional compatibility vectors and deterministic ranking.
              </p>
            </div>
          )}

          {!loadingRecs && recommendationsData && (
            <div className="space-y-6">
              {/* Metadata Banner */}
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold">
                    <Users className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Recommendation Engine Evaluation</h3>
                    <p className="text-xs text-slate-600">
                      Model checkpoint: <code className="text-indigo-700 font-mono">{recommendationsData.model_version}</code>
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white text-indigo-700 border border-indigo-200 shadow-xs">
                    {recommendationsData.total_eligible_candidates} Eligible Candidates Evaluated
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Top {recommendationsData.recommendations.length} Ranked
                  </span>
                </div>
              </div>

              {/* Action Notification Banner */}
              {inviteNotice && (
                <div
                  className={`p-4 rounded-xl border flex items-center justify-between text-sm ${
                    inviteNotice.type === 'success'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border-rose-200 text-rose-800'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {inviteNotice.type === 'success' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    )}
                    <span className="font-medium">{inviteNotice.message}</span>
                  </div>
                  <button
                    onClick={() => setInviteNotice(null)}
                    className="text-slate-400 hover:text-slate-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Empty Candidates State */}
              {recommendationsData.recommendations.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-8 sm:p-12 text-center space-y-3 shadow-sm">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
                    <Users className="w-6 h-6" />
                  </div>
                  <h4 className="text-base font-bold text-slate-800">No Candidate Recommendations Found</h4>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    There are currently no eligible student candidates that meet the compatibility criteria
                    excluding existing members and the project lead.
                  </p>
                </div>
              ) : (
                /* Ranked Candidate Cards */
                <div className="space-y-4">
                  {recommendationsData.recommendations.map((rec) => (
                    <div
                      key={rec.student_id}
                      className="bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 p-5 sm:p-6 transition-all shadow-xs space-y-4"
                    >
                      {/* Candidate Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex items-center space-x-3.5">
                          <span className="w-8 h-8 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center text-xs font-bold shrink-0">
                            #{rec.rank}
                          </span>
                          <div>
                            <div className="flex items-center space-x-2">
                              <h3 className="font-bold text-slate-900 text-base">{rec.student_name}</h3>
                              {isDemoMode && (
                                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-200">
                                  Demo Candidate
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-500">
                              {rec.academic_year ? `Year ${rec.academic_year} Student` : 'Student Candidate'}
                            </p>
                          </div>
                        </div>

                        {/* Compatibility Score & Voluntary Invitation Action */}
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {Math.round(rec.compatibility_score * 100)}% Compatibility
                          </span>

                          {rec.invitation_status === 'accepted' ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Team Member</span>
                            </span>
                          ) : rec.invitation_status === 'pending' ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                              <Clock className="w-3.5 h-3.5 text-amber-600" />
                              <span>Invitation Sent</span>
                            </span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleInviteCandidate(rec.student_id, rec.student_name)}
                              disabled={invitingStudentId === rec.student_id}
                              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white shadow-xs transition-colors"
                            >
                              {invitingStudentId === rec.student_id ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  <span>Sending...</span>
                                </>
                              ) : (
                                <>
                                  <Send className="w-3.5 h-3.5" />
                                  <span>Invite to Team</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Factual Metrics Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100 text-xs">
                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-slate-500 block text-[11px] font-medium">Skill Coverage</span>
                          <span className="font-bold text-slate-800 text-sm">
                            {Math.round(rec.explanation.skill_coverage_ratio * 100)}%
                          </span>
                        </div>

                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-slate-500 block text-[11px] font-medium">Proficiency Alignment</span>
                          <span className="font-bold text-slate-800 text-sm">
                            {Math.round(rec.explanation.proficiency_alignment * 100)}%
                          </span>
                        </div>

                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-slate-500 block text-[11px] font-medium">Interest Overlap</span>
                          <span className="font-bold text-slate-800 text-sm">
                            {rec.explanation.interest_overlap ? 'Aligned' : 'None'}
                          </span>
                        </div>

                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-slate-500 block text-[11px] font-medium">Prior Projects</span>
                          <span className="font-bold text-slate-800 text-sm">
                            {Math.round(rec.explanation.experience_signal * 10)} completed
                          </span>
                        </div>
                      </div>

                      {/* Matched Skills */}
                      {rec.explanation.matched_skills.length > 0 && (
                        <div className="space-y-1.5">
                          <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Matched Skills ({rec.explanation.matched_skills.length})</span>
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {rec.explanation.matched_skills.map((m, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs bg-emerald-50 text-emerald-700 border border-emerald-200"
                              >
                                <span className="font-semibold">{m.skill_name}</span>
                                <span className="text-[10px] text-emerald-600 font-medium">
                                  (Lvl {m.student_proficiency} / Req {m.required_proficiency})
                                </span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Missing Skills (Skill Gaps) */}
                      {rec.explanation.missing_skills.length > 0 && (
                        <div className="space-y-1.5">
                          <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                            <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
                            <span>Skill Gaps ({rec.explanation.missing_skills.length})</span>
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {rec.explanation.missing_skills.map((ms, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-100 text-slate-600 border border-slate-200"
                              >
                                <span className="font-medium">{ms.skill_name}</span>
                                <span className="text-[10px] text-slate-500">
                                  (Req Lvl {ms.required_proficiency})
                                </span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skill Gap Analysis Drilldown */}
                      <div className="pt-3 border-t border-slate-100">
                        <button
                          type="button"
                          onClick={() => toggleSkillGap(rec.student_id)}
                          className="inline-flex items-center space-x-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
                        >
                          <Target className="w-3.5 h-3.5" />
                          <span>
                            {expandedGapStudentId === rec.student_id
                              ? 'Hide Skill Gap Analysis'
                              : 'View Skill Gap Analysis'}
                          </span>
                          <ChevronDown
                            className={`w-3.5 h-3.5 transition-transform ${
                              expandedGapStudentId === rec.student_id ? 'rotate-180' : ''
                            }`}
                          />
                        </button>

                        {expandedGapStudentId === rec.student_id && (
                          <div className="mt-3">
                            <SkillGapView
                              data={gapDataMap[rec.student_id] || null}
                              loading={!!loadingGapMap[rec.student_id]}
                              error={gapErrorMap[rec.student_id]}
                              isDemo={isDemoMode}
                              title={`${rec.student_name} — Skill Gap Analysis`}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Advisory Disclaimer */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 leading-relaxed italic">
                {isDemoMode ? (
                  <span>
                    Demonstration Notice: Demo-mode recommendation results are demonstrations of the implemented pipeline and must not be presented as evidence of performance on real student data.
                  </span>
                ) : (
                  <span>
                    Advisory Notice: Student candidate recommendations are generated dynamically using the PyTorch MLP compatibility model. All recommendations are strictly advisory — no invitations, admissions, or team roster changes are performed automatically.
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default RecommendationsPage;
