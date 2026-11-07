import React from 'react';
import { FieldStatus, ConfirmationStatus } from '../../types';
import { CheckCircle2, AlertCircle, AlertTriangle, HelpCircle, FileText, XCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: FieldStatus;
  confirmationStatus?: ConfirmationStatus;
  className?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  confirmationStatus,
  className = '',
  size = 'md',
}) => {
  const isConfirmed = confirmationStatus === 'confirmed';

  const config = {
    confirmed: {
      bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      label: 'Confirmed',
      icon: CheckCircle2,
    },
    extracted: {
      bg: isConfirmed
        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
        : 'bg-blue-50 text-blue-700 border-blue-200',
      label: isConfirmed ? 'Confirmed' : 'Extracted',
      icon: isConfirmed ? CheckCircle2 : FileText,
    },
    needs_review: {
      bg: 'bg-amber-50 text-amber-700 border-amber-200',
      label: 'Needs Review',
      icon: AlertTriangle,
    },
    missing: {
      bg: 'bg-slate-100 text-slate-600 border-slate-200',
      label: 'Missing',
      icon: HelpCircle,
    },
    conflicting: {
      bg: 'bg-purple-50 text-purple-700 border-purple-200',
      label: 'Conflict Detected',
      icon: AlertCircle,
    },
    invalid: {
      bg: 'bg-rose-50 text-rose-700 border-rose-200',
      label: 'Invalid Format',
      icon: XCircle,
    },
  };

  const activeStatus = isConfirmed ? 'confirmed' : status;
  const current = config[activeStatus] || config.missing;
  const Icon = current.icon;

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses} ${className}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{current.label}</span>
    </span>
  );
};
