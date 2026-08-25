import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { CustomerKYCFlow } from './pages/CustomerKYCFlow';
import { ReviewerPortal } from './pages/ReviewerPortal';
import { AdminConsole } from './pages/AdminConsole';
import { ExecutiveDemoSandbox } from './pages/ExecutiveDemoSandbox';

export function App() {
  const [activeTab, setActiveTab] = useState<'customer' | 'reviewer' | 'admin' | 'sandbox'>('customer');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 pb-16">
        {activeTab === 'customer' && <CustomerKYCFlow />}
        {activeTab === 'reviewer' && <ReviewerPortal />}
        {activeTab === 'admin' && <AdminConsole />}
        {activeTab === 'sandbox' && <ExecutiveDemoSandbox />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Enterprise Digital KYC Platform v2.4 — Powered by AWS AI & OpenCV</span>
          <span>Compliant with RBI KYC Directions & Data Protection Standards</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
