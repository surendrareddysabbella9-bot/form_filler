import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Upload,
  Cpu,
  FileCheck2,
  ShieldCheck,
  CheckCircle2,
  FileText,
  User,
  Clock,
} from 'lucide-react';
import { LoginModal } from '../components/common/LoginModal';

export const LandingPage: React.FC = () => {
  const [showLoginModal, setShowLoginModal] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Navigation Header */}
      <header className="h-20 border-b border-slate-200/60 bg-white/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-500 flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-tight text-base">
                Intelligent Form Filler
              </span>
              <span className="block text-[11px] text-slate-500 font-medium">
                AI Document Understanding & Auto-Completion
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <Link
              to="/dashboard"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors hidden sm:inline-block"
            >
              Dashboard
            </Link>

            {/* Visible Login Button in Header */}
            <button
              type="button"
              onClick={() => setShowLoginModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            >
              <User className="w-4 h-4 text-slate-500" />
              <span>Login</span>
            </button>

            <Link
              to="/new-form"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-sm transition-colors"
            >
              <span>Start Filling a Form</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-16 px-6 text-center max-w-4xl mx-auto flex-1 flex flex-col justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-50 border border-brand-200/70 text-brand-700 text-xs font-semibold mx-auto mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Universal Form-Filling Engine for Any Structured Document</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
          Complete Forms Without the <span className="text-brand-600">Manual Work</span>.
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Upload your form and supporting documents. Our intelligent assistant extracts information,
          identifies missing details, and helps you complete your form with verified source lineage.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/new-form"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-base font-medium text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm transition-all hover:shadow"
          >
            <span>Start Filling a Form</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 text-base font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-colors"
          >
            How It Works
          </a>
        </div>

        {/* Feature Badges */}
        <div className="mt-14 pt-8 border-t border-slate-200/60 flex flex-wrap items-center justify-center gap-y-3 gap-x-8 text-xs font-medium text-slate-500">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            PDF, DOCX & Image Forms (PNG/JPG)
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            Temporary Private Guest Sessions
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            Tesseract Local OCR & Coordinates
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            Digital Signatures & Custom Ink
          </span>
        </div>
      </section>

      {/* 3-Step "How It Works" Section */}
      <section id="how-it-works" className="py-16 bg-white border-t border-slate-200/80">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Three Simple Steps
            </h2>
            <p className="text-slate-500 text-sm mt-2">
              From raw documents to finalized submissions in minutes — no account required.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all">
              <div className="w-12 h-12 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center font-bold text-lg mb-5">
                1
              </div>
              <h3 className="text-base font-semibold text-slate-900">Upload Your Form</h3>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                Provide a blank PDF, DOCX, or scanned image form. The engine detects fields, bounding boxes, and coordinates.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all">
              <div className="w-12 h-12 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center font-bold text-lg mb-5">
                2
              </div>
              <h3 className="text-base font-semibold text-slate-900">Add Supporting Documents</h3>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                Upload IDs, pay stubs, certificates, or statements. The engine reads digital text and runs local OCR on scans.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all">
              <div className="w-12 h-12 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center font-bold text-lg mb-5">
                3
              </div>
              <h3 className="text-base font-semibold text-slate-900">Customize, Sign & Download</h3>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                Select custom font typography and ink color, apply your digital signature, and download your completed form locally.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-slate-200 text-center text-xs text-slate-400">
        <p>© 2026 Intelligent Form Filler. Private Guest Processing • No Permanent User Workspaces.</p>
      </footer>

      {/* Login Under Construction Modal */}
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </div>
  );
};
