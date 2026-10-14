'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, ArrowUpLeft, X } from 'lucide-react';
import { searchAdminNavigation } from '@/lib/admin-navigation';
import { adminPath } from '@/lib/basePath';

export function CommandMenu({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const router = useRouter();
  const results = searchAdminNavigation(query);

  useEffect(() => {
    if (open && !dialog.current?.open) dialog.current?.showModal();
    if (!open && dialog.current?.open) dialog.current?.close();
  }, [open]);

  useEffect(() => {
    document.getElementById(`command-${selected}`)?.scrollIntoView({ block: 'nearest' });
  }, [selected]);

  function navigate(href: string) { onClose(); router.push(adminPath(href)); }

  return <dialog ref={dialog} className="admin-command-dialog" onCancel={onClose} onClick={(event) => { if (event.currentTarget === event.target) onClose(); }} aria-labelledby="command-title">
    <div className="admin-command-search"><Search size={20} aria-hidden /><label id="command-title" className="sr-only" htmlFor="admin-command-input">البحث في أقسام الإدارة</label>
      <input id="admin-command-input" autoFocus value={query} onChange={(event) => { setQuery(event.target.value); setSelected(0); }} placeholder="إلى أين تريد الانتقال؟" role="combobox" aria-autocomplete="list" aria-expanded="true" aria-controls="admin-command-results" aria-activedescendant={results[selected] ? `command-${selected}` : undefined} onKeyDown={(event) => {
        if (event.key === 'ArrowDown') { event.preventDefault(); setSelected((value) => Math.max(0, Math.min(value + 1, results.length - 1))); }
        if (event.key === 'ArrowUp') { event.preventDefault(); setSelected((value) => Math.max(value - 1, 0)); }
        if (event.key === 'Enter' && results[selected]) { event.preventDefault(); navigate(results[selected].href); }
      }} />
      <button className="admin-icon-button" onClick={onClose} aria-label="إغلاق البحث"><X size={18} /></button>
    </div>
    <div id="admin-command-results" role="listbox" aria-label="الأقسام" className="admin-command-results">
      {results.length ? results.map((item, index) => { const Icon = item.icon; return <button key={item.href} id={`command-${index}`} type="button" role="option" aria-selected={index === selected} className={`admin-command-result ${index === selected ? 'is-selected' : ''}`} onClick={() => navigate(item.href)} onMouseEnter={() => setSelected(index)}>
        <Icon size={20} aria-hidden /><span><strong>{item.title}</strong><small>{item.group} / {item.description}</small></span><ArrowUpLeft size={16} aria-hidden />
      </button>; }) : <p className="p-8 text-center text-sm text-[var(--text-muted)]">لا توجد نتائج. جرّب اسم قسم مثل العقارات أو المستخدمين.</p>}
    </div>
    <div className="admin-command-footer">استخدم الأسهم للتنقل و Enter للفتح <kbd>Esc للإغلاق</kbd></div>
  </dialog>;
}
