import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  FileText,
  ArrowRight,
  Sparkles,
  Edit2,
  Check,
  ChevronLeft,
  XCircle,
  PenTool,
  Palette,
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { FormSession, FormFieldState } from '../types';
import { api } from '../services/apiClient';
import { StyleCustomizer, StyleValues } from '../components/common/StyleCustomizer';
import { DigitalSignatureModal } from '../components/common/DigitalSignatureModal';

export const ReviewPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<FormSession | null>(null);
  const [fields, setFields] = useState<FormFieldState[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [format, setFormat] = useState<'pdf' | 'docx'>('pdf');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Styling & Digital Signature state
  const [stylePreferences, setStylePreferences] = useState<StyleValues>({
    font_family: 'helvetica',
    font_size: 10,
    text_color: '#0f172a',
  });
  const [showSignatureModal, setShowSignatureModal] = useState<boolean>(false);
  const [signaturePath, setSignaturePath] = useState<string | null>(null);

  // Quick edit state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editVal, setEditVal] = useState<string>('');

  useEffect(() => {
    if (sessionId) {
      loadData();
    }
  }, [sessionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data: any = await api.get(`/sessions/${sessionId}`);
      setSession(data);
      if (data.fields) {
        setFields(data.fields);
        if (data.template?.file_type?.includes('docx')) {
          setFormat('docx');
        }
      }
      if (data.signature_path) {
        setSignaturePath(data.signature_path);
      }
      if (data.style_preferences) {
        setStylePreferences({
          font_family: data.style_preferences.font_family || 'helvetica',
          font_size: data.style_preferences.font_size || 10,
          text_color: data.style_preferences.text_color || '#0f172a',
        });
      }
    } catch (err) {
      console.error('Failed to load session for review:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStyleChange = async (newStyles: StyleValues) => {
    setStylePreferences(newStyles);
    try {
      await api.patch(`/sessions/${sessionId}/style`, newStyles);
    } catch (err) {
      console.error('Failed to update style preferences:', err);
    }
  };

  const handleSignatureUpdated = (newSig: string | null) => {
    setSignaturePath(newSig);
    loadData();
  };

  const handleConfirm = async (fieldId: string) => {
    const f = fields.find((item) => item.field_id === fieldId);
    if (!f) return;
    try {
      const updated: any = await api.patch(`/sessions/${sessionId}/fields/${fieldId}`, {
        current_value: f.current_value,
        confirm: true,
      });
      setFields((prev) => prev.map((item) => (item.field_id === fieldId ? { ...item, ...updated } : item)));
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveEdit = async (fieldId: string) => {
    try {
      const updated: any = await api.patch(`/sessions/${sessionId}/fields/${fieldId}`, {
        current_value: editVal,
        confirm: true,
      });
      setFields((prev) => prev.map((item) => (item.field_id === fieldId ? { ...item, ...updated } : item)));
      setEditingFieldId(null);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setErrorMsg(null);
      await api.post(`/sessions/${sessionId}/generate`, {
        format,
        font_family: stylePreferences.font_family,
        font_size: stylePreferences.font_size,
        text_color: stylePreferences.text_color,
      });
      navigate(`/download/${sessionId}`);
    } catch (err: any) {
      console.error('Generation failed:', err);
      setErrorMsg(err.message || 'Generation failed. Please ensure all mandatory fields are valid.');
    } finally {
      setGenerating(false);
    }
  };

  const totalFields = fields.length;
  const confirmedCount = fields.filter((f) => f.confirmation_status === 'confirmed').length;
  const missingMandatoryCount = fields.filter(
    (f) => f.required && (!f.current_value || f.validation_status === 'missing')
  ).length;
  const conflictCount = fields.filter((f) => f.validation_status === 'conflicting').length;
  const invalidCount = fields.filter((f) => f.validation_status === 'invalid').length;

  const canGenerate = missingMandatoryCount === 0 && invalidCount === 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to={`/workspace/${sessionId}`}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 mb-2 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Back to Completion Workspace</span>
          </Link>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Review & Validation</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Confirm all extracted information before generating your final completed document.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as 'pdf' | 'docx')}
            className="px-3 py-2 bg-white rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 focus:outline-none"
          >
            <option value="pdf">Export as PDF (.pdf)</option>
            <option value="docx">Export as Word (.docx)</option>
          </select>

          <button
            onClick={handleGenerate}
            disabled={!canGenerate || generating}
            className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition-all ${
              !canGenerate || generating
                ? 'bg-slate-300 cursor-not-allowed'
                : 'bg-brand-600 hover:bg-brand-700 hover:shadow-md'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>{generating ? 'Generating Document...' : 'Generate Completed Form'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Validation Summary Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <StatCard title="Total Fields" value={totalFields} icon={FileText} variant="default" />
        <StatCard title="Confirmed" value={confirmedCount} icon={CheckCircle2} variant="success" />
        <StatCard
          title="Missing Required"
          value={missingMandatoryCount}
          icon={AlertCircle}
          variant={missingMandatoryCount > 0 ? 'warning' : 'default'}
        />
        <StatCard
          title="Conflicts"
          value={conflictCount}
          icon={AlertTriangle}
          variant={conflictCount > 0 ? 'warning' : 'default'}
        />
        <StatCard
          title="Invalid Formats"
          value={invalidCount}
          icon={XCircle}
          variant={invalidCount > 0 ? 'warning' : 'default'}
        />
      </div>

      {/* Validation Requirement Warning if blocked */}
      {!canGenerate && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              Mandatory fields are still missing or have formatting errors. Please complete and validate them below before final generation.
            </span>
          </div>
        </div>
      )}

      {/* Document Customization & Digital Signature Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <StyleCustomizer values={stylePreferences} onChange={handleStyleChange} />
        </div>

        {/* Digital Signature Review Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                  <PenTool className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Digital Signature
                </h4>
              </div>
              {signaturePath && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  <span>Applied</span>
                </span>
              )}
            </div>

            <p className="text-xs text-slate-500 leading-relaxed mb-4">
              Your signature is embedded directly onto the completed document along with an audit verification certificate stamp.
            </p>

            <div className="p-3 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 text-center mb-3">
              {signaturePath ? (
                <div className="text-xs text-emerald-700 font-semibold flex items-center justify-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Legal signature is ready for embedding</span>
                </div>
              ) : (
                <span className="text-xs text-slate-400 italic">No signature attached yet (optional)</span>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowSignatureModal(true)}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xs transition-colors cursor-pointer"
          >
            <PenTool className="w-3.5 h-3.5" />
            <span>{signaturePath ? 'Modify / Change Signature' : 'Add Digital Signature'}</span>
          </button>
        </div>
      </div>

      {/* Fields Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Form Verification Checklist</h3>
          <span className="text-xs text-slate-500 font-medium">
            {confirmedCount} of {totalFields} confirmed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Field</th>
                <th className="px-6 py-3.5">Proposed / Current Value</th>
                <th className="px-6 py-3.5">Source Lineage</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {fields.map((f) => {
                const isEditing = editingFieldId === f.field_id;
                return (
                  <tr key={f.field_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900 flex items-center gap-1.5">
                        <span>{f.label}</span>
                        {f.required && (
                          <span className="text-rose-500 text-xs font-bold" title="Required">*</span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">{f.field_key}</div>
                    </td>

                    <td className="px-6 py-4">
                      {isEditing ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={editVal}
                            onChange={(e) => setEditVal(e.target.value)}
                            className="px-2.5 py-1 text-xs border border-brand-400 rounded-lg focus:outline-none"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveEdit(f.field_id)}
                            className="p-1 bg-brand-600 text-white rounded hover:bg-brand-700 text-xs"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div>
                          <span className={f.current_value ? 'text-slate-900 font-medium' : 'text-slate-400 italic text-xs'}>
                            {f.current_value || 'Missing value'}
                          </span>
                          {f.validation_error && (
                            <p className="text-[11px] text-rose-600 mt-0.5">{f.validation_error}</p>
                          )}
                        </div>
                      )}
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {f.source_document_name ? (
                        <div>
                          <span className="font-medium text-slate-700">{f.source_document_name}</span>
                          {f.source_page && <span className="text-slate-400"> (p.{f.source_page})</span>}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">—</span>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <StatusBadge
                        status={f.validation_status}
                        confirmationStatus={f.confirmation_status}
                        size="sm"
                      />
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {f.current_value && f.confirmation_status !== 'confirmed' && (
                          <button
                            onClick={() => handleConfirm(f.field_id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Confirm</span>
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setEditingFieldId(f.field_id);
                            setEditVal(f.current_value || '');
                          }}
                          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {sessionId && (
        <DigitalSignatureModal
          isOpen={showSignatureModal}
          onClose={() => setShowSignatureModal(false)}
          sessionId={sessionId}
          initialSignature={signaturePath}
          onSignatureUpdated={handleSignatureUpdated}
        />
      )}
    </div>
  );
};
