import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyProjects, getProjects } from '../services/api';
import { Project } from '../types';
import {
  FolderPlus,
  FolderKanban,
  Eye,
  Edit3,
  Calendar,
  AlertCircle,
  Loader2,
  Archive,
  Clock,
  CheckCircle2,
  Users,
  Compass,
} from 'lucide-react';

export const ProjectsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'my' | 'joined' | 'discover'>('my');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);
      try {
        let data: Project[] = [];
        if (activeTab === 'my') {
          data = await getMyProjects();
        } else if (activeTab === 'joined') {
          data = await getProjects('joined');
        } else {
          data = await getProjects('discover');
        }
        if (isMounted) {
          setProjects(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load projects';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchProjects();
    return () => {
      isMounted = false;
    };
  }, [activeTab]);

  const getStatusBadge = (status: Project['status']) => {
    switch (status) {
      case 'open':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Open (Recruiting)</span>
          </span>
        );
      case 'in_progress':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Clock className="w-3 h-3" />
            <span>In Progress</span>
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'archived':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-300">
            <Archive className="w-3 h-3" />
            <span>Archived</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="py-20 px-4 max-w-5xl mx-auto text-center space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto" />
        <h2 className="text-xl font-semibold text-slate-800">Loading Projects...</h2>
        <p className="text-sm text-slate-500">Fetching your project portfolio.</p>
      </div>
    );
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 flex items-center space-x-2">
            <FolderKanban className="w-7 h-7 text-indigo-600" />
            <span>Projects</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Create, manage, and specify required skills for your projects.
          </p>
        </div>

        <Link
          to="/projects/new"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm self-start sm:self-auto"
        >
          <FolderPlus className="w-4 h-4" />
          <span>Create Project</span>
        </Link>
      </div>

      {/* Scope Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('my')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center space-x-2 whitespace-nowrap ${
            activeTab === 'my'
              ? 'border-indigo-600 text-indigo-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FolderKanban className="w-4 h-4" />
          <span>My Projects</span>
        </button>
        <button
          onClick={() => setActiveTab('joined')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center space-x-2 whitespace-nowrap ${
            activeTab === 'joined'
              ? 'border-indigo-600 text-indigo-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Teams I Joined</span>
        </button>
        <button
          onClick={() => setActiveTab('discover')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center space-x-2 whitespace-nowrap ${
            activeTab === 'discover'
              ? 'border-indigo-600 text-indigo-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>Explore Projects</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Empty State */}
      {projects.length === 0 && !error ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4 shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
            <FolderKanban className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              {activeTab === 'my'
                ? 'No Projects Found'
                : activeTab === 'joined'
                ? 'No Teams Joined Yet'
                : 'No Open Projects Found'}
            </h3>
            <p className="text-slate-500 text-sm max-w-md mx-auto mt-1">
              {activeTab === 'my'
                ? "You haven't created any projects yet. Start a new project to assemble your dream team and specify the exact skills you need."
                : activeTab === 'joined'
                ? "You are not an active member of any collaborative teams yet. Check your received invitations or explore open projects!"
                : "There are currently no active projects seeking collaborators. Be the first to create one!"}
            </p>
          </div>
          <div className="pt-2">
            {activeTab === 'my' ? (
              <Link
                to="/projects/new"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm"
              >
                <FolderPlus className="w-4 h-4" />
                <span>Create Your First Project</span>
              </Link>
            ) : activeTab === 'joined' ? (
              <Link
                to="/invitations"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm"
              >
                <span>View My Invitations</span>
              </Link>
            ) : (
              <Link
                to="/projects/new"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm"
              >
                <FolderPlus className="w-4 h-4" />
                <span>Create a Project</span>
              </Link>
            )}
          </div>
        </div>
      ) : (
        /* Project Cards List */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              className={`bg-white rounded-2xl border transition-all p-6 flex flex-col justify-between space-y-4 shadow-sm ${
                project.status === 'archived'
                  ? 'border-slate-200 bg-slate-50/50 opacity-90'
                  : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-bold text-lg text-slate-900 line-clamp-1">{project.title}</h3>
                  {getStatusBadge(project.status)}
                </div>

                <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">
                  {project.description}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
                <span className="flex items-center space-x-1.5 text-slate-400">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                </span>

                <div className="flex items-center space-x-2">
                  <Link
                    to={`/projects/${project.id}`}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View</span>
                  </Link>

                  {project.status !== 'archived' && (
                    <Link
                      to={`/projects/${project.id}/edit`}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
