'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Search, FileSpreadsheet } from 'lucide-react';
import { mockTransactions } from '@/data/mockData';

export default function FinancialTransactionsPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'paid' | 'pending' | 'refunded'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTxns = mockTransactions.filter((txn) => {
    const matchesSearch =
      txn.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.description.includes(searchQuery) ||
      txn.tenant.includes(searchQuery);

    if (!matchesSearch) return false;

    if (activeTab === 'paid') return txn.status === 'مدفوع';
    if (activeTab === 'pending') return txn.status === 'معلق';
    if (activeTab === 'refunded') return txn.status === 'مسترد';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="سجل المعاملات المالية"
        subtitle="تتبع التحويلات الملاية، إيجارات المنصة ورسوم التوثيق والاسترداد"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-80">
              <input
                type="text"
                placeholder="بحث برقم المعاملة..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-4 pr-10 py-2 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all placeholder:text-[var(--text-subtle)]"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3" />
            </div>

            <button className="flex items-center gap-2 bg-[var(--card-bg)] px-4 py-2 rounded-xl border border-[var(--card-border)] text-xs font-bold text-[var(--foreground)] hover:bg-[var(--card-hover)] transition-colors shadow-[var(--shadow-card)]">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              <span>تصدير Excel</span>
            </button>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto justify-end">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                activeTab === 'all'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              الكل
            </button>
            <button
              onClick={() => setActiveTab('paid')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                activeTab === 'paid'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مدفوع
            </button>
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                activeTab === 'pending'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              معلق
            </button>
            <button
              onClick={() => setActiveTab('refunded')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                activeTab === 'refunded'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مسترد
            </button>
          </div>
        </div>

        {/* Transactions Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-slate-200 text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">TXN ID</th>
                  <th className="py-4 px-6">الوصف</th>
                  <th className="py-4 px-6">المالك</th>
                  <th className="py-4 px-6">المستأجر</th>
                  <th className="py-4 px-6">المبلغ</th>
                  <th className="py-4 px-6">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs">
                {filteredTxns.map((txn) => (
                  <tr
                    key={txn.id}
                    className="hover:bg-[var(--table-row-hover)] transition-colors"
                  >
                    <td className="py-4 px-6 font-mono font-bold text-[var(--foreground)] dir-ltr text-right">
                      {txn.id}
                    </td>
                    <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                      {txn.description}
                    </td>
                    <td className="py-4 px-6 text-[var(--text-muted)] font-medium">
                      {txn.landlord}
                    </td>
                    <td className="py-4 px-6 text-[var(--foreground)] font-semibold">
                      {txn.tenant}
                    </td>
                    <td
                      className={`py-4 px-6 font-extrabold font-mono dir-ltr text-right text-sm ${
                        txn.isPositive ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {txn.amount}
                    </td>
                    <td className="py-4 px-6 font-bold">
                      {txn.status === 'مدفوع' && (
                        <span className="text-emerald-600">مدفوع</span>
                      )}
                      {txn.status === 'معلق' && (
                        <span className="text-amber-500">معلق</span>
                      )}
                      {txn.status === 'مسترد' && (
                        <span className="text-rose-600">مسترد</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
