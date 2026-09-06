import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, Loader2 } from 'lucide-react';

const AdblockTester = () => {
  const [status, setStatus] = useState('checking'); // 'checking', 'safe', 'vulnerable'

  useEffect(() => {
    // Reset dummy ad flag in case of re-renders
    window.adblockerTestDummyAdLoaded = false;

    // We dynamically create a script tag to load our bait file.
    // Adblockers usually block scripts named "dummy-ad.js" or similar.
    const script = document.createElement('script');
    script.src = import.meta.env.BASE_URL + 'dummy-ad.js?bypassCache=' + new Date().getTime();
    script.async = true;

    script.onload = () => {
      // If the script successfully loads and executes, our flag will be true.
      if (window.adblockerTestDummyAdLoaded) {
        setStatus('vulnerable');
      }
    };

    script.onerror = () => {
      // If the script fails to load (e.g., blocked by network or browser extension)
      setStatus('safe');
    };

    document.body.appendChild(script);

    // Cleanup
    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  return (
    <div className="glass-panel tester-container">
      <div className={`status-indicator status-${status}`}>
        {status === 'checking' && <Loader2 size={32} className="animate-spin" />}
        {status === 'safe' && <Shield size={40} />}
        {status === 'vulnerable' && <ShieldAlert size={40} />}
      </div>
      
      <h2 style={{ marginBottom: '0.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
        {status === 'checking' && 'Testing your connection...'}
        {status === 'safe' && 'Awesome! You are protected.'}
        {status === 'vulnerable' && 'Warning! Ads are not blocked.'}
      </h2>
      
      <p style={{ color: 'var(--text-secondary)' }}>
        {status === 'checking' && 'Attempting to load a dummy tracker...'}
        {status === 'safe' && 'Your current setup (like DNS66) successfully blocked our test tracker.'}
        {status === 'vulnerable' && 'Our test tracker loaded successfully. You are exposed to tracking and ads.'}
      </p>
    </div>
  );
};

export default AdblockTester;
