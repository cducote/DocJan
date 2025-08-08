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
    { key: 'duplicates', label: 'Duplicates', icon: 'duplicates' },
    { key: 'merge_history', label: 'Merge History', icon: 'merge_history' },
    { key: 'settings', label: 'Settings', icon: 'settings' }
  ];

  return (
    <div className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 h-full flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
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

      {/* Platform Selection */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Platform</h3>
        <select
          value={platform}
          onChange={(e) => onPlatformChange(e.target.value as 'confluence' | 'sharepoint')}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          <option value="confluence">Confluence</option>
          <option value="sharepoint">SharePoint</option>
        </select>
      </div>

      {/* Navigation Menu */}
      <div className="p-4 flex-1">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Menu</h3>
        <div className="space-y-2">
          {navigationItems.map((item) => (
            <button
              key={item.key}
              onClick={() => onPageChange(item.key)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                currentPage === item.key
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
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
