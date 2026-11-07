import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PlusCircle,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';
import { FormSession } from '../types';
import { api } from '../services/apiClient';

export const DashboardPage: React.FC = () => {
  const [sessions, setSessions] = useState<FormSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const data = await api.get<FormSession[]>('/sessions');
      setSessions(data);
    } catch (err) {
      console.warn('Could not load sessions from backend, using empty list:', err);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const totalForms = sessions.length;
  const completedForms = sessions.filter((s) => s.status === 'completed').length;
  const inProgressForms = sessions.filter(
    (s) => s.status === 'in_progress' || s.status === 'processing'
  ).length;
  const awaitingReviewForms = sessions.filter((s) => s.status === 'awaiting_review').length;

  return (
    <div className="space-y-8">
      {/* Welcome & Primary Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-brand-900 via-brand-800 to-slate-900 p-8 rounded-2xl text-white shadow-sm relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 text-brand-200 text-xs font-medium mb-3 backdrop-blur-xs">
            <Sparkles className="w-3.5 h-3.5 text-brand-300" />
            <span>Private Guest Session Active</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Temporary Form Workspace</h2>
          <p className="text-brand-100 text-sm mt-1 max-w-lg">
            Upload forms, extract details with AI and OCR, customize typography, apply digital signatures, and download your finished documents.
          </p>
        </div>

        <div className="relative z-10 flex-shrink-0">
          <Link
            to="/new-form"
            className="inline-flex items-center gap-2 px-5 py-3 text-sm font-semibold text-slate-900 bg-white hover:bg-brand-50 rounded-xl shadow transition-all hover:shadow-md"
          >
            <PlusCircle className="w-4 h-4 text-brand-600" />
            <span>Create New Form</span>
          </Link>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-brand-500/20 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Forms"
          value={totalForms}
          subtitle="All created sessions"
          icon={FileText}
          variant="default"
        />
        <StatCard
          title="Completed Forms"
          value={completedForms}
          subtitle="Ready & downloaded"
          icon={CheckCircle2}
          variant="success"
        />
        <StatCard
          title="In Progress"
          value={inProgressForms}
          subtitle="Mapping & chat active"
          icon={Clock}
          variant="info"
        />
        <StatCard
          title="Awaiting Review"
          value={awaitingReviewForms}
          subtitle="Requires user confirmation"
          icon={AlertTriangle}
          variant="warning"
        />
      </div>

      {/* Recent Forms Section */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Recent Forms</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Forms currently in progress or completed
            </p>
          </div>
          {sessions.length > 0 && (
            <Link
              to="/forms"
              className="text-xs font-medium text-brand-600 hover:text-brand-700 inline-flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {loading ? (
          <div className="p-12 text-center text-sm text-slate-400">Loading forms...</div>
        ) : sessions.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={FileText}
              title="You haven't created any forms yet"
              description="Upload your first form template along with supporting documents, and let the AI assistant handle the rest."
              actionLabel="Create Your First Form"
              onAction={() => {
                window.location.href = '/new-form';
              }}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-3.5">Form Title</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Completion</th>
                  <th className="px-6 py-3.5">Last Updated</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sessions.slice(0, 5).map((session) => (
                  <tr key={session.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{session.title}</div>
                      <div className="text-xs text-slate-400">ID: {session.id.slice(0, 8)}...</div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge
                        status={
                          session.status === 'completed'
                            ? 'confirmed'
                            : session.status === 'awaiting_review'
                            ? 'needs_review'
                            : 'extracted'
                        }
                        size="sm"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="w-36">
                        <div className="flex items-center justify-between text-xs font-medium text-slate-600 mb-1">
                          <span>{Math.round(session.completion_percentage)}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-brand-500 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(100, session.completion_percentage)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(session.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={
                          session.status === 'completed'
                            ? `/download/${session.id}`
                            : session.status === 'awaiting_review'
                            ? `/review/${session.id}`
                            : `/workspace/${session.id}`
                        }
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-brand-600 hover:text-brand-800 hover:bg-brand-50 rounded-lg transition-colors"
                      >
                        <span>Open</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
