import React, { useState } from 'react';

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const wsRef = React.useRef<WebSocket | null>(null);

  /* ------------------------------------------------------------------
   * Establish WebSocket connection to backend once on mount.
   * ------------------------------------------------------------------ */
  React.useEffect(() => {
    // NOTE: Adjust URL if backend runs on a different host / protocol.
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      console.info('[Chat] WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const text = data?.text ?? event.data;
        setMessages((prev) => [...prev, { text, sender: 'bot' }]);
      } catch {
        // Fallback to raw text if JSON parsing fails
        setMessages((prev) => [...prev, { text: event.data, sender: 'bot' }]);
      }
    };

    ws.onerror = (e) => {
      console.error('[Chat] WebSocket error', e);
    };

    ws.onclose = () => {
      console.info('[Chat] WebSocket disconnected');
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  const handleSend = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: 'user' }]);
      // Send message via WebSocket if connected
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            text: input,
            timestamp: Date.now(),
          }),
        );
      }
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.map((msg, index) => (
          <div key={index} className={`p-2 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="border-t border-green-500 p-2 flex">
        <input
          type="text"
          className="bg-black w-full focus:outline-none"
          placeholder="Enter your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} className="ml-2 px-4 py-1 border border-green-500 rounded">Send</button>
      </div>
    </div>
  );
};

export default Chat;
