import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/api';
import { ReviewCaseItem } from '../types';
import { ShieldAlert, CheckCircle2, XCircle, FileText, User, RefreshCw, ZoomIn, Check, ShieldCheck, MessageSquare, AlertTriangle } from 'lucide-react';

export const ReviewerPortal: React.FC = () => {
  const [cases, setCases] = useState<ReviewCaseItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<ReviewCaseItem | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingCases();
  }, []);

  const fetchPendingCases = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getReviewCases();
      setCases(data);
      if (data.length > 0) {
        setSelectedCase(data[0]);
      }
    } catch (err) {
      console.error('Failed to load review cases', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED' | 'RETRY_REQUESTED') => {
    if (!selectedCase) return;
    setLoading(true);
    try {
      await adminApi.submitReviewDecision(selectedCase.caseId, decision, notes);
      setActionSuccess(`Application ${decision} successfully`);
      setNotes('');
      await fetchPendingCases();
    } catch (err) {
      console.error('Failed to submit decision', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-white flex items-center space-x-3 tracking-tight">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <span>Human-in-the-Loop Triage Workspace</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Review borderline identity applications routed by the AI Risk Engine</p>
        </div>

        <button
          onClick={fetchPendingCases}
          className="px-4 py-2.5 rounded-2xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-200 text-xs font-bold flex items-center space-x-2 transition-all shadow-lg"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue ({cases.length})</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center justify-between shadow-lg">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white font-bold text-sm">×</button>
        </div>
      )}

      {cases.length === 0 ? (
        <div className="glass-panel rounded-3xl p-16 text-center border border-slate-800/80 space-y-3">
          <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/10">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-white">Review Queue Clear</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All submitted applications have been processed automatically within STP benchmark thresholds.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: Application Selection Queue */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider px-1">
              Pending Applications ({cases.length})
            </h3>
            
            <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
              {cases.map((c) => (
                <div
                  key={c.caseId}
                  onClick={() => setSelectedCase(c)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    selectedCase?.caseId === c.caseId
                      ? 'bg-sky-500/15 border-sky-500 text-white glow-blue shadow-lg shadow-sky-500/20'
                      : 'bg-slate-900/70 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-extrabold text-sm text-white truncate max-w-[180px]">
                      {c.customer.fullName}
                    </span>
                    <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 font-extrabold">
                      Risk {c.risk.score}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="font-medium">{c.document.docType}</span>
                    <span className="font-mono text-[11px]">
                      {new Date(c.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Center & Right Columns: Split-Screen Investigation Workspace */}
          {selectedCase && (
            <div className="lg:col-span-8 space-y-6">
              
              {/* Top Demographic Bar */}
              <div className="glass-panel rounded-3xl p-5 border border-slate-800/80">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Customer Profile</span>
                    <h3 className="text-lg font-black text-white">{selectedCase.customer.fullName}</h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400">{selectedCase.customer.email}</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">Mobile</span>
                    <span className="font-semibold text-slate-300">{selectedCase.customer.phone || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">DOB</span>
                    <span className="font-semibold text-slate-300">{selectedCase.customer.dob || 'N/A'}</span>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-[10px] text-slate-500 block uppercase">Address</span>
                    <span className="font-semibold text-slate-300 truncate block">{selectedCase.customer.address || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Side-by-Side Face Comparison Verification */}
              <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <User className="w-4 h-4 text-sky-400" />
                    <span>Side-by-Side Biometric Comparison (ID vs Live Selfie)</span>
                  </h4>
                  <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    Match Similarity: {selectedCase.biometrics.faceMatchScore}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-2">
                    <div className="w-24 h-24 mx-auto rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500 font-bold text-xs shadow-inner">
                      ID Photo
                    </div>
                    <span className="text-[11px] font-bold text-slate-400 block uppercase">Cropped Document Face</span>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-2">
                    <div className="w-24 h-24 mx-auto rounded-2xl bg-sky-950/60 border border-sky-500/40 flex items-center justify-center text-sky-400 font-bold text-xs shadow-inner">
                      Live Selfie
                    </div>
                    <span className="text-[11px] font-bold text-sky-400 block uppercase">3D Liveness Selfie</span>
                  </div>
                </div>
              </div>

              {/* OCR Extracted Data vs Document Details */}
              <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Real OCR Data Fields ({selectedCase.document.docType})
                </h4>
                <div className="bg-slate-900/80 rounded-2xl p-3 border border-slate-800 divide-y divide-slate-800">
                  {selectedCase.document.extractedFields.map((f, idx) => (
                    <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                      <span className="text-slate-400 capitalize font-medium">{f.fieldName}</span>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white">{f.value}</span>
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          {f.confidence}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risk Reasons & Decision Action Box */}
              <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Explainable AI Risk Reasons:</span>
                  </h4>
                  <ul className="text-xs text-amber-200/90 space-y-1 list-disc pl-5">
                    {selectedCase.risk.reasons.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Compliance Notes</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Enter verification rationale..."
                    className="w-full h-20 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <button
                    onClick={() => handleDecision('APPROVED')}
                    className="py-3.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-black text-xs flex items-center justify-center space-x-2 shadow-xl shadow-emerald-500/20 transition-all transform hover:-translate-y-0.5"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve KYC Application</span>
                  </button>

                  <button
                    onClick={() => handleDecision('REJECTED')}
                    className="py-3.5 rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-black text-xs flex items-center justify-center space-x-2 shadow-xl shadow-rose-600/20 transition-all transform hover:-translate-y-0.5"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject Application</span>
                  </button>
                </div>
              </div>

            </div>
          )}

        </div>
      )}
    </div>
  );
};
