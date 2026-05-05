import React from 'react';

/*
  Converted Dashboard UI based on provided Tailwind HTML.
  This component is presentational — hook it up to App state as needed.
*/

export default function Dashboard({ callStatus = 'idle', incomingCall = null, backendStatus = 'checking' }) {
  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface font-body-md antialiased">
      <header className="bg-slate-950/80 backdrop-blur-xl border-b border-white/10 sticky top-0 z-50">
        <div className="flex justify-between items-center px-8 py-4 max-w-[1280px] mx-auto">
          <div className="text-2xl font-bold tracking-tighter text-white">GenCal AI</div>
          <nav className="hidden md:flex items-center gap-8">
            <button className="text-blue-400 font-semibold border-b-2 border-blue-500 pb-1" onClick={() => {}}>Dashboard</button>
            <button className="text-slate-400 font-medium" onClick={() => {}}>History</button>
          </nav>
          <div className="flex items-center gap-4">
            <button className="material-symbols-outlined text-slate-400">account_circle</button>
          </div>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto px-gutter py-xl flex flex-col gap-xl">
        <section className="flex justify-center w-full">
          <div className="glass-surface w-full max-w-4xl rounded-3xl p-12 flex flex-col items-center text-center relative overflow-hidden">
            <div className="absolute -top-24 -left-24 w-64 h-64 bg-primary/10 rounded-full blur-[80px]"></div>
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-secondary/10 rounded-full blur-[80px]"></div>
            <h1 className="font-display-xl text-display-xl text-on-background mb-sm">Start AI Call</h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant mb-xl max-w-md">Talk with your AI assistant instantly and optimize your schedule.</p>
            <div className="flex flex-col items-center gap-md group">
              <button className="w-24 h-24 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-xl hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-white text-5xl" style={{fontVariationSettings: '"FILL" 1'}}>mic</span>
              </button>
              <span className="font-headline-md text-headline-md text-primary tracking-wide">Start Call</span>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter w-full">
          <div className="glass-surface rounded-2xl p-6">
            <span className="font-label-sm uppercase tracking-widest text-outline">Last Call</span>
            <div className="flex items-baseline gap-xs mt-2">
              <span className="font-headline-lg text-headline-lg text-on-surface">2m ago</span>
            </div>
            <div className="mt-2 h-1 w-full bg-surface-variant rounded-full overflow-hidden">
              <div className="h-full bg-primary w-2/3"></div>
            </div>
          </div>

          <div className="glass-surface rounded-2xl p-6">
            <span className="font-label-sm uppercase tracking-widest text-outline">Total Interactions</span>
            <div className="flex items-baseline gap-xs mt-2">
              <span className="font-headline-lg text-headline-lg text-on-surface">128</span>
              <span className="font-label-sm text-secondary ml-2">+12%</span>
            </div>
            <div className="mt-2 h-1 w-full bg-surface-variant rounded-full overflow-hidden">
              <div className="h-full bg-secondary w-1/2"></div>
            </div>
          </div>

          <div className="glass-surface rounded-2xl p-6 relative">
            <span className="font-label-sm uppercase tracking-widest text-outline">AI Status</span>
            <div className="flex items-center gap-sm mt-2">
              <span className="font-headline-lg text-headline-lg text-on-surface">Online</span>
              <div className="ml-3 relative w-4 h-4">
                <div className="absolute w-4 h-4 bg-secondary/30 rounded-full animate-ping"></div>
                <div className="w-3 h-3 bg-secondary rounded-full shadow-[0_0_10px_rgba(78,222,163,0.5)]"></div>
              </div>
            </div>
            <p className="font-label-sm text-on-surface-variant mt-2">Low latency mode active</p>
          </div>
        </section>

        <section className="flex flex-col gap-lg w-full">
          <div className="flex justify-between items-end">
            <h2 className="font-headline-lg text-headline-lg text-on-background">Recent Activity</h2>
            <button className="font-label-sm text-primary hover:underline">View All History</button>
          </div>

          <div className="glass-surface rounded-3xl overflow-hidden border border-white/5">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between p-6 border-b border-white/10 gap-md">
              <div className="flex items-center gap-md">
                <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined">call</span>
                </div>
                <div>
                  <p className="font-headline-md text-body-md text-on-surface">Oct 24, 2023</p>
                  <p className="font-label-sm text-outline">Duration: 4:12</p>
                </div>
              </div>
              <div className="flex-1 px-0 md:px-lg max-w-xl">
                <p className="text-on-surface-variant italic font-body-md line-clamp-1 border-l-2 border-primary/30 pl-4">"Scheduled the quarterly sync with the marketing department and summarized priority action items..."</p>
              </div>
              <div className="flex items-center gap-sm">
                <button className="material-symbols-outlined p-2 rounded-lg hover:bg-surface-variant text-outline">play_arrow</button>
                <button className="material-symbols-outlined p-2 rounded-lg hover:bg-surface-variant text-outline">more_vert</button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-xl py-lg border-t border-white/5 text-center">
        <p className="font-body-md text-outline">Your AI assistant, one call away</p>
      </footer>
    </div>
  );
}
