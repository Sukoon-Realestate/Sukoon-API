'use client';
import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';
import type React from 'react';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose?: () => void;
  onCancel?: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message?: string;
  description?: string;
  confirmText?: string;
  confirmLabel?: string;
  cancelText?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'success' | 'warning' | 'info' | string;
  confirmVariant?: 'danger' | 'success' | 'warning' | 'info' | string;
  children?: React.ReactNode;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen, onClose, onCancel, onConfirm, title, message, description,
  confirmText, confirmLabel, cancelText, cancelLabel, variant, confirmVariant, children,
}) => {
  const dialog = useRef<HTMLDialogElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(false);
  const close = onClose || onCancel || (() => {});
  const tone = variant || confirmVariant || 'danger';
  const Icon = tone === 'success' ? CheckCircle2 : tone === 'info' ? Info : AlertTriangle;

  useEffect(() => {
    if (isOpen && !dialog.current?.open) dialog.current?.showModal();
    if (!isOpen && dialog.current?.open) dialog.current?.close();
  }, [isOpen]);

  async function confirm() {
    setPending(true);
    setError(false);
    try { await onConfirm(); close(); } catch { setError(true); } finally { setPending(false); }
  }

  return <dialog ref={dialog} className="admin-confirm-dialog" aria-label={title} onCancel={(event) => { if (pending) event.preventDefault(); else close(); }}>
    <div className="flex items-start justify-between gap-4"><span className={`inline-flex p-2 rounded-lg ${tone === 'danger' ? 'text-rose-600 bg-rose-50 dark:bg-rose-950 dark:text-rose-300' : 'text-[var(--primary-text)] bg-[var(--primary-subtle)]'}`}><Icon size={22} aria-hidden /></span><button type="button" className="admin-icon-button" disabled={pending} onClick={close} aria-label="إغلاق"><X size={19} /></button></div>
    <h2 className="text-lg font-medium mt-4">{title}</h2><p className="text-sm leading-7 text-[var(--text-muted)] mt-2">{message || description || ''}</p>
    {children && <div className="mt-4">{children}</div>}
    {error && <p role="alert" className="text-sm text-rose-600 dark:text-rose-300 mt-3">تعذر إكمال الإجراء. حاول مرة أخرى.</p>}
    <div className="flex items-center justify-end gap-2 mt-6 pt-4 border-t border-[var(--divider)]"><button type="button" disabled={pending} className="admin-button admin-button-secondary" onClick={close}>{cancelText || cancelLabel || 'إلغاء'}</button><button type="button" disabled={pending} onClick={() => void confirm()} className={`admin-button ${tone === 'danger' ? 'bg-rose-700 hover:bg-rose-800 text-white' : 'admin-button-primary'}`}>{pending ? 'جاري التنفيذ…' : confirmText || confirmLabel || 'تأكيد الإجراء'}</button></div>
  </dialog>;
};
