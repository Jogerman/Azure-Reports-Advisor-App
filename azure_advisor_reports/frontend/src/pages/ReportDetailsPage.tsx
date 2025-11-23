/**
 * Report Details Page (v1.7.0)
 *
 * Displays report details and allows adding manual recommendations.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ManualRecommendationForm } from '../components/reports/ManualRecommendationForm';
import {
  getReport,
  addManualRecommendations,
  generateReport,
  downloadReport,
  type ManualRecommendation,
  type Report,
} from '../services/api';

export const ReportDetailsPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isManualFormOpen, setIsManualFormOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Load report data
  useEffect(() => {
    if (reportId) {
      loadReport();
    }
  }, [reportId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getReport(reportId!);
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load report');
      console.error('Error loading report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddManualRecommendations = async (
    recommendations: ManualRecommendation[]
  ) => {
    try {
      const result = await addManualRecommendations(reportId!, recommendations);

      if (result.status === 'success') {
        // Show success message
        alert(
          `${result.message}\n\n` +
            `Added: ${result.data?.recommendations_created} recommendations\n` +
            `Total: ${result.data?.total_recommendations} recommendations\n` +
            `Total Savings: $${result.data?.total_potential_savings?.toFixed(2) || 0}`
        );

        // Reload report to show updated data
        await loadReport();
      } else {
        alert(`Error: ${result.message}\n${JSON.stringify(result.errors, null, 2)}`);
      }
    } catch (error: any) {
      console.error('Failed to add manual recommendations:', error);
      alert('Failed to add recommendations. Please try again.');
      throw error;
    }
  };

  const handleGenerateReport = async () => {
    try {
      setIsGenerating(true);
      await generateReport(reportId!, 'pdf');
      alert('Report generated successfully!');
      await loadReport(); // Refresh to get updated report with PDF link
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadReport = async (format: 'html' | 'pdf' = 'pdf') => {
    try {
      const blob = await downloadReport(reportId!, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${reportId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to download report. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-bold text-lg mb-2">Error Loading Report</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => navigate('/reports')}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Back to Reports
          </button>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">Report not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <button
                  onClick={() => navigate('/reports')}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ← Back
                </button>
                <h1 className="text-2xl font-bold text-gray-900">
                  {report.title || 'Report Details'}
                </h1>
              </div>

              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <span className="font-medium">Status:</span>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      report.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : report.status === 'processing'
                        ? 'bg-blue-100 text-blue-800'
                        : report.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {report.status}
                  </span>
                </span>
                <span>
                  <span className="font-medium">Created:</span>{' '}
                  {new Date(report.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              {/* Add Manual Data Button */}
              {(report.status === 'completed' ||
                report.status === 'pending' ||
                report.status === 'processing') && (
                <button
                  onClick={() => setIsManualFormOpen(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium flex items-center gap-2"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  Add Manual Data
                </button>
              )}

              {/* Generate Report Button */}
              {report.status === 'completed' && (
                <button
                  onClick={handleGenerateReport}
                  disabled={isGenerating}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGenerating ? 'Generating...' : 'Generate PDF'}
                </button>
              )}

              {/* Download Button */}
              {report.status === 'completed' && (
                <button
                  onClick={() => handleDownloadReport('pdf')}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
                >
                  Download
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Report Content */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Report Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Add your report details here */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Report ID</h3>
              <p className="text-gray-900">{report.id}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
              <p className="text-gray-900">{report.status}</p>
            </div>

            {/* Add more report fields as needed */}
          </div>

          {/* Information Box */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-blue-600 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-blue-900">
                  Manual Recommendations Feature
                </h4>
                <p className="text-sm text-blue-700 mt-1">
                  Click "Add Manual Data" to input custom recommendations that aren't
                  captured by Azure Advisor. This is useful for adding optimization
                  opportunities from other sources or custom findings.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Manual Recommendation Form Modal */}
        <ManualRecommendationForm
          isOpen={isManualFormOpen}
          onClose={() => setIsManualFormOpen(false)}
          onSubmit={handleAddManualRecommendations}
          reportId={reportId}
        />
      </div>
    </div>
  );
};

export default ReportDetailsPage;
