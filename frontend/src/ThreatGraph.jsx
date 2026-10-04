import { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Network, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

export default function ThreatGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fgRef = useRef();

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/infrastructure/graph?limit=100')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch graph data');
        return res.json();
      })
      .then(data => {
        // Convert Cytoscape format to ForceGraph format
        const nodes = data.nodes.map(n => ({
          id: n.data.id,
          name: n.data.label,
          type: n.data.type,
          classification: n.data.classification,
          val: n.data.type === 'domain' ? 2 : 1, // Size
        }));
        
        nodes.forEach(n => {
            if (n.type === 'domain') {
              if (n.classification === 'GAMBLING_INDICATED') n.color = '#ef4444'; // Red
              else if (n.classification === 'LEGITIMATE') n.color = '#22c55e'; // Green
              else n.color = '#eab308'; // Yellow (Suspicious)
            } else if (n.type === 'ip') {
                n.color = '#3b82f6'; // Blue
            } else if (n.type === 'nameserver') {
                n.color = '#a855f7'; // Purple
            } else {
                n.color = '#9ca3af'; // Gray
            }
        });
        
        const links = data.edges.map(e => ({
          source: e.data.source,
          target: e.data.target,
          type: e.data.type
        }));
        
        setGraphData({ nodes, links });
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleZoomIn = useCallback(() => {
    if (fgRef.current) fgRef.current.zoom(fgRef.current.zoom() * 1.2, 400);
  }, []);

  const handleZoomOut = useCallback(() => {
    if (fgRef.current) fgRef.current.zoom(fgRef.current.zoom() / 1.2, 400);
  }, []);

  const handleFit = useCallback(() => {
    if (fgRef.current) fgRef.current.zoomToFit(400, 50);
  }, []);

  return (
    <div className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col h-[600px] relative w-full mt-8">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card/80 backdrop-blur z-10 flex items-center justify-between absolute top-0 left-0 right-0">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-white">Threat Infrastructure Graph</h3>
        </div>
        
        <div className="flex space-x-2">
          <button onClick={handleZoomIn} className="p-1.5 rounded-lg bg-background hover:bg-gray-800 text-gray-400 hover:text-white transition-colors border border-border">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={handleZoomOut} className="p-1.5 rounded-lg bg-background hover:bg-gray-800 text-gray-400 hover:text-white transition-colors border border-border">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={handleFit} className="p-1.5 rounded-lg bg-background hover:bg-gray-800 text-gray-400 hover:text-white transition-colors border border-border">
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur border border-border p-3 rounded-xl z-10 text-xs text-gray-300 shadow-xl">
        <div className="font-semibold text-white mb-2 pb-2 border-b border-border/50">Nodes</div>
        <div className="space-y-2">
          <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div> Gambling Domain</div>
          <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div> Safe Domain</div>
          <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div> Suspicious Domain</div>
          <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div> IP Address</div>
          <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-purple-500 mr-2"></div> Nameserver</div>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 bg-[#0f172a] relative w-full h-full">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-20">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-20">
            <div className="text-red-400 bg-red-900/20 px-4 py-2 rounded-lg border border-red-900/50">
              Error loading graph: {error}
            </div>
          </div>
        )}

        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor="color"
          nodeRelSize={6}
          linkColor={() => 'rgba(255,255,255,0.1)'}
          linkWidth={1.5}
          backgroundColor="#0f172a"
          onEngineStop={() => {
            if (fgRef.current) {
              fgRef.current.zoomToFit(400, 50);
            }
          }}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12/globalScale;
            
            // Draw Node
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.val * 3, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.color;
            ctx.fill();
            
            // Draw Label
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillText(label, node.x, node.y + (node.val * 3) + fontSize);
          }}
        />
      </div>
    </div>
  );
}
