import React from 'react';

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, details) {
    console.error('Nexora route failed safely:', error, details);
  }

  componentDidUpdate(previousProps) {
    if (previousProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main style={{ minHeight: '70vh', display: 'grid', placeItems: 'center', padding: 32, color: '#f0edff' }}>
        <section style={{ maxWidth: 620, padding: 28, border: '1px solid rgba(251,113,133,.25)', borderRadius: 16, background: 'rgba(15,16,28,.92)' }}>
          <span style={{ color: '#fb7185', letterSpacing: 2, fontSize: 12 }}>ROUTE RECOVERY</span>
          <h1>This view hit a recoverable error</h1>
          <p>The rest of Nexora is still running. Reload this view or choose another section from the navigation.</p>
          <button onClick={() => window.location.reload()}>Reload view</button>
        </section>
      </main>
    );
  }
}

export default AppErrorBoundary;
