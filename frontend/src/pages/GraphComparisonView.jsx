import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { GitCompare, GitMerge, TrendingUp, Download, Loader2, FileText } from 'lucide-react';
import GraphVisualization from '../components/GraphVisualization';
import { api } from '../api';

function GraphComparisonView({ currentGraphData }) {
  const [graph1, setGraph1] = useState(null);
  const [graph2, setGraph2] = useState(null);
  const [graph1Name, setGraph1Name] = useState('Graph 1');
  const [graph2Name, setGraph2Name] = useState('Graph 2');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [mergeResult, setMergeResult] = useState(null);
  const [evolutionData, setEvolutionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('compare');
  const [mergeStrategy, setMergeStrategy] = useState('union');
  const [sessions, setSessions] = useState([]);
  const [selectedSession1, setSelectedSession1] = useState('');
  const [selectedSession2, setSelectedSession2] = useState('');

  const API_BASE = 'http://127.0.0.1:8000/api/graph-comparison';

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const res = await api.get('/api/sessions/');
      setSessions(res.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadSessionAsGraph1 = async (sessionId) => {
    if (!sessionId || sessionId === 'current') {
      setGraph1(currentGraphData);
      setGraph1Name('Current Graph');
      setSelectedSession1('current');
      return;
    }
    
    try {
      const res = await api.get(`/api/sessions/${sessionId}`);
      const session = res.data;
      if (session.graph_data) {
        setGraph1(session.graph_data);
        setGraph1Name(session.name);
        setSelectedSession1(sessionId);
      } else {
        alert('Selected session has no graph data');
      }
    } catch (error) {
      console.error('Error loading session:', error);
      alert('Failed to load session');
    }
  };

  const loadSessionAsGraph2 = async (sessionId) => {
    if (!sessionId || sessionId === 'current') {
      setGraph2(currentGraphData);
      setGraph2Name('Current Graph');
      setSelectedSession2('current');
      return;
    }
    
    try {
      const res = await api.get(`/api/sessions/${sessionId}`);
      const session = res.data;
      if (session.graph_data) {
        setGraph2(session.graph_data);
        setGraph2Name(session.name);
        setSelectedSession2(sessionId);
      } else {
        alert('Selected session has no graph data');
      }
    } catch (error) {
      console.error('Error loading session:', error);
      alert('Failed to load session');
    }
  };

  const compareGraphs = async () => {
    if (!graph1 || !graph2) {
      alert('Please load both graphs to compare');
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/compare`, {
        graph1,
        graph2,
        name1: graph1Name,
        name2: graph2Name,
        save: false
      });
      setComparisonResult(res.data);
    } catch (error) {
      console.error('Error comparing graphs:', error);
      alert('Failed to compare graphs');
    } finally {
      setLoading(false);
    }
  };

  const mergeGraphs = async () => {
    if (!graph1 || !graph2) {
      alert('Please load both graphs to merge');
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/merge`, {
        graph1,
        graph2,
        merge_strategy: mergeStrategy
      });
      setMergeResult(res.data);
    } catch (error) {
      console.error('Error merging graphs:', error);
      alert('Failed to merge graphs');
    } finally {
      setLoading(false);
    }
  };

  const trackEvolution = async () => {
    if (!graph1 || !graph2) {
      alert('Please load both graphs to track evolution');
      return;
    }

    try {
      setLoading(true);
      const versions = [
        { ...graph1, timestamp: new Date().toISOString() },
        { ...graph2, timestamp: new Date().toISOString() }
      ];
      const res = await axios.post(`${API_BASE}/evolution/track`, {
        graph_versions: versions
      });
      setEvolutionData(res.data);
    } catch (error) {
      console.error('Error tracking evolution:', error);
      alert('Failed to track evolution');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-teal-400 mb-2">Graph Comparison</h1>
        <p className="text-gray-400">Compare, merge, and track evolution of graph versions</p>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">Graph 1</label>
            <div className="space-y-2">
              <select
                value={selectedSession1}
                onChange={(e) => loadSessionAsGraph1(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              >
                <option value="current">Current Graph</option>
                <option value="">-- Select Saved Session --</option>
                {sessions.map((session) => (
                  <option key={session.session_id} value={session.session_id}>
                    {session.name} (v{session.version})
                  </option>
                ))}
              </select>
              {graph1 && (
                <div className="space-y-1">
                  <p className="text-xs text-gray-400">
                    Loaded: {graph1Name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {graph1.nodes?.length || 0} nodes, {graph1.links?.length || 0} links
                  </p>
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Graph 2</label>
            <div className="space-y-2">
              <select
                value={selectedSession2}
                onChange={(e) => loadSessionAsGraph2(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              >
                <option value="current">Current Graph</option>
                <option value="">-- Select Saved Session --</option>
                {sessions.map((session) => (
                  <option key={session.session_id} value={session.session_id}>
                    {session.name} (v{session.version})
                  </option>
                ))}
              </select>
              {graph2 && (
                <div className="space-y-1">
                  <p className="text-xs text-gray-400">
                    Loaded: {graph2Name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {graph2.nodes?.length || 0} nodes, {graph2.links?.length || 0} links
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('compare')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'compare'
              ? 'border-b-2 border-teal-500 text-teal-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          <GitCompare className="w-4 h-4 inline mr-2" />
          Compare
        </button>
        <button
          onClick={() => setActiveTab('merge')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'merge'
              ? 'border-b-2 border-teal-500 text-teal-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          <GitMerge className="w-4 h-4 inline mr-2" />
          Merge
        </button>
        <button
          onClick={() => setActiveTab('evolution')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'evolution'
              ? 'border-b-2 border-teal-500 text-teal-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          <TrendingUp className="w-4 h-4 inline mr-2" />
          Evolution
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'compare' && (
          <div className="space-y-4">
            <button
              onClick={compareGraphs}
              disabled={loading || !graph1 || !graph2}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null}
              Compare Graphs
            </button>

            {comparisonResult && (
              <div className="space-y-4">
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                  <h2 className="text-xl font-bold mb-4">Comparison Results</h2>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <h3 className="font-medium mb-2">{comparisonResult.version1?.name}</h3>
                      <p className="text-sm text-gray-400">
                        {comparisonResult.version1?.graph_data?.nodes?.length || 0} nodes,{' '}
                        {comparisonResult.version1?.graph_data?.links?.length || 0} links
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">{comparisonResult.version2?.name}</h3>
                      <p className="text-sm text-gray-400">
                        {comparisonResult.version2?.graph_data?.nodes?.length || 0} nodes,{' '}
                        {comparisonResult.version2?.graph_data?.links?.length || 0} links
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-gray-700 rounded mb-4">
                    <h3 className="font-medium mb-2">Similarity Score</h3>
                    <div className="text-3xl font-bold text-teal-400">
                      {(comparisonResult.differences?.similarity_score * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-medium mb-2">Node Differences</h3>
                      <div className="space-y-1 text-sm">
                        <p className="text-green-400">
                          +{comparisonResult.differences?.nodes?.count_added || 0} added
                        </p>
                        <p className="text-red-400">
                          -{comparisonResult.differences?.nodes?.count_removed || 0} removed
                        </p>
                        <p className="text-yellow-400">
                          ~{comparisonResult.differences?.nodes?.count_modified || 0} modified
                        </p>
                        <p className="text-gray-400">
                          ={comparisonResult.differences?.nodes?.count_unchanged || 0} unchanged
                        </p>
                      </div>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">Link Differences</h3>
                      <div className="space-y-1 text-sm">
                        <p className="text-green-400">
                          +{comparisonResult.differences?.links?.count_added || 0} added
                        </p>
                        <p className="text-red-400">
                          -{comparisonResult.differences?.links?.count_removed || 0} removed
                        </p>
                        <p className="text-yellow-400">
                          ~{comparisonResult.differences?.links?.count_modified || 0} modified
                        </p>
                        <p className="text-gray-400">
                          ={comparisonResult.differences?.links?.count_unchanged || 0} unchanged
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'merge' && (
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <label className="block text-sm font-medium mb-2">Merge Strategy</label>
              <select
                value={mergeStrategy}
                onChange={(e) => setMergeStrategy(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="union">Union (All nodes and links)</option>
                <option value="intersection">Intersection (Common only)</option>
                <option value="prefer_first">Prefer First</option>
                <option value="prefer_second">Prefer Second</option>
              </select>
            </div>

            <button
              onClick={mergeGraphs}
              disabled={loading || !graph1 || !graph2}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null}
              Merge Graphs
            </button>

            {mergeResult && (
              <div className="space-y-4">
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                  <h2 className="text-xl font-bold mb-4">Merge Results</h2>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <h3 className="font-medium mb-2">Statistics</h3>
                      <div className="space-y-1 text-sm">
                        <p>Total Nodes: {mergeResult.statistics?.total_nodes || 0}</p>
                        <p>Total Links: {mergeResult.statistics?.total_links || 0}</p>
                        <p className="text-green-400">
                          From Graph 1: {mergeResult.statistics?.nodes_from_1 || 0} nodes,{' '}
                          {mergeResult.statistics?.links_from_1 || 0} links
                        </p>
                        <p className="text-blue-400">
                          From Graph 2: {mergeResult.statistics?.nodes_from_2 || 0} nodes,{' '}
                          {mergeResult.statistics?.links_from_2 || 0} links
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4" style={{ height: '400px' }}>
                    <GraphVisualization
                      graphData={mergeResult.merged_graph}
                      graphReady={true}
                      transcriptId={null}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'evolution' && (
          <div className="space-y-4">
            <button
              onClick={trackEvolution}
              disabled={loading || !graph1 || !graph2}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null}
              Track Evolution
            </button>

            {evolutionData && (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h2 className="text-xl font-bold mb-4">Evolution Timeline</h2>
                <div className="space-y-4">
                  {evolutionData.evolution_steps?.map((step, idx) => (
                    <div key={idx} className="border-l-2 border-teal-500 pl-4">
                      <h3 className="font-medium">
                        Version {step.from_version} → Version {step.to_version}
                      </h3>
                      <p className="text-xs text-gray-400 mb-2">{step.timestamp}</p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-green-400">+{step.nodes_added} nodes added</p>
                          <p className="text-red-400">-{step.nodes_removed} nodes removed</p>
                          <p className="text-yellow-400">~{step.nodes_modified} nodes modified</p>
                        </div>
                        <div>
                          <p className="text-green-400">+{step.links_added} links added</p>
                          <p className="text-red-400">-{step.links_removed} links removed</p>
                          <p className="text-yellow-400">~{step.links_modified} links modified</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  <div className="mt-4 p-4 bg-gray-700 rounded">
                    <h3 className="font-medium mb-2">Summary</h3>
                    <div className="text-sm space-y-1">
                      <p>
                        Total Node Additions: {evolutionData.summary?.total_node_additions || 0}
                      </p>
                      <p>
                        Total Node Removals: {evolutionData.summary?.total_node_removals || 0}
                      </p>
                      <p>
                        Total Link Additions: {evolutionData.summary?.total_link_additions || 0}
                      </p>
                      <p>
                        Total Link Removals: {evolutionData.summary?.total_link_removals || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default GraphComparisonView;

