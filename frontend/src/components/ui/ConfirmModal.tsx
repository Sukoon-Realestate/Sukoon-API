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

const OpenConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen, onClose, onCancel, onConfirm, title, message, description,
  confirmText, confirmLabel, cancelText, cancelLabel, variant, confirmVariant, children,
}) => {
  const dialog = useRef<HTMLDialogElement>(null);
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const [error, setError] = useState(false);
  const close = onClose || onCancel || (() => {});
  const tone = variant || confirmVariant || 'danger';
  const Icon = tone === 'success' ? CheckCircle2 : tone === 'info' ? Info : AlertTriangle;

  useEffect(() => {
    if (isOpen && !dialog.current?.open) dialog.current?.showModal();
    if (!isOpen && dialog.current?.open) dialog.current?.close();
  }, [isOpen]);

  async function confirm() {
    if (inFlight.current) return;
    inFlight.current = true;
    setPending(true);
    setError(false);
    try { await onConfirm(); close(); } catch { setError(true); } finally { inFlight.current = false; setPending(false); }
  }

  return <dialog ref={dialog} className="m-auto w-[calc(100%_-_2rem)] max-w-md max-h-[90dvh] overflow-y-auto rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 text-[var(--foreground)] backdrop:bg-black/50" aria-label={title} onCancel={(event) => { if (inFlight.current) event.preventDefault(); else close(); }}>
    <div className="flex items-start justify-between gap-4"><span className={`inline-flex p-2 rounded-lg ${tone === 'danger' ? 'text-rose-600 bg-rose-50 dark:bg-rose-950 dark:text-rose-300' : 'text-[var(--primary-text)] bg-[var(--primary-subtle)]'}`}><Icon size={22} aria-hidden /></span><button type="button" className="min-h-12 min-w-12 rounded-lg border" disabled={pending} onClick={close} aria-label="إغلاق"><X size={19} /></button></div>
    <h2 className="text-lg font-medium mt-4">{title}</h2><p className="text-sm leading-7 text-[var(--text-muted)] mt-2">{message || description || ''}</p>
    {children && <div className="mt-4">{children}</div>}
    {error && <p role="alert" className="text-sm text-rose-600 dark:text-rose-300 mt-3">لم تتأكد نتيجة الإجراء. راجع الحالة الحالية قبل إعادة الإرسال.</p>}
    <div className="flex items-center justify-end gap-2 mt-6 pt-4 border-t border-[var(--divider)]"><button type="button" disabled={pending} className="min-h-12 rounded-lg border px-4 py-3" onClick={close}>{cancelText || cancelLabel || 'إلغاء'}</button><button type="button" disabled={pending} onClick={() => void confirm()} className={`min-h-12 rounded-lg px-4 py-3 ${tone === 'danger' ? 'bg-rose-700 hover:bg-rose-800 text-white' : 'bg-teal-700 text-white'}`}>{pending ? 'جاري التنفيذ…' : confirmText || confirmLabel || 'تأكيد الإجراء'}</button></div>
  </dialog>;
};

export function ConfirmModal(props: ConfirmModalProps) {
  return props.isOpen ? <OpenConfirmModal {...props} /> : null;
}
