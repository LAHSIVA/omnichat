import "./LoadingScreen.css";

interface LoadingScreenProps {
  message?: string;
}

function LoadingScreen({
  message = "Preparing your workspace",
}: LoadingScreenProps) {
  return (
    <main
      className="loading-screen"
      aria-label="Loading OmniChat"
      aria-busy="true"
    >
      <div className="loading-background" />

      <section className="loading-content">
        <div className="loading-brand">
          <div className="loading-logo-wrapper">
            <div className="loading-logo-glow" />

            <div className="loading-logo">
              <span>✦</span>
            </div>
          </div>

          <div className="loading-brand-name">
            OmniChat
          </div>
        </div>

        <div className="loading-status">
          <div className="loading-status-message">
            {message}
          </div>

          <div className="loading-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>

        <div className="loading-progress" aria-hidden="true">
          <div className="loading-progress-bar" />
        </div>

        <p className="loading-caption">
          Intelligent conversations, ready when you are.
        </p>
      </section>
    </main>
  );
}

export default LoadingScreen;
