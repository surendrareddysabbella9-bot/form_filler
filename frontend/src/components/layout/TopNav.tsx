import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { PlusCircle, Cpu, User } from 'lucide-react';
import { SessionBanner } from '../common/SessionBanner';
import { LoginModal } from '../common/LoginModal';

interface TopNavProps {
  sidebarCollapsed: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({ sidebarCollapsed }) => {
  const location = useLocation();
  const [showLoginModal, setShowLoginModal] = useState(false);

  const getPageTitle = (pathname: string) => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/new-form') return 'New Form Workflow';
    if (pathname.startsWith('/processing')) return 'Processing Documents';
    if (pathname.startsWith('/workspace')) return 'Form Completion Workspace';
    if (pathname.startsWith('/review')) return 'Review & Validation';
    if (pathname.startsWith('/download')) return 'Download Ready';
    if (pathname === '/documents') return 'Session Documents';
    if (pathname === '/forms') return 'Active Forms (Session)';
    if (pathname === '/settings') return 'Settings & Privacy Policy';
    return 'Form Filler';
  };

  const title = getPageTitle(location.pathname);

  return (
    <>
      <header
        className={`fixed top-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 z-20 flex items-center justify-between px-6 transition-all duration-200 ${
          sidebarCollapsed ? 'left-20' : 'left-64'
        }`}
      >
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold text-slate-800">{title}</h1>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          {/* Guest Session Status & Auto-Cleanup Banner */}
          <SessionBanner />

          {/* Backend & AI status pill */}
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium border border-slate-200/60">
            <Cpu className="w-3.5 h-3.5 text-brand-600" />
            <span>Groq AI + Local OCR</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>

          {location.pathname !== '/new-form' && (
            <Link
              to="/new-form"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New Form</span>
            </Link>
          )}

          {/* Visible Login Button — Opens polished Under Construction Modal */}
          <button
            type="button"
            onClick={() => setShowLoginModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 rounded-lg border border-slate-200 transition-colors cursor-pointer"
            title="Account Login (Under Construction)"
          >
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>Login</span>
          </button>
        </div>
      </header>

      {/* Modular Login Placeholder Modal */}
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </>
  );
};
