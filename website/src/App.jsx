import React from 'react';
import AdblockTester from './components/AdblockTester';
import { Download, ShieldCheck, Zap, Globe, Heart, Code } from 'lucide-react';
import './index.css';

const GithubIcon = ({ size = 24 }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.02c3.18-.35 6.5-1.56 6.5-7.14a5.2 5.2 0 0 0-1.45-3.8 4.9 4.9 0 0 0-.1-3.72s-1.18-.37-3.88 1.4a13.3 13.3 0 0 0-7 0c-2.7-1.77-3.88-1.4-3.88-1.4a4.9 4.9 0 0 0-.1 3.72 5.2 5.2 0 0 0-1.45 3.8c0 5.57 3.3 6.79 6.47 7.14A4.8 4.8 0 0 0 6 18v4"></path>
    <path d="M9 18c-4.51 2-5-2-7-2"></path>
  </svg>
);

function App() {
  return (
    <div className="app-container">
      <header style={{ position: 'relative' }}>
        <a 
          href="https://github.com/rickeydas/dns66-linux" 
          target="_blank" 
          rel="noopener noreferrer" 
          style={{ position: 'absolute', top: '1rem', right: '1rem', color: 'var(--text-primary)' }}
          title="View on GitHub"
        >
          <GithubIcon size={32} />
        </a>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <img src={import.meta.env.BASE_URL + "dns66-icon.svg"} alt="DNS66 Logo" width="64" height="64" />
          <h1 style={{ margin: 0 }}>
            DNS66 for <span className="gradient-text">Linux</span>
          </h1>
        </div>
        <p>
          A native, system-wide DNS Proxy and Adblocker. Immune to browser restrictions. Keep your entire desktop ad-free.
        </p>
        <div style={{ marginTop: '2rem' }}>
          <a href="https://github.com/rickeydas/dns66-linux" target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
            <button className="btn-primary">
              <Download size={20} />
              Download Latest Release
            </button>
          </a>
        </div>
      </header>

      <main style={{ display: 'flex', flexDirection: 'column', gap: '4rem' }}>
        <section>
          <div style={{ maxWidth: '600px', margin: '0 auto' }}>
            <AdblockTester />
          </div>
        </section>

        <section className="glass-panel" style={{ textAlign: 'center' }}>
          <h2 style={{ marginBottom: '2rem', fontSize: '2rem' }}>See it in action</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2rem' }}>
            <div style={{ flex: '0 1 350px', maxWidth: '350px' }}>
              <img 
                src={import.meta.env.BASE_URL + "image1.png"} 
                alt="DNS66 Client - Home" 
                style={{ width: '100%', height: 'auto', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)' }} 
              />
            </div>
            <div style={{ flex: '0 1 350px', maxWidth: '350px' }}>
              <img 
                src={import.meta.env.BASE_URL + "image2.png"} 
                alt="DNS66 Client - Test AdBlock" 
                style={{ width: '100%', height: 'auto', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)' }} 
              />
            </div>
          </div>
        </section>

        <section className="glass-panel">
          <h2 style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '2rem' }}>Why DNS66 Linux?</h2>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <ShieldCheck size={24} />
              </div>
              <h3>Manifest V3 Immune</h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Unlike traditional browser extensions, DNS66 operates at the system level (`systemd-resolved`), making it completely immune to Chrome's new restrictive adblocking policies.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Globe size={24} />
              </div>
              <h3>System-Wide Blocking</h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Don't just block ads in your browser. Block tracking scripts, telemetry, and ads across all applications on your Linux desktop.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Zap size={24} />
              </div>
              <h3>Lightweight & Native</h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Built specifically for Linux. Low memory footprint, fast DNS resolution via `dnslib`, and a clean UI for managing your blocklists.
              </p>
            </div>
          </div>
        </section>

        <section className="glass-panel" style={{ marginTop: '2rem' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '2rem' }}>Community & Support</h2>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
                <Heart size={24} />
              </div>
              <h3>Donation</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                If you find this project useful, please consider supporting its development.
              </p>
              <a href="https://github.com/rickeydas/dns66-linux" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)' }}>
                Support the project →
              </a>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <GithubIcon size={24} />
              </div>
              <h3>Contribution</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                DNS66 for Linux is completely open-source. We welcome issues, feature requests, and pull requests.
              </p>
              <a href="https://github.com/rickeydas/dns66-linux" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)' }}>
                Contribute on GitHub →
              </a>
            </div>

            <div className="feature-card">
              <div className="feature-icon" style={{ backgroundColor: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>
                <Code size={24} />
              </div>
              <h3>Credits</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Inspired by the original DNS66 for Android. Built with Python, dnslib, GTK, and React.
              </p>
              <a href="https://github.com/rickeydas/dns66-linux#credits" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)' }}>
                View all credits →
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem 0' }}>
        <p>Inspired by DNS66 for Android. Open Source and Free.</p>
      </footer>
    </div>
  );
}

export default App;
