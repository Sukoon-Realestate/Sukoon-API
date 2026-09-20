'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Send, CheckCircle, AlertOctagon } from 'lucide-react';
import { mockSupportTickets } from '@/data/mockData';

export default function SupportTicketDetailPage() {
  const params = useParams();
  const ticketId = (params?.id as string) || 'SUP-201';

  const ticket =
    mockSupportTickets.find((t) => t.id === ticketId) || mockSupportTickets[0];

  const [messages, setMessages] = useState([
    {
      id: 'm1',
      sender: 'user',
      text: 'أهلاً، أنا بحاول أؤكد زيارة من ساعتين ومش بتتأكد، فيه مشكلة؟',
      time: 'منذ ساعتين',
    },
    {
      id: 'm2',
      sender: 'agent',
      text: 'أهلاً سارة، شكراً للتواصل. هنشوف الموضوع دلوقتي وهنرد عليك خلال ساعة.',
      time: 'منذ ساعة',
    },
  ]);

  const [newReply, setNewReply] = useState('');
  const [internalNote, setInternalNote] = useState('');

  const handleSendMessage = () => {
    if (!newReply.trim()) return;
    setMessages((prev) => [
      ...prev,
      {
        id: `m-${Date.now()}`,
        sender: 'agent',
        text: newReply,
        time: 'الآن',
      },
    ]);
    setNewReply('');
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title={`تذكرة ${ticket.id} – تفاصيل`}
        subtitle="متابعة محادثة الدعم، الملاحظات الداخلية وإغلاق أو تصعيد التذكرة"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Ticket Info (4 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4 text-xs">
            <h3 className="font-extrabold text-[var(--foreground)] text-sm border-b border-[var(--divider)] pb-3">
              معلومات التذكرة
            </h3>

            <div className="flex items-center justify-between">
              <span className="text-[var(--text-subtle)] font-medium">رقم التذكرة</span>
              <span className="font-bold font-mono text-teal-700 dir-ltr text-sm">
                {ticket.id}
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">الموضوع</span>
              <span className="font-bold text-[var(--foreground)]">{ticket.subject}</span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">المستخدم</span>
              <span className="font-bold text-[var(--foreground)]">{ticket.user}</span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">النوع</span>
              <StatusBadge type="userType" value={ticket.userType} />
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">الأولوية</span>
              <span className="font-bold text-rose-600">{ticket.priority}</span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">الحالة</span>
              <span className="font-bold text-teal-700">{ticket.status}</span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">وقت الفتح</span>
              <span className="font-bold text-[var(--foreground)]">{ticket.timeAgo}</span>
            </div>

            <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
              <span className="text-[var(--text-subtle)] font-medium">المسند إلى</span>
              <span className="font-bold text-[var(--foreground)]">
                {ticket.assignedTo || 'دينا حسام'}
              </span>
            </div>
          </div>

          {/* Right Column: Chat Conversation & Internal Notes (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* User Conversation Card */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
              <h3 className="font-extrabold text-[var(--foreground)] text-sm border-b border-[var(--divider)] pb-3">
                المحادثة مع المستخدم
              </h3>

              {/* Chat bubbles */}
              <div className="space-y-4 min-h-[160px] max-h-[300px] overflow-y-auto p-2">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${
                      msg.sender === 'user' ? 'items-start' : 'items-end'
                    }`}
                  >
                    <div
                      className={`max-w-md p-4 rounded-2xl text-xs font-semibold leading-relaxed shadow-2xs ${
                        msg.sender === 'user'
                          ? 'bg-teal-50 text-[var(--foreground)] rounded-tr-none border border-teal-100'
                          : 'bg-[var(--badge-bg-muted)] text-[var(--foreground)] rounded-tl-none border border-slate-200/60'
                      }`}
                    >
                      {msg.text}
                    </div>
                    <span className="text-[10px] text-[var(--text-subtle)] mt-1 px-1">
                      {msg.time}
                    </span>
                  </div>
                ))}
              </div>

              {/* Reply Box */}
              <div className="pt-2 flex items-center gap-3">
                <textarea
                  rows={2}
                  value={newReply}
                  onChange={(e) => setNewReply(e.target.value)}
                  placeholder="اكتب رداً..."
                  className="flex-1 p-3 bg-[var(--card-hover)] border border-[var(--card-border)] rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 placeholder:text-[var(--text-subtle)] resize-none"
                ></textarea>
                <button
                  onClick={handleSendMessage}
                  className="h-full px-5 bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5 shrink-0 py-4"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>إرسال</span>
                </button>
              </div>
            </div>

            {/* Internal Notes Box */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
              <h3 className="font-extrabold text-[var(--foreground)] text-sm border-b border-[var(--divider)] pb-3">
                ملاحظات داخلية (لا تُشارك مع المستخدم)
              </h3>

              <textarea
                rows={3}
                value={internalNote}
                onChange={(e) => setInternalNote(e.target.value)}
                placeholder="ملاحظات الفريق الداخلي..."
                className="w-full p-3 bg-[var(--card-hover)] border border-[var(--card-border)] rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500 placeholder:text-[var(--text-subtle)] resize-none"
              ></textarea>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <button className="py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-xs rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>إغلاق كـ محلول</span>
                </button>

                <button className="py-3 bg-amber-500/15 hover:bg-amber-500/25 text-amber-800 font-extrabold text-xs rounded-xl border border-amber-200/60 transition-colors flex items-center justify-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-amber-600" />
                  <span>تصعيد</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
