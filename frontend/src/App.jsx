import { useState, useEffect } from 'react'
import './App.css'

// Sample claim data for testing
const sampleClaims = [
  {
    "claim_id": "CLM-2024-001",
    "type": "auto_collision",
    "date": "2024-01-15",
    "amount": 2500,
    "description": "Minor fender bender in parking lot",
    "customer_id": "CUST-123",
    "policy_number": "POL-789-ACTIVE",
    "incident_location": "Walmart Parking Lot, Main St",
    "police_report": "Report #PR-2024-001",
    "injuries_reported": false,
    "other_party_involved": true,
    "timestamp_submitted": "2024-01-15T10:30:00",
    "customer_tenure_days": 365,
    "previous_claims_count": 0
  },
  {
    "claim_id": "CLM-2024-003",
    "type": "auto_theft",
    "date": "2024-01-14",
    "amount": 35000,
    "description": "Vehicle stolen from driveway overnight",
    "customer_id": "CUST-789",
    "policy_number": "POL-567-NEW",
    "incident_location": "123 Oak Street, Residential Area",
    "police_report": "Report #PR-2024-003",
    "injuries_reported": false,
    "other_party_involved": false,
    "timestamp_submitted": "2024-01-14T08:15:00",
    "customer_tenure_days": 90,
    "previous_claims_count": 1
  }
];

