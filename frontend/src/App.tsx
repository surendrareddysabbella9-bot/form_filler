import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { NewFormPage } from './pages/NewFormPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { FormWorkspacePage } from './pages/FormWorkspacePage';
import { ReviewPage } from './pages/ReviewPage';
import { DownloadPage } from './pages/DownloadPage';
import { MyDocumentsPage } from './pages/MyDocumentsPage';
import { MyFormsPage } from './pages/MyFormsPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Welcome / Landing Screen */}
          <Route path="/" element={<LandingPage />} />

          {/* Core Application Shell & Workspace */}
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/new-form" element={<NewFormPage />} />
            <Route path="/processing/:sessionId" element={<ProcessingPage />} />
            <Route path="/workspace/:sessionId" element={<FormWorkspacePage />} />
            <Route path="/review/:sessionId" element={<ReviewPage />} />
            <Route path="/download/:sessionId" element={<DownloadPage />} />
            <Route path="/documents" element={<MyDocumentsPage />} />
            <Route path="/forms" element={<MyFormsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
