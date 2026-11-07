import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  Sparkles,
  Send,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Check,
  Edit2,
  ChevronRight,
  ArrowRight,
  ShieldAlert,
  Clock,
  Layers,
  RefreshCw,
  Eye,
  ExternalLink,
  FileCheck,
  Palette,
  PenTool,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { FormSession, FormFieldState, ChatMessage, FieldStatus } from '../types';
import { api } from '../services/apiClient';
import { StyleCustomizer, StyleValues } from '../components/common/StyleCustomizer';
import { DigitalSignatureModal } from '../components/common/DigitalSignatureModal';

export const FormWorkspacePage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // Session & field state
  const [session, setSession] = useState<FormSession | null>(null);
  const [fields, setFields] = useState<FormFieldState[]>([]);
  const [selectedSection, setSelectedSection] = useState<string>('All');
  const [activeFieldKey, setActiveFieldKey] = useState<string | null>(null);
  const [activeCenterTab, setActiveCenterTab] = useState<'cards' | 'preview' | 'styling'>('cards');
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(true);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  // Styling & Digital Signature state
  const [stylePreferences, setStylePreferences] = useState<StyleValues>({
    font_family: 'helvetica',
    font_size: 10,
    text_color: '#0f172a',
  });
  const [showSignatureModal, setShowSignatureModal] = useState<boolean>(false);
  const [signaturePath, setSignaturePath] = useState<string | null>(null);

  // Inline editing state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [suggestedReplies, setSuggestedReplies] = useState<string[]>([]);
  const [isSendingChat, setIsSendingChat] = useState<boolean>(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) return;
    loadSessionData();
    loadChatHistory();
  }, [sessionId]);

  useEffect(() => {
    chatScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadSessionData = async () => {
    try {
      setSessionError(null);
      const data: any = await api.get(`/sessions/${sessionId}`);
      setSession(data);
      if (data.fields) {
        setFields(data.fields);
        if (!activeFieldKey && data.fields.length > 0) {
          setActiveFieldKey(data.fields[0].field_key);
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
    } catch (err: any) {
      console.error('Failed to load session:', err);
      setSessionError(err?.message || 'Could not load form session.');
    } finally {
      setIsLoadingSession(false);
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
    loadSessionData();
  };

  const handleTriggerAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      await api.post(`/sessions/${sessionId}/analyze`);
      await loadSessionData();
    } catch (err: any) {
      console.error('Failed to trigger analysis:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadChatHistory = async () => {
    try {
      const msgs: any = await api.get(`/sessions/${sessionId}/chat`);
      setChatMessages(msgs);
      if (msgs.length === 0) {
        // Seed initial friendly greeting
        setChatMessages([
          {
            id: 'init_1',
            session_id: sessionId!,
            role: 'assistant',
            message:
              "Hello! I have mapped your supporting documents against your form. Let's review the extracted details or fill in any missing fields together.",
            suggested_replies: ['Review extracted fields', 'What fields are missing?'],
            created_at: new Date().toISOString(),
          },
        ]);
        setSuggestedReplies(['Review extracted fields', 'What fields are missing?']);
      } else {
        const lastMsg = msgs[msgs.length - 1];
        if (lastMsg && lastMsg.suggested_replies) {
          setSuggestedReplies(lastMsg.suggested_replies);
        }
      }
    } catch (err) {
      console.warn('Could not load chat history:', err);
    }
  };

  // Handle manual field value save
  const handleSaveFieldValue = async (fieldId: string, confirm: boolean = true) => {
    try {
      const updated: any = await api.patch(`/sessions/${sessionId}/fields/${fieldId}`, {
        current_value: editValue,
        confirm: confirm,
      });

      // Update state locally & refresh session metrics
      setFields((prev) =>
        prev.map((f) => (f.field_id === fieldId ? { ...f, ...updated } : f))
      );
      setEditingFieldId(null);
      loadSessionData(); // Refresh metrics
    } catch (err) {
      console.error('Failed to update field:', err);
    }
  };

  // Confirm extracted value
  const handleConfirmField = async (fieldId: string) => {
    const target = fields.find((f) => f.field_id === fieldId);
    if (!target) return;
    try {
      const updated: any = await api.patch(`/sessions/${sessionId}/fields/${fieldId}`, {
        current_value: target.current_value,
        confirm: true,
      });
      setFields((prev) =>
        prev.map((f) => (f.field_id === fieldId ? { ...f, ...updated } : f))
      );
      loadSessionData();
    } catch (err) {
      console.error('Failed to confirm field:', err);
    }
  };

  // Send message to AI assistant
  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || chatInput;
    if (!textToSend.trim() || isSendingChat) return;

    const tempUserMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      session_id: sessionId!,
      role: 'user',
      message: textToSend,
      created_at: new Date().toISOString(),
    };

    setChatMessages((prev) => [...prev, tempUserMsg]);
    setChatInput('');
    setSuggestedReplies([]);
    setIsSendingChat(true);

    try {
      const turnRes: any = await api.post(`/sessions/${sessionId}/chat`, {
        message: textToSend,
      });

      const assistantMsg: ChatMessage = {
        id: `asst_${Date.now()}`,
        session_id: sessionId!,
        role: 'assistant',
        message: turnRes.assistant_reply,
        suggested_replies: turnRes.suggested_replies,
        created_at: new Date().toISOString(),
      };

      setChatMessages((prev) => [...prev, assistantMsg]);
      setSuggestedReplies(turnRes.suggested_replies || []);

      // Refresh form fields & preview synchronously!
      await loadSessionData();
    } catch (err) {
      console.error('Chat error:', err);
      setChatMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          session_id: sessionId!,
          role: 'assistant',
          message: 'Sorry, I had trouble processing that request. Please try again.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSendingChat(false);
    }
  };

  // Unique sections list
  const sections = ['All', ...Array.from(new Set(fields.map((f) => f.section || 'General')))];

  const filteredFields =
    selectedSection === 'All'
      ? fields
      : fields.filter((f) => (f.section || 'General') === selectedSection);

  const missingCount = fields.filter(
    (f) => !f.current_value || f.validation_status === 'missing'
  ).length;

  return (
    <div className="h-[calc(100vh-6.5rem)] flex flex-col space-y-4">
      {/* Top Workspace Bar */}
      <div className="flex items-center justify-between bg-white px-6 py-3.5 rounded-2xl border border-slate-200/80 shadow-xs flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 leading-tight">
              {session?.title || 'Form Completion Workspace'}
            </h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span>{fields.length} Total Fields</span>
              <span>•</span>
              <span className="text-brand-600 font-medium">
                {Math.round(session?.completion_percentage || 0)}% Complete
              </span>
              {missingCount > 0 && (
                <>
                  <span>•</span>
                  <span className="text-amber-600 font-medium">{missingCount} Missing</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowSignatureModal(true)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
              signaturePath
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                : 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100'
            }`}
            title="Add or update digital signature"
          >
            <PenTool className="w-3.5 h-3.5" />
            <span>{signaturePath ? 'Signed ✓' : 'Add Signature'}</span>
          </button>

          <button
            onClick={() => setActiveCenterTab('styling')}
            className={`hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
              activeCenterTab === 'styling'
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
            title="Document font and color styling"
          >
            <Palette className="w-3.5 h-3.5" />
            <span>Style</span>
          </button>

          <button
            onClick={() => loadSessionData()}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer"
            title="Refresh form state"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to={`/review/${sessionId}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-xs transition-colors"
          >
            <span>Final Review & Submit</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* 3-Part Workspace Grid */}
      <div className="flex-1 grid grid-cols-12 gap-5 overflow-hidden">
        {/* LEFT PANEL: Form Structure & Sections (2.5 cols) */}
        <div className="col-span-12 md:col-span-3 bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs flex flex-col overflow-hidden">
          <div className="px-2 py-1 mb-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Sections & Fields
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {sections.map((sec) => {
              const secCount =
                sec === 'All'
                  ? fields.length
                  : fields.filter((f) => (f.section || 'General') === sec).length;
              const isSelected = selectedSection === sec;

              return (
                <button
                  key={sec}
                  onClick={() => setSelectedSection(sec)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-brand-50 text-brand-900 border border-brand-200/60'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <span className="truncate">{sec}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      isSelected
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {secCount}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Completion Progress widget */}
          <div className="pt-4 border-t border-slate-100 px-2 mt-auto">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5 font-medium">
              <span>Completion</span>
              <span className="font-bold text-slate-800">
                {Math.round(session?.completion_percentage || 0)}%
              </span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all duration-300"
                style={{ width: `${session?.completion_percentage || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* CENTER PANEL: Form Preview (5.5 cols) */}
        <div className="col-span-12 md:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-xs flex flex-col overflow-hidden">
          {/* Center Panel Header with Mode Tabs */}
          <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 flex-shrink-0">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveCenterTab('cards')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeCenterTab === 'cards'
                    ? 'bg-white text-brand-700 shadow-xs border border-slate-200/80'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Field Cards ({filteredFields.length})</span>
              </button>
              <button
                onClick={() => setActiveCenterTab('preview')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeCenterTab === 'preview'
                    ? 'bg-white text-brand-700 shadow-xs border border-slate-200/80'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Live Document Preview</span>
              </button>
              <button
                onClick={() => setActiveCenterTab('styling')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeCenterTab === 'styling'
                    ? 'bg-white text-indigo-700 shadow-xs border border-slate-200/80'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                <Palette className="w-3.5 h-3.5" />
                <span>Font & Signature</span>
              </button>
            </div>

            {activeCenterTab === 'preview' && session?.id && (
              <a
                href={`${api.getBaseUrl()}/sessions/${session.id}/preview`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 shadow-2xs transition-colors cursor-pointer"
                title="Open in new tab"
              >
                <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                <span>Open in Tab</span>
              </a>
            )}
          </div>

          {/* Active Center Tab Content */}
          {activeCenterTab === 'styling' ? (
            <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/50">
              <StyleCustomizer values={stylePreferences} onChange={handleStyleChange} />

              {/* Digital Signature Management Card */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                      <PenTool className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Digital Signature
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Placed on designated signature fields and on the generated certificate stamp
                      </p>
                    </div>
                  </div>

                  {signaturePath && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Signature Active</span>
                    </span>
                  )}
                </div>

                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">
                      {signaturePath ? 'Digital Signature Configured' : 'No Digital Signature Configured'}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      {signaturePath
                        ? 'Your signature is stored securely in this guest session.'
                        : 'Draw, type in cursive, or upload a signature image to automatically sign documents.'}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowSignatureModal(true)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xs transition-colors cursor-pointer flex-shrink-0"
                  >
                    <PenTool className="w-3.5 h-3.5" />
                    <span>{signaturePath ? 'Modify Signature' : 'Add Signature'}</span>
                  </button>
                </div>
              </div>
            </div>
          ) : activeCenterTab === 'preview' ? (
            <div className="flex-1 bg-slate-100 p-2 flex flex-col overflow-hidden">
              <iframe
                src={`${api.getBaseUrl()}/sessions/${session?.id}/preview`}
                className="w-full h-full border border-slate-200 rounded-xl bg-white shadow-2xs"
                title="Document Preview"
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {isLoadingSession && (
                <div className="space-y-4 py-8">
                  {[1, 2, 3].map((n) => (
                    <div key={n} className="p-4 rounded-xl border border-slate-100 animate-pulse space-y-2">
                      <div className="h-4 bg-slate-200 rounded w-1/3"></div>
                      <div className="h-8 bg-slate-100 rounded w-full"></div>
                    </div>
                  ))}
                </div>
              )}

              {sessionError && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    <span>{sessionError}</span>
                  </div>
                  <button
                    onClick={() => loadSessionData()}
                    className="px-2.5 py-1 bg-white border border-rose-300 rounded-lg font-semibold hover:bg-rose-100"
                  >
                    Retry
                  </button>
                </div>
              )}

              {!isLoadingSession && !sessionError && filteredFields.length === 0 && (
                <div className="py-12 px-6 rounded-2xl border-2 border-dashed border-slate-200 text-center flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-semibold text-slate-800 mb-1">
                    No Form Fields Mapped Yet
                  </h4>
                  <p className="text-xs text-slate-500 max-w-sm mb-4">
                    The template has not yet been processed with your supporting documents. Trigger the AI analysis pipeline to automatically extract and map fields.
                  </p>
                  <button
                    onClick={handleTriggerAnalysis}
                    disabled={isAnalyzing}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-xs transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{isAnalyzing ? 'Analyzing Documents...' : 'Extract Fields with AI'}</span>
                  </button>
                </div>
              )}

              {!isLoadingSession && filteredFields.map((field) => {
                const isActive = activeFieldKey === field.field_key;
                const isEditing = editingFieldId === field.field_id;

                return (
                  <div
                    key={field.field_id}
                    onClick={() => setActiveFieldKey(field.field_key)}
                    className={`p-4 rounded-xl border transition-all ${
                      isActive
                        ? 'border-brand-500 bg-brand-50/20 shadow-xs ring-1 ring-brand-500/20'
                        : 'border-slate-200/80 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold text-slate-800">
                            {field.label}
                          </span>
                          {field.required && (
                            <span className="text-rose-500 text-xs font-bold" title="Mandatory field">
                              *
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {field.field_key}
                        </span>
                      </div>
                      <StatusBadge
                        status={field.validation_status}
                        confirmationStatus={field.confirmation_status}
                        size="sm"
                      />
                    </div>

                    {/* Field Value Display or Inline Edit */}
                    {isEditing ? (
                      <div className="space-y-2 mt-2">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg border border-brand-400 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                          autoFocus
                        />
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleSaveFieldValue(field.field_id, true)}
                            className="px-2.5 py-1 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-md"
                          >
                            Save & Confirm
                          </button>
                          <button
                            onClick={() => setEditingFieldId(null)}
                            className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-1 flex items-center justify-between">
                        <div className="text-sm font-medium text-slate-900">
                          {field.current_value ? (
                            <span>{field.current_value}</span>
                          ) : (
                            <span className="text-slate-400 italic font-normal text-xs">
                              Not provided (missing)
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {field.current_value && field.confirmation_status !== 'confirmed' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleConfirmField(field.field_id);
                              }}
                              className="p-1 text-emerald-600 hover:bg-emerald-50 rounded-md transition-colors"
                              title="Confirm this value"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingFieldId(field.field_id);
                              setEditValue(field.current_value || '');
                            }}
                            className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
                            title="Edit value"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Source Document Lineage info */}
                    {field.source_document_name && (
                      <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                        <span className="truncate max-w-[220px]">
                          Source: <span className="font-medium text-slate-700">{field.source_document_name}</span>
                          {field.source_page && ` (p.${field.source_page})`}
                        </span>
                        {field.confidence > 0 && (
                          <span className="font-medium text-emerald-600">
                            {Math.round(field.confidence * 100)}% conf
                          </span>
                        )}
                      </div>
                    )}

                    {/* Conflicting Candidates notification */}
                    {field.candidate_values && field.candidate_values.length > 1 && (
                      <div className="mt-2.5 p-2 rounded-lg bg-purple-50 border border-purple-200 text-purple-900 text-xs space-y-1">
                        <div className="font-semibold flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5 text-purple-600" />
                          <span>Conflicting Candidates:</span>
                        </div>
                        {field.candidate_values.map((cand, idx) => (
                          <div key={idx} className="flex items-center justify-between text-[11px] pl-4">
                            <span>
                              "{cand.value}" ({cand.source_document_name})
                            </span>
                            <button
                              onClick={() => {
                                setEditValue(cand.value);
                                handleSaveFieldValue(field.field_id, true);
                              }}
                              className="text-purple-700 font-semibold hover:underline"
                            >
                              Use this
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Validation error if invalid */}
                    {field.validation_error && (
                      <p className="mt-1 text-xs text-rose-600">{field.validation_error}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* RIGHT PANEL: Conversational Form Assistant (4 cols) */}
        <div className="col-span-12 md:col-span-4 bg-white rounded-2xl border border-slate-200/80 shadow-xs flex flex-col overflow-hidden">
          {/* Assistant Header */}
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white flex items-center justify-center shadow-xs">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Form Assistant</h3>
                <p className="text-[11px] text-slate-500">Let's complete your form together.</p>
              </div>
            </div>
          </div>

          {/* Chat Messages Log */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              return (
                <div
                  key={msg.id}
                  className={`flex ${isAssistant ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                      isAssistant
                        ? 'bg-slate-100 text-slate-800 rounded-bl-xs'
                        : 'bg-brand-600 text-white rounded-br-xs shadow-xs'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.message}</p>
                  </div>
                </div>
              );
            })}
            {isSendingChat && (
              <div className="flex justify-start">
                <div className="bg-slate-100 text-slate-400 rounded-2xl px-4 py-2 text-xs flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce delay-150" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce delay-300" />
                </div>
              </div>
            )}
            <div ref={chatScrollRef} />
          </div>

          {/* Suggested Quick Reply Chips */}
          {suggestedReplies.length > 0 && (
            <div className="px-4 py-2 flex flex-wrap gap-1.5 border-t border-slate-100 bg-slate-50/30 flex-shrink-0">
              {suggestedReplies.map((reply, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(reply)}
                  className="px-2.5 py-1 text-xs font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200/60 rounded-full transition-colors"
                >
                  {reply}
                </button>
              ))}
            </div>
          )}

          {/* Chat Input Bar */}
          <div className="p-3 border-t border-slate-100 bg-white flex-shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Answer question or ask for help..."
                className="flex-1 px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || isSendingChat}
                className={`p-2 rounded-xl text-white shadow-xs transition-all ${
                  !chatInput.trim() || isSendingChat
                    ? 'bg-slate-200 cursor-not-allowed'
                    : 'bg-brand-600 hover:bg-brand-700'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
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
