import React from 'react';
import { Type, Palette, Sparkles, Check } from 'lucide-react';

export interface StyleValues {
  font_family: string;
  font_size: number;
  text_color: string;
}

interface StyleCustomizerProps {
  values: StyleValues;
  onChange: (newValues: StyleValues) => void;
  compact?: boolean;
}

const FONT_OPTIONS = [
  { id: 'helvetica', label: 'Helvetica / Arial', category: 'Sans-Serif (Modern & Clean)', cssFont: 'sans-serif' },
  { id: 'times', label: 'Times New Roman', category: 'Serif (Formal & Legal)', cssFont: 'serif' },
  { id: 'courier', label: 'Courier New', category: 'Monospace (Typewriter)', cssFont: 'monospace' },
];

const SIZE_OPTIONS = [
  { size: 8, label: '8 pt', desc: 'Compact' },
  { size: 10, label: '10 pt', desc: 'Standard' },
  { size: 12, label: '12 pt', desc: 'Large' },
  { size: 14, label: '14 pt', desc: 'Extra' },
];

const COLOR_SWATCHES = [
  { hex: '#0f172a', label: 'Deep Slate' },
  { hex: '#1e3a8a', label: 'Navy Blue' },
  { hex: '#000000', label: 'Pure Black' },
  { hex: '#334155', label: 'Charcoal' },
  { hex: '#15803d', label: 'Forest Green' },
];

export const StyleCustomizer: React.FC<StyleCustomizerProps> = ({
  values,
  onChange,
  compact = false,
}) => {
  const currentFont = values.font_family || 'helvetica';
  const currentSize = values.font_size || 10;
  const currentColor = values.text_color || '#0f172a';

  const update = (patch: Partial<StyleValues>) => {
    onChange({
      font_family: patch.font_family ?? currentFont,
      font_size: patch.font_size ?? currentSize,
      text_color: patch.text_color ?? currentColor,
    });
  };

  const getCssFamily = (fid: string) => {
    if (fid === 'times') return '"Times New Roman", Times, serif';
    if (fid === 'courier') return '"Courier New", Courier, monospace';
    return 'Helvetica, Arial, sans-serif';
  };

  return (
    <div className={`bg-white rounded-2xl border border-slate-200/80 shadow-xs ${compact ? 'p-3' : 'p-5'} space-y-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Palette className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Document Typography & Ink
            </h4>
            {!compact && (
              <p className="text-[11px] text-slate-500">
                Customize the typography and ink color applied to generated field text
              </p>
            )}
          </div>
        </div>
      </div>

      <div className={`grid ${compact ? 'grid-cols-1 gap-3' : 'grid-cols-1 md:grid-cols-3 gap-4'}`}>
        {/* Font Family Selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
            <Type className="w-3.5 h-3.5 text-slate-500" />
            <span>Font Family</span>
          </label>
          <div className="space-y-1.5">
            {FONT_OPTIONS.map((opt) => {
              const active = currentFont === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => update({ font_family: opt.id })}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left border transition-all text-xs cursor-pointer ${
                    active
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-semibold ring-1 ring-indigo-500/20'
                      : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                  }`}
                  style={{ fontFamily: opt.cssFont }}
                >
                  <div className="truncate">
                    <div>{opt.label}</div>
                    <div className="text-[10px] text-slate-400 font-normal">{opt.category}</div>
                  </div>
                  {active && <Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Font Size Selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-slate-500" />
            <span>Font Size ({currentSize} pt)</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {SIZE_OPTIONS.map((opt) => {
              const active = currentSize === opt.size;
              return (
                <button
                  key={opt.size}
                  type="button"
                  onClick={() => update({ font_size: opt.size })}
                  className={`flex flex-col items-center justify-center p-2 rounded-xl border transition-all cursor-pointer ${
                    active
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold ring-1 ring-indigo-500/20'
                      : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                  }`}
                >
                  <span className="text-sm font-semibold">{opt.label}</span>
                  <span className="text-[10px] text-slate-400">{opt.desc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Ink / Text Color */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
            <Palette className="w-3.5 h-3.5 text-slate-500" />
            <span>Ink Color</span>
          </label>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            {COLOR_SWATCHES.map((swatch) => {
              const active = currentColor.toLowerCase() === swatch.hex.toLowerCase();
              return (
                <button
                  key={swatch.hex}
                  type="button"
                  onClick={() => update({ text_color: swatch.hex })}
                  className={`w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all cursor-pointer shadow-xs ${
                    active ? 'border-indigo-600 scale-110 ring-2 ring-indigo-400/40' : 'border-white'
                  }`}
                  style={{ backgroundColor: swatch.hex }}
                  title={`${swatch.label} (${swatch.hex})`}
                >
                  {active && <Check className="w-3.5 h-3.5 text-white" />}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 mt-2">
            <input
              type="color"
              value={currentColor}
              onChange={(e) => update({ text_color: e.target.value })}
              className="w-8 h-8 rounded-lg cursor-pointer border border-slate-200 p-0.5"
            />
            <input
              type="text"
              value={currentColor}
              onChange={(e) => update({ text_color: e.target.value })}
              placeholder="#000000"
              className="flex-1 px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-mono uppercase text-slate-800"
            />
          </div>
        </div>
      </div>

      {/* Live Sample Preview Chip */}
      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Live Form Text Preview:
        </span>
        <div
          className="px-3 py-1.5 rounded-lg bg-white border border-slate-200/90 shadow-2xs transition-all overflow-hidden"
          style={{
            fontFamily: getCssFamily(currentFont),
            fontSize: `${Math.max(11, currentSize + 1)}px`,
            color: currentColor,
          }}
        >
          Sample Value: Jane Doe • 1042 Maple Street, Suite 4B
        </div>
      </div>
    </div>
  );
};
