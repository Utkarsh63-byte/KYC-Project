import React from 'react';
import { ShieldCheck, UserCheck, LayoutDashboard, Sparkles, Building2, Lock } from 'lucide-react';

interface NavbarProps {
  activeTab: 'customer' | 'reviewer' | 'admin' | 'sandbox';
  setActiveTab: (tab: 'customer' | 'reviewer' | 'admin' | 'sandbox') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-2xl shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3 cursor-pointer select-none" onClick={() => setActiveTab('customer')}>
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-sky-500/25 border border-white/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base text-white tracking-tight">KryptonKYC</span>
              <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30">
                PRO v2.5
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Digital Identity & Biometrics</p>
          </div>
        </div>

        {/* Mode Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1.5 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800/80 backdrop-blur-md">
          <button
            onClick={() => setActiveTab('customer')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
              activeTab === 'customer'
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 glow-blue'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Customer KYC</span>
          </button>

          <button
            onClick={() => setActiveTab('reviewer')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
              activeTab === 'reviewer'
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 glow-blue'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Reviewer Workspace</span>
          </button>

          <button
            onClick={() => setActiveTab('admin')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
              activeTab === 'admin'
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 glow-blue'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Admin Console</span>
          </button>

          <button
            onClick={() => setActiveTab('sandbox')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
              activeTab === 'sandbox'
                ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 shadow-lg shadow-amber-500/25 font-extrabold'
                : 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Executive Demo</span>
          </button>
        </nav>

        {/* Tenant & Security Badges */}
        <div className="flex items-center space-x-2.5">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs font-medium text-slate-300">
            <Building2 className="w-3.5 h-3.5 text-sky-400" />
            <span>Bank ABC International</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold">
            <Lock className="w-3 h-3" />
            <span>Encrypted</span>
          </div>
        </div>

      </div>
    </header>
  );
};