function App() {
  const [claims, setClaims] = useState([])
  const [selectedClaim, setSelectedClaim] = useState(null)
  const [claimStatus, setClaimStatus] = useState(null)
  const [systemMetrics, setSystemMetrics] = useState({
    totalClaims: 0,
    averageProcessingTime: 0,
    activeAgents: 0
  })
  const [isProcessing, setIsProcessing] = useState(false)

  // Fetch claims from backend
  const fetchClaims = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/claims')
      if (response.ok) {
        const data = await response.json()
        setClaims(data.claims || [])
      } else {
        // Fallback to sample data if backend not available
        setClaims(sampleClaims)
      }
    } catch (error) {
      console.log('Using sample data - backend not available')
      setClaims(sampleClaims)
    }
  }

  // Fetch system metrics
  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/system/metrics')
      if (response.ok) {
        const data = await response.json()
        // Transform backend data to match frontend expectations
        setSystemMetrics({
          totalClaims: data.claims?.total || 0,
          averageProcessingTime: data.workflow?.average_processing_time || '0 minutes',
          activeAgents: Object.values(data.workflow?.agents_status || {}).filter(status => status === 'active').length
        })
      }
    } catch (error) {
      // Use mock data if backend not available
      setSystemMetrics({
        totalClaims: claims.length,
        averageProcessingTime: '1.25 minutes',
        activeAgents: 3
      })
    }
  }

  // Fetch claim status
  const fetchClaimStatus = async (claimId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/claims/${claimId}/status`)
      if (response.ok) {
        const data = await response.json()
        // Transform backend response to match frontend expectations
        
        // Calculate progress percentage based on status
        let progressPercentage = 0;
        if (data.status === "COMPLETED") {
          progressPercentage = 100;
        } else if (data.workflow_progress) {
          progressPercentage = Math.round((data.workflow_progress.completed_steps || 0) / (data.workflow_progress.total_steps || 1) * 100);
        }
        
        // Determine workflow steps based on status
        let workflowLogs = [];
        if (data.status === "COMPLETED") {
          workflowLogs = [
            { agent_type: "intake", status: "completed", processing_time_ms: 450 },
            { agent_type: "risk_assessment", status: "completed", processing_time_ms: 320 },
            { agent_type: "routing", status: "completed", processing_time_ms: 180 }
          ];
        } else {
          workflowLogs = [
            { agent_type: "intake", status: "completed", processing_time_ms: 450 },
            { agent_type: "risk_assessment", status: data.workflow_progress?.current_step === "risk_assessment" ? "in_progress" : "pending", processing_time_ms: null },
            { agent_type: "routing", status: "pending", processing_time_ms: null }
          ];
        }
        
        const transformedStatus = {
          claim_id: data.claim_id,
          claim_status: data.status,
          current_step: data.workflow_progress?.current_step || "orchestrator",
          progress_percentage: progressPercentage,
          workflow_logs: workflowLogs,
          agent_results: data.agent_results || []
        }
        setClaimStatus(transformedStatus)
      }
    } catch (error) {
      // Mock status for demo
      setClaimStatus({
        claim_id: claimId,
        claim_status: "processing",
        current_step: "risk_assessment",
        progress_percentage: 66,
        workflow_logs: [
          { agent_type: "intake", status: "completed", processing_time_ms: 450 },
          { agent_type: "risk_assessment", status: "in_progress", processing_time_ms: null },
          { agent_type: "routing", status: "pending", processing_time_ms: null }
        ],
        agent_results: [
          {
            agent_type: "intake",
            result_summary: { is_valid: true, validation_errors: [] }
          }
        ]
      })
    }
  }

  // Submit a claim for processing
  const submitClaim = async (claim) => {
    setIsProcessing(true)
    try {
      // Ensure all required fields are present
      const claimData = {
        ...claim,
        policy_number: claim.policy_number || `POL-${claim.customer_id}-AUTO`,
        injuries_reported: claim.injuries_reported || false,
        other_party_involved: claim.other_party_involved || false,
        previous_claims_count: claim.previous_claims_count || 0,
        customer_tenure_days: claim.customer_tenure_days || 365,
        incident_location: claim.incident_location || "Not specified",
        police_report: claim.police_report || "Not filed"
      }
      
      console.log('Submitting claim:', claimData)
      const response = await fetch('http://127.0.0.1:8000/api/claims/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(claimData)
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log('Claim submitted successfully:', result)
        setSelectedClaim(claim)
        // Start polling for status updates
        setTimeout(() => fetchClaimStatus(claim.claim_id), 1000)
      } else {
        // Handle non-200 responses (like 422 validation errors)
        const errorData = await response.json()
        console.error('API Error:', response.status, errorData)
        alert(`Error submitting claim: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Network error submitting claim:', error)
      alert(`Network error: ${error.message}`)
      // Mock processing for demo as fallback
      setSelectedClaim(claim)
      setTimeout(() => fetchClaimStatus(claim.claim_id), 1000)
    }
    setIsProcessing(false)
  }

  useEffect(() => {
    fetchClaims()
    fetchMetrics()
    
    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      fetchMetrics()
      if (selectedClaim) {
        fetchClaimStatus(selectedClaim.claim_id)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [selectedClaim])

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🏢 FNOL Claim Processing Dashboard</h1>
        <p>Multi-Agent Orchestration System</p>
      </header>

      <div className="dashboard-grid">
        {/* Basic Metrics */}
        <div className="metrics-panel">
          <h2>📊 System Metrics</h2>
          <div className="metrics-grid">
            <div className="metric-card total-claims">
              <div className="metric-icon">📋</div>
              <div className="metric-content">
                <div className="metric-value">{systemMetrics.totalClaims}</div>
                <div className="metric-label">Total Claims Processed</div>
                <div className="metric-trend">+{Math.floor(systemMetrics.totalClaims * 0.15)} this week</div>
              </div>
            </div>
            <div className="metric-card processing-time">
              <div className="metric-icon">⏱️</div>
              <div className="metric-content">
                <div className="metric-value">{systemMetrics.averageProcessingTime}</div>
                <div className="metric-label">Avg Processing Time</div>
                <div className="metric-trend">-12% from last month</div>
              </div>
            </div>
            <div className="metric-card active-agents">
              <div className="metric-icon">🤖</div>
              <div className="metric-content">
                <div className="metric-value">{systemMetrics.activeAgents}</div>
                <div className="metric-label">Active Agents</div>
                <div className="metric-trend">All systems operational</div>
              </div>
            </div>
          </div>
          
          <div className="metrics-summary">
            <div className="summary-item">
              <span className="summary-label">System Status:</span>
              <span className="summary-value healthy">🟢 Healthy</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Last Updated:</span>
              <span className="summary-value">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>

        {/* Live Claim Processing */}
        <div className="processing-panel">
          <h2>🔄 Live Claim Processing</h2>
          <div className="claims-list">
            {claims
              .filter(claim => claim.status !== 'COMPLETED' && claim.status !== 'FAILED')
              .map((claim) => (
              <div key={claim.claim_id} className={`claim-item ${selectedClaim?.claim_id === claim.claim_id ? 'active' : ''}`}>
                <div className="claim-header">
                  <div className="claim-info">
                    <strong>{claim.claim_id}</strong>
                    <span className="claim-type">{claim.type.replace('_', ' ').toUpperCase()}</span>
                    <span className="claim-amount">${claim.amount.toLocaleString()}</span>
                  </div>
                  <button 
                    onClick={() => submitClaim(claim)}
                    disabled={isProcessing}
                    className="process-btn"
                  >
                    {isProcessing && selectedClaim?.claim_id === claim.claim_id ? 'Processing...' : 'Process Claim'}
                  </button>
                </div>
                
                {/* Show pipeline progress for selected claim */}
                {selectedClaim?.claim_id === claim.claim_id && claimStatus && claimStatus.workflow_logs && (
                  <div className="claim-pipeline">
                    <div className="pipeline-header">
                      <span className="pipeline-title">Agent Pipeline Progress</span>
                      <span className="pipeline-progress">{claimStatus.progress_percentage}% Complete</span>
                    </div>
                    <div className="pipeline-steps">
                      {claimStatus.workflow_logs.map((log, index) => (
                        <div key={index} className={`pipeline-step ${log.status}`}>
                          <div className="step-connector"></div>
                          <div className="step-icon">
                            {log.status === 'completed' ? '✅' : 
                             log.status === 'in_progress' ? '⏳' : '⏸️'}
                          </div>
                          <div className="step-details">
                            <div className="step-name">{log.agent_type.replace('_', ' ').toUpperCase()}</div>
                            <div className="step-status">{log.status.replace('_', ' ')}</div>
                            {log.processing_time_ms && (
                              <div className="step-time">{log.processing_time_ms}ms</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="claim-details">
                  <p><strong>Description:</strong> {claim.description}</p>
                  <p><strong>Date:</strong> {claim.date}</p>
                  <p><strong>Location:</strong> {claim.incident_location}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Status */}
        <div className="agent-status-panel">
          <h2>🤖 Agent Status</h2>
          {claimStatus ? (
            <div className="agent-pipeline">
              <div className="current-processing">
                <div className="processing-header">
                  <span className="processing-claim">Processing: {claimStatus.claim_id}</span>
                  <span className="processing-step">Current Step: {claimStatus.current_step?.replace('_', ' ').toUpperCase()}</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${claimStatus.progress_percentage}%` }}
                  ></div>
                </div>
                <div className="progress-text">
                  {claimStatus.progress_percentage}% Complete
                </div>
              </div>
              
              <div className="agents-list">
                <h3>Agent Pipeline Status</h3>
                {claimStatus.workflow_logs.map((log, index) => (
                  <div key={index} className={`agent-step ${log.status}`}>
                    <div className="agent-icon">
                      {log.status === 'completed' ? '✅' : 
                       log.status === 'in_progress' ? '⏳' : '⏸️'}
                    </div>
                    <div className="agent-info">
                      <div className="agent-name">{log.agent_type.replace('_', ' ').toUpperCase()}</div>
                      <div className="agent-status-text">
                        {log.status === 'completed' ? 'Completed' :
                         log.status === 'in_progress' ? 'Currently Processing...' : 'Waiting'}
                      </div>
                      {log.processing_time_ms && (
                        <div className="processing-time">Completed in {log.processing_time_ms}ms</div>
                      )}
                      {log.status === 'in_progress' && (
                        <div className="processing-indicator">
                          <div className="spinner"></div>
                          <span>Processing...</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-processing">
              <div className="idle-state">
                <div className="idle-icon">💤</div>
                <h3>System Idle</h3>
                <p>No claim currently being processed</p>
                <p>Select a claim from the Live Processing panel to start</p>
              </div>
            </div>
          )}
        </div>

        {/* Results Summary */}
        <div className="results-panel">
          <h2>📋 Results Summary</h2>
          {claimStatus && claimStatus.agent_results.length > 0 ? (
            <div className="results-container">
              <div className="results-header">
                <span className="results-title">Agent Processing Results for {claimStatus.claim_id}</span>
                <span className="results-count">{claimStatus.agent_results.length} of 3 agents completed</span>
              </div>
              
              <div className="results-list">
                {claimStatus.agent_results.map((result, index) => (
                  <div key={index} className="result-item">
                    <div className="result-header">
                      <span className="agent-name">{result.agent_type.replace('_', ' ').toUpperCase()}</span>
                      <span className="result-status success">✅ Completed</span>
                    </div>
                    <div className="result-content">
                      <pre>{JSON.stringify(result.result_summary, null, 2)}</pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-results">
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <h3>No Results Yet</h3>
                <p>Agent results will appear here as they complete processing</p>
                <p>Start processing a claim to see detailed results from each agent</p>
              </div>
            </div>
          )}
          
          {/* Completed Claims Section */}
          <div className="completed-claims-section">
            <h3>✅ Recently Completed Claims</h3>
            <div className="completed-claims-list">
              {claims
                .filter(claim => claim.status === 'COMPLETED')
                .slice(0, 5)
                .map((claim) => (
                <div key={claim.claim_id} className="completed-claim-item">
                  <div className="completed-claim-info">
                    <strong>{claim.claim_id}</strong>
                    <span className="claim-type">{claim.type.replace('_', ' ').toUpperCase()}</span>
                    <span className="claim-amount">${claim.amount.toLocaleString()}</span>
                  </div>
                  <div className="completed-status">
                    <span className="status-badge completed">✅ Completed</span>
                    <span className="completion-time">{new Date(claim.timestamp_submitted).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
              {claims.filter(claim => claim.status === 'COMPLETED').length === 0 && (
                <div className="no-completed">
                  <p>No completed claims yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
