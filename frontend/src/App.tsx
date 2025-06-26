// frontend/src/App.tsx
import { useState } from 'react';
import './index.css';
import { Canvas } from './components/Canvas';

type Message = {
  sender: 'user' | 'agent';
  text: string;
  options?: string[];
  response_type?: 'answer' | 'clarification' | 'canvas';
  widgets?: any[];
};

function App() {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sharedContext, setSharedContext] = useState({});

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { sender: 'user', text };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: newMessages,
          shared_context: sharedContext
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      const agentResponseData = data.agent_response;
      
      if (data.shared_context) {
        setSharedContext(data.shared_context);
      }

      // --- FINAL FIX: Check if agentResponseData exists before processing ---
      if (agentResponseData) {
        const agentMessage: Message = {
          sender: 'agent',
          text: agentResponseData.text,
          options: agentResponseData.options,
          response_type: agentResponseData.response_type,
          widgets: agentResponseData.widgets,
        };
        setMessages(prev => [...prev, agentMessage]);
      } else {
        console.log("Received a response without a displayable message.");
      }

    } catch (error) {
      console.error("Failed to fetch:", error); // This line is App.tsx:59
      const errorMessage: Message = { sender: 'agent', text: 'Sorry, I had trouble connecting to the server.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };
  
  const handleFormSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    handleSendMessage(inputValue);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}><h1>Agentive Pro</h1></div>
      <div style={styles.chatHistory}>
        {messages.map((msg, index) => (
          <div key={index}>
            {msg.response_type !== 'canvas' && (
              <div style={msg.sender === 'user' ? styles.userMessage : styles.agentMessage}>
                {msg.text}
                {msg.response_type === 'clarification' && msg.options && (
                  <div style={styles.optionsContainer}>
                    {msg.options.map((option, i) => (
                      <button key={i} style={styles.optionButton} onClick={() => handleSendMessage(option)}>
                        {option}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            {msg.response_type === 'canvas' && msg.widgets && (
              <Canvas widgets={msg.widgets} />
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleFormSubmit} style={styles.chatInputForm}>
        <input
          type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask a question or state a goal..." style={styles.chatInput}
        />
        <button type="submit" style={styles.sendButton}>Send</button>
      </form>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
    container: { display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', backgroundColor: '#f0f2f5' },
    header: { backgroundColor: '#fff', padding: '10px 20px', borderBottom: '1px solid #ddd', textAlign: 'center' },
    chatHistory: { flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column' },
    userMessage: { alignSelf: 'flex-end', backgroundColor: '#0084ff', color: 'white', padding: '10px 15px', borderRadius: '20px', marginBottom: '10px', maxWidth: '70%', marginLeft: 'auto' },
    agentMessage: { alignSelf: 'flex-start', backgroundColor: '#e4e6eb', color: '#050505', padding: '10px 15px', borderRadius: '20px', marginBottom: '10px', maxWidth: '70%', marginRight: 'auto' },
    chatInputForm: { display: 'flex', padding: '20px', borderTop: '1px solid #ddd', backgroundColor: '#fff' },
    chatInput: { flex: 1, padding: '10px 15px', borderRadius: '20px', border: '1px solid #ccc', fontSize: '16px' },
    sendButton: { marginLeft: '10px', padding: '10px 20px', border: 'none', borderRadius: '20px', backgroundColor: '#0084ff', color: 'white', fontSize: '16px', cursor: 'pointer' },
    optionsContainer: { display: 'flex', flexWrap: 'wrap', marginTop: '10px' },
    optionButton: { backgroundColor: '#fff', border: '1px solid #0084ff', color: '#0084ff', padding: '8px 12px', borderRadius: '20px', margin: '5px 5px 0 0', cursor: 'pointer', fontSize: '14px' }
  };

export default App;