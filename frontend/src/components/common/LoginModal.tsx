import React from 'react';
import { Lock, Construction, ArrowLeft, ShieldCheck, Sparkles, X } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden transform transition-all"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-headline"
      >
        {/* Top Decorative Banner */}
        <div className="bg-gradient-to-r from-amber-500 via-brand-600 to-indigo-600 h-2 w-full" />

        <div className="p-6 sm:p-8">
          {/* Header & Icon */}
          <div className="flex items-start justify-between">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200/80 flex items-center justify-center text-amber-600 shadow-xs">
              <Construction className="w-6 h-6" />
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mt-5">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Preview Roadmap</span>
            </div>
            <h3 id="modal-headline" className="text-xl font-bold text-slate-900 tracking-tight">
              Login — Under Construction
            </h3>
            <p className="mt-3 text-sm text-slate-600 leading-relaxed">
              User accounts and saved workspaces are coming soon. For now, you can use the application through a temporary private session without creating an account.
            </p>
          </div>

          {/* Guest Session Privacy Pill */}
          <div className="mt-5 p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-600 leading-relaxed">
              <span className="font-semibold text-slate-800">Private Guest Session Active:</span> Complete access to all features (PDF/DOCX/image form filling, AI mapping, OCR, signatures, and document downloads) is immediately available right now.
            </div>
          </div>

          {/* Action Button */}
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Application</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
