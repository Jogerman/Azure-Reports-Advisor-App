"""
URL configuration for analytics app.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard analytics endpoints
    path('dashboard/', views.DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('metrics/', views.DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('trends/', views.TrendDataView.as_view(), name='trend-data'),
    path('categories/', views.CategoryDistributionView.as_view(), name='category-distribution'),
    path('recent-activity/', views.RecentActivityView.as_view(), name='recent-activity'),
    path('client-performance/', views.ClientPerformanceView.as_view(), name='client-performance'),
    path('business-impact/', views.BusinessImpactDistributionView.as_view(), name='business-impact'),

    # User activity endpoints
    path('user-activity/', views.UserActivityView.as_view(), name='user-activity'),
    path('activity-summary/', views.ActivitySummaryView.as_view(), name='activity-summary'),

    # System health endpoint
    path('system-health/', views.SystemHealthView.as_view(), name='system-health'),

    # Cache management
    path('cache/invalidate/', views.CacheInvalidationView.as_view(), name='cache-invalidate'),
]