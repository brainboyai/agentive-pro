// frontend/src/App.tsx
import { useState } from 'react';
import './index.css';
import { PlanWidget } from './components/widgets/PlanWidget'; // Import the new widget

type Message = {
  sender: 'user' | 'agent';
  text?: string; // Text is now optional
  response_type?: 'answer' | 'plan';
  steps?: { title: string; description: string }[];
};

function App() {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { sender: 'user', text };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [userMessage] }), // Send only the latest message
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      const agentResponseData = data.agent_response;
      
      if (agentResponseData) {
        const agentMessage: Message = {
          sender: 'agent',
          text: agentResponseData.text,
          response_type: agentResponseData.response_type,
          steps: agentResponseData.steps,
        };
        setMessages(prev => [...prev, agentMessage]);
      } else {
        console.log("Received a response without a displayable message.");
      }

    } catch (error) {
      console.error("Failed to fetch:", error);
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
      <div style={styles.header}><h1>Agentive Pro (Simple Planner)</h1></div>
      <div style={styles.chatHistory}>
        {messages.map((msg, index) => (
          <div key={index} style={{ width: '100%' }}>
            {/* Render a standard text message */}
            {msg.text && (
              <div style={msg.sender === 'user' ? styles.userMessage : styles.agentMessage}>
                {msg.text}
              </div>
            )}
            
            {/* Render the plan widget */}
            {msg.response_type === 'plan' && msg.steps && (
              <PlanWidget steps={msg.steps} onStepClick={(stepTitle) => handleSendMessage(stepTitle)} />
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleFormSubmit} style={styles.chatInputForm}>
        <input
          type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter a goal..." style={styles.chatInput}
        />
        <button type="submit" style={styles.sendButton}>Send</button>
      </form>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
    container: { display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', backgroundColor: '#f0f2f5' },
    header: { backgroundColor: '#fff', padding: '10px 20px', borderBottom: '1px solid #ddd', textAlign: 'center' },
    chatHistory: { flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-start' },
    userMessage: { alignSelf: 'flex-end', backgroundColor: '#0084ff', color: 'white', padding: '10px 15px', borderRadius: '20px', marginBottom: '10px', maxWidth: '70%'},
    agentMessage: { alignSelf: 'flex-start', backgroundColor: '#e4e6eb', color: '#050505', padding: '10px 15px', borderRadius: '20px', marginBottom: '10px', maxWidth: '70%' },
    chatInputForm: { display: 'flex', padding: '20px', borderTop: '1px solid #ddd', backgroundColor: '#fff' },
    chatInput: { flex: 1, padding: '10px 15px', borderRadius: '20px', border: '1px solid #ccc', fontSize: '16px' },
    sendButton: { marginLeft: '10px', padding: '10px 20px', border: 'none', borderRadius: '20px', backgroundColor: '#0084ff', color: 'white', fontSize: '16px', cursor: 'pointer' },
};

export default App;