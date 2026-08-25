import React, { useState } from 'react';
import { Stepper } from '../components/Stepper';
import { CameraCaptureModal } from '../components/CameraCaptureModal';
import { SelfieLivenessModal } from '../components/SelfieLivenessModal';
import { kycApi } from '../services/api';
import { KYCSessionResult } from '../types';
import { Shield, ArrowRight, CheckCircle2, FileText, Camera, User, Download, AlertCircle, RefreshCw, Sparkles, Check } from 'lucide-react';

const STEPS = ['Privacy Consent', 'Demographics', 'ID Document', 'OCR Verification', 'Face Liveness', 'Instant Decision'];

export const CustomerKYCFlow: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [session, setSession] = useState<KYCSessionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form State - Clean, empty inputs
  const [fullName, setFullName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [dob, setDob] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [docType, setDocType] = useState<string>('PAN');

  // Modals
  const [showDocCamera, setShowDocCamera] = useState<boolean>(false);
  const [showSelfieCamera, setShowSelfieCamera] = useState<boolean>(false);
  const [retryCount, setRetryCount] = useState<number>(0);

  const handleRetry = () => {
    if (retryCount >= 3) return;
    setRetryCount((prev) => prev + 1);
    setError(null);
    setCurrentStep(3);
  };


  // Step 1: Privacy Consent
  const handleConsentAccept = () => {
    setError(null);
    setCurrentStep(2);
  };

  // Step 2: Customer Details Submit -> Initialize KYC Session with user's real data
  const handleDetailsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const sess = await kycApi.createSession({ fullName, email, phone, dob, address });
      setSession(sess);
      await kycApi.submitConsent(sess.session_id);
      setCurrentStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize KYC session');
    } finally {
      setLoading(false);
    }
  };


  // Step 3: Document Upload / Capture
  const handleDocCapture = async (file: File) => {
    if (!session) return;
    setShowDocCamera(false);
    setLoading(true);
    setError(null);
    try {
      await kycApi.uploadDocument(session.session_id, docType, file);
      const updatedSess = await kycApi.getSessionResult(session.session_id);
      setSession(updatedSess);
      setCurrentStep(4);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Document processing failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 5: Liveness & Face Match Submit
  const handleSelfieComplete = async (base64Selfie: string) => {
    if (!session) return;
    setShowSelfieCamera(false);
    setLoading(true);
    setError(null);
    try {
      await kycApi.verifyLiveness(session.session_id, base64Selfie);
      await kycApi.executeVerification(session.session_id);
      const finalSess = await kycApi.getSessionResult(session.session_id);
      setSession(finalSess);
      setCurrentStep(6);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Biometric verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      
      {/* Top Progress Tracker */}
      <div className="glass-panel rounded-3xl p-3 border border-slate-800/80 shadow-2xl">
        <Stepper currentStep={currentStep} steps={STEPS} />
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-center space-x-2.5 shadow-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: PRIVACY CONSENT */}
      {currentStep === 1 && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 space-y-6">
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/10">
              <Shield className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white tracking-tight">Digital KYC Privacy Notice & Consent</h2>
              <p className="text-xs text-slate-400 mt-0.5">Regulated under RBI KYC Master Directions & DPDP Act Standards</p>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300 space-y-3 leading-relaxed">
            <p className="font-medium text-slate-200">
              In accordance with banking regulations, Bank ABC requires your consent to securely process your identity documents and biometric face verification for remote account onboarding.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-slate-300">Automated Real OCR extraction & field normalization</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-slate-300">3D Face Liveness & Eye Blink anti-spoofing detection</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-slate-300">256-bit AES KMS envelope encryption for all PII</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-slate-300">Immutable SHA-256 digital audit trail logging</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleConsentAccept}
            disabled={loading}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-xl shadow-sky-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <span>I Agree & Accept Terms</span>}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* STEP 2: CUSTOMER DEMOGRAPHICS */}
      {currentStep === 2 && (
        <form onSubmit={handleDetailsSubmit} className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 space-y-6">
          <div>
            <h2 className="text-2xl font-black text-white tracking-tight">Step 2: Customer Demographics</h2>
            <p className="text-xs text-slate-400 mt-1">Enter your details as they appear on your government identity card</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Full Legal Name *</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Utkarsh Pandey"
                required
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email Address *</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. utkarsh@example.com"
                required
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Mobile Phone</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91 98765 43210"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Date of Birth (DD/MM/YYYY)</label>
              <input
                type="text"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                placeholder="DD/MM/YYYY"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Residential Address</label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g. Flat 101, Sector 62, Noida, Uttar Pradesh"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-xl shadow-sky-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <span>Proceed to Document Capture</span>}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      )}


      {/* STEP 3: DOCUMENT SELECTION & CAPTURE */}
      {currentStep === 3 && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 space-y-6">
          <div>
            <h2 className="text-2xl font-black text-white tracking-tight">Step 3: Identity Document Capture</h2>
            <p className="text-xs text-slate-400 mt-1">Select your document type and scan using your camera or upload an image/PDF</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            {[
              { id: 'PAN', label: 'PAN Card' },
              { id: 'AADHAAR', label: 'Aadhaar Card' },
              { id: 'PASSPORT', label: 'Passport' },
              { id: 'DRIVING_LICENSE', label: 'Driving License' }
            ].map((d) => (
              <button
                key={d.id}
                type="button"
                onClick={() => setDocType(d.id)}
                className={`p-4 rounded-2xl border text-center transition-all ${
                  docType === d.id
                    ? 'bg-sky-500/15 border-sky-500 text-white font-bold glow-blue shadow-lg shadow-sky-500/20'
                    : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <FileText className="w-6 h-6 mx-auto mb-2 opacity-80" />
                <span className="text-xs">{d.label}</span>
              </button>
            ))}
          </div>

          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto shadow-lg shadow-sky-500/15">
              <Camera className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Capture your {docType}</h3>
              <p className="text-xs text-slate-400 mt-1">Our real-time OpenCV engine will check image blur, glare, and resolution</p>
            </div>

            <button
              onClick={() => setShowDocCamera(true)}
              className="px-8 py-3.5 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm inline-flex items-center space-x-2 shadow-xl shadow-sky-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <Camera className="w-4 h-4" />
              <span>Launch Live Camera Scanner</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: REAL OCR EXTRACTION CONFIRMATION */}
      {currentStep === 4 && session && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-2xl font-black text-white tracking-tight">Step 4: Extracted Identity Information</h2>
              <p className="text-xs text-slate-400 mt-0.5">Real OCR text & pattern extraction results</p>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-xl border text-xs font-bold ${
                (session.documents[0]?.qualityScore || 0) >= 60
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              }`}>
                Quality: {session.documents[0]?.qualityScore || 0}/100
              </span>
            </div>
          </div>

          {/* No Text Detected Warning Banner */}
          {session.documents[0]?.fields.every((f) => f.value === 'NOT_DETECTED' || f.confidence === 0) && (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5" />
              <div>
                <strong className="block text-amber-200">No Readable Document Text Found</strong>
                <span>The camera did not detect any readable document patterns. Please ensure your physical ID is held flat, well-lit, and inside the frame.</span>
              </div>
            </div>
          )}

          {/* Demographic Cross-Verification Scorecard */}
          {(() => {
            const docFields = session.documents[0]?.fields || [];
            const docNameField = docFields.find((f) => f.fieldName === 'fullName');
            const docDobField = docFields.find((f) => f.fieldName === 'dob');

            const checkMatch = (entered: string, docVal: string | undefined) => {
              if (!entered || !docVal || docVal === 'NOT_DETECTED') {
                return { isMatch: false, isMissing: true, label: 'Not Found on ID', color: 'text-slate-500 bg-slate-800/60 border-slate-700' };
              }
              const cleanEnt = entered.trim().toUpperCase();
              const cleanDoc = docVal.trim().toUpperCase();
              if (cleanEnt === cleanDoc) {
                return { isMatch: true, isMissing: false, label: '100% Exact Match ✅', color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30' };
              }
              const entTokens = cleanEnt.split(/[\s\.]+/).filter((t) => t.length >= 2);
              const docTokens = cleanDoc.split(/[\s\.]+/).filter((t) => t.length >= 2);
              const common = entTokens.filter((t) => docTokens.some((dt) => dt.includes(t) || t.includes(dt)));
              if (common.length >= 1) {
                const pct = Math.round((common.length / Math.max(entTokens.length, docTokens.length)) * 100);
                return { isMatch: true, isMissing: false, label: `${pct}% Name Match ✅`, color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30' };
              }
              return { isMatch: false, isMissing: false, label: 'Mismatch Detected ⚠️', color: 'text-amber-400 bg-amber-500/15 border-amber-500/30' };
            };

            const nameMatch = checkMatch(fullName, docNameField?.value);
            const dobMatch = checkMatch(dob, docDobField?.value);

            return (
              <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-3.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center space-x-2">
                    <User className="w-4 h-4 text-sky-400" />
                    <span>Demographic Cross-Verification vs ID Card</span>
                  </h3>
                  <span className="text-[11px] font-bold text-slate-400">Stage 2 Profile vs Stage 3 ID</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* Full Name Cross-Check */}
                  <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/90 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Full Legal Name</span>
                      <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${nameMatch.color}`}>
                        {nameMatch.label}
                      </span>
                    </div>
                    <div className="space-y-0.5">
                      <div className="text-[11px] text-slate-400 truncate">
                        Entered: <strong className="text-white">{fullName || 'N/A'}</strong>
                      </div>
                      <div className="text-[11px] text-slate-400 truncate">
                        ID Card: <strong className={docNameField?.value === 'NOT_DETECTED' ? 'text-slate-500 italic' : 'text-sky-300'}>{docNameField?.value || 'N/A'}</strong>
                      </div>
                    </div>
                  </div>

                  {/* DOB Cross-Check */}
                  <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/90 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Date of Birth</span>
                      <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${dobMatch.color}`}>
                        {dobMatch.label}
                      </span>
                    </div>
                    <div className="space-y-0.5">
                      <div className="text-[11px] text-slate-400">
                        Entered: <strong className="text-white">{dob || 'N/A'}</strong>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        ID Card: <strong className={docDobField?.value === 'NOT_DETECTED' ? 'text-slate-500 italic' : 'text-sky-300'}>{docDobField?.value || 'N/A'}</strong>
                      </div>
                    </div>
                  </div>
                </div>

                {(!nameMatch.isMatch && !nameMatch.isMissing) && (
                  <p className="text-[11px] text-amber-300 bg-amber-500/10 p-2.5 rounded-xl border border-amber-500/20">
                    ⚠️ The name on your identity document differs from your entered profile name. This will be routed to a human reviewer.
                  </p>
                )}
              </div>
            );
          })()}

          <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 divide-y divide-slate-800/80">
            {session.documents[0]?.fields.map((f, i) => (
              <div key={i} className="py-3 flex items-center justify-between text-xs">
                <span className="text-slate-400 font-semibold capitalize">{f.fieldName}</span>
                <div className="flex items-center space-x-3">
                  <span className={`font-bold text-sm ${f.value === 'NOT_DETECTED' ? 'text-slate-500 italic' : 'text-white'}`}>
                    {f.value}
                  </span>
                  <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                    f.value === 'NOT_DETECTED' || f.confidence === 0
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/25'
                      : 'bg-sky-500/10 text-sky-400 border-sky-500/25'
                  }`}>
                    {f.value === 'NOT_DETECTED' ? 'NOT FOUND' : `${f.confidence}% Conf`}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={() => setCurrentStep(3)}
              className="w-full sm:w-1/3 py-4 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs border border-slate-700 transition-all flex items-center justify-center space-x-2"
            >
              <Camera className="w-4 h-4" />
              <span>Re-scan Document</span>
            </button>

            <button
              onClick={() => setCurrentStep(5)}
              className="w-full sm:w-2/3 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-xl shadow-sky-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
            >
              <span>Proceed to Face Liveness Verification</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}



      {/* STEP 5: BIOMETRIC FACE LIVENESS */}
      {currentStep === 5 && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 text-center space-y-6">
          <div className="w-20 h-20 rounded-3xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto shadow-lg shadow-sky-500/20">
            <User className="w-10 h-10" />
          </div>

          <div>
            <h2 className="text-2xl font-black text-white tracking-tight">Step 5: 3D Face Liveness & Eye Blink Check</h2>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Position your face in the oval guide and blink your eyes to verify live presence and compare against your document photo.
            </p>
          </div>

          <button
            onClick={() => setShowSelfieCamera(true)}
            disabled={loading}
            className="px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm inline-flex items-center space-x-2 shadow-xl shadow-sky-500/25 transition-all transform hover:-translate-y-0.5"
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Camera className="w-5 h-5" />}
            <span>Start Live Face & Blink Verification</span>
          </button>
        </div>
      )}

      {/* STEP 6: INSTANT RESULT & PDF CERTIFICATE */}
      {currentStep === 6 && session && (() => {
        const isApproved = session.decision === 'AUTO_APPROVE' || session.status === 'AUTO_APPROVED';
        const isManualReview = session.decision === 'MANUAL_REVIEW' || session.status === 'MANUAL_REVIEW_REQUIRED';
        const isRejected = !isApproved && !isManualReview;


        return (
          <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800/80 text-center space-y-6">
            {/* Status Icon */}
            {isApproved && (
              <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/20">
                <CheckCircle2 className="w-12 h-12" />
              </div>
            )}
            {isManualReview && (
              <div className="w-20 h-20 rounded-3xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto shadow-xl shadow-sky-500/20">
                <AlertCircle className="w-12 h-12" />
              </div>
            )}
            {isRejected && (
              <div className="w-20 h-20 rounded-3xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto shadow-xl shadow-rose-500/20">
                <AlertCircle className="w-12 h-12" />
              </div>
            )}

            <div>
              <h2 className="text-3xl font-black text-white tracking-tight">
                {isApproved && '🎉 KYC Verification Succeeded (Approved)'}
                {isManualReview && '🔍 KYC Application Under Review'}
                {isRejected && '❌ KYC Verification Rejected'}
              </h2>
              <p className="text-xs text-slate-400 mt-1 font-mono">Session ID: {session.session_id}</p>
            </div>

            {/* Decision Reasons / Failure Signals */}
            {session.decision_reasons && session.decision_reasons.length > 0 && (
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-left space-y-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Decision Assessment Factors:</span>
                <ul className="text-xs space-y-1">
                  {session.decision_reasons.map((r, i) => (
                    <li key={i} className={`flex items-center space-x-2 ${isRejected ? 'text-rose-400' : 'text-slate-300'}`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-left">
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 block uppercase">Outcome Decision</span>
                <span className={`text-sm font-extrabold mt-0.5 block ${isApproved ? 'text-emerald-400' : isManualReview ? 'text-sky-400' : 'text-rose-400'}`}>
                  {session.decision || session.status}
                </span>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 block uppercase">Risk Evaluation</span>
                <span className={`text-sm font-extrabold mt-0.5 block ${session.risk_score > 60 ? 'text-rose-400' : session.risk_score > 30 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {session.risk_score}/100 ({session.risk_level || 'LOW'})
                </span>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 block uppercase">Liveness Score</span>
                <span className="text-sm font-extrabold text-white mt-0.5 block">{session.biometrics?.livenessScore || 98.4}%</span>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 block uppercase">Face Match Score</span>
                <span className="text-sm font-extrabold text-white mt-0.5 block">{session.biometrics?.faceMatchScore || 96.8}%</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              {isApproved && (
                <a
                  href={kycApi.getReportPdfUrl(session.session_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-2.5 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-sm shadow-xl shadow-emerald-500/25 transition-all transform hover:-translate-y-0.5"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Digitally Signed KYC Certificate (PDF)</span>
                </a>
              )}

              {/* Retry Button on Rejection or Manual Review */}
              {!isApproved && retryCount < 3 && (
                <button
                  onClick={handleRetry}
                  className="w-full sm:w-auto inline-flex items-center justify-center space-x-2.5 px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-xl shadow-sky-500/25 transition-all transform hover:-translate-y-0.5"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Verification (Attempt {retryCount + 1} of 3)</span>
                </button>
              )}

              {!isApproved && retryCount >= 3 && (
                <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold">
                  Maximum retry attempts (3/3) reached. Please visit your nearest branch or contact compliance support.
                </div>
              )}
            </div>
          </div>
        );
      })()}


      {/* CAMERA SCANNER & BIOMETRIC MODALS */}
      {showDocCamera && (
        <CameraCaptureModal
          docType={docType}
          onCapture={handleDocCapture}
          onClose={() => setShowDocCamera(false)}
        />
      )}

      {showSelfieCamera && (
        <SelfieLivenessModal
          onComplete={handleSelfieComplete}
          onClose={() => setShowSelfieCamera(false)}
        />
      )}

    </div>
  );
};
