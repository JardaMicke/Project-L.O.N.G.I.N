import React from 'react';
import ThinkingIndicator from './components/ThinkingIndicator';
import Chat from './components/Chat';

const App: React.FC = () => {
  return (
    <div className="bg-black text-green-500 min-h-screen font-mono">
      <header className="border-b border-green-500 p-4 flex justify-between items-center">
        <h1 className="text-2xl">L.O.N.G.I.N.</h1>
        <div className="flex items-center space-x-4">
          <div>Provider: LM Studio</div>
          <div>Model: stable-code-...</div>
        </div>
      </header>
      <div className="flex">
        <aside className="w-64 border-r border-green-500 p-4">
          <ul>
            <li>Chat</li>
          </ul>
        </aside>
        <main className="flex-1 p-4">
          <div className="border border-green-500 p-4 h-full">
            <div className="flex flex-col h-full">
              <div className="flex-1">
                <Chat />
              </div>
              <div className="border-t border-green-500 p-2">
                <input type="text" className="bg-black w-full focus:outline-none" placeholder="Enter your message..." />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
