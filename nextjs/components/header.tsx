'use client'

import { useState } from 'react'
import { UserButton, OrganizationSwitcher } from '@clerk/nextjs'
import { useUser, useClerk } from '@clerk/nextjs'
import { ThemeToggle } from './theme-toggle'

export function Header() {
  const { user } = useUser()
  const { signOut } = useClerk()

  const handleSignOut = () => {
    signOut()
  }

  return (
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-foreground">
              Concatly Dashboard
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Organization Switcher */}
            <OrganizationSwitcher 
              appearance={{
                elements: {
                  rootBox: "flex items-center",
                  organizationSwitcherTrigger: "text-muted-foreground text-sm",
                  organizationPreviewTextContainer: "text-muted-foreground",
                  organizationPreviewMainIdentifier: "text-muted-foreground text-sm"
                }
              }}
            />
            
            <span className="text-sm text-muted-foreground">
              Welcome, {user?.firstName || 'User'}
            </span>
            
            {/* User Button with sign out */}
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
