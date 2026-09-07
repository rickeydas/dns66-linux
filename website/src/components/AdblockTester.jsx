import React, { useState, useEffect, useRef } from 'react';
import { Shield, ShieldAlert, Loader2, Play, Square } from 'lucide-react';

const AdblockTester = () => {
  const [status, setStatus] = useState('idle'); // 'idle', 'loading_list', 'checking', 'done', 'stopped', 'error'
  const [testStats, setTestStats] = useState({ tested: 0, blocked: 0, total: 200 });
  const abortControllerRef = useRef(null);

  const startTest = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setStatus('loading_list');
    setTestStats({ tested: 0, blocked: 0, total: 200 });

    try {
      const response = await fetch(import.meta.env.BASE_URL + 'ad_domains.json', { signal });
      if (!response.ok) throw new Error('Failed to load domains');
      
      const data = await response.json();
      const allDomains = Object.keys(data);
      
      const numToTest = 200;
      const shuffled = allDomains.sort(() => 0.5 - Math.random());
      const domainsToTest = shuffled.slice(0, numToTest);

      if (signal.aborted) return;
      setStatus('checking');
      
      let blockedCount = 0;
      let testedCount = 0;

      const batchSize = 20;
      for (let i = 0; i < domainsToTest.length; i += batchSize) {
        if (signal.aborted) return;
        const batch = domainsToTest.slice(i, i + batchSize);
        
        const promises = batch.map(async (domain) => {
          try {
            const reqController = new AbortController();
            const timeoutId = setTimeout(() => reqController.abort(), 3000);
            
            const onMainAbort = () => reqController.abort();
            signal.addEventListener('abort', onMainAbort);

            await fetch(`https://${domain}/favicon.ico`, { 
              mode: 'no-cors', 
              signal: reqController.signal,
              cache: 'no-store'
            });
            
            clearTimeout(timeoutId);
            signal.removeEventListener('abort', onMainAbort);
          } catch (err) {
            blockedCount++;
          } finally {
            testedCount++;
            if (!signal.aborted) {
              setTestStats({ tested: testedCount, blocked: blockedCount, total: numToTest });
            }
          }
        });

        await Promise.allSettled(promises);
      }

      if (!signal.aborted) {
        setStatus('done');
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error("Test failed to run:", err);
      if (!signal.aborted) setStatus('error');
    }
  };

  const stopTest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setStatus('stopped');
  };

  useEffect(() => {
    startTest();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  let score = 0;
  if (testStats.total > 0 && testStats.tested > 0) {
    score = Math.round((testStats.blocked / testStats.tested) * 100);
  }

  let finalStatusClass = 'safe';
  if ((status === 'done' || status === 'stopped') && score < 50) {
    finalStatusClass = 'vulnerable';
  } else if (status === 'checking') {
    finalStatusClass = 'checking';
  } else if (status === 'stopped') {
    finalStatusClass = 'safe';
  }

  const isRunning = status === 'checking' || status === 'loading_list';

  return (
    <div className="glass-panel tester-container">
      <div className={`status-indicator status-${finalStatusClass}`}>
        {isRunning && <Loader2 size={32} className="animate-spin" />}
        {(status === 'done' || status === 'stopped') && score >= 50 && <Shield size={40} />}
        {(status === 'done' || status === 'stopped') && score < 50 && <ShieldAlert size={40} />}
        {status === 'idle' && <Shield size={40} />}
      </div>
      
      <h2 style={{ marginBottom: '0.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
        {status === 'loading_list' && 'Preparing test...'}
        {status === 'checking' && `Testing ad links... (${testStats.tested}/${testStats.total})`}
        {status === 'done' && `Test Complete! Score: ${score}%`}
        {status === 'stopped' && `Test Stopped. Current Score: ${score}%`}
        {status === 'error' && 'Failed to run test'}
      </h2>
      
      <p style={{ color: 'var(--text-secondary)' }}>
        {status === 'loading_list' && 'Downloading list of ad domains...'}
        {status === 'checking' && 'Attempting to reach randomly selected ad domains...'}
        {(status === 'done' || status === 'stopped') && score >= 80 && `Excellent! Your adblocker is highly effective. Blocked ${testStats.blocked} out of ${testStats.tested} trackers.`}
        {(status === 'done' || status === 'stopped') && score >= 50 && score < 80 && `Moderate protection. Blocked ${testStats.blocked} out of ${testStats.tested} trackers.`}
        {(status === 'done' || status === 'stopped') && score < 50 && `Warning! Your adblocker is missing a lot. Blocked only ${testStats.blocked} out of ${testStats.tested} trackers.`}
      </p>

      {(status === 'done' || status === 'stopped' || isRunning) && testStats.tested > 0 && (
        <div style={{ marginTop: '1.5rem', width: '100%', backgroundColor: 'rgba(255,255,255,0.1)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${score}%`, backgroundColor: score >= 50 ? 'var(--status-safe-color, #10b981)' : 'var(--status-vulnerable-color, #ef4444)', transition: 'width 1s ease-in-out' }}></div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'center' }}>
        <button 
          onClick={startTest} 
          disabled={isRunning}
          style={{ 
            padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', 
            background: 'var(--primary-color)', border: 'none', borderRadius: '4px', color: 'white', 
            cursor: isRunning ? 'not-allowed' : 'pointer', opacity: isRunning ? 0.5 : 1 
          }}
        >
          <Play size={16} /> Start Test
        </button>
        <button 
          onClick={stopTest} 
          disabled={!isRunning}
          style={{ 
            padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', 
            background: '#ef4444', border: 'none', borderRadius: '4px', color: 'white', 
            cursor: !isRunning ? 'not-allowed' : 'pointer', opacity: !isRunning ? 0.5 : 1 
          }}
        >
          <Square size={16} /> Stop Test
        </button>
      </div>
    </div>
  );
};

export default AdblockTester;
