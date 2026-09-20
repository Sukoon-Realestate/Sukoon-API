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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div
        className="relative w-full max-w-md bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-2xl p-6 space-y-5 animate-scaleIn text-right"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 left-4 p-1 rounded-lg text-[var(--text-subtle)] hover:bg-[var(--card-hover)] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="p-3 rounded-full bg-[var(--card-hover)] shrink-0">
            {getIcon()}
          </div>
          <div>
            <h3 className="font-extrabold text-base text-[var(--foreground)]">{title}</h3>
            <p className="text-xs text-[var(--text-subtle)] mt-0.5">{message}</p>
          </div>
        </div>

        {children && <div className="pt-2">{children}</div>}

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--divider)]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] text-xs font-bold rounded-xl transition-colors"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-5 py-2 text-xs font-extrabold rounded-xl transition-all shadow-sm ${getButtonBg()}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
