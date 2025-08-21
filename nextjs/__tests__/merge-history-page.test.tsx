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

    // Wait for the loading to complete and data to appear
    await waitFor(() => {
      expect(screen.getByText(/merge operation/i)).toBeInTheDocument();
    });

    // Check that statistics are rendered correctly
    expect(screen.getByText('1')).toBeInTheDocument(); // Total operations
    expect(screen.getByText('Successful Merges')).toBeInTheDocument();
  });

  test('handles error when API fails', async () => {
    // Mock API failure
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<MergeHistoryPage platform="confluence" />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load merge history/i)).toBeInTheDocument();
    });
  });
});
