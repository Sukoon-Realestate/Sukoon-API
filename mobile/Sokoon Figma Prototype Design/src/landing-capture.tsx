import React, { useLayoutEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { Signal, Wifi, BatteryFull } from 'lucide-react';
import { FilterSheetScreen, SavedListingsScreen, BookVisitScreen, TenantChatThreadScreen, TenantNotificationsScreen, RatePropertyScreen, TenantSubmitTicketScreen } from './app/screens-tenant';
import { OwnerDashboardScreen } from './app/screens-owner';
import './styles/index.css';
const screens = { discovery: FilterSheetScreen, shortlist: SavedListingsScreen, viewings: BookVisitScreen, owners: OwnerDashboardScreen, conversations: TenantChatThreadScreen, notifications: TenantNotificationsScreen, reviews: RatePropertyScreen, support: TenantSubmitTicketScreen };
const params = new URLSearchParams(location.search);
const key = params.get('screen') as keyof typeof screens;
const Screen = screens[key] || FilterSheetScreen;
const dark = params.get('theme') === 'dark';
const photos = ['/landing-photos/living-room.jpg', '/landing-photos/apartment.jpg', '/landing-photos/interior.jpg'];

// Marketing captures use sample photography and a palette matching the site.
// These adaptations are isolated to this capture entry; app screens stay intact.
function Capture() {
  const root = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (!root.current) return;
    // Replace each prototype's status bar with the same iPhone safe areas.
    root.current.firstElementChild?.querySelector(':scope > .h-11')?.remove();
    if (key === 'shortlist') {
      root.current.querySelectorAll('.relative.h-32').forEach((slot, index) => {
        const image = document.createElement('img');
        image.src = photos[index % photos.length];
        image.alt = 'Sample apartment interior';
        image.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block';
        slot.firstElementChild?.replaceWith(image);
      });
    }
    if (key === 'viewings') {
      const icon = root.current.querySelector('.lucide-building-2');
      if (icon?.parentElement) {
        icon.parentElement.style.cssText += `;background-image:url(${photos[0]});background-size:cover;background-position:center`;
        icon.remove();
      }
    }
    if (key === 'discovery' || key === 'reviews') {
      const screen = root.current.firstElementChild as HTMLElement;
      screen.style.background = `${dark ? '#0e1912' : '#ecf2ea'} url(${photos[0]}) center / cover`;
      const spacer = screen.firstElementChild as HTMLElement;
      spacer.style.background = dark ? 'rgba(6,15,10,.45)' : 'rgba(6,15,10,.15)';
    }
    if (!dark) return;
    const backgrounds: Record<string, string> = {
      'rgb(250, 250, 248)': '#0e1912', 'rgb(255, 255, 255)': '#16241b',
      'rgb(224, 242, 241)': '#173a24', 'rgb(238, 245, 255)': '#172d3b',
      'rgb(234, 251, 241)': '#173a24', 'rgb(255, 248, 231)': '#352e1c',
      'rgb(255, 247, 230)': '#352e1c', 'rgb(255, 241, 241)': '#3b2023',
      'rgb(243, 244, 246)': '#213628', 'rgb(226, 232, 240)': '#213628',
      'rgb(15, 118, 110)': '#167c42', 'rgb(209, 213, 219)': '#304637',
      'rgba(255, 255, 255, 0.9)': '#16241b',
    };
    const foregrounds: Record<string, string> = {
      'rgb(17, 24, 39)': '#ecf2ea', 'rgb(107, 114, 128)': '#a1b0a6',
      'rgb(15, 118, 110)': '#7fe08d', 'rgb(37, 99, 235)': '#83b7ee',
      'rgb(209, 213, 219)': '#6b8071', 'rgb(156, 163, 175)': '#a1b0a6',
    };
    root.current.querySelectorAll<HTMLElement>('[style]').forEach(element => {
      const style = element.style;
      if (backgrounds[style.backgroundColor]) style.backgroundColor = backgrounds[style.backgroundColor];
      if (foregrounds[style.color]) style.color = foregrounds[style.color];
      if (style.borderColor) style.borderColor = '#2c4233';
      if (style.borderTopColor) style.borderTopColor = '#2c4233';
      if (style.borderBottomColor) style.borderBottomColor = '#2c4233';
      if (style.borderLeftColor) style.borderLeftColor = '#2c4233';
      if (style.borderRightColor) style.borderRightColor = '#2c4233';
      if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
        style.backgroundColor = '#16241b';
        style.color = '#ecf2ea';
      }
    });
  }, []);
  const ink = dark ? '#ecf2ea' : '#111827';
  return (
    <div ref={root} style={{ position: 'relative', width: 390, height: 844, paddingTop: 59, paddingBottom: 34, boxSizing: 'border-box', overflow: 'hidden', background: dark ? '#0e1912' : '#fafaf8', colorScheme: dark ? 'dark' : 'light' }}>
      <Screen />
      <div data-iphone-status-bar dir="ltr" style={{ position: 'absolute', zIndex: 10, inset: '0 0 auto', height: 59, color: ink, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 27px', fontFamily: 'Arial, sans-serif' }}>
        <span style={{ fontSize: 15, fontWeight: 700, width: 48, textAlign: 'center' }}>9:41</span>
        <span data-dynamic-island style={{ position: 'absolute', left: '50%', top: 11, transform: 'translateX(-50%)', width: 112, height: 32, borderRadius: 24, background: '#000' }}>
          <span style={{ position: 'absolute', right: 11, top: 11, width: 10, height: 10, borderRadius: '50%', background: '#10151d', boxShadow: 'inset 0 0 0 2px #080b10' }} />
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><Signal size={17} /><Wifi size={16} /><BatteryFull size={23} /></span>
      </div>
      <div data-home-indicator style={{ position: 'absolute', zIndex: 10, bottom: 9, left: '50%', transform: 'translateX(-50%)', width: 134, height: 5, borderRadius: 8, background: ink }} />
    </div>
  );
}
createRoot(document.getElementById('root')!).render(<Capture />);
