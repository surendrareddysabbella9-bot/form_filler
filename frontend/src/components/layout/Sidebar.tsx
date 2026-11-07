import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Files,
  FileCheck2,
  Settings,
  HelpCircle,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'New Form', path: '/new-form', icon: PlusCircle },
    { label: 'Active Forms', path: '/forms', icon: FileCheck2 },
    { label: 'Session Documents', path: '/documents', icon: Files },
    { label: 'Settings & Policy', path: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-30 flex flex-col bg-white border-r border-slate-200 transition-all duration-200 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100">
        <NavLink to="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-white shadow-sm flex-shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-slate-900 text-sm tracking-tight leading-tight">
                Form Filler
              </span>
              <span className="text-[11px] text-slate-400 font-medium">AI Document Engine</span>
            </div>
          )}
        </NavLink>
        <button
          onClick={onToggle}
          className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Main Navigation Links */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </div>

      {/* Footer / Support */}
      <div className="p-3 border-t border-slate-100">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors"
        >
          <HelpCircle className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>Support & Guide</span>}
        </NavLink>
      </div>
    </aside>
  );
};
