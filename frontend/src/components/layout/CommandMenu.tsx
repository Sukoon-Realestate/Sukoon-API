'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { adminPath } from '@/lib/basePath';
import { searchAdminNavigation } from '../../lib/admin-navigation';
import { canOpenAdminPath } from '../../lib/admin-access';

export function CommandMenu({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const router = useRouter();
  const { user } = useAuth();
  const results = searchAdminNavigation(query).filter(item => canOpenAdminPath(user?.allowedPaths, item.href));
  useEffect(() => {
    if (open && !dialog.current?.open) dialog.current?.showModal();
    if (!open && dialog.current?.open) dialog.current?.close();
  }, [open]);
  useEffect(() => { document.getElementById(`command-${selected}`)?.scrollIntoView({ block: 'nearest' }); }, [selected]);
  function navigate(href: string) { onClose(); router.push(adminPath(href)); }
  return <dialog ref={dialog} dir="rtl" className="m-auto max-h-[85dvh] w-[calc(100%_-_2rem)] max-w-xl overflow-y-auto rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 text-[var(--foreground)] backdrop:bg-black/50"
    onCancel={onClose} aria-labelledby="command-title">
    <div className="flex items-center gap-3 border-b border-[var(--divider)] pb-3">
      <Search size={20} className="shrink-0" aria-hidden /><label id="command-title" className="sr-only" htmlFor="admin-command-input">البحث في أقسام الإدارة</label>
      <input id="admin-command-input" autoFocus className="min-h-12 min-w-0 flex-1 bg-transparent" value={query} onChange={event => { setQuery(event.target.value); setSelected(0); }} placeholder="اسم القسم…"
        role="combobox" aria-autocomplete="list" aria-expanded="true" aria-controls="admin-command-results" aria-activedescendant={results[selected] ? `command-${selected}` : undefined}
        onKeyDown={event => {
          if (event.key === 'ArrowDown') { event.preventDefault(); setSelected(value => Math.max(0, Math.min(value + 1, results.length - 1))); }
          if (event.key === 'ArrowUp') { event.preventDefault(); setSelected(value => Math.max(value - 1, 0)); }
          if (event.key === 'Enter' && results[selected]) { event.preventDefault(); navigate(results[selected].href); }
        }} />
      <button className="min-h-12 min-w-12" onClick={onClose} aria-label="إغلاق البحث"><X className="mx-auto" size={20} /></button>
    </div>
    <div id="admin-command-results" role="listbox" aria-label="الأقسام" className="my-3 space-y-2">
      {results.map((item, index) => { const Icon = item.icon; return <button key={item.href} id={`command-${index}`} type="button" role="option" aria-selected={index === selected}
        className={`flex min-h-12 w-full items-start gap-3 rounded-lg p-3 text-start ${index === selected ? 'bg-[var(--card-hover)]' : ''}`}
        onClick={() => navigate(item.href)} onMouseEnter={() => setSelected(index)}>
        <Icon size={20} className="shrink-0" aria-hidden /><span><strong className="block">{item.title}</strong><small>{item.group} / {item.description}</small></span>
      </button>; })}
      {!results.length && <p className="p-4">لا توجد أقسام مخولة مطابقة. جرّب اسمًا آخر.</p>}
    </div>
    <p className="border-t pt-3 text-xs">الأسهم للتنقل، Enter للفتح، Esc للإغلاق.</p>
  </dialog>;
}
