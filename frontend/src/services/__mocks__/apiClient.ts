/**
 * Mock API Client for Testing
 *
 * This mock provides jest-compatible mocks for all API client methods.
 * Used by service tests to mock HTTP requests.
 */

const mockApiClient = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: null })),
  request: jest.fn(() => Promise.resolve({ data: {} })),
};

export default mockApiClient;
