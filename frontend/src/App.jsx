import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import HomeView from './pages/HomeView';
import AboutView from './pages/AboutView';
import SettingsView from './pages/SettingsView';
import HelpView from './pages/HelpView';
import SessionsView from './pages/SessionsView';
import GraphComparisonView from './pages/GraphComparisonView';
import CustomViewsView from './pages/CustomViewsView';
import DocumentsView from './pages/DocumentsView';
import { mockGraphData } from './utils/mockData';

function App() {
  const [activeView, setActiveView] = useState('home');
  const [graphData, setGraphData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [graphReady, setGraphReady] = useState(false);
  const [transcriptId, setTranscriptId] = useState(null);

  // Add callback
  const handleGraphReady = ({ transcriptId }) => {
    setTranscriptId(transcriptId ?? null);
    setGraphReady(true);
  };

  // Add callback to handle transcription complete with graph data
  const handleTranscribeComplete = ({ graphData, conversationId, audioId, skipped }) => {
    console.log('App received transcribe complete:', { graphData, conversationId, audioId, skipped });
    
    if (graphData) {
      setGraphData(graphData);
      setGraphReady(true);
    }
    
    if (conversationId) {
      setTranscriptId(conversationId);
      setGraphReady(true);
    }
  };

  const handleSendMessage = (msg) => {
    setMessages([...messages, { id: Date.now(), text: msg, sender: 'user' }]);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: 'Processing your request...',
          sender: 'assistant',
        },
      ]);
      setGraphData(mockGraphData);
    }, 500);
  };

  const handleLoadSession = ({ messages, graphData, transcriptId }) => {
    if (messages) setMessages(messages);
    if (graphData) setGraphData(graphData);
    if (transcriptId) setTranscriptId(transcriptId);
    setGraphReady(true);
  };

  const handleApplyView = ({ activeFilters, layoutConfig, nodePositions }) => {
    // This can be passed to GraphVisualization component if needed
    console.log('Applying view:', { activeFilters, layoutConfig, nodePositions });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onUpload={() => setGraphData(mockGraphData)}
        onClearGraph={() => {
          setGraphData(null);
          setGraphReady(false);
          setTranscriptId(null);
        }}
        onGraphReady={handleGraphReady}
        onTranscribeComplete={handleTranscribeComplete}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav activeView={activeView} setActiveView={setActiveView} />

        <main className="flex-1 overflow-auto p-6">
          {activeView === 'home' && (
            <HomeView 
              graphData={graphData} 
              graphReady={graphReady} 
              transcriptId={transcriptId} 
              messages={messages} 
              onSendMessage={handleSendMessage} 
            />
          )}
          {activeView === 'sessions' && (
            <SessionsView
              currentMessages={messages}
              currentGraphData={graphData}
              currentTranscriptId={transcriptId}
              onLoadSession={handleLoadSession}
            />
          )}
          {activeView === 'comparison' && (
            <GraphComparisonView currentGraphData={graphData} />
          )}
          {activeView === 'views' && (
            <CustomViewsView
              currentGraphData={graphData}
              onApplyView={handleApplyView}
            />
          )}
          {activeView === 'documents' && (
            <DocumentsView
              currentGraphData={graphData}
              currentMessages={messages}
            />
          )}
          {activeView === 'about' && <AboutView />}
          {activeView === 'settings' && <SettingsView />}
          {activeView === 'help' && <HelpView />}
        </main>
      </div>
    </div>
  );
}

export default App;