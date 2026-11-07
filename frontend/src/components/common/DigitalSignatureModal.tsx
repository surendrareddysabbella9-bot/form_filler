import React, { useState, useRef, useEffect } from 'react';
import { PenTool, Type, Upload, Trash2, Check, X, ShieldCheck, AlertCircle } from 'lucide-react';
import { api } from '../../services/apiClient';

interface DigitalSignatureModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  initialSignature?: string | null;
  onSignatureUpdated: (signatureData: string | null) => void;
}

export const DigitalSignatureModal: React.FC<DigitalSignatureModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  initialSignature,
  onSignatureUpdated,
}) => {
  const [tab, setTab] = useState<'draw' | 'type' | 'upload'>('draw');
  const [typedName, setTypedName] = useState('');
  const [fontStyle, setFontStyle] = useState<'cursive' | 'italic-serif' | 'handwriting'>('cursive');
  const [inkColor, setInkColor] = useState<'#0f172a' | '#1e3a8a'>('#0f172a');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Canvas drawing state
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);

  useEffect(() => {
    if (isOpen && tab === 'draw') {
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.strokeStyle = inkColor;
          ctx.lineWidth = 2.5;
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
        }
      }
    }
  }, [isOpen, tab, inkColor]);

  if (!isOpen) return null;

  // --- Canvas Drawing Handlers ---
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsDrawing(true);
    setHasDrawn(true);
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setHasDrawn(false);
    }
  };

  // --- Type Mode Canvas Generator ---
  const generateTypedSignatureDataUrl = (): string => {
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = inkColor;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    if (fontStyle === 'cursive') {
      ctx.font = 'italic 52px "Brush Script MT", "Segoe Script", "Snell Roundhand", cursive';
    } else if (fontStyle === 'italic-serif') {
      ctx.font = 'italic bold 44px "Georgia", "Times New Roman", serif';
    } else {
      ctx.font = 'italic 46px "Caveat", "Comic Sans MS", cursive, sans-serif';
    }

    ctx.fillText(typedName || 'Signature', canvas.width / 2, canvas.height / 2);
    return canvas.toDataURL('image/png');
  };

  // --- Upload Mode Handler ---
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please upload a valid image file (.png, .jpg, .jpeg)');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setUploadedImage(reader.result as string);
      setErrorMsg(null);
    };
    reader.readAsDataURL(file);
  };

  // --- Save / Submit Signature ---
  const handleSaveSignature = async () => {
    try {
      setIsSaving(true);
      setErrorMsg(null);
      let signatureDataUrl = '';

      if (tab === 'draw') {
        const canvas = canvasRef.current;
        if (!canvas || !hasDrawn) {
          setErrorMsg('Please sign on the canvas before saving.');
          setIsSaving(false);
          return;
        }
        signatureDataUrl = canvas.toDataURL('image/png');
      } else if (tab === 'type') {
        if (!typedName.trim()) {
          setErrorMsg('Please type your full name for the signature.');
          setIsSaving(false);
          return;
        }
        signatureDataUrl = generateTypedSignatureDataUrl();
      } else if (tab === 'upload') {
        if (!uploadedImage) {
          setErrorMsg('Please upload an image of your signature.');
          setIsSaving(false);
          return;
        }
        signatureDataUrl = uploadedImage;
      }

      // Send to backend
      const res: any = await api.post(`/sessions/${sessionId}/signature`, {
        signature_data: signatureDataUrl,
      });

      onSignatureUpdated(res.signature_path || signatureDataUrl);
      onClose();
    } catch (err: any) {
      console.error('Failed to save signature:', err);
      setErrorMsg(err.message || 'Failed to save signature. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveSignature = async () => {
    try {
      setIsSaving(true);
      await api.delete(`/sessions/${sessionId}/signature`);
      onSignatureUpdated(null);
      clearCanvas();
      setUploadedImage(null);
      setTypedName('');
      onClose();
    } catch (err: any) {
      console.error('Failed to remove signature:', err);
      setErrorMsg(err.message || 'Failed to delete signature.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200/80 flex items-center justify-center text-indigo-600 shadow-2xs">
              <PenTool className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Add Digital Signature</h3>
              <p className="text-xs text-slate-500">Apply your legal signature to the filled document</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 px-6 pt-3 gap-6 bg-white text-xs font-semibold">
          <button
            type="button"
            onClick={() => setTab('draw')}
            className={`pb-2.5 border-b-2 flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'draw'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <PenTool className="w-4 h-4" />
            <span>Draw Signature</span>
          </button>
          <button
            type="button"
            onClick={() => setTab('type')}
            className={`pb-2.5 border-b-2 flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'type'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Type className="w-4 h-4" />
            <span>Type Name</span>
          </button>
          <button
            type="button"
            onClick={() => setTab('upload')}
            className={`pb-2.5 border-b-2 flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'upload'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Upload Image</span>
          </button>
        </div>

        {/* Content Area */}
        <div className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* TAB 1: DRAW */}
          {tab === 'draw' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Draw inside the box using your mouse or finger:</span>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Ink:</span>
                  <button
                    type="button"
                    onClick={() => setInkColor('#0f172a')}
                    className={`w-5 h-5 rounded-full bg-slate-900 border-2 cursor-pointer ${
                      inkColor === '#0f172a' ? 'border-indigo-600 ring-2 ring-indigo-400/40' : 'border-white'
                    }`}
                    title="Black ink"
                  />
                  <button
                    type="button"
                    onClick={() => setInkColor('#1e3a8a')}
                    className={`w-5 h-5 rounded-full bg-blue-900 border-2 cursor-pointer ${
                      inkColor === '#1e3a8a' ? 'border-indigo-600 ring-2 ring-indigo-400/40' : 'border-white'
                    }`}
                    title="Blue ink"
                  />
                  <button
                    type="button"
                    onClick={clearCanvas}
                    className="ml-2 text-slate-500 hover:text-rose-600 underline font-medium cursor-pointer"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="border-2 border-dashed border-slate-300 rounded-2xl bg-slate-50/60 overflow-hidden relative shadow-inner">
                <canvas
                  ref={canvasRef}
                  width={520}
                  height={180}
                  className="w-full h-44 cursor-crosshair touch-none"
                  onMouseDown={startDrawing}
                  onMouseMove={draw}
                  onMouseUp={stopDrawing}
                  onMouseLeave={stopDrawing}
                  onTouchStart={startDrawing}
                  onTouchMove={draw}
                  onTouchEnd={stopDrawing}
                />
                {!hasDrawn && (
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center text-slate-400 text-xs italic">
                    Draw your signature here
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: TYPE */}
          {tab === 'type' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Type Your Full Name
                </label>
                <input
                  type="text"
                  value={typedName}
                  onChange={(e) => setTypedName(e.target.value)}
                  placeholder="e.g. Eleanor Vance"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setFontStyle('cursive')}
                  className={`p-3 rounded-xl border text-center transition-all cursor-pointer ${
                    fontStyle === 'cursive'
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-semibold'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="text-base italic font-serif" style={{ fontFamily: 'Brush Script MT, cursive' }}>
                    {typedName || 'Eleanor Vance'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Script</div>
                </button>

                <button
                  type="button"
                  onClick={() => setFontStyle('italic-serif')}
                  className={`p-3 rounded-xl border text-center transition-all cursor-pointer ${
                    fontStyle === 'italic-serif'
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-semibold'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="text-sm italic font-serif font-bold">
                    {typedName || 'Eleanor Vance'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Formal Serif</div>
                </button>

                <button
                  type="button"
                  onClick={() => setFontStyle('handwriting')}
                  className={`p-3 rounded-xl border text-center transition-all cursor-pointer ${
                    fontStyle === 'handwriting'
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-semibold'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="text-sm italic font-sans">
                    {typedName || 'Eleanor Vance'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Handwriting</div>
                </button>
              </div>

              {/* Ink color */}
              <div className="flex items-center gap-3 pt-1">
                <span className="text-xs text-slate-500">Ink Color:</span>
                <button
                  type="button"
                  onClick={() => setInkColor('#0f172a')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer border ${
                    inkColor === '#0f172a' ? 'bg-slate-900 text-white border-slate-900' : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}
                >
                  Deep Black
                </button>
                <button
                  type="button"
                  onClick={() => setInkColor('#1e3a8a')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer border ${
                    inkColor === '#1e3a8a' ? 'bg-blue-900 text-white border-blue-900' : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}
                >
                  Navy Blue
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: UPLOAD */}
          {tab === 'upload' && (
            <div className="space-y-3">
              <input
                type="file"
                id="signature-file-input"
                accept="image/png,image/jpeg,image/jpg"
                onChange={handleFileUpload}
                className="hidden"
              />
              <label
                htmlFor="signature-file-input"
                className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-indigo-50/30 transition-all group"
              >
                <Upload className="w-8 h-8 text-slate-400 group-hover:text-indigo-600 mb-2 transition-colors" />
                <span className="text-xs font-semibold text-slate-700">Click to upload signature image</span>
                <span className="text-[11px] text-slate-400 mt-0.5">PNG or JPG with transparent or light background</span>
              </label>

              {uploadedImage && (
                <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <img src={uploadedImage} alt="Uploaded signature" className="h-10 max-w-[140px] object-contain" />
                    <span className="text-xs text-slate-600 font-medium">Signature image loaded</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setUploadedImage(null)}
                    className="p-1 text-slate-400 hover:text-rose-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Privacy & Certificate Notice */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div className="text-[11px] text-slate-500 leading-relaxed">
              Signatures are stored within your <strong>temporary private guest session</strong> and automatically purged on session expiration or manual deletion. A verification certificate stamp is embedded onto the generated document.
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
          {initialSignature ? (
            <button
              type="button"
              onClick={handleRemoveSignature}
              disabled={isSaving}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-rose-600 hover:text-rose-700 cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Remove Signature</span>
            </button>
          ) : (
            <span />
          )}

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSaveSignature}
              disabled={isSaving}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition-colors cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{isSaving ? 'Saving...' : 'Apply Signature'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
