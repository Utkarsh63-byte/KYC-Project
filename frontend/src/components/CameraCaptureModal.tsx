import React, { useRef, useState, useEffect } from 'react';
import { Camera, X, RefreshCw, CheckCircle2, AlertTriangle, Upload } from 'lucide-react';

interface CameraCaptureModalProps {
  docType: string;
  onCapture: (file: File) => void;
  onClose: () => void;
}

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({ docType, onCapture, onClose }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [guidance, setGuidance] = useState<string>('Hold document inside frame');
  const [qualityFeedback, setQualityFeedback] = useState<'GOOD' | 'WARNNING'>('GOOD');

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      setCameraError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setCameraError('Camera permission denied or camera device unavailable. You can upload a document image below.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `${docType.toLowerCase()}_capture.jpg`, { type: 'image/jpeg' });
          stopCamera();
          onCapture(file);
        }
      }, 'image/jpeg', 0.95);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      stopCamera();
      onCapture(e.target.files[0]);
    }
  };

  const loadSampleDocument = () => {
    // Generate synthetic canvas document image for testing
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 500;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, 800, 500);
      
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 4;
      ctx.strokeRect(20, 20, 760, 460);

      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 24px sans-serif';
      ctx.fillText(`INCOME TAX DEPARTMENT — ${docType.toUpperCase()}`, 50, 70);

      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('Name: RAHUL SHARMA', 50, 150);
      ctx.fillText('Father: VIKRAM SHARMA', 50, 200);
      ctx.fillText('DOB: 15/08/1992', 50, 250);
      ctx.fillText('ID No: ABCPS1234K', 50, 300);

      ctx.fillStyle = '#334155';
      ctx.fillRect(550, 100, 180, 220);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('PORTRAIT', 580, 220);

      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `sample_${docType.toLowerCase()}.jpg`, { type: 'image/jpeg' });
          stopCamera();
          onCapture(file);
        }
      }, 'image/jpeg', 0.95);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-2xl glass-panel rounded-2xl p-6 border border-slate-800 shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <Camera className="w-5 h-5 text-sky-400" />
              <span>Capture {docType} Document</span>
            </h3>
            <p className="text-xs text-slate-400">Position the document within the clear rectangle guide</p>
          </div>
          <button onClick={() => { stopCamera(); onClose(); }} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Camera Container */}
        <div className="relative my-4 aspect-video bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center border border-slate-800">
          {cameraError ? (
            <div className="text-center px-6">
              <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-2" />
              <p className="text-sm text-slate-300 mb-4">{cameraError}</p>
            </div>
          ) : (
            <>
              <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              
              {/* Document Framing Overlay */}
              <div className="absolute inset-8 border-2 border-dashed border-sky-400/80 rounded-lg pointer-events-none flex flex-col justify-between p-4 shadow-[0_0_50px_rgba(56,189,248,0.2)]">
                <div className="flex justify-between">
                  <div className="w-6 h-6 border-t-4 border-l-4 border-sky-400"></div>
                  <div className="w-6 h-6 border-t-4 border-r-4 border-sky-400"></div>
                </div>
                <div className="flex justify-between">
                  <div className="w-6 h-6 border-b-4 border-l-4 border-sky-400"></div>
                  <div className="w-6 h-6 border-b-4 border-r-4 border-sky-400"></div>
                </div>
              </div>

              {/* Dynamic Feedback Banner */}
              <div className="absolute bottom-4 px-4 py-1.5 rounded-full bg-slate-950/80 backdrop-blur-md border border-slate-700 text-xs font-semibold text-sky-400 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{guidance}</span>
              </div>
            </>
          )}
        </div>

        <canvas ref={canvasRef} className="hidden" />

        {/* Action Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          {!cameraError && (
            <button
              onClick={capturePhoto}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-sky-600/30 transition-all"
            >
              <Camera className="w-4 h-4" />
              <span>Capture Image</span>
            </button>
          )}

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <label className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium cursor-pointer border border-slate-700 flex items-center justify-center space-x-2">
              <Upload className="w-4 h-4 text-slate-400" />
              <span>Upload File</span>
              <input type="file" accept="image/*,.pdf" onChange={handleFileUpload} className="hidden" />
            </label>

            <button
              onClick={loadSampleDocument}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-indigo-900/40 hover:bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 text-xs font-medium flex items-center justify-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
              <span>Use Test Sample</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
