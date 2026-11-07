import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Search, PlusCircle, ArrowRight, Clock, CheckCircle2 } from 'lucide-react';
import { FormSession } from '../types';
import { api } from '../services/apiClient';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';

export const MyFormsPage: React.FC = () => {
  const [sessions, setSessions] = useState<FormSession[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const data: any = await api.get('/sessions');
      setSessions(data);
    } catch (err) {
      console.warn('Could not load sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = sessions.filter((s) => {
    const matchesSearch = s.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' ? true : s.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Active Forms (Session)</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            View all form completion sessions active in your current temporary private guest session.
          </p>
        </div>
        <Link
          to="/new-form"
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-xs transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Form</span>
        </Link>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search forms by title..."
            className="w-full pl-10 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-white rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 focus:outline-none"
        >
          <option value="all">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="awaiting_review">Awaiting Review</option>
          <option value="in_progress">In Progress</option>
          <option value="draft">Draft</option>
        </select>
      </div>

      {/* Forms Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-sm text-slate-400">Loading forms...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={FileText}
              title="No forms found"
              description="Start a new form filling session by uploading your template."
              actionLabel="Create New Form"
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
                  <th className="px-6 py-3.5">Title</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Progress</th>
                  <th className="px-6 py-3.5">Last Updated</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{s.title}</div>
                      <div className="text-xs text-slate-400 font-mono">ID: {s.id.slice(0, 8)}...</div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge
                        status={
                          s.status === 'completed'
                            ? 'confirmed'
                            : s.status === 'awaiting_review'
                            ? 'needs_review'
                            : 'extracted'
                        }
                        size="sm"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="w-32">
                        <div className="text-xs font-semibold text-slate-700 mb-1">
                          {Math.round(s.completion_percentage)}%
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-brand-500 rounded-full"
                            style={{ width: `${Math.min(100, s.completion_percentage)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(s.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={
                          s.status === 'completed'
                            ? `/download/${s.id}`
                            : s.status === 'awaiting_review'
                            ? `/review/${s.id}`
                            : `/workspace/${s.id}`
                        }
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-brand-600 hover:text-brand-800 hover:bg-brand-50 rounded-lg transition-colors"
                      >
                        <span>Resume</span>
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
