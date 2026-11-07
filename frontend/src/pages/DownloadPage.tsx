import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  CheckCircle2,
  Download,
  FileText,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { FormSession } from '../types';
import { api } from '../services/apiClient';

export const DownloadPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<FormSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewMode, setPreviewMode] = useState<'image' | 'pdf'>('image');
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [pageCount, setPageCount] = useState<number>(2);

  useEffect(() => {
    if (sessionId) {
      loadSession();
      loadPageCount();
    }
  }, [sessionId]);

  const loadSession = async () => {
    try {
      const data: any = await api.get(`/sessions/${sessionId}`);
      setSession(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadPageCount = async () => {
    try {
      const res: any = await api.get(`/sessions/${sessionId}/page-count`);
      if (res && res.page_count) {
        setPageCount(res.page_count);
      }
    } catch {
      setPageCount(2);
    }
  };

  const downloadUrl = `${api.getBaseUrl()}/sessions/${sessionId}/download`;
  const previewUrl = `${api.getBaseUrl()}/sessions/${sessionId}/preview`;
  const pageImageUrl = `${api.getBaseUrl()}/sessions/${sessionId}/page-image/${currentPage}`;

  return (
    <div className="max-w-2xl mx-auto py-12 px-4 space-y-8 text-center">
      <div className="w-16 h-16 rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto shadow-sm">
        <CheckCircle2 className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Your form is ready!</h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Your document has been populated with validated details while preserving the original template's structure.
        </p>
      </div>

      {/* Document Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs text-left space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div className="truncate">
            <h4 className="text-sm font-semibold text-slate-900 truncate">
              {session?.generated_document_path
                ? session.generated_document_path.split(/[\\/]/).pop()
                : `${session?.title || 'Completed_Form'}.pdf`}
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Completed on {new Date().toLocaleDateString()} • Verified Lineage
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center gap-3">
          <a
            href={downloadUrl}
            download
            className="w-full sm:flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Download Completed Form</span>
          </a>
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Open PDF in New Tab</span>
          </a>
        </div>
      </div>

      {/* Embedded Live Preview of Completed Document */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden text-left">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-800">Document Live Preview</span>
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 shadow-2xs transition-colors cursor-pointer"
          >
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
            <span>Open in Tab</span>
          </a>
        </div>

        <div className="h-[650px] w-full bg-slate-100 p-2 flex flex-col">
          <iframe
            src={previewUrl}
            className="w-full h-full border border-slate-200/90 rounded-xl bg-white shadow-xs"
            title="Completed Document Preview"
          />
        </div>
      </div>

      {/* Safety Notice & Guest Session Retention Alert */}
      <div className="space-y-2">
        <div className="p-4 rounded-xl bg-slate-100/70 text-slate-500 text-xs text-left flex items-start gap-3">
          <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-700">Template Preservation Guarantee:</span>{' '}
            Your original uploaded template remains unaltered. The completed document was generated as a separate output file.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200/80 text-amber-900 text-xs text-left flex items-start gap-3">
          <CheckCircle2 className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-950">Temporary Guest Session Notice:</span>{' '}
            Completed documents and uploaded files are temporary and will be permanently purged when your session expires or when manually deleted. Please download your files to your local device now.
          </div>
        </div>
      </div>

      {/* Navigation shortcuts */}
      <div className="flex items-center justify-center gap-4 pt-4">
        <Link
          to="/dashboard"
          className="text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          Return to Dashboard
        </Link>
        <span className="text-slate-300">•</span>
        <Link
          to="/new-form"
          className="text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors"
        >
          Fill Another Form
        </Link>
      </div>
    </div>
  );
};
