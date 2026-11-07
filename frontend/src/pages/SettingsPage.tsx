import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Shield,
  FileCheck2,
  Database,
  CheckCircle2,
  Info,
  Server,
} from 'lucide-react';
import { api } from '../services/apiClient';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    loadHealth();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await api.get('/health');
      setHealth(data);
    } catch (err) {
      console.warn('Could not load health:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Settings & System Info</h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Configure application preferences, data privacy parameters, and check AI provider status.
        </p>
      </div>

      {/* AI Provider & Engine Status */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">AI Provider & OCR Engine</h3>
            <p className="text-xs text-slate-500">Active intelligence orchestration status</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-1">
            <div className="text-xs font-semibold text-slate-500">Active AI Engine</div>
            <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <span>{health?.ai_provider || 'Groq API / Mock Engine'}</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-[11px] text-slate-400">
              Cloud LLM for semantic mapping & natural language clarification.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-1">
            <div className="text-xs font-semibold text-slate-500">Local OCR Engine</div>
            <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <span>Tesseract OCR + OpenCV</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-[11px] text-slate-400">
              Preprocesses images and extracts text locally without paid vision APIs.
            </p>
          </div>
        </div>
      </div>

      {/* Privacy and Data Retention */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Privacy & Temporary Guest Sessions</h3>
            <p className="text-xs text-slate-500">Privacy by default • Temporary processing by design</p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-600 leading-relaxed pt-1">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>No Permanent Workspaces:</strong> This MVP operates entirely through temporary private guest sessions. No user accounts, registration, passwords, or permanent user tracking exist in this version.
            </span>
          </div>
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Automated Session Expiration:</strong> All temporary files, uploaded documents, OCR bounding boxes, digital signatures, and filled forms automatically expire after <strong>1 hour of inactivity</strong> or <strong>24 hours maximum</strong>.
            </span>
          </div>
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Instant Manual Deletion:</strong> You can purge your entire session and all associated data at any time via the session badge in the navigation bar.
            </span>
          </div>
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>External AI Notice:</strong> Document field mapping is assisted by the Groq cloud inference engine, subject to standard cloud inference terms.
            </span>
          </div>
        </div>
      </div>

      {/* Database & Architecture */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Data Persistence Layer</h3>
            <p className="text-xs text-slate-500">PostgreSQL with automated local SQLite fallback</p>
          </div>
        </div>

        <p className="text-xs text-slate-500 leading-relaxed">
          The application uses PostgreSQL with SQLAlchemy ORM. If PostgreSQL connection credentials are not supplied in <code>.env</code>, it seamlessly initializes SQLite locally so testing is zero-friction.
        </p>
      </div>

      {/* System Information */}
      <div className="p-4 rounded-xl bg-slate-100/70 border border-slate-200/60 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-slate-400" />
          <span>Intelligent Form Filler v1.0.0 • Python 3.12 + FastAPI + React + TypeScript</span>
        </div>
        <span className="font-mono text-slate-400">Environment: Development</span>
      </div>
    </div>
  );
};
