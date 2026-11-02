'use client';

import React, { useState, useEffect, useRef } from 'react';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { Search } from 'lucide-react';
import { fetchTransactions } from '@/lib/api/financials';
import { Pagination } from '@/components/ui/Pagination';
import { PaginatedResponse, TransactionItem } from '@/lib/api/types';

type TransactionStatus = 'all' | 'paid' | 'pending' | 'refunded';
type TransactionPage = PaginatedResponse<TransactionItem> & {
  page: number;
  per_page: number;
  total_pages: number;
};

function transactionPage(response: unknown, requestedPage: number): TransactionPage {
  const value = response as Partial<TransactionPage> | null;
  if (!value || !Array.isArray(value.results) ||
      !Number.isSafeInteger(value.page) || value.page !== requestedPage ||
      !Number.isSafeInteger(value.per_page) || value.per_page! < 1 ||
      !Number.isSafeInteger(value.count) || value.count! < 0 ||
      !Number.isSafeInteger(value.total_pages) || value.total_pages! < 1) {
    throw new Error('Invalid transaction pagination');
  }
  const { page, per_page: perPage, count, total_pages: totalPages } = value as TransactionPage;
  if (totalPages !== Math.max(1, Math.ceil(count / perPage)) || page > totalPages ||
      value.results.length !== Math.min(perPage, Math.max(0, count - (page - 1) * perPage)) ||
      value.next !== (page < totalPages ? `?page=${page + 1}` : null) ||
      value.previous !== (page > 1 ? `?page=${page - 1}` : null)) {
    throw new Error('Invalid transaction pagination');
  }
  return value as TransactionPage;
}

export default function FinancialTransactionsPage() {
  const [query, setQuery] = useState({ status: 'all' as TransactionStatus, search: '', page: 1 });
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; page: TransactionPage | null; failed: boolean }>({
    key: '', page: null, failed: false,
  });
  const requestVersion = useRef(0);
  const requestKey = JSON.stringify([query.status, query.search, query.page, retry]);
  const activeTab = query.status;
  const searchQuery = query.search;
  const isLoading = result.key !== requestKey;
  const hasError = !isLoading && result.failed;
  const currentPage = !isLoading && !hasError ? result.page : null;
  const transactions = currentPage?.results ?? [];

  function filter(status: TransactionStatus, search: string) {
    if (status === query.status && search === query.search) return;
    requestVersion.current += 1;
    setQuery({ status, search, page: 1 });
  }

  function changePage(page: number) {
    if (!currentPage || !Number.isSafeInteger(page) || page < 1 ||
        page > currentPage.total_pages || page === query.page) return;
    requestVersion.current += 1;
    setQuery({ ...query, page });
  }

  useEffect(() => {
    let isCancelled = false;
    const version = ++requestVersion.current;
    const timer = setTimeout(async () => {
      try {
        const response = await fetchTransactions({
          status: query.status,
          search: query.search.trim() || undefined,
          page: query.page,
        });
        const page = transactionPage(response, query.page);
        if (!isCancelled && version === requestVersion.current) {
          setResult({ key: requestKey, page, failed: false });
        }
      } catch {
        if (!isCancelled && version === requestVersion.current) {
          setResult({ key: requestKey, page: null, failed: true });
        }
      }
    }, 300);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [query.status, query.search, query.page, requestKey]);

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="سجل المعاملات المالية"
        subtitle="تتبع التحويلات الملاية، إيجارات المنصة ورسوم التوثيق والاسترداد"
      />

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-80">
              <input
                type="text"
                placeholder="بحث برقم المعاملة..."
                value={searchQuery}
                aria-label="بحث برقم المعاملة"
                onChange={(e) => filter(activeTab, e.target.value)}
                className="w-full pl-4 pr-10 py-2 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all placeholder:text-[var(--text-subtle)] text-[var(--foreground)]"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3" />
            </div>

          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto justify-end">
            <button
              type="button"
              aria-pressed={activeTab === 'all'}
              onClick={() => filter('all', searchQuery)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                activeTab === 'all'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              الكل
            </button>
            <button
              type="button"
              aria-pressed={activeTab === 'paid'}
              onClick={() => filter('paid', searchQuery)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                activeTab === 'paid'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مدفوع
            </button>
            <button
              type="button"
              aria-pressed={activeTab === 'pending'}
              onClick={() => filter('pending', searchQuery)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                activeTab === 'pending'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              معلق
            </button>
            <button
              type="button"
              aria-pressed={activeTab === 'refunded'}
              onClick={() => filter('refunded', searchQuery)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                activeTab === 'refunded'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مسترد
            </button>
          </div>
        </div>

        {hasError && (
          <div role="alert" className="rounded-xl border border-rose-300 p-4 text-sm text-[var(--foreground)]">
            <p>تعذر تحميل المعاملات. أعد المحاولة لقراءة الصفحة الحالية.</p>
            <button
              type="button"
              onClick={() => { requestVersion.current += 1; setRetry((value) => value + 1); }}
              className="mt-2 rounded-lg border border-[var(--card-border)] px-3 py-2 font-bold focus-visible:outline-2 focus-visible:outline-teal-600"
            >
              إعادة المحاولة
            </button>
          </div>
        )}

        {/* Transactions Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <div aria-busy={isLoading}>
          <TableScroll>
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">TXN ID</th>
                  <th className="py-4 px-6">الوصف</th>
                  <th className="py-4 px-6">المالك</th>
                  <th className="py-4 px-6">المستأجر</th>
                  <th className="py-4 px-6">المبلغ</th>
                  <th className="py-4 px-6">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-[var(--text-subtle)] font-medium">
                      جاري تحميل المعاملات...
                    </td>
                  </tr>
                ) : hasError ? null : transactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-[var(--text-subtle)] font-medium">
                      لا توجد معاملات مطابقة
                    </td>
                  </tr>
                ) : (
                  transactions.map((txn) => (
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
                  ))
                )}
              </tbody>
            </table>
          </TableScroll>
          </div>
          {currentPage && (
            <nav aria-label="صفحات المعاملات المالية">
              <p role="status" aria-live="polite" className="px-4 pt-3 text-xs text-[var(--text-muted)]">
                الصفحة {currentPage.page} من {currentPage.total_pages} — إجمالي المعاملات: {currentPage.count}
              </p>
              <Pagination
                currentPage={currentPage.page}
                totalPages={currentPage.total_pages}
                totalItems={currentPage.count}
                itemsPerPage={currentPage.per_page}
                onPageChange={changePage}
              />
            </nav>
          )}
        </div>
      </div>
    </div>
  );
}
