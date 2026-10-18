import React, { useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  NodeProps,
  Edge,
  Node,
} from 'reactflow';
import { ShieldAlert, Code2, TestTube2, ArrowRight, Layers } from 'lucide-react';

// Custom Node for Target Symbol
const TargetNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="bg-slate-900 border-2 border-indigo-500 rounded-xl p-3.5 shadow-2xl shadow-indigo-500/30 min-w-[200px] text-white">
      <Handle type="target" position={Position.Left} className="bg-indigo-400" />
      <div className="flex items-center space-x-2 mb-1.5">
        <span className="p-1 rounded-md bg-indigo-500/20 text-indigo-400">
          <ShieldAlert className="w-4 h-4" />
        </span>
        <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400">
          Change Target (Origin)
        </span>
      </div>
      <p className="font-bold text-sm font-mono text-white truncate">{data.label}()</p>
      <p className="text-[11px] text-slate-400 font-mono truncate mt-0.5">{data.sublabel}</p>
      <Handle type="source" position={Position.Right} className="bg-indigo-400" />
    </div>
  );
};

// Custom Node for Dependent Symbols
const DependentNode: React.FC<NodeProps> = ({ data }) => {
  const isDirect = data.impact_type === 'direct';
  return (
    <div
      className={`bg-slate-900 border rounded-xl p-3 shadow-lg min-w-[190px] text-white ${
        isDirect ? 'border-amber-500/70 shadow-amber-500/10' : 'border-slate-700'
      }`}
    >
      <Handle type="target" position={Position.Left} className="bg-slate-400" />
      <div className="flex items-center justify-between mb-1">
        <span
          className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
            isDirect ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'
          }`}
        >
          {data.hop_count} {data.hop_count === 1 ? 'Hop' : 'Hops'}
        </span>
        <span className="text-[10px] text-slate-400 capitalize">{data.symbol_type}</span>
      </div>
      <p className="font-semibold text-xs font-mono text-slate-200 truncate">{data.label}()</p>
      <p className="text-[10px] text-slate-400 font-mono truncate">{data.sublabel}</p>
      <Handle type="source" position={Position.Right} className="bg-slate-400" />
    </div>
  );
};

// Custom Node for Tests
const TestNode: React.FC<NodeProps> = ({ data }) => {
  const isDirect = data.hop_count === 1;
  return (
    <div
      className={`bg-slate-900 border rounded-xl p-3 shadow-lg min-w-[200px] text-white ${
        isDirect ? 'border-emerald-500 shadow-emerald-500/20' : 'border-emerald-700/60'
      }`}
    >
      <Handle type="target" position={Position.Left} className="bg-emerald-400" />
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1 text-[9px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
          <TestTube2 className="w-3 h-3" />
          {data.confidence}
        </span>
        <span className="text-[9px] text-slate-500 font-mono">NOT_EXECUTED</span>
      </div>
      <p className="font-semibold text-xs font-mono text-emerald-300 truncate">{data.label}()</p>
      <p className="text-[10px] text-slate-400 font-mono truncate">{data.sublabel}</p>
      <Handle type="source" position={Position.Right} className="bg-emerald-400" />
    </div>
  );
};

interface DependencyGraphProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (node: Node) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({
  nodes,
  edges,
  onNodeClick,
}) => {
  const nodeTypes = useMemo(
    () => ({
      targetNode: TargetNode,
      dependentNode: DependentNode,
      testNode: TestNode,
    }),
    []
  );

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl h-[520px] relative overflow-hidden shadow-2xl">
      <div className="absolute top-4 left-4 z-10 bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-xl border border-slate-800 text-xs text-slate-300 flex items-center space-x-3 shadow-md">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
          Target
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
          Direct
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
          Indirect
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          Tests
        </span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick && onNodeClick(node)}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#334155" gap={24} size={1} />
        <Controls className="bg-slate-900 border border-slate-800 fill-slate-300" />
        <MiniMap
          nodeColor={(node) => {
            if (node.type === 'targetNode') return '#6366f1';
            if (node.type === 'testNode') return '#10b981';
            if (node.data?.impact_type === 'direct') return '#f59e0b';
            return '#64748b';
          }}
          className="bg-slate-900 border border-slate-800 rounded-xl"
        />
      </ReactFlow>
    </div>
  );
};
