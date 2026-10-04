import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createProject } from '../services/api';
import { FolderPlus, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';

export const CreateProjectPage: React.FC = () => {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<'open' | 'in_progress' | 'completed'>('open');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

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

    setSubmitting(true);
    try {
      const created = await createProject({
        title: trimmedTitle,
        description: trimmedDesc,
        status,
      });

      navigate(`/projects/${created.id}`, {
        state: { message: 'Project created successfully! You can now specify required skills.' },
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create project. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          to="/projects"
          className="inline-flex items-center space-x-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </Link>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 flex items-center space-x-2">
          <FolderPlus className="w-7 h-7 text-indigo-600" />
          <span>Create New Project</span>
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Specify your project ideation, team goals, and recruitment requirements.
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
          {/* Project Title */}
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
              placeholder="e.g., Autonomous Drone Path Planner"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          {/* Project Description */}
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
              placeholder="Describe the problem, target objectives, technical architecture, and team roles needed..."
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm leading-relaxed"
            />
          </div>

          {/* Initial Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-semibold text-slate-800 mb-1">
              Initial Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as 'open' | 'in_progress' | 'completed')}
              className="w-full sm:w-64 px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white"
            >
              <option value="open">Open (Actively Recruiting)</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
            <p className="text-xs text-slate-400 mt-1">
              "Open" projects are prominently displayed in the project feed for peer recruitment.
            </p>
          </div>

          {/* Submit & Cancel */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
            <Link
              to="/projects"
              className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating Project...</span>
                </>
              ) : (
                <>
                  <FolderPlus className="w-4 h-4" />
                  <span>Create Project</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
