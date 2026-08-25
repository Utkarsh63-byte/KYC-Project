import React, { useState } from 'react';
import { sandboxApi, kycApi } from '../services/api';
import { KYCSessionResult } from '../types';
import { Sparkles, Play, CheckCircle2, AlertTriangle, XCircle, ShieldAlert, FileText, Download, Check } from 'lucide-react';

const DEMO_SCENARIOS = [
  {
    key: 'SUCCESSFUL_PASS',
    title: '1. Clean Pass (Auto-Approve)',
    desc: 'Valid PAN card, high OCR confidence (99%), clean liveness (98%), 97% face match.',
    badge: 'AUTO_APPROVE',
    badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
  },
  {
    key: 'BLURRED_DOCUMENT',
    title: '2. Blurry Document Quality',
    desc: 'Low Laplacian variance sharpness (48/100). Triggers interactive re-capture prompt.',
    badge: 'RE_CAPTURE',
    badgeClass: 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  },
  {
    key: 'LOW_OCR_CONFIDENCE',
    title: '3. Low OCR Confidence (Worn ID)',
    desc: 'Worn Aadhaar card with 72% extraction confidence. Routed to Human-in-the-Loop review queue.',
    badge: 'MANUAL_REVIEW',
    badgeClass: 'bg-sky-500/15 text-sky-400 border-sky-500/30'
  },
  {
    key: 'SPOOF_ATTEMPT',
    title: '4. Biometric Spoof Attack',
    desc: 'Printed photograph presentation attack. Liveness confidence drops to 32%.',
    badge: 'REJECT',
    badgeClass: 'bg-rose-500/15 text-rose-400 border-rose-500/30'
  },
  {
    key: 'FACE_MISMATCH',
    title: '5. Face Mismatch (Impersonation)',
    desc: 'Uploaded document photo does not match live selfie. Face match similarity 38%.',
    badge: 'HIGH_RISK_REJECT',
    badgeClass: 'bg-rose-500/15 text-rose-400 border-rose-500/30'
  },
  {
    key: 'SUSPICIOUS_SCREENSHOT',
    title: '6. Suspicious Digital Screenshot',
    desc: 'FFT frequency Moire pattern & copy-paste edge noise detected (Tamper 75/100).',
    badge: 'TAMPER_ALERT',
    badgeClass: 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  }
];

export const ExecutiveDemoSandbox: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('SUCCESSFUL_PASS');
  const [result, setResult] = useState<KYCSessionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const runScenario = async (key: string) => {
    setSelectedScenario(key);
    setLoading(true);
    try {
      const res = await sandboxApi.triggerScenario(key);
      setResult(res);
    } catch (err) {
      console.error('Failed to run scenario', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      
      {/* Top Banner */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-amber-500/30 bg-gradient-to-r from-amber-950/30 via-slate-900/90 to-indigo-950/30 shadow-2xl">
        <div className="flex items-center space-x-3 text-amber-400 mb-2">
          <Sparkles className="w-6 h-6" />
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">Executive Bank Presentation Demo Controller</h1>
        </div>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          Demonstrate end-to-end automated KYC execution, real-time risk scoring, edge failure cases, and liveness anti-spoofing live to bank executives with synthetic test profiles.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Scenario List */}
        <div className="lg:col-span-5 space-y-3">
          <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider px-1">Select Scenario:</h3>
          
          <div className="space-y-3">
            {DEMO_SCENARIOS.map((scen) => (
              <div
                key={scen.key}
                onClick={() => runScenario(scen.key)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                  selectedScenario === scen.key
                    ? 'bg-amber-500/15 border-amber-500 text-white glow-amber shadow-lg shadow-amber-500/20'
                    : 'bg-slate-900/70 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-black text-sm text-white">{scen.title}</span>
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full border font-extrabold ${scen.badgeClass}`}>
                    {scen.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-normal">{scen.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Live Execution Output Telemetry */}
        <div className="lg:col-span-7 space-y-4">
          <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider px-1">Execution Telemetry:</h3>

          {loading ? (
            <div className="glass-panel rounded-3xl p-16 text-center border border-slate-800/80 space-y-3">
              <Play className="w-10 h-10 text-amber-400 animate-spin mx-auto" />
              <p className="text-sm font-bold text-white">Running Multi-Signal AI & Biometrics Matrix...</p>
            </div>
          ) : result ? (
            <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800/80 space-y-6">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Simulated Profile</span>
                  <h2 className="text-xl font-black text-white">{result.customer.fullName}</h2>
                </div>

                <div className="text-left sm:text-right">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Outcome Decision</span>
                  <span className={`text-sm font-black px-3.5 py-1 rounded-full border inline-block mt-0.5 ${
                    result.decision === 'AUTO_APPROVE'
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : result.decision === 'MANUAL_REVIEW'
                      ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  }`}>
                    {result.decision || result.status}
                  </span>
                </div>
              </div>

              {/* Signals Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Calculated Risk</span>
                  <span className="text-base font-black text-amber-400 mt-0.5 block">{result.risk_score} / 100</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Quality Score</span>
                  <span className="text-base font-black text-white mt-0.5 block">{result.documents[0]?.qualityScore || 90.0}/100</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Liveness Score</span>
                  <span className="text-base font-black text-white mt-0.5 block">{result.biometrics?.livenessScore || 98.0}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Face Match</span>
                  <span className="text-base font-black text-white mt-0.5 block">{result.biometrics?.faceMatchScore || 96.0}%</span>
                </div>
              </div>

              {/* Reason Codes */}
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-slate-300 block uppercase tracking-wider">Explainable AI Reason Codes:</span>
                <ul className="space-y-1.5 text-xs text-slate-400 list-disc pl-5">
                  {result.decision_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              <a
                href={kycApi.getReportPdfUrl(result.session_id)}
                target="_blank"
                rel="noreferrer"
                className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-xs shadow-xl shadow-sky-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
              >
                <Download className="w-4 h-4" />
                <span>Download Sample KYC Report PDF</span>
              </a>

            </div>
          ) : null}

        </div>

      </div>
    </div>
  );
};
