import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  FileCheck2,
  X,
  AlertCircle,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Layers,
} from 'lucide-react';
import { api } from '../services/apiClient';

interface UploadFileItem {
  file: File;
  id: string;
}

export const NewFormPage: React.FC = () => {
  const navigate = useNavigate();

  // State
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [supportingFiles, setSupportingFiles] = useState<UploadFileItem[]>([]);
  const [formTitle, setFormTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // File input refs
  const templateInputRef = useRef<HTMLInputElement>(null);
  const supportingInputRef = useRef<HTMLInputElement>(null);

  // Handle template selection
  const handleTemplateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg'].includes(ext)) {
        setErrorMsg('Please select a valid PDF, Word DOCX, or image form template (PNG, JPG).');
        return;
      }
      setTemplateFile(file);
      setErrorMsg(null);
      if (!formTitle) {
        setFormTitle(file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      }
    }
  };

  // Handle supporting files selection
  const handleSupportingChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const allowed = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.tiff'];
      const newItems: UploadFileItem[] = [];

      Array.from(e.target.files).forEach((file) => {
        const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
        if (allowed.includes(ext)) {
          newItems.push({
            file,
            id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          });
        }
      });

      setSupportingFiles((prev) => [...prev, ...newItems]);
      setErrorMsg(null);
    }
  };

  const removeSupportingFile = (id: string) => {
    setSupportingFiles((prev) => prev.filter((item) => item.id !== id));
  };

  // Submit and start workflow
  const handleStartAnalysis = async () => {
    if (!templateFile) {
      setErrorMsg('A form template document is required to proceed.');
      return;
    }

    try {
      setIsUploading(true);
      setErrorMsg(null);

      // 1. Upload Template
      const templateFormData = new FormData();
      templateFormData.append('file', templateFile);
      const templateRes: any = await api.post('/templates/upload', templateFormData);

      // 2. Create Session
      const sessionRes: any = await api.post('/sessions', {
        template_id: templateRes.id,
        title: formTitle || templateFile.name,
      });

      // 3. Upload Supporting Documents attached to session
      if (supportingFiles.length > 0) {
        const docsFormData = new FormData();
        docsFormData.append('session_id', sessionRes.id);
        supportingFiles.forEach((item) => {
          docsFormData.append('files', item.file);
        });
        await api.post('/documents/upload', docsFormData);
      }

      // 4. Navigate to real-time Processing Screen
      navigate(`/processing/${sessionRes.id}`);
    } catch (err: any) {
      console.error('Upload failed:', err);
      setErrorMsg(err.message || 'Failed to upload files. Please check network connection.');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Title & Instructions */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Create New Form</h2>
        <p className="text-sm text-slate-500 mt-1">
          Follow the two-step guide below. Upload your blank template and the evidence documents that contain your details.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Form Session Title input */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <label className="block text-sm font-semibold text-slate-800 mb-1">
          Form Title / Session Name
        </label>
        <input
          type="text"
          value={formTitle}
          onChange={(e) => setFormTitle(e.target.value)}
          placeholder="e.g. 2026 Tax Return Filing, University Application, Internship Form"
          className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
        />
      </div>

      {/* STEP A: Upload Form Template */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-700 font-bold flex items-center justify-center text-sm">
            A
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Upload the form you want to complete
            </h3>
            <p className="text-xs text-slate-500">
              Start with a blank PDF, Word document, or image form (.pdf, .docx, .png, .jpg, .jpeg).
            </p>
          </div>
        </div>

        <input
          type="file"
          ref={templateInputRef}
          onChange={handleTemplateChange}
          accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
          className="hidden"
        />

        {!templateFile ? (
          <div
            onClick={() => templateInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-2xl p-8 text-center cursor-pointer bg-slate-50/50 hover:bg-brand-50/30 transition-all group"
          >
            <div className="w-12 h-12 rounded-xl bg-white text-slate-400 group-hover:text-brand-600 border border-slate-200 mx-auto flex items-center justify-center mb-3 shadow-xs transition-colors">
              <Upload className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-800">
              Click to browse or drag & drop blank template
            </p>
            <p className="text-xs text-slate-400 mt-1">Accepted: PDF, Word DOCX, PNG, JPG (up to 25 MB)</p>
          </div>
        ) : (
          <div className="flex items-center justify-between p-4 rounded-xl border border-brand-200 bg-brand-50/40">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-600 text-white flex items-center justify-center shadow-xs">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900">{templateFile.name}</p>
                <p className="text-xs text-slate-500">
                  {(templateFile.size / 1024 / 1024).toFixed(2)} MB • Ready for analysis
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setTemplateFile(null);
                if (templateInputRef.current) templateInputRef.current.value = '';
              }}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-lg transition-colors"
              title="Replace file"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* STEP B: Upload Supporting Documents */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-700 font-bold flex items-center justify-center text-sm">
            B
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Add documents containing your information
            </h3>
            <p className="text-xs text-slate-500">
              Upload documents such as identification cards, salary slips, certificates, or statements.
            </p>
          </div>
        </div>

        <input
          type="file"
          ref={supportingInputRef}
          onChange={handleSupportingChange}
          multiple
          accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.tiff"
          className="hidden"
        />

        <div
          onClick={() => supportingInputRef.current?.click()}
          className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-2xl p-6 text-center cursor-pointer bg-slate-50/50 hover:bg-brand-50/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-white text-slate-400 group-hover:text-brand-600 border border-slate-200 mx-auto flex items-center justify-center mb-2 shadow-xs transition-colors">
            <Layers className="w-5 h-5" />
          </div>
          <p className="text-sm font-medium text-slate-800">
            Click to add supporting files (multiple files supported)
          </p>
          <p className="text-xs text-slate-400 mt-1">
            PDF, DOCX, Scanned Images (PNG, JPG, TIFF)
          </p>
        </div>

        {/* Selected supporting files list */}
        {supportingFiles.length > 0 && (
          <div className="space-y-2 mt-4 pt-2 border-t border-slate-100">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Attached Documents ({supportingFiles.length})
            </div>
            {supportingFiles.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="p-2 rounded-lg bg-slate-100 text-slate-600 flex-shrink-0">
                    <FileCheck2 className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="text-xs font-medium text-slate-900 truncate">
                      {item.file.name}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      {(item.file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeSupportingFile(item.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors flex-shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Primary Action Button */}
      <div className="flex items-center justify-end gap-4 pt-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleStartAnalysis}
          disabled={!templateFile || isUploading}
          className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white shadow-sm transition-all ${
            !templateFile || isUploading
              ? 'bg-slate-300 cursor-not-allowed'
              : 'bg-brand-600 hover:bg-brand-700 hover:shadow-md'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>{isUploading ? 'Preparing Session...' : 'Analyze My Documents'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
