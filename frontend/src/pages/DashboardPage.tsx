import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMyProjects, getMyInvitations, getStudentSkills } from '../services/api';
import { LayoutDashboard, User, FolderPlus, Sparkles, Mail, CheckCircle2, LogOut, FolderKanban } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [projectCount, setProjectCount] = useState<number | null>(null);
  const [pendingInvitesCount, setPendingInvitesCount] = useState<number | null>(null);
  const [skillCount, setSkillCount] = useState<number | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchCounts = async () => {
      try {
        const [projs, invites, skills] = await Promise.allSettled([
          getMyProjects(),
          getMyInvitations('pending', 'received'),
          getStudentSkills(),
        ]);
        if (isMounted) {
          if (projs.status === 'fulfilled') setProjectCount(projs.value.length);
          if (invites.status === 'fulfilled') setPendingInvitesCount(invites.value.length);
          if (skills.status === 'fulfilled') setSkillCount(skills.value.length);
        }
      } catch {
        // Fallback gracefully
      }
    };

    fetchCounts();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 flex items-center space-x-2">
            <LayoutDashboard className="w-7 h-7 text-indigo-600" />
            <span>Student Dashboard</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Logged in as <strong className="text-slate-800">{user?.email || 'Authenticated Student'}</strong>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/profile"
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-sm"
          >
            <User className="w-3.5 h-3.5" />
            <span>My Profile</span>
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition-colors"
          >
            <FolderPlus className="w-3.5 h-3.5" />
            <span>Projects</span>
          </Link>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Active Session
          </span>
          <button
            onClick={() => logout()}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Link
          to="/profile"
          className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-indigo-300 shadow-sm flex items-center justify-between group transition-all"
        >
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <User className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Student Profile</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">
                {skillCount !== null ? `${skillCount} Skills Defined` : 'Manage Skills & Bio'}
              </p>
              <p className="text-xs text-indigo-600 font-medium">Configure profile &rarr;</p>
            </div>
          </div>
        </Link>

        <Link
          to="/projects"
          className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-300 shadow-sm flex items-center justify-between group transition-all"
        >
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <FolderKanban className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">My Projects</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">
                {projectCount !== null ? `${projectCount} Active Projects` : 'Manage & Create'}
              </p>
              <p className="text-xs text-blue-600 font-medium">View projects &rarr;</p>
            </div>
          </div>
        </Link>

        <Link
          to="/recommendations"
          className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-purple-300 shadow-sm flex items-center justify-between group transition-all"
        >
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">AI Recommendations</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">PyTorch MLP</p>
              <p className="text-xs text-purple-600 font-medium">Find team matches &rarr;</p>
            </div>
          </div>
        </Link>

        <Link
          to="/invitations"
          className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-amber-300 shadow-sm flex items-center justify-between group transition-all"
        >
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Team Invitations</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">
                {pendingInvitesCount !== null ? `${pendingInvitesCount} Pending` : 'Voluntary Teams'}
              </p>
              <p className="text-xs text-amber-600 font-medium">View invitations &rarr;</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Main Action Box */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-5 shadow-sm">
        <div className="w-16 h-16 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
          <Sparkles className="w-8 h-8" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900">AI Skill Matching & Team Formation</h3>
          <p className="text-slate-600 max-w-xl mx-auto text-sm leading-relaxed mt-2">
            Configure your technical skills and domain proficiencies, discover collaborative projects, review AI compatibility scores, and assemble complementary project teams.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <Link
            to="/profile"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm"
          >
            <User className="w-4 h-4" />
            <span>Profile & Skills</span>
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-50 text-indigo-700 font-medium text-sm hover:bg-indigo-100 transition-colors"
          >
            <FolderKanban className="w-4 h-4" />
            <span>Explore Projects</span>
          </Link>
          <Link
            to="/recommendations"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-50 text-purple-700 font-medium text-sm hover:bg-purple-100 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Recommendations</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
