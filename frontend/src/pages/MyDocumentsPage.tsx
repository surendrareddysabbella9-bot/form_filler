import React, { useEffect, useState } from 'react';
import { Files, Search, Trash2, FileCheck2, PlusCircle, ExternalLink } from 'lucide-react';
import { UploadedDoc } from '../types';
import { api } from '../services/apiClient';
import { EmptyState } from '../components/common/EmptyState';

export const MyDocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<UploadedDoc[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const data: any = await api.get('/documents');
      setDocuments(data);
    } catch (err) {
      console.warn('Could not load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.delete(`/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      typeFilter === 'all'
        ? true
        : typeFilter === 'pdf'
        ? doc.file_type.includes('pdf')
        : typeFilter === 'docx'
        ? doc.file_type.includes('doc')
        : doc.file_type.includes('png') || doc.file_type.includes('jpg');
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Session Documents</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Uploaded evidence and supporting documents associated with your current temporary private guest session.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by filename..."
            className="w-full pl-10 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 bg-white rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 focus:outline-none"
        >
          <option value="all">All File Formats</option>
          <option value="pdf">PDF Documents</option>
          <option value="docx">Word DOCX</option>
          <option value="image">Scanned Images</option>
        </select>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-sm text-slate-400">Loading documents...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Files}
              title="No documents found"
              description="Upload evidence documents during form creation or attach them to form sessions."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-3.5">Document Name</th>
                  <th className="px-6 py-3.5">Format</th>
                  <th className="px-6 py-3.5">Size</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900 flex items-center gap-2">
                        <FileCheck2 className="w-4 h-4 text-brand-600 flex-shrink-0" />
                        <span className="truncate max-w-xs">{doc.filename}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-500 uppercase">
                      {doc.file_type.replace('.', '')}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {doc.processing_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
