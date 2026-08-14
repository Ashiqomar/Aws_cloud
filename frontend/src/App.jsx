import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import ConnectModal from './components/ConnectModal';
import RemediationModal from './components/RemediationModal';
import Toast from './components/Toast';
import Dashboard from './pages/Dashboard';
import Recommendations from './pages/Recommendations';
import {
  getTenants,
  getCostSummary,
  getRecommendations,
  getRecommendationsSummary,
  getAISummary,
  connectAWSAccount,
  triggerAWSSync,
  triggerAnalysis,
  seedDemoData,
  applyRemediation,
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Data State
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [costSummary, setCostSummary] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recoSummary, setRecoSummary] = useState(null);
  const [aiData, setAiData] = useState(null);
  
  // UI State
  const [isConnectOpen, setIsConnectOpen] = useState(false);
  const [targetRemediation, setTargetRemediation] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAILoading, setIsAILoading] = useState(false);
  const [isRemediating, setIsRemediating] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch AI Insights
  const fetchAISummary = useCallback(async () => {
    setIsAILoading(true);
    try {
      const tenantId = selectedTenant?.id || null;
      const res = await getAISummary({ tenant_id: tenantId });
      setAiData(res.data);
    } catch (err) {
      console.error('Failed to load AI summary:', err);
    } finally {
      setIsAILoading(false);
    }
  }, [selectedTenant]);

  // Fetch all dashboard & recommendations data
  const fetchData = useCallback(async () => {
    try {
      const tenantId = selectedTenant?.id || null;

      // 1. Fetch Cost Summary
      const costRes = await getCostSummary({ tenant_id: tenantId, days: 30 });
      setCostSummary(costRes.data);

      // 2. Fetch Recommendations List
      const recoRes = await getRecommendations({ tenant_id: tenantId });
      setRecommendations(recoRes.data.items || []);

      // 3. Fetch Recommendations Summary
      const recoSumRes = await getRecommendationsSummary({ tenant_id: tenantId });
      setRecoSummary(recoSumRes.data);

      // 4. Fetch AI Summary
      await fetchAISummary();

    } catch (err) {
      console.error('Failed to load FinOps data:', err);
    }
  }, [selectedTenant, fetchAISummary]);

  // Load Tenants list on mount
  const loadTenants = useCallback(async () => {
    try {
      const res = await getTenants();
      const list = res.data.tenants || [];
      setTenants(list);
      if (list.length > 0 && !selectedTenant) {
        setSelectedTenant(list[0]);
      }
    } catch (err) {
      console.error('Failed to load tenants:', err);
    }
  }, [selectedTenant]);

  useEffect(() => {
    loadTenants();
  }, [loadTenants]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Seed demo data handler
  const handleSeedDemo = async () => {
    try {
      const res = await seedDemoData();
      showToast(res.data.message || 'FinOps Demo Data Seeded!', 'success');
      await loadTenants();
      await fetchData();
    } catch (err) {
      showToast('Failed to seed demo data', 'error');
    }
  };

  // Connect AWS account handler
  const handleConnect = async (formData) => {
    setIsConnecting(true);
    try {
      const res = await connectAWSAccount(formData);
      showToast(res.data.message || 'AWS Account Connected!', 'success');
      setIsConnectOpen(false);
      await loadTenants();
      await fetchData();
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to connect AWS Account. Check IAM Role credentials.';
      showToast(errMsg, 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  // Sync AWS Data handler
  const handleSyncData = async () => {
    if (!selectedTenant) {
      showToast('Please connect an AWS Account or select a tenant first.', 'info');
      setIsConnectOpen(true);
      return;
    }
    setIsSyncing(true);
    try {
      const res = await triggerAWSSync(selectedTenant.id);
      showToast(`AWS Sync task queued (Task ID: ${res.data.task_id})`, 'info');
      setTimeout(() => {
        fetchData();
        setIsSyncing(false);
      }, 2000);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to trigger AWS Sync', 'error');
      setIsSyncing(false);
    }
  };

  // Trigger Rules Engine analysis handler
  const handleTriggerAnalysis = async () => {
    if (!selectedTenant) {
      showToast('Please select a tenant or seed demo data first.', 'info');
      return;
    }
    setIsAnalyzing(true);
    try {
      const res = await triggerAnalysis(selectedTenant.id);
      showToast('Rules Engine analysis triggered!', 'success');
      setTimeout(() => {
        fetchData();
        setIsAnalyzing(false);
      }, 1500);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to trigger rules engine', 'error');
      setIsAnalyzing(false);
    }
  };

  // Apply or Dismiss recommendation state handlers
  const handleApplyReco = (item) => {
    setRecommendations((prev) =>
      prev.map((r) => (r.id === item.id ? { ...r, status: 'applied' } : r))
    );
    showToast(`Recommendation for ${item.resource_id} marked as APPLIED`, 'success');
  };

  const handleDismissReco = (item) => {
    setRecommendations((prev) =>
      prev.map((r) => (r.id === item.id ? { ...r, status: 'dismissed' } : r))
    );
    showToast(`Recommendation for ${item.resource_id} DISMISSED`, 'info');
  };

  // Handle Remediation Action execution
  const handleConfirmRemediation = async (payload) => {
    setIsRemediating(true);
    try {
      const res = await applyRemediation(payload);
      const isDry = res.data.dry_run;
      const msg = isDry
        ? `🧪 Dry Run Success: ${res.data.message}`
        : `🚀 Remediation Applied: ${res.data.message}`;

      showToast(msg, 'success');
      setTargetRemediation(null);

      if (!isDry) {
        setRecommendations((prev) =>
          prev.map((r) => (r.id === payload.recommendation_id ? { ...r, status: 'applied' } : r))
        );
        fetchData();
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to execute remediation action';
      showToast(errMsg, 'error');
    } finally {
      setIsRemediating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 font-sans pb-12">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        tenants={tenants}
        selectedTenant={selectedTenant}
        setSelectedTenant={setSelectedTenant}
        onOpenConnect={() => setIsConnectOpen(true)}
        onSeedDemo={handleSeedDemo}
        onSyncData={handleSyncData}
        isSyncing={isSyncing}
      />

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'dashboard' ? (
          <Dashboard
            costSummary={costSummary}
            recoSummary={recoSummary}
            aiData={aiData}
            onRefreshAI={fetchAISummary}
            isAILoading={isAILoading}
            onNavigateToRecos={() => setActiveTab('recommendations')}
            onSeedDemo={handleSeedDemo}
          />
        ) : (
          <Recommendations
            recommendations={recommendations}
            recoSummary={recoSummary}
            onTriggerAnalysis={handleTriggerAnalysis}
            isAnalyzing={isAnalyzing}
            onApplyReco={handleApplyReco}
            onDismissReco={handleDismissReco}
            onRemediateReco={(reco) => setTargetRemediation(reco)}
          />
        )}
      </main>

      {/* AWS AssumeRole Connect Modal */}
      <ConnectModal
        isOpen={isConnectOpen}
        onClose={() => setIsConnectOpen(false)}
        onConnect={handleConnect}
        isLoading={isConnecting}
      />

      {/* Safety Confirmation Remediation Modal */}
      <RemediationModal
        isOpen={!!targetRemediation}
        onClose={() => setTargetRemediation(null)}
        recommendation={targetRemediation}
        onConfirm={handleConfirmRemediation}
        isLoading={isRemediating}
      />

      {/* Toast Feedback Banner */}
      <Toast toast={toast} onClose={() => setToast(null)} />

    </div>
  );
}
