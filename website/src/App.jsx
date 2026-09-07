import React from 'react';
import AdblockTester from './components/AdblockTester';
import { Download, ShieldCheck, Zap, Globe, Heart, Github, Code } from 'lucide-react';
import './index.css';

function App() {
  return (
    <div className="app-container">
      <header>
        <h1>
          DNS66 for <span className="gradient-text">Linux</span>
        </h1>
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
                <Github size={24} />
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
