import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ToastProvider } from "./components/Toast";
import { Layout } from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Hr from "./pages/Hr";
import HrDetail from "./pages/HrDetail";
import Lookups from "./pages/Lookups";
import Standards from "./pages/Standards";
import Documents from "./pages/Documents";
import Records from "./pages/Records";
import Training from "./pages/Training";
import TrainingDetail from "./pages/TrainingDetail";
import Financial from "./pages/Financial";
import Reports from "./pages/Reports";
import Admin from "./pages/Admin";
import Backup from "./pages/Backup";
import Remote from "./pages/Remote";
import Settings from "./pages/Settings";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) {
    return <div className="flex h-full items-center justify-center text-ink-muted">جاري التحميل...</div>;
  }
  if (!user) return <Navigate to="/login" replace state={{ from: loc }} />;
  return <Layout>{children}</Layout>;
}

function Page({ children }: { children: React.ReactNode }) {
  return <Protected>{children}</Protected>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Page><Dashboard /></Page>} />
            <Route path="/standards" element={<Page><Standards /></Page>} />
            <Route path="/documents" element={<Page><Documents /></Page>} />
            <Route path="/records" element={<Page><Records /></Page>} />
            <Route path="/training" element={<Page><Training /></Page>} />
            <Route path="/training/:id" element={<Page><TrainingDetail /></Page>} />
            <Route path="/hr" element={<Page><Hr /></Page>} />
            <Route path="/hr/:id" element={<Page><HrDetail /></Page>} />
            <Route path="/financial" element={<Page><Financial /></Page>} />
            <Route path="/reports" element={<Page><Reports /></Page>} />
            <Route path="/lookups" element={<Page><Lookups /></Page>} />
            <Route path="/admin" element={<Page><Admin /></Page>} />
            <Route path="/backup" element={<Page><Backup /></Page>} />
            <Route path="/remote" element={<Page><Remote /></Page>} />
            <Route path="/settings" element={<Page><Settings /></Page>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
