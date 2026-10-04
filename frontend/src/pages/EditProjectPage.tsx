import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getProjectById, updateProject } from '../services/api';
import { ProjectStatus } from '../types';
import { Edit3, ArrowLeft, Loader2, AlertCircle, Save } from 'lucide-react';

export const EditProjectPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<ProjectStatus>('open');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unauthorized, setUnauthorized] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchProject = async () => {
      if (!projectId) return;
      setLoading(true);
      setError(null);
      try {
        const data = await getProjectById(projectId);
        if (!isMounted) return;

        // Check ownership
        if (user && data.owner?.user_id !== user.id) {
          setUnauthorized(true);
          return;
        }

        setTitle(data.title);
        setDescription(data.description);
        setStatus(data.status);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Failed to load project details';
        setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchProject();
    return () => {
      isMounted = false;
    };
  }, [projectId, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId) return;

    const trimmedTitle = title.trim();
    const trimmedDesc = description.trim();

    if (!trimmedTitle) {
      setError('Project title is required.');
      return;
    }

    if (trimmedTitle.length > 150) {
      setError('Project title cannot exceed 150 characters.');
      return;
    }

    if (!trimmedDesc) {
      setError('Project description is required.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await updateProject(projectId, {
        title: trimmedTitle,
        description: trimmedDesc,
        status,
      });

      navigate(`/projects/${projectId}`, {
        state: { message: 'Project updated successfully!' },
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update project.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 px-4 max-w-3xl mx-auto text-center space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto" />
        <h2 className="text-xl font-semibold text-slate-800">Loading Project...</h2>
      </div>
    );
  }

  if (unauthorized) {
    return (
      <div className="py-16 px-4 max-w-xl mx-auto text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Unauthorized Access</h2>
        <p className="text-sm text-slate-500">
          You do not have permission to edit this project. Only the project owner can modify project details.
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
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          to={`/projects/${projectId}`}
          className="inline-flex items-center space-x-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Project Details</span>
        </Link>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 flex items-center space-x-2">
          <Edit3 className="w-7 h-7 text-indigo-600" />
          <span>Edit Project</span>
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Update project specifications, status, and requirements.
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="title" className="block text-sm font-semibold text-slate-800">
                Project Title <span className="text-rose-500">*</span>
              </label>
              <span className={`text-xs ${title.length > 140 ? 'text-amber-600 font-bold' : 'text-slate-400'}`}>
                {title.length}/150
              </span>
            </div>
            <input
              id="title"
              type="text"
              required
              maxLength={150}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-semibold text-slate-800 mb-1">
              Project Description <span className="text-rose-500">*</span>
            </label>
            <textarea
              id="description"
              required
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm leading-relaxed"
            />
          </div>

          {/* Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-semibold text-slate-800 mb-1">
              Project Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as ProjectStatus)}
              className="w-full sm:w-64 px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white"
            >
              <option value="open">Open (Recruiting)</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
            <Link
              to={`/projects/${projectId}`}
              className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
