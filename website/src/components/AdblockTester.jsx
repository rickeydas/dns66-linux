import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, Loader2 } from 'lucide-react';

const AdblockTester = () => {
  const [status, setStatus] = useState('idle'); // 'idle', 'loading_list', 'checking', 'done'
  const [testStats, setTestStats] = useState({ tested: 0, blocked: 0, total: 200 });

  useEffect(() => {
    let isMounted = true;

    const runTest = async () => {
      setStatus('loading_list');
      try {
        const response = await fetch(import.meta.env.BASE_URL + 'ad_domains.json');
        if (!response.ok) throw new Error('Failed to load domains');
        
        const data = await response.json();
        const allDomains = Object.keys(data);
        
        // Randomly select 200 domains
        const numToTest = 200;
        const shuffled = allDomains.sort(() => 0.5 - Math.random());
        const domainsToTest = shuffled.slice(0, numToTest);

        setStatus('checking');
        
        let blockedCount = 0;
        let testedCount = 0;

        // Test domains concurrently in batches to speed it up but not overwhelm the browser
        const batchSize = 20;
        for (let i = 0; i < domainsToTest.length; i += batchSize) {
          if (!isMounted) return;
          const batch = domainsToTest.slice(i, i + batchSize);
          
          const promises = batch.map(async (domain) => {
            try {
              // Try to fetch something from the domain. We use no-cors to avoid CORS errors.
              // If DNS is blocked, it throws a network error.
              // Using a short timeout via AbortController is also a good idea.
              const controller = new AbortController();
              const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout per request
              
              await fetch(`https://${domain}/favicon.ico`, { 
                mode: 'no-cors', 
                signal: controller.signal,
                cache: 'no-store'
              });
              clearTimeout(timeoutId);
              // If it reaches here without error, it's NOT blocked
            } catch (err) {
              // Network error or timeout -> assume blocked
              blockedCount++;
            } finally {
              testedCount++;
              if (isMounted) {
                setTestStats({ tested: testedCount, blocked: blockedCount, total: numToTest });
              }
            }
          });

          await Promise.allSettled(promises);
        }

        if (isMounted) {
          setStatus('done');
        }
      } catch (err) {
        console.error("Test failed to run:", err);
        if (isMounted) setStatus('error');
      }
    };

    runTest();

    return () => {
      isMounted = false;
    };
  }, []);

  let score = 0;
  if (testStats.total > 0) {
    score = Math.round((testStats.blocked / testStats.total) * 100);
  }

  let finalStatusClass = 'safe';
  if (status === 'done' && score < 50) {
    finalStatusClass = 'vulnerable';
  } else if (status === 'checking') {
    finalStatusClass = 'checking';
  }

  return (
    <div className="glass-panel tester-container">
      <div className={`status-indicator status-${finalStatusClass}`}>
        {(status === 'checking' || status === 'loading_list') && <Loader2 size={32} className="animate-spin" />}
        {status === 'done' && score >= 50 && <Shield size={40} />}
        {status === 'done' && score < 50 && <ShieldAlert size={40} />}
      </div>
      
      <h2 style={{ marginBottom: '0.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
        {status === 'loading_list' && 'Preparing test...'}
        {status === 'checking' && `Testing ad links... (${testStats.tested}/${testStats.total})`}
        {status === 'done' && `Test Complete! Score: ${score}%`}
        {status === 'error' && 'Failed to run test'}
      </h2>
      
      <p style={{ color: 'var(--text-secondary)' }}>
        {status === 'loading_list' && 'Downloading list of ad domains...'}
        {status === 'checking' && 'Attempting to reach randomly selected ad domains...'}
        {status === 'done' && score >= 80 && `Excellent! Your adblocker is highly effective. Blocked ${testStats.blocked} out of ${testStats.total} trackers.`}
        {status === 'done' && score >= 50 && score < 80 && `Moderate protection. Blocked ${testStats.blocked} out of ${testStats.total} trackers.`}
        {status === 'done' && score < 50 && `Warning! Your adblocker is missing a lot. Blocked only ${testStats.blocked} out of ${testStats.total} trackers.`}
      </p>

      {status === 'done' && (
        <div style={{ marginTop: '1.5rem', width: '100%', backgroundColor: 'rgba(255,255,255,0.1)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${score}%`, backgroundColor: score >= 50 ? 'var(--status-safe-color, #10b981)' : 'var(--status-vulnerable-color, #ef4444)', transition: 'width 1s ease-in-out' }}></div>
        </div>
      )}
    </div>
  );
};

export default AdblockTester;
