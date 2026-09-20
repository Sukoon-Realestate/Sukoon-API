'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

interface ToastItem {
  id: string;
  message: string;
  type?: 'success' | 'error' | 'info';
}

interface ToastContextType {
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 left-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto relative overflow-hidden flex items-center justify-between gap-3 px-4 py-3.5 rounded-2xl shadow-2xl border backdrop-blur-md animate-fadeInUp text-xs font-extrabold transition-all ${
              toast.type === 'success'
                ? 'bg-emerald-950/95 text-emerald-100 border-emerald-600/50 glow-teal-sm'
                : toast.type === 'error'
                ? 'bg-rose-950/95 text-rose-100 border-rose-600/50 glow-rose-sm'
                : 'bg-slate-950/95 text-slate-100 border-slate-700/50 glow-blue-sm'
            }`}
          >
            <div className="flex items-center gap-2.5">
              {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
              {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />}
              {toast.type === 'info' && <Info className="w-4 h-4 text-cyan-400 shrink-0" />}
              <span className="leading-snug">{toast.message}</span>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="p-1 hover:opacity-75 transition-opacity cursor-pointer shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>

            {/* Bottom animated progress bar */}
            <div
              className={`absolute bottom-0 left-0 right-0 h-0.5 animate-barGrow ${
                toast.type === 'success'
                  ? 'bg-emerald-400'
                  : toast.type === 'error'
                  ? 'bg-rose-400'
                  : 'bg-cyan-400'
              }`}
            ></div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      showToast: (msg: string) => console.log(msg),
    };
  }
  return context;
};
