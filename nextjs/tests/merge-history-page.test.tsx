/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useOrganization } from '@clerk/nextjs';
import MergeHistoryPage from '../components/merge-history-page';

// Mock Clerk
jest.mock('@clerk/nextjs', () => ({
  useOrganization: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock environment variable
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

describe('MergeHistoryPage', () => {
  const mockOrganization = {
    id: 'org_test123',
    name: 'Test Organization'
  };

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    (useOrganization as jest.Mock).mockReturnValue({
      organization: mockOrganization
    });
  });

  test('renders loading state initially', () => {
    render(<MergeHistoryPage platform="confluence" />);
    
    expect(screen.getByText(/loading merge history/i)).toBeInTheDocument();
  });

  test('displays merge history when loaded', async () => {
    const mockMergeHistory = [
      {
        id: 'merge_001',
        page_id: 'page_123',
        duplicate_page_id: 'page_456',
        timestamp: '2024-01-01T10:00:00Z',
        status: 'completed',
        page_title: 'Test Page',
        duplicate_page_title: 'Duplicate Test Page'
      }
    ];

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMergeHistory
    });

    render(<MergeHistoryPage platform="confluence" />);

    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByText('Duplicate Test Page')).toBeInTheDocument();
    });
  });

  test('handles undo operation correctly', async () => {
    const mockMergeHistory = [
      {
        id: 'merge_001',
        page_id: 'page_123',
        duplicate_page_id: 'page_456',
        timestamp: '2024-01-01T10:00:00Z',
        status: 'completed',
        page_title: 'Test Page',
        duplicate_page_title: 'Duplicate Test Page'
      }
    ];

    // Mock initial history fetch
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMergeHistory
      })
      // Mock credentials fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          base_url: 'https://test.atlassian.net',
          username: 'test@example.com',
          api_token: 'token'
        })
      })
      // Mock undo operation
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Merge undone successfully'
        })
      })
      // Mock refresh history
      .mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

    render(<MergeHistoryPage platform="confluence" />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });

    // Find and click undo button
    const undoButton = screen.getByRole('button', { name: /undo/i });
    fireEvent.click(undoButton);

    // Wait for undo operation
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/merge/undo',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: expect.stringContaining('merge_001')
        })
      );
    });
  });

  test('handles sequential undo validation error', async () => {
    const mockMergeHistory = [
      {
        id: 'merge_001',
        page_id: 'page_123',
        duplicate_page_id: 'page_456',
        timestamp: '2024-01-01T10:00:00Z',
        status: 'completed',
        page_title: 'Test Page',
        duplicate_page_title: 'Duplicate Test Page'
      }
    ];

    // Mock responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMergeHistory
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ /* credentials */ })
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({
          success: false,
          requires_sequential_undo: true,
          next_required_undo: {
            id: 'merge_002',
            timestamp: '2024-01-01T11:00:00Z'
          },
          reason: 'Must undo more recent operations first'
        })
      });

    render(<MergeHistoryPage platform="confluence" />);

    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });

    const undoButton = screen.getByRole('button', { name: /undo/i });
    fireEvent.click(undoButton);

    // Should show sequential undo modal or error
    await waitFor(() => {
      expect(screen.getByText(/must undo more recent operations first/i)).toBeInTheDocument();
    });
  });

  test('refreshes history when refresh button clicked', async () => {
    const mockMergeHistory = [
      {
        id: 'merge_001',
        page_id: 'page_123',
        duplicate_page_id: 'page_456',
        timestamp: '2024-01-01T10:00:00Z',
        status: 'completed',
        page_title: 'Test Page',
        duplicate_page_title: 'Duplicate Test Page'
      }
    ];

    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockMergeHistory
    });

    render(<MergeHistoryPage platform="confluence" />);

    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });

    // Find and click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    // Should call fetch again
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });
});
