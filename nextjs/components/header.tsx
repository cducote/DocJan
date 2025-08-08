'use client'

import { useState } from 'react'
import { UserButton, OrganizationSwitcher } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'

export function Header() {
  const { user } = useUser()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              Concatly Dashboard
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Organization Switcher */}
            <OrganizationSwitcher 
              appearance={{
                elements: {
                  rootBox: "flex items-center"
                }
              }}
            />
            
            <span className="text-sm text-gray-700">
              Welcome, {user?.firstName || 'User'}
            </span>
            <UserButton 
              appearance={{
                elements: {
                  avatarBox: "h-8 w-8"
                }
              }}
            />
          </div>
        </div>
      </div>
    </header>
  )
}
