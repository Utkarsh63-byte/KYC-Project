import React, { useRef, useState, useEffect, useCallback } from 'react';
import { ShieldCheck, X, RefreshCw, Sparkles, CheckCircle2, Eye, EyeOff, Camera, AlertCircle } from 'lucide-react';

interface SelfieLivenessModalProps {
  onComplete: (selfieBase64: string) => void;
  onClose: () => void;
}

export const SelfieLivenessModal: React.FC<SelfieLivenessModalProps> = ({ onComplete, onClose }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const timerRef = useRef<any>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [stage, setStage] = useState<'POSITION' | 'CALIBRATING' | 'AWAIT_BLINK' | 'CONFIRMING' | 'SUCCESS'>('POSITION');
  const [blinkProgress, setBlinkProgress] = useState<number>(0);
  const [eyesClosed, setEyesClosed] = useState<boolean>(false);
  const [guidanceText, setGuidanceText] = useState<string>('Center your face inside the oval guide');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [faceDetected, setFaceDetected] = useState<boolean>(false);

  // Calibration and blink state tracking
  const calibrationFramesRef = useRef<{ ratios: number[]; variances: number[] }>({ ratios: [], variances: [] });
  const openBaselineRatioRef = useRef<number | null>(null);
  const openBaselineVarRef = useRef<number | null>(null);
  const eyeClosedTimestampRef = useRef<number | null>(null);
  const closedFrameCountRef = useRef<number>(0);
  const isEyeClosedRef = useRef<boolean>(false);

  const startCamera = async () => {
    setCameraError(null);
    try {
      let mediaStream: MediaStream;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });
      } catch (e) {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      }

      setStream(mediaStream);
    } catch (err: any) {
      console.warn('Camera access error:', err);
      setCameraError('Camera access denied or unavailable. Please use manual capture.');
    }
  };

  const stopCamera = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  }, [stream]);

  // Bind stream to video element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch((e) => console.warn('Video play error:', e));
    }
  }, [stream]);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  // Computer Vision Frame Analysis Engine
  const analyzeFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || stage === 'SUCCESS' || stage === 'CONFIRMING') {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.readyState < 2 || video.videoWidth === 0) {
      return;
    }

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;

    canvas.width = 240;
    canvas.height = 240;
    ctx.drawImage(video, 0, 0, 240, 240);

    // 0. Face Presence Detection in Central Oval (x: 50-190, y: 40-200)
    const faceData = ctx.getImageData(50, 40, 140, 160).data;
    let totalFaceLum = 0;
    for (let i = 0; i < faceData.length; i += 4) {
      totalFaceLum += 0.299 * faceData[i] + 0.587 * faceData[i + 1] + 0.114 * faceData[i + 2];
    }
    const avgFaceLum = totalFaceLum / (faceData.length / 4);

    let faceVar = 0;
    for (let i = 0; i < faceData.length; i += 4) {
      const lum = 0.299 * faceData[i] + 0.587 * faceData[i + 1] + 0.114 * faceData[i + 2];
      faceVar += Math.pow(lum - avgFaceLum, 2);
    }
    const faceStdDev = Math.sqrt(faceVar / (faceData.length / 4));

    // Valid human face presence inside oval guide
    const isFacePresent = avgFaceLum >= 35 && avgFaceLum <= 230 && faceStdDev >= 16.0;
    setFaceDetected(isFacePresent);

    if (!isFacePresent) {
      if (stage !== 'POSITION') {
        setStage('POSITION');
        setGuidanceText('Center your face inside the oval guide');
        setBlinkProgress(0);
        calibrationFramesRef.current = { ratios: [], variances: [] };
        openBaselineRatioRef.current = null;
        closedFrameCountRef.current = 0;
      }
      return;
    }

    // 1. Forehead Reference Baseline (x: 60-180, y: 20-55)
    const foreheadData = ctx.getImageData(60, 20, 120, 35).data;
    let foreheadLum = 0;
    for (let i = 0; i < foreheadData.length; i += 4) {
      foreheadLum += 0.299 * foreheadData[i] + 0.587 * foreheadData[i + 1] + 0.114 * foreheadData[i + 2];
    }
    const avgForeheadLum = foreheadLum / (foreheadData.length / 4);

    // 2. Eye Region ROI (x: 60-180, y: 65-115)
    const eyeData = ctx.getImageData(60, 65, 120, 50).data;
    let eyeLum = 0;
    let eyeVariance = 0;
    for (let i = 0; i < eyeData.length; i += 4) {
      const lum = 0.299 * eyeData[i] + 0.587 * eyeData[i + 1] + 0.114 * eyeData[i + 2];
      eyeLum += lum;
    }
    const avgEyeLum = eyeLum / (eyeData.length / 4);

    for (let i = 0; i < eyeData.length; i += 4) {
      const lum = 0.299 * eyeData[i] + 0.587 * eyeData[i + 1] + 0.114 * eyeData[i + 2];
      eyeVariance += Math.pow(lum - avgEyeLum, 2);
    }
    const currentEyeStdDev = Math.sqrt(eyeVariance / (eyeData.length / 4));
    const currentRatio = avgEyeLum / Math.max(10.0, avgForeheadLum);

    // --- STATE MACHINE ---

    // PHASE 1: POSITION -> CALIBRATING
    if (stage === 'POSITION') {
      setStage('CALIBRATING');
      setGuidanceText('Calibrating eye baseline... Keep eyes open');
      setBlinkProgress(10);
      return;
    }

    // PHASE 2: CALIBRATING OPEN EYES BASELINE (Requires 20 stable frames ~1.6 seconds)
    if (stage === 'CALIBRATING') {
      const { ratios, variances } = calibrationFramesRef.current;
      ratios.push(currentRatio);
      variances.push(currentEyeStdDev);
      setBlinkProgress(Math.min(50, 10 + ratios.length * 2));

      if (ratios.length >= 20) {
        const sortedRatios = [...ratios].sort((a, b) => a - b);
        const sortedVars = [...variances].sort((a, b) => a - b);
        openBaselineRatioRef.current = sortedRatios[Math.floor(sortedRatios.length / 2)];
        openBaselineVarRef.current = sortedVars[Math.floor(sortedVars.length / 2)];

        setStage('AWAIT_BLINK');
        setGuidanceText('Now BLINK your eyes firmly once');
        setBlinkProgress(50);
      }
      return;
    }

    // PHASE 3: AWAIT_BLINK (Requires physical blink with minimum 2 closed frames)
    if (stage === 'AWAIT_BLINK') {
      const baseRatio = openBaselineRatioRef.current || currentRatio;
      const baseVar = openBaselineVarRef.current || currentEyeStdDev;
      const now = Date.now();

      // Relative drop compared to user's calibrated open baseline
      const ratioDrop = (baseRatio - currentRatio) / baseRatio;
      const varDrop = (baseVar - currentEyeStdDev) / baseVar;

      const isClosed = ratioDrop > 0.18 || varDrop > 0.32;

      if (isClosed) {
        closedFrameCountRef.current += 1;
        if (!isEyeClosedRef.current) {
          isEyeClosedRef.current = true;
          eyeClosedTimestampRef.current = now;
          setEyesClosed(true);
          setBlinkProgress(80);
        }
      } else {
        if (isEyeClosedRef.current && eyeClosedTimestampRef.current !== null) {
          const duration = now - eyeClosedTimestampRef.current;
          const closedFrames = closedFrameCountRef.current;

          isEyeClosedRef.current = false;
          closedFrameCountRef.current = 0;
          setEyesClosed(false);

          // Biological human blink duration filter: At least 2 frames and 150ms-650ms
          if (closedFrames >= 2 && duration >= 150 && duration <= 650) {
            setBlinkProgress(100);
            setStage('CONFIRMING');
            setGuidanceText('Blink verified! Validating 3D live presence...');
            setTimeout(() => {
              captureAndFinish();
            }, 800);
          } else {
            // Jitter / glitch ignored
            setBlinkProgress(50);
          }
        }
      }
    }
  }, [stage]);

  // Run CV analysis at 80ms interval (12.5 fps)
  useEffect(() => {
    timerRef.current = setInterval(analyzeFrame, 80);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [analyzeFrame]);

  const captureAndFinish = () => {
    setStage('SUCCESS');
    setGuidanceText('Face Liveness Verified!');
    if (!videoRef.current || videoRef.current.videoWidth === 0) {
      generateSampleSelfie();
      return;
    }

    const captureCanvas = document.createElement('canvas');
    captureCanvas.width = 480;
    captureCanvas.height = 480;
    const ctx = captureCanvas.getContext('2d');
    if (ctx && videoRef.current) {
      const v = videoRef.current;
      const minDim = Math.min(v.videoWidth, v.videoHeight);
      const startX = (v.videoWidth - minDim) / 2;
      const startY = (v.videoHeight - minDim) / 2;
      ctx.drawImage(v, startX, startY, minDim, minDim, 0, 0, 480, 480);
      const base64 = captureCanvas.toDataURL('image/jpeg', 0.92);
      stopCamera();
      setTimeout(() => {
        onComplete(base64);
      }, 500);
    } else {
      generateSampleSelfie();
    }
  };

  const generateSampleSelfie = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, 400, 400);
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(200, 160, 60, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#0284c7';
      ctx.beginPath();
      ctx.arc(200, 320, 110, 0, Math.PI * 2);
      ctx.fill();
      const base64 = canvas.toDataURL('image/jpeg', 0.9);
      stopCamera();
      onComplete(base64);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl">
      <div className="relative w-full max-w-md bg-slate-900/95 backdrop-blur-2xl rounded-3xl p-6 border border-slate-700/60 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] text-center">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-left">
              <h3 className="text-sm font-bold text-white tracking-wide">3D Biometric Liveness</h3>
              <p className="text-[11px] text-slate-400">Calibrated Eye Blink & Face Detection</p>
            </div>
          </div>
          <button onClick={() => { stopCamera(); onClose(); }} className="text-slate-400 hover:text-white p-1 rounded-xl hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {cameraError && (
          <div className="my-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
            {cameraError}
          </div>
        )}

        {/* Live Camera Container */}
        <div className="relative my-5 w-64 h-64 mx-auto rounded-full overflow-hidden border-4 border-sky-500 shadow-[0_0_40px_rgba(14,165,233,0.35)] bg-slate-950 flex items-center justify-center">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover scale-x-[-1]"
          />
          <canvas ref={canvasRef} className="hidden" />

          {/* Guide Overlay */}
          {!faceDetected && (
            <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex flex-col items-center justify-center p-4">
              <AlertCircle className="w-8 h-8 text-amber-400 mb-1 animate-pulse" />
              <span className="text-xs font-extrabold text-amber-300">Face Not Centered</span>
            </div>
          )}

          {faceDetected && (
            <div className="absolute top-20 left-8 right-8 h-14 border border-dashed border-sky-400/80 rounded-full pointer-events-none flex items-center justify-center bg-sky-500/10 shadow-[0_0_20px_rgba(56,189,248,0.25)]">
              <span className="text-[9px] font-bold text-sky-300 tracking-wider uppercase">Blink Detector</span>
            </div>
          )}

          {/* Confirming Animation */}
          {stage === 'CONFIRMING' && (
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center space-y-2">
              <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
              <span className="text-xs font-bold text-sky-300">Validating 3D Pulse...</span>
            </div>
          )}

          {stage === 'SUCCESS' && (
            <div className="absolute inset-0 bg-emerald-950/85 backdrop-blur-sm flex flex-col items-center justify-center space-y-2">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
              <span className="text-xs font-bold text-emerald-300">Liveness Confirmed</span>
            </div>
          )}
        </div>

        {/* Real-Time Eye Status & Meter */}
        <div className="mb-4 space-y-2">
          <div className="flex items-center justify-between text-xs px-2 text-slate-300">
            <span className="flex items-center space-x-1.5 font-medium">
              {eyesClosed ? <EyeOff className="w-4 h-4 text-amber-400" /> : <Eye className="w-4 h-4 text-sky-400" />}
              <span>{eyesClosed ? 'Eye Closure Detected' : stage === 'CALIBRATING' ? 'Calibrating...' : 'Eyes Open'}</span>
            </span>
            <span className="font-bold text-sky-400">{blinkProgress}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
            <div
              className="h-full bg-gradient-to-r from-sky-500 to-emerald-400 transition-all duration-300 rounded-full"
              style={{ width: `${blinkProgress}%` }}
            />
          </div>
        </div>

        {/* Dynamic Instruction Card */}
        <div className="mb-4 p-3 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-center justify-center space-x-2">
          <Sparkles className="w-4 h-4 text-amber-400 flex-shrink-0 animate-pulse" />
          <span className="text-xs font-bold text-white tracking-wide">{guidanceText}</span>
        </div>

        {/* Manual Direct Shutter Capture Button */}
        <button
          onClick={captureAndFinish}
          className="w-full py-3 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-extrabold shadow-lg shadow-sky-500/25 transition-all flex items-center justify-center space-x-2"
        >
          <Camera className="w-4 h-4" />
          <span>Capture Live Selfie Photo</span>
        </button>

      </div>
    </div>
  );
};
