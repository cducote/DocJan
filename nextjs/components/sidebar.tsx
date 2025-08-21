'use client';

import { useState } from 'react';
import Image from 'next/image';

interface SidebarProps {
  currentPage: string;
  platform: 'confluence' | 'sharepoint';
  onPageChange: (page: string) => void;
  onPlatformChange: (platform: 'confluence' | 'sharepoint') => void;
}

export default function Sidebar({ currentPage, platform, onPageChange, onPlatformChange }: SidebarProps) {
  const navigationItems = [
    { key: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    ...(platform === 'confluence' ? [{ key: 'spaces', label: 'Spaces', icon: 'spaces' }] : []),
    { key: 'search', label: 'Search', icon: 'search' },
    { key: 'content-report', label: 'Content Report', icon: 'duplicates' },
    { key: 'merge_history', label: 'Merge History', icon: 'merge_history' },
    { key: 'settings', label: 'Settings', icon: 'settings' }
  ];

  return (
    <div className="w-64 bg-card border-r border-border h-full flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-border">
        <div className="flex justify-center">
          <Image
            src="/clogo.png"
            alt="Concatly Logo"
            width={200}
            height={60}
            className="object-contain"
          />
        </div>
      </div>

      {/* Navigation Menu */}
      <div className="p-4 flex-1">
        <h3 className="font-semibold text-foreground mb-3">Menu</h3>
        <div className="space-y-2">
          {navigationItems.map((item) => (
            <button
              key={item.key}
              onClick={() => onPageChange(item.key)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                currentPage === item.key
                  ? 'bg-primary text-primary-foreground'
                  : 'text-foreground hover:bg-accent hover:text-accent-foreground'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
