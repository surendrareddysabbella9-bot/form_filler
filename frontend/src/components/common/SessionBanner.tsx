import React, { useState, useEffect } from 'react';
import { ShieldAlert, Trash2, Clock, Info, CheckCircle2, AlertTriangle, X } from 'lucide-react';
import { api } from '../../services/apiClient';

interface SessionData {
  session_id: string;
  is_active: boolean;
  remaining_idle_seconds: number;
  remaining_lifetime_seconds: number;
  active_forms_count: number;
  active_documents_count: number;
  policy: {
    mode: string;
    permanent_storage: boolean;
    idle_timeout_hours: number;
    max_lifetime_hours: number;
    summary: string;
    ai_notice: string;
  };
}

export const SessionBanner: React.FC = () => {
  const [session, setSession] = useState<SessionData | null>(null);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchSessionInfo();
    const interval = setInterval(fetchSessionInfo, 60000); // Poll status every minute
    return () => clearInterval(interval);
  }, []);

  const fetchSessionInfo = async () => {
    try {
      const data = await api.get<SessionData>('/guest/session');
      setSession(data);
    } catch {
      // Quiet fail if backend is restarting
    }
  };

  const handleDeleteSession = async () => {
    try {
      setIsDeleting(true);
      await api.delete('/guest/session');
      api.clearLocalSession();
      window.location.href = '/';
    } catch (err) {
      console.error('Failed to delete session:', err);
      setIsDeleting(false);
      setShowConfirmDelete(false);
    }
  };

  const formatRemainingMinutes = (seconds?: number) => {
    if (!seconds || seconds <= 0) return 'Expiring';
    const mins = Math.floor(seconds / 60);
    if (mins < 60) return `${mins}m idle`;
    const hours = (mins / 60).toFixed(1);
    return `${hours}h idle`;
  };

  return (
    <>
      {/* Session Top Bar Pill */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowPolicyModal(true)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-200/80 hover:bg-emerald-100 transition-colors cursor-pointer"
          title="Click to view temporary session security policy"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold">Guest Session</span>
          <span className="text-emerald-600 hidden md:inline">({formatRemainingMinutes(session?.remaining_idle_seconds)})</span>
          <Info className="w-3.5 h-3.5 text-emerald-600 ml-0.5" />
        </button>

        <button
          onClick={() => setShowConfirmDelete(true)}
          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
          title="Clear session and delete all temporary files immediately"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Policy Details Modal */}
      {showPolicyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Temporary Session & Privacy Policy</h3>
                  <span className="text-xs text-slate-500">Privacy by default • Temporary processing by design</span>
                </div>
              </div>
              <button
                onClick={() => setShowPolicyModal(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-5 space-y-3.5 text-xs text-slate-600 leading-relaxed">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                <div className="font-semibold text-slate-900 mb-1 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-brand-600" />
                  <span>Session Expiration & Auto-Cleanup</span>
                </div>
                Your temporary session expires after <strong>1 hour of inactivity</strong> or <strong>24 hours maximum</strong>. Upon expiration, all uploaded documents, templates, extracted OCR values, and signatures are automatically purged from the server.
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                <div className="font-semibold text-slate-900 mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>No Permanent User Workspaces</span>
                </div>
                This MVP operates entirely through temporary private guest sessions. We do not maintain user databases, persistent profiles, or cloud history. Download your completed forms to your local device.
              </div>

              <div className="p-3 bg-amber-50/70 rounded-xl border border-amber-200/70 text-amber-900">
                <div className="font-semibold mb-1 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-amber-700" />
                  <span>Third-Party AI Inference Notice</span>
                </div>
                Document field extractions and AI mapping are processed via the Groq cloud inference engine. Third-party inference is governed by standard external provider retention and confidentiality policies.
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between gap-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => {
                  setShowPolicyModal(false);
                  setShowConfirmDelete(true);
                }}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-rose-600 hover:text-rose-700"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Session Now</span>
              </button>
              <button
                onClick={() => setShowPolicyModal(false)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800 transition-colors"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Delete Session Confirmation Modal */}
      {showConfirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-slate-200">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <h3 className="text-lg font-bold text-slate-900">Delete Current Guest Session?</h3>
            <p className="mt-2 text-xs text-slate-600 leading-relaxed">
              This will immediately and permanently erase all uploaded templates, supporting documents, OCR extractions, digital signatures, and filled documents on this server. This action cannot be undone.
            </p>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowConfirmDelete(false)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteSession}
                disabled={isDeleting}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-xs"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isDeleting ? 'Deleting...' : 'Permanently Delete Session'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
