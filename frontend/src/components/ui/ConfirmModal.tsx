'use client';

import React from 'react';
import { AlertTriangle, CheckCircle2, X, Info } from 'lucide-react';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'success' | 'warning' | 'info';
  children?: React.ReactNode;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'تأكيد الإجراء',
  cancelText = 'إلغاء',
  variant = 'danger',
  children,
}) => {
  if (!isOpen) return null;

  const getIcon = () => {
    switch (variant) {
      case 'danger':
        return <AlertTriangle className="w-6 h-6 text-rose-500" />;
      case 'success':
        return <CheckCircle2 className="w-6 h-6 text-emerald-500" />;
      case 'warning':
        return <AlertTriangle className="w-6 h-6 text-amber-500" />;
      default:
        return <Info className="w-6 h-6 text-teal-500" />;
    }
  };

  const getButtonBg = () => {
    switch (variant) {
      case 'danger':
        return 'bg-rose-500 hover:bg-rose-600 text-white';
      case 'success':
        return 'bg-emerald-500 hover:bg-emerald-600 text-white';
      case 'warning':
        return 'bg-amber-500 hover:bg-amber-600 text-white';
      default:
        return 'bg-teal-600 hover:bg-teal-700 text-white';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div
        className="relative w-full max-w-md bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-2xl p-6 space-y-5 animate-scaleIn text-right glass-card"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 left-4 p-1.5 rounded-xl text-[var(--text-subtle)] hover:bg-[var(--card-hover)] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-[var(--card-hover)] border border-[var(--card-border)] shrink-0 flex items-center justify-center">
            {getIcon()}
          </div>
          <div>
            <h3 className="font-black text-base text-[var(--foreground)] leading-tight">{title}</h3>
            <p className="text-xs font-semibold text-[var(--text-muted)] mt-1">{message}</p>
          </div>
        </div>

        {children && <div className="pt-2">{children}</div>}

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--divider)]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] text-xs font-bold rounded-xl transition-all cursor-pointer btn-press border border-[var(--card-border)]"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-5 py-2 text-xs font-extrabold rounded-xl transition-all shadow-md cursor-pointer btn-press ${getButtonBg()}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
