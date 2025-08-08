'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/sidebar'
import { Header } from '@/components/header'

export default function DuplicatesPage() {
  const [duplicates] = useState([
    {
      id: 1,
      title: "Product Overview",
      space: "Product Documentation",
      similarity: 95,
      pages: [
        { id: "101", title: "Product Overview - Main", lastModified: "2024-01-15" },
        { id: "102", title: "Product Overview - Copy", lastModified: "2024-01-10" }
      ]
    },
    {
      id: 2,
      title: "Getting Started Guide",
      space: "User Documentation",
      similarity: 87,
      pages: [
        { id: "201", title: "Getting Started - New", lastModified: "2024-01-20" },
        { id: "202", title: "Getting Started - Old", lastModified: "2023-12-15" },
        { id: "203", title: "Getting Started Tutorial", lastModified: "2024-01-05" }
      ]
    },
    {
      id: 3,
      title: "API Documentation",
      space: "Developer Resources",
      similarity: 78,
      pages: [
        { id: "301", title: "API Reference v2", lastModified: "2024-01-25" },
        { id: "302", title: "API Docs", lastModified: "2024-01-18" }
      ]
    }
  ])

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 90) return "text-red-600 bg-red-100"
    if (similarity >= 75) return "text-yellow-600 bg-yellow-100"
    return "text-green-600 bg-green-100"
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          <div className="container mx-auto px-6 py-8">
            <div className="mb-6">
              <h1 className="text-3xl font-semibold text-gray-800">Duplicate Detection</h1>
              <p className="text-gray-600 mt-2">
                Found {duplicates.length} sets of duplicate content across your Confluence spaces
              </p>
            </div>

            {/* Filter and Actions */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                <div className="flex space-x-4">
                  <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
                    <option>All Spaces</option>
                    <option>Product Documentation</option>
                    <option>User Documentation</option>
                    <option>Developer Resources</option>
                  </select>
                  <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
                    <option>All Similarities</option>
                    <option>High (90%+)</option>
                    <option>Medium (75-89%)</option>
                    <option>Low (60-74%)</option>
                  </select>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                  Scan for New Duplicates
                </button>
              </div>
            </div>

            {/* Duplicates List */}
            <div className="space-y-6">
              {duplicates.map((duplicate) => (
                <div key={duplicate.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{duplicate.title}</h3>
                        <p className="text-sm text-gray-600">Space: {duplicate.space}</p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSimilarityColor(duplicate.similarity)}`}>
                          {duplicate.similarity}% similar
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="px-6 py-4">
                    <div className="space-y-3">
                      {duplicate.pages.map((page) => (
                        <div key={page.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                          <div>
                            <h4 className="font-medium text-gray-900">{page.title}</h4>
                            <p className="text-sm text-gray-600">Last modified: {page.lastModified}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button className="text-blue-600 hover:text-blue-800 text-sm">View</button>
                            <button className="text-gray-600 hover:text-gray-800 text-sm">Compare</button>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-4 flex justify-end space-x-3">
                      <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm">
                        Ignore
                      </button>
                      <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                        Review & Merge
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {duplicates.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="text-gray-400 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No duplicates found</h3>
                <p className="text-gray-600">Great! Your Confluence spaces are clean of duplicate content.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
