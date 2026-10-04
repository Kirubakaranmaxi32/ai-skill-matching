import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getMyInvitations,
  acceptInvitation,
  rejectInvitation,
  cancelInvitation,
} from '../services/api';
import { InvitationResponse, InvitationStatus } from '../types';
import {
  Mail,
  CheckCircle2,
  XCircle,
  Clock,
  MinusCircle,
  AlertCircle,
  Loader2,
  Send,
  Inbox,
  User,
  FolderKanban,
  Check,
  X,
  ArrowRight,
} from 'lucide-react';

export const InvitationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'received' | 'sent'>('received');
  const [statusFilter, setStatusFilter] = useState<InvitationStatus | 'all'>('all');
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Track in-flight action per invitation
  const [processingId, setProcessingId] = useState<string | null>(null);

  const fetchInvitations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyInvitations(
        statusFilter === 'all' ? undefined : statusFilter,
        activeTab
      );
      setInvitations(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load invitations';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, [activeTab, statusFilter]);

  const handleAccept = async (invitationId: string, projectTitle: string) => {
    setProcessingId(invitationId);
    setActionNotice(null);
    try {
      await acceptInvitation(invitationId);
      setActionNotice({
        type: 'success',
        message: `You voluntarily joined "${projectTitle}"! You are now an active team member.`,
      });
      await fetchInvitations();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to accept invitation';
      setActionNotice({ type: 'error', message: msg });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (invitationId: string, projectTitle: string) => {
    setProcessingId(invitationId);
    setActionNotice(null);
    try {
      await rejectInvitation(invitationId);
      setActionNotice({
        type: 'success',
        message: `Declined invitation for "${projectTitle}".`,
      });
      await fetchInvitations();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to decline invitation';
      setActionNotice({ type: 'error', message: msg });
    } finally {
      setProcessingId(null);
    }
  };

  const handleCancel = async (invitationId: string) => {
    setProcessingId(invitationId);
    setActionNotice(null);
    try {
      await cancelInvitation(invitationId);
      setActionNotice({
        type: 'success',
        message: 'Pending invitation was cancelled successfully.',
      });
      await fetchInvitations();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to cancel invitation';
      setActionNotice({ type: 'error', message: msg });
    } finally {
      setProcessingId(null);
    }
  };

  const pendingReceivedCount = invitations.filter(
    (i) => i.status === 'pending'
  ).length;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2.5">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                <Mail className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Team Invitations</h1>
            </div>
            <p className="text-sm text-slate-500 pl-12">
              Voluntary team formation: review invitations from project owners, accept to join collaborative teams, or decline.
            </p>
          </div>

          {/* Quick link to Recommendations */}
          <Link
            to="/recommendations"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-colors self-start sm:self-auto shrink-0"
          >
            <FolderKanban className="w-4 h-4" />
            <span>Find Candidates</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-3 pt-6 border-t border-slate-100 mt-6">
          <button
            type="button"
            onClick={() => setActiveTab('received')}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'received'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Inbox className="w-4 h-4" />
            <span>Received Invitations</span>
            {activeTab === 'received' && pendingReceivedCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-white text-indigo-700 font-extrabold ml-1">
                {pendingReceivedCount}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('sent')}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'sent'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Send className="w-4 h-4" />
            <span>Sent Invitations</span>
          </button>
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-4">
          <span className="text-xs font-semibold text-slate-400 mr-1">Status:</span>
          {(['all', 'pending', 'accepted', 'rejected', 'cancelled'] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-colors ${
                statusFilter === st
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications */}
      {actionNotice && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-sm ${
            actionNotice.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {actionNotice.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span className="font-medium">{actionNotice.message}</span>
          </div>
          <button
            onClick={() => setActionNotice(null)}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="py-16 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-800">Loading invitations...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && invitations.length === 0 && (
        <div className="py-16 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <Mail className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">
            {activeTab === 'received' ? 'No Received Invitations' : 'No Sent Invitations'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {activeTab === 'received'
              ? 'When project owners discover your matching skills and invite you, their invitations will appear here.'
              : 'You have not sent any project team invitations yet. Use the Candidate Recommendation Engine to invite top-matching peers.'}
          </p>
          {activeTab === 'sent' && (
            <Link
              to="/recommendations"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors"
            >
              <FolderKanban className="w-4 h-4" />
              <span>Explore Recommendations</span>
            </Link>
          )}
        </div>
      )}

      {/* Invitations List */}
      {!loading && invitations.length > 0 && (
        <div className="space-y-4">
          {invitations.map((inv) => {
            const isPending = inv.status === 'pending';
            const isAccepted = inv.status === 'accepted';
            const isRejected = inv.status === 'rejected';
            const isCancelled = inv.status === 'cancelled';
            const isProcessing = processingId === inv.id;

            return (
              <div
                key={inv.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-slate-300 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/projects/${inv.project_id}`}
                        className="text-lg font-bold text-slate-900 hover:text-indigo-600 transition-colors"
                      >
                        {inv.project?.title || 'Project Invitation'}
                      </Link>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {inv.project?.status || 'Active'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      <span className="flex items-center space-x-1">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          {activeTab === 'received'
                            ? `Invited by ${inv.inviter?.full_name || 'Project Owner'}`
                            : `Sent to ${inv.invited_student?.full_name || 'Candidate Student'}`}
                        </span>
                      </span>

                      <span>•</span>

                      <span className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          {new Date(inv.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </span>
                      </span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div>
                    {isPending && (
                      <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Pending Response</span>
                      </span>
                    )}
                    {isAccepted && (
                      <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Accepted</span>
                      </span>
                    )}
                    {isRejected && (
                      <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Declined</span>
                      </span>
                    )}
                    {isCancelled && (
                      <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                        <MinusCircle className="w-3.5 h-3.5" />
                        <span>Cancelled</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Project Description Excerpt */}
                {inv.project?.description && (
                  <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                    {inv.project.description}
                  </p>
                )}

                {/* Actions Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  {/* Status Explanatory Text */}
                  <p className="text-[11px] text-slate-400 italic">
                    {activeTab === 'received' && isPending && (
                      <span>Voluntary choice: Accept to join team roster or decline with no penalty.</span>
                    )}
                    {activeTab === 'received' && isAccepted && (
                      <span className="text-emerald-600 font-medium">
                        You voluntarily accepted this invitation and are an active team member.
                      </span>
                    )}
                    {activeTab === 'received' && isRejected && (
                      <span>You declined this project invitation.</span>
                    )}
                    {activeTab === 'sent' && isPending && (
                      <span>Awaiting response from candidate student. You may cancel if needed.</span>
                    )}
                    {activeTab === 'sent' && isAccepted && (
                      <span className="text-emerald-600 font-medium">Candidate accepted and joined your team roster!</span>
                    )}
                    {activeTab === 'sent' && isRejected && (
                      <span>Candidate declined this invitation.</span>
                    )}
                    {isCancelled && <span>Invitation has been withdrawn.</span>}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex items-center space-x-2 self-end sm:self-auto">
                    {/* Received & Pending: Accept or Reject */}
                    {activeTab === 'received' && isPending && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleReject(inv.id, inv.project?.title || 'Project')}
                          disabled={isProcessing}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-semibold disabled:opacity-50 transition-colors"
                        >
                          {isProcessing ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <X className="w-3.5 h-3.5 text-rose-500" />
                          )}
                          <span>Decline</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleAccept(inv.id, inv.project?.title || 'Project')}
                          disabled={isProcessing}
                          className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
                        >
                          {isProcessing ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          <span>Accept & Join Team</span>
                        </button>
                      </>
                    )}

                    {/* Sent & Pending: Cancel */}
                    {activeTab === 'sent' && isPending && (
                      <button
                        type="button"
                        onClick={() => handleCancel(inv.id)}
                        disabled={isProcessing}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-rose-200 hover:bg-rose-50 text-rose-600 text-xs font-semibold disabled:opacity-50 transition-colors"
                      >
                        {isProcessing ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <X className="w-3.5 h-3.5" />
                        )}
                        <span>Cancel Invitation</span>
                      </button>
                    )}

                    {/* View Project button if accepted */}
                    {isAccepted && (
                      <Link
                        to={`/projects/${inv.project_id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors"
                      >
                        <span>View Project</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
