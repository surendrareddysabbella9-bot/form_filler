 import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  FileSearch,
  Cpu,
  Layers,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { api } from '../services/apiClient';

interface Stage {
  id: string;
  label: string;
  description: string;
}

const STAGES: Stage[] = [
  { id: 'template_analysis', label: '1. Template Analysis', description: 'Inspecting form fields, input areas, tables, and constraints' },
  { id: 'document_reading', label: '2. Document Reading', description: 'Parsing digital PDF and Word document text structures' },
  { id: 'ocr_processing', label: '3. OCR Processing', description: 'Running Tesseract image-to-text extraction on scanned pages' },
  { id: 'information_extraction', label: '4. Information Extraction', description: 'Normalizing entities, financial values, and identification tags' },
  { id: 'field_mapping', label: '5. AI Field Mapping', description: 'Groq LLM correlating evidence records with target template fields' },
  { id: 'validation_prep', label: '6. Validation Preparation', description: 'Enforcing deterministic Pydantic rules and conflict detection' },
];

export const ProcessingPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    executePipeline();
  }, [sessionId]);

  const executePipeline = async () => {
    try {
      // Advance stages visually as stages complete
      setCurrentStageIndex(1);
      await new Promise((r) => setTimeout(r, 600));

      setCurrentStageIndex(2);
      await new Promise((r) => setTimeout(r, 600));

      setCurrentStageIndex(3);
      await new Promise((r) => setTimeout(r, 600));

      setCurrentStageIndex(4);
      // Trigger backend end-to-end analysis & AI mapping
      const result: any = await api.post(`/sessions/${sessionId}/analyze`);

      setCurrentStageIndex(5);
      await new Promise((r) => setTimeout(r, 500));

      setCurrentStageIndex(6); // All done
      setIsDone(true);

      // Auto-navigate to form completion workspace
      setTimeout(() => {
        navigate(`/workspace/${sessionId}`);
      }, 900);
    } catch (err: any) {
      console.error('Processing pipeline failed:', err);
      setErrorMsg(err.message || 'Error occurred during document analysis and mapping.');
    }
  };

  const progressPercent = Math.min(100, Math.round((currentStageIndex / STAGES.length) * 100));

  return (
    <div className="max-w-2xl mx-auto py-12 px-4 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto shadow-sm">
          <Sparkles className="w-7 h-7 animate-pulse" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
          {isDone ? 'Analysis Complete!' : 'Analyzing Documents & Mapping Fields'}
        </h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          {isDone
            ? 'Your form fields have been populated. Redirecting to completion workspace...'
            : 'Please hold on while our engine reads your files and correlates information.'}
        </p>
      </div>

      {errorMsg ? (
        <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 space-y-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm">Processing Encountered an Issue</h4>
              <p className="text-xs mt-1 text-rose-700">{errorMsg}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={() => {
                setErrorMsg(null);
                executePipeline();
              }}
              className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors"
            >
              Retry Analysis
            </button>
            <button
              onClick={() => navigate(`/workspace/${sessionId}`)}
              className="px-4 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-colors"
            >
              Continue to Workspace Anyway
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-6">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-slate-600">
              <span>Overall Progress</span>
              <span className="font-bold text-brand-600">{progressPercent}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-600 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Sequential Stages List */}
          <div className="space-y-4 pt-2">
            {STAGES.map((stage, idx) => {
              const isFinished = currentStageIndex > idx;
              const isCurrent = currentStageIndex === idx;

              return (
                <div
                  key={stage.id}
                  className={`flex items-start gap-3.5 p-3 rounded-xl transition-all ${
                    isCurrent
                      ? 'bg-brand-50/60 border border-brand-200/60'
                      : isFinished
                      ? 'opacity-80'
                      : 'opacity-40'
                  }`}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {isFinished ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : isCurrent ? (
                      <div className="w-5 h-5 rounded-full border-2 border-brand-600 border-t-transparent animate-spin" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border border-slate-300" />
                    )}
                  </div>
                  <div>
                    <h4
                      className={`text-sm font-semibold ${
                        isCurrent ? 'text-brand-900' : 'text-slate-800'
                      }`}
                    >
                      {stage.label}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                      {stage.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {isDone && (
            <div className="pt-4 text-center">
              <button
                onClick={() => navigate(`/workspace/${sessionId}`)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition-all"
              >
                <span>Open Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
