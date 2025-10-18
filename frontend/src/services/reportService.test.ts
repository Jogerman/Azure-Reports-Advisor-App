import reportService from './reportService';
import apiClient from './apiClient';
import { mockReport, mockClient, createMockFile } from '../utils/test-utils';

// Mock the apiClient
jest.mock('./apiClient');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('ReportService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('uploadCSV', () => {
    // Test 1: Upload CSV with minimal data
    it('uploads CSV file with minimal data', async () => {
      const file = createMockFile('test.csv', 1024, 'text/csv');
      const uploadData = {
        client_id: mockClient.id,
        csv_file: file,
      };

      mockedApiClient.post.mockResolvedValue({ data: mockReport });

      const result = await reportService.uploadCSV(uploadData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/reports/upload/',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result).toEqual(mockReport);
    });

    // Test 2: Upload CSV with report type
    it('uploads CSV file with report type specified', async () => {
      const file = createMockFile('test.csv');
      const uploadData = {
        client_id: mockClient.id,
        csv_file: file,
        report_type: 'detailed' as const,
      };

      mockedApiClient.post.mockResolvedValue({ data: mockReport });

      await reportService.uploadCSV(uploadData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/reports/upload/',
        expect.any(FormData),
        expect.any(Object)
      );
    });

    // Test 3: Handle upload error
    it('throws error when upload fails', async () => {
      const file = createMockFile('test.csv');
      const uploadData = {
        client_id: mockClient.id,
        csv_file: file,
      };

      mockedApiClient.post.mockRejectedValue({
        response: { status: 400, data: { message: 'Invalid file format' } },
      });

      await expect(reportService.uploadCSV(uploadData)).rejects.toMatchObject({
        response: { status: 400 },
      });
    });
  });

  describe('generateReport', () => {
    // Test 4: Generate HTML/PDF files successfully
    it('generates report files successfully', async () => {
      const responseData = {
        status: 'success',
        message: 'Report generation started',
        data: {
          report_id: mockReport.id,
          task_id: 'task-123',
        },
      };

      mockedApiClient.post.mockResolvedValue({ data: responseData });

      const result = await reportService.generateReport(mockReport.id, 'both');

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/generate/`,
        { format: 'both' }
      );
      expect(result).toEqual(responseData);
    });

    // Test 5: Generate PDF only
    it('generates PDF file only', async () => {
      const responseData = {
        status: 'success',
        message: 'PDF generation started',
      };

      mockedApiClient.post.mockResolvedValue({ data: responseData });

      await reportService.generateReport(mockReport.id, 'pdf');

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/generate/`,
        { format: 'pdf' }
      );
    });

    // Test 6: Generate HTML only
    it('generates HTML file only', async () => {
      const responseData = {
        status: 'success',
        message: 'HTML generation started',
      };

      mockedApiClient.post.mockResolvedValue({ data: responseData });

      await reportService.generateReport(mockReport.id, 'html');

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/generate/`,
        { format: 'html' }
      );
    });

    // Test 7: Handle generation error
    it('throws error when generation fails', async () => {
      mockedApiClient.post.mockRejectedValue({
        response: { status: 500, data: { message: 'Generation failed' } },
      });

      await expect(reportService.generateReport(mockReport.id)).rejects.toMatchObject({
        response: { status: 500 },
      });
    });
  });

  describe('getReports', () => {
    // Test 7: Get reports without filters
    it('fetches reports list without filters', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockReport],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await reportService.getReports();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/reports/', {
        params: undefined,
      });
      expect(result.results).toHaveLength(1);
    });

    // Test 8: Get reports with client filter
    it('fetches reports filtered by client', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockReport],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { client_id: mockClient.id };
      await reportService.getReports(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/reports/', {
        params,
      });
    });

    // Test 9: Get reports with status filter
    it('fetches reports filtered by status', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockReport],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { status: 'completed' as const };
      await reportService.getReports(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/reports/', {
        params,
      });
    });

    // Test 10: Get reports with report type filter
    it('fetches reports filtered by type', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockReport],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { report_type: 'detailed' as const };
      await reportService.getReports(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/reports/', {
        params,
      });
    });

    // Test 11: Get reports with pagination
    it('fetches reports with pagination', async () => {
      const mockResponse = {
        count: 50,
        next: 'next-url',
        previous: null,
        results: [mockReport],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { page: 2, page_size: 10 };
      await reportService.getReports(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/reports/', {
        params,
      });
    });
  });

  describe('getReport', () => {
    // Test 12: Get single report
    it('fetches single report by ID', async () => {
      mockedApiClient.get.mockResolvedValue({ data: mockReport });

      const result = await reportService.getReport(mockReport.id);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/`
      );
      expect(result).toEqual(mockReport);
    });

    // Test 13: Handle report not found
    it('throws error when report not found', async () => {
      mockedApiClient.get.mockRejectedValue({
        response: { status: 404, data: { message: 'Report not found' } },
      });

      await expect(reportService.getReport('invalid-id')).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });

  describe('getReportStatus', () => {
    // Test 14: Get report status
    it('fetches report status', async () => {
      const statusResponse = {
        status: 'processing' as const,
        progress: 50,
        message: 'Generating PDF...',
      };

      mockedApiClient.get.mockResolvedValue({ data: statusResponse });

      const result = await reportService.getReportStatus(mockReport.id);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/status/`
      );
      expect(result.status).toBe('processing');
      expect(result.progress).toBe(50);
    });

    // Test 15: Get completed status
    it('fetches completed report status', async () => {
      const statusResponse = {
        status: 'completed' as const,
        progress: 100,
        message: 'Report ready',
      };

      mockedApiClient.get.mockResolvedValue({ data: statusResponse });

      const result = await reportService.getReportStatus(mockReport.id);

      expect(result.status).toBe('completed');
      expect(result.progress).toBe(100);
    });

    // Test 16: Get failed status
    it('fetches failed report status with error message', async () => {
      const statusResponse = {
        status: 'failed' as const,
        error_message: 'Invalid CSV format',
      };

      mockedApiClient.get.mockResolvedValue({ data: statusResponse });

      const result = await reportService.getReportStatus(mockReport.id);

      expect(result.status).toBe('failed');
      expect(result.error_message).toBe('Invalid CSV format');
    });
  });

  describe('downloadReport', () => {
    // Test 17: Download PDF report
    it('downloads PDF report', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      mockedApiClient.get.mockResolvedValue({ data: mockBlob });

      const result = await reportService.downloadReport(mockReport.id, 'pdf');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/download/pdf/`,
        {
          responseType: 'blob',
        }
      );
      expect(result).toBeInstanceOf(Blob);
    });

    // Test 18: Download HTML report
    it('downloads HTML report', async () => {
      const mockBlob = new Blob(['<html>Report</html>'], { type: 'text/html' });

      mockedApiClient.get.mockResolvedValue({ data: mockBlob });

      const result = await reportService.downloadReport(mockReport.id, 'html');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/download/html/`,
        {
          responseType: 'blob',
        }
      );
      expect(result).toBeInstanceOf(Blob);
    });

    // Test 19: Download PDF by default
    it('downloads PDF format by default', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      mockedApiClient.get.mockResolvedValue({ data: mockBlob });

      await reportService.downloadReport(mockReport.id);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/download/pdf/`,
        {
          responseType: 'blob',
        }
      );
    });
  });

  describe('deleteReport', () => {
    // Test 20: Delete report successfully
    it('deletes report successfully', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null });

      await reportService.deleteReport(mockReport.id);

      expect(mockedApiClient.delete).toHaveBeenCalledWith(
        `/reports/${mockReport.id}/`
      );
    });

    // Test 21: Handle delete error
    it('throws error when delete fails', async () => {
      mockedApiClient.delete.mockRejectedValue({
        response: { status: 404, data: { message: 'Report not found' } },
      });

      await expect(reportService.deleteReport('invalid-id')).rejects.toMatchObject(
        {
          response: { status: 404 },
        }
      );
    });
  });

  describe('downloadFile', () => {
    // Mock DOM elements for file download
    let createElementSpy: jest.SpyInstance;
    let createObjectURLSpy: jest.SpyInstance;
    let revokeObjectURLSpy: jest.SpyInstance;
    let mockLink: any;

    beforeEach(() => {
      mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      };

      createElementSpy = jest
        .spyOn(document, 'createElement')
        .mockReturnValue(mockLink);
      createObjectURLSpy = jest
        .spyOn(window.URL, 'createObjectURL')
        .mockReturnValue('blob:mock-url');
      revokeObjectURLSpy = jest
        .spyOn(window.URL, 'revokeObjectURL')
        .mockImplementation(() => {});

      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink);
    });

    afterEach(() => {
      createElementSpy.mockRestore();
      createObjectURLSpy.mockRestore();
      revokeObjectURLSpy.mockRestore();
    });

    // Test 22: Trigger file download in browser
    it('triggers file download in browser', () => {
      const blob = new Blob(['content'], { type: 'application/pdf' });
      const filename = 'report.pdf';

      reportService.downloadFile(blob, filename);

      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(window.URL.createObjectURL).toHaveBeenCalledWith(blob);
      expect(mockLink.href).toBe('blob:mock-url');
      expect(mockLink.download).toBe(filename);
      expect(mockLink.click).toHaveBeenCalled();
      expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });
});
