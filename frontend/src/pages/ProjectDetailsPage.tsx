import React, { useEffect, useState, useMemo } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getProjectById,
  getSkills,
  addProjectSkill,
  deleteProjectSkill,
  archiveProject,
  analyzeProject,
  getProjectRecommendations,
  getProjectSkillGap,
} from '../services/api';
import {
  ProjectDetail,
  Skill,
  ProjectAnalysisResult,
  ProjectRecommendationResponse,
  SkillGapResponse,
} from '../types';
import {
  ArrowLeft,
  Calendar,
  User,
  Users,
  Award,
  Plus,
  Trash2,
  Archive,
  Edit3,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  X,
  Sparkles,
} from 'lucide-react';
import { SkillGapView } from '../components/SkillGapView';
import { ProjectProgressFeedback } from '../components/ProjectProgressFeedback';

export const ProjectDetailsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const location = useLocation();
  const { user } = useAuth();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [taxonomySkills, setTaxonomySkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(
    (location.state as { message?: string })?.message || null
  );

  // Add Skill state
  const [selectedSkillId, setSelectedSkillId] = useState<string>('');
  const [requiredProficiency, setRequiredProficiency] = useState<number>(2);
  const [skillSearchQuery, setSkillSearchQuery] = useState<string>('');
  const [addingSkill, setAddingSkill] = useState<boolean>(false);
  const [deletingSkillId, setDeletingSkillId] = useState<string | null>(null);

  // Archive modal / confirmation state
  const [showArchiveConfirm, setShowArchiveConfirm] = useState<boolean>(false);
  const [archiving, setArchiving] = useState<boolean>(false);

  // AI Project Analysis state
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<ProjectAnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Recommendations state
  const [loadingRecs, setLoadingRecs] = useState<boolean>(false);
  const [recommendationsData, setRecommendationsData] = useState<ProjectRecommendationResponse | null>(null);
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null);

  // Skill Gap state (viewer vs project)
  const [skillGapData, setSkillGapData] = useState<SkillGapResponse | null>(null);
  const [loadingSkillGap, setLoadingSkillGap] = useState<boolean>(false);
  const [skillGapError, setSkillGapError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      if (!projectId) return;
      setLoading(true);
      setError(null);
      setLoadingSkillGap(true);
      try {
        const [projData, skillsData] = await Promise.all([
          getProjectById(projectId),
          getSkills(),
        ]);

        let gapData: SkillGapResponse | null = null;
        if (user && typeof getProjectSkillGap === 'function') {
          try {
            gapData = await Promise.resolve(getProjectSkillGap(projectId));
          } catch (err: unknown) {
            gapData = null;
            if (isMounted) {
              setSkillGapError(err instanceof Error ? err.message : 'Failed to load skill gap');
            }
          }
        }

        if (isMounted) {
          setProject(projData);
          setTaxonomySkills(skillsData);
          if (gapData) {
            setSkillGapData(gapData);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load project details';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
          setLoadingSkillGap(false);
        }
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, [projectId, user]);

  // Determine if authenticated user is the owner
  const isOwner = useMemo(() => {
    if (!project || !user) return false;
    // Check match against owner user_id
    return project.owner?.user_id === user.id;
  }, [project, user]);

  // Filter skills not yet added to this project
  const unselectedSkills = useMemo(() => {
    if (!project) return [];
    const addedIds = new Set(project.required_skills.map((s) => s.skill_id));
    return taxonomySkills
      .filter((s) => !addedIds.has(s.id))
      .filter((s) =>
        skillSearchQuery.trim() === ''
          ? true
          : s.name.toLowerCase().includes(skillSearchQuery.toLowerCase()) ||
            s.category.toLowerCase().includes(skillSearchQuery.toLowerCase())
      );
  }, [taxonomySkills, project, skillSearchQuery]);

  const showNotification = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 4000);
  };

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !selectedSkillId) return;

    setAddingSkill(true);
    try {
      const added = await addProjectSkill(projectId, selectedSkillId, requiredProficiency);
      setProject((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          required_skills: [...prev.required_skills, added],
        };
      });
      setSelectedSkillId('');
      setSkillSearchQuery('');
      showNotification('Required skill added successfully!');
      try {
        Promise.resolve(getProjectSkillGap(projectId))
          .then((res) => {
            if (res) setSkillGapData(res);
          })
          .catch(() => {});
      } catch {
        // Safe fallback in test mocks
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add required skill';
      setError(msg);
    } finally {
      setAddingSkill(false);
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    if (!projectId) return;
    setDeletingSkillId(skillId);
    try {
      await deleteProjectSkill(projectId, skillId);
      setProject((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          required_skills: prev.required_skills.filter((s) => s.skill_id !== skillId),
        };
      });
      showNotification('Required skill removed.');
      try {
        Promise.resolve(getProjectSkillGap(projectId))
          .then((res) => {
            if (res) setSkillGapData(res);
          })
          .catch(() => {});
      } catch {
        // Safe fallback in test mocks
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to remove skill';
      setError(msg);
    } finally {
      setDeletingSkillId(null);
    }
  };

  const handleArchive = async () => {
    if (!projectId) return;
    setArchiving(true);
    try {
      const updated = await archiveProject(projectId);
      setProject((prev) => (prev ? { ...prev, status: updated.status } : null));
      setShowArchiveConfirm(false);
      showNotification('Project has been archived.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to archive project';
      setError(msg);
    } finally {
      setArchiving(false);
    }
  };

  const handleAnalyzeProject = async () => {
    if (!projectId) return;
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const result = await analyzeProject(projectId);
      setAnalysisResult(result);
      showNotification('AI project analysis completed.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to analyze project description';
      setAnalysisError(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGetRecommendations = async () => {
    if (!projectId) return;
    setLoadingRecs(true);
    setRecommendationsError(null);
    try {
      const result = await getProjectRecommendations(projectId, 10, 0.0);
      setRecommendationsData(result);
      showNotification('Candidate recommendations updated via PyTorch MLP model.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve candidate recommendations';
      setRecommendationsError(msg);
    } finally {
      setLoadingRecs(false);
    }
  };

  const getProficiencyBadge = (level: number) => {
    switch (level) {
      case 1:
        return { label: 'Level 1: Beginner', color: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 2:
        return { label: 'Level 2: Intermediate', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 3:
        return { label: 'Level 3: Advanced', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' };
      case 4:
        return { label: 'Level 4: Expert', color: 'bg-purple-50 text-purple-700 border-purple-200' };
      default:
        return { label: `Level ${level}`, color: 'bg-slate-50 text-slate-700 border-slate-200' };
    }
  };

  if (loading) {
    return (
      <div className="py-20 px-4 max-w-4xl mx-auto text-center space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto" />
        <h2 className="text-xl font-semibold text-slate-800">Loading Project Details...</h2>
        <p className="text-sm text-slate-500">Retrieving specifications, requirements, and roster.</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="py-16 px-4 max-w-3xl mx-auto text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Project Not Found</h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          {error || 'The requested project could not be found or has been archived.'}
        </p>
        <div className="pt-2">
          <Link
            to="/projects"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Projects</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      {/* Navigation & Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/projects"
          className="inline-flex items-center space-x-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </Link>

        {isOwner && (
          <div className="flex items-center space-x-2">
            {project.status !== 'archived' && (
              <>
                <button
                  onClick={handleAnalyzeProject}
                  disabled={analyzing}
                  title="Run advisory AI skill and embedding analysis"
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 text-sm font-semibold transition-colors disabled:opacity-50"
                >
                  {analyzing ? (
                    <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                  ) : (
                    <Sparkles className="w-4 h-4 text-purple-600" />
                  )}
                  <span>{analyzing ? 'Analyzing...' : 'Analyze Project'}</span>
                </button>

                <button
                  onClick={handleGetRecommendations}
                  disabled={loadingRecs}
                  title="Compute student compatibility recommendations using PyTorch MLP"
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm font-semibold transition-colors disabled:opacity-50"
                >
                  {loadingRecs ? (
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                  ) : (
                    <Users className="w-4 h-4 text-indigo-600" />
                  )}
                  <span>{loadingRecs ? 'Finding Candidates...' : 'Recommended Students'}</span>
                </button>

                <Link
                  to={`/projects/${project.id}/edit`}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Edit Project</span>
                </Link>

                <button
                  onClick={() => setShowArchiveConfirm(true)}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-700 text-sm font-semibold transition-colors"
                >
                  <Archive className="w-4 h-4" />
                  <span>Archive</span>
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="text-sm font-medium">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Project Overview Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{project.title}</h1>
              {project.status === 'open' && (
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Open (Recruiting)</span>
                </span>
              )}
              {project.status === 'in_progress' && (
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  <Clock className="w-3.5 h-3.5" />
                  <span>In Progress</span>
                </span>
              )}
              {project.status === 'completed' && (
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Completed</span>
                </span>
              )}
              {project.status === 'archived' && (
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-300">
                  <Archive className="w-3.5 h-3.5" />
                  <span>Archived</span>
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5" />
                <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
              </span>
            </div>
          </div>

          {project.owner && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 flex items-center space-x-3 shrink-0">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                <User className="w-4 h-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-slate-800">{project.owner.full_name}</p>
                <p className="text-slate-500">
                  Project Lead {project.owner.academic_year ? `• Year ${project.owner.academic_year}` : ''}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Project Overview</h3>
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{project.description}</p>
        </div>
      </div>

      {/* AI Analysis Error Alert */}
      {analysisError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span className="text-sm font-medium">{analysisError}</span>
          </div>
          <button onClick={() => setAnalysisError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* AI Project Analysis Advisory Card */}
      {analysisResult && (
        <div className="bg-white rounded-2xl border border-purple-200 p-6 sm:p-8 shadow-sm space-y-5 bg-gradient-to-br from-white to-purple-50/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-100 pb-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">AI Project Analysis (Advisory)</h3>
                <p className="text-xs text-slate-500">NLP preprocessing, embedding representation, and taxonomy alignment</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Status Badge */}
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize border ${
                analysisResult.analysis_status === 'completed'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : analysisResult.analysis_status === 'partial'
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}>
                Status: {analysisResult.analysis_status}
              </span>

              {/* Embedding Badge */}
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${
                analysisResult.embedding_available
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}>
                {analysisResult.embedding_available
                  ? `Dense Embedding: ${analysisResult.embedding_dimension}-dim (${analysisResult.model_name || 'all-MiniLM-L6-v2'})`
                  : 'Dense Embedding: Skipped / Unavailable'}
              </span>

              <button
                onClick={() => setAnalysisResult(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
                title="Dismiss analysis"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Extracted Skills List */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Detected Skills from Description ({analysisResult.extracted_skills.length})
            </h4>

            {analysisResult.extracted_skills.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No technical skills detected matching the master taxonomy.</p>
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {analysisResult.extracted_skills.map((s, idx) => (
                  <div
                    key={idx}
                    className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-purple-200 bg-white shadow-xs text-xs"
                  >
                    <span className="font-semibold text-slate-800">{s.skill_name}</span>
                    {s.category && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                        {s.category}
                      </span>
                    )}
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                      s.source.startsWith('taxonomy')
                        ? 'bg-purple-50 text-purple-700 border border-purple-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {Math.round(s.confidence * 100)}% Match
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Warnings (if any) */}
          {analysisResult.warnings.length > 0 && (
            <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-800 text-xs space-y-1">
              <p className="font-semibold flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Diagnostic Notes:</span>
              </p>
              <ul className="list-disc pl-5 space-y-0.5 text-amber-700">
                {analysisResult.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Advisory Disclaimer */}
          <p className="text-[11px] text-slate-400 border-t border-purple-100/60 pt-3 italic">
            Advisory Notice: AI analysis is non-destructive and advisory. It does not automatically modify project required skills or team requirements.
          </p>
        </div>
      )}

      {/* Recommendation Error Alert */}
      {recommendationsError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span className="text-sm font-medium">{recommendationsError}</span>
          </div>
          <button onClick={() => setRecommendationsError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Recommended Students Card */}
      {recommendationsData && (
        <div className="bg-white rounded-2xl border border-indigo-200 p-6 sm:p-8 shadow-sm space-y-6 bg-gradient-to-br from-white to-indigo-50/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-indigo-100 pb-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Recommended Students</h3>
                <p className="text-xs text-slate-500">
                  Scored via trained PyTorch MLP compatibility model ({recommendationsData.model_version})
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                Eligible Candidates: {recommendationsData.total_eligible_candidates}
              </span>
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Top {recommendationsData.recommendations.length} Shown
              </span>
              <Link
                to={`/recommendations?projectId=${project.id}`}
                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-white hover:bg-slate-50 text-indigo-700 border border-indigo-200 transition-colors"
                title="Open recommendations in dedicated view"
              >
                <span>Full View</span>
              </Link>
              <button
                onClick={() => setRecommendationsData(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
                title="Dismiss recommendations"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Candidates List */}
          {recommendationsData.recommendations.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm">
              No matching candidates found meeting the minimum score criteria.
            </div>
          ) : (
            <div className="space-y-4">
              {recommendationsData.recommendations.map((rec) => (
                <div
                  key={rec.student_id}
                  className="p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition-all shadow-xs space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-3">
                      <span className="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold shrink-0">
                        #{rec.rank}
                      </span>
                      <div>
                        <h4 className="font-semibold text-slate-900 text-sm">{rec.student_name}</h4>
                        <div className="flex items-center space-x-2 text-xs text-slate-500">
                          {rec.academic_year && <span>Year {rec.academic_year} Student</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {Math.round(rec.compatibility_score * 100)}% Compatibility
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Factual Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-xs">
                    <div className="p-2 rounded-lg bg-slate-50">
                      <span className="text-slate-500 block text-[11px]">Skill Coverage</span>
                      <span className="font-semibold text-slate-800">
                        {Math.round(rec.explanation.skill_coverage_ratio * 100)}%
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50">
                      <span className="text-slate-500 block text-[11px]">Proficiency Alignment</span>
                      <span className="font-semibold text-slate-800">
                        {Math.round(rec.explanation.proficiency_alignment * 100)}%
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50">
                      <span className="text-slate-500 block text-[11px]">Interest Overlap</span>
                      <span className="font-semibold text-slate-800">
                        {rec.explanation.interest_overlap ? 'Aligned' : 'None'}
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50">
                      <span className="text-slate-500 block text-[11px]">Past Projects</span>
                      <span className="font-semibold text-slate-800">
                        {Math.round(rec.explanation.experience_signal * 10)}
                      </span>
                    </div>
                  </div>

                  {/* Matched Skills */}
                  {rec.explanation.matched_skills.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        Matched Skills ({rec.explanation.matched_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {rec.explanation.matched_skills.map((m, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-xs bg-emerald-50 text-emerald-700 border border-emerald-200"
                          >
                            <span>{m.skill_name}</span>
                            <span className="text-[10px] text-emerald-600 font-medium">
                              (Lvl {m.student_proficiency} / Req {m.required_proficiency})
                            </span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {rec.explanation.missing_skills.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        Skill Gaps ({rec.explanation.missing_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {rec.explanation.missing_skills.map((ms, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-xs bg-slate-100 text-slate-600 border border-slate-200"
                          >
                            <span>{ms.skill_name}</span>
                            <span className="text-[10px] text-slate-500 font-medium">
                              (Req Lvl {ms.required_proficiency})
                            </span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Advisory Disclaimer */}
          <p className="text-[11px] text-slate-400 border-t border-indigo-100/60 pt-3 italic">
            Advisory Notice: Recommendations are computed dynamically using the PyTorch MLP compatibility model. No invitations or team assignments are made automatically.
          </p>
        </div>
      )}

      {/* Skill-Gap Analysis Section (for authenticated student viewer) */}
      {user && (
        <SkillGapView
          data={skillGapData}
          loading={loadingSkillGap}
          error={skillGapError}
          isDemo={false}
          title={isOwner ? "Project Skill Requirement Analysis" : "Your Skill Gap Analysis"}
        />
      )}

      {/* REQUIRED SKILLS SECTION */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <span>Required Technical Skills ({project.required_skills.length})</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Target proficiencies and domain capabilities needed for team positions.
            </p>
          </div>
        </div>

        {/* Add Skill Form (Owner only & non-archived) */}
        {isOwner && project.status !== 'archived' && (
          <form onSubmit={handleAddSkill} className="bg-slate-50 border border-slate-200 rounded-2xl p-4 sm:p-5 space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
              <Plus className="w-4 h-4 text-indigo-600" />
              <span>Add Skill Requirement</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Search & Select Skill */}
              <div className="sm:col-span-2 space-y-1.5">
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search taxonomy skills..."
                    value={skillSearchQuery}
                    onChange={(e) => setSkillSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <select
                  value={selectedSkillId}
                  onChange={(e) => setSelectedSkillId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Choose skill ({unselectedSkills.length} available) --</option>
                  {unselectedSkills.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.category})
                    </option>
                  ))}
                </select>
              </div>

              {/* Proficiency & Submit */}
              <div className="space-y-1.5">
                <select
                  value={requiredProficiency}
                  onChange={(e) => setRequiredProficiency(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value={1}>Level 1: Beginner</option>
                  <option value={2}>Level 2: Intermediate</option>
                  <option value={3}>Level 3: Advanced</option>
                  <option value={4}>Level 4: Expert</option>
                </select>

                <button
                  type="submit"
                  disabled={addingSkill || !selectedSkillId}
                  className="w-full inline-flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs transition-colors disabled:opacity-50"
                >
                  {addingSkill ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>Add Skill</span>
                </button>
              </div>
            </div>
          </form>
        )}

        {/* Required Skills Grid */}
        {project.required_skills.length === 0 ? (
          <div className="py-8 text-center text-slate-500 space-y-1">
            <Award className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="text-sm font-medium text-slate-700">No skills required yet</p>
            <p className="text-xs text-slate-400">Add technical requirements to guide prospective team collaborators.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {project.required_skills.map((s) => {
              const prof = getProficiencyBadge(s.required_proficiency);
              return (
                <div
                  key={s.id}
                  className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between group hover:bg-white transition-all"
                >
                  <div className="space-y-1">
                    <span className="font-semibold text-sm text-slate-900 block">{s.skill_name || 'Skill'}</span>
                    <span className={`inline-block text-[11px] px-2 py-0.5 rounded font-semibold border ${prof.color}`}>
                      {prof.label}
                    </span>
                  </div>

                  {isOwner && project.status !== 'archived' && (
                    <button
                      onClick={() => handleDeleteSkill(s.skill_id)}
                      disabled={deletingSkillId === s.skill_id}
                      title="Remove skill"
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                    >
                      {deletingSkillId === s.skill_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-500" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* TEAM MEMBERS SECTION (PREPARATION) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
        <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
          <Users className="w-5 h-5 text-indigo-600" />
          <span>Team Roster ({project.members.length})</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {project.members.map((member) => (
            <div
              key={member.id}
              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{member.student_name || 'Member'}</p>
                  <p className="text-xs text-slate-400">Joined {new Date(member.joined_at).toLocaleDateString()}</p>
                </div>
              </div>

              <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold capitalize bg-white border border-slate-200 text-slate-700">
                {member.role}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* PHASE 14: PROJECT PROGRESS, TASKS & COLLABORATION FEEDBACK */}
      <ProjectProgressFeedback
        projectId={project.id}
        isOwner={isOwner}
        members={project.members}
        isDemo={project.id.startsWith('00000000-de00')}
      />

      {/* ARCHIVE CONFIRMATION MODAL */}
      {showArchiveConfirm && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Archive className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">Archive this project?</h3>
              <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                Archived projects will no longer be visible to peers in open recruitment. This action does not delete any data and can be reviewed anytime.
              </p>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowArchiveConfirm(false)}
                className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleArchive}
                disabled={archiving}
                className="inline-flex items-center space-x-2 px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm transition-colors disabled:opacity-50"
              >
                {archiving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Archive className="w-4 h-4" />}
                <span>Confirm Archive</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
