import { motion } from "framer-motion";
import { GitBranch } from "lucide-react";

const treeData = {
  label: "India",
  children: [
    {
      label: "Maharashtra",
      risk: "high" as const,
      children: [
        { label: "Mumbai", risk: "high" as const },
        { label: "Pune", risk: "medium" as const },
        { label: "Satara", risk: "low" as const },
      ],
    },
    {
      label: "Karnataka",
      risk: "medium" as const,
      children: [
        { label: "Bengaluru", risk: "high" as const },
        { label: "Mysuru", risk: "medium" as const },
        { label: "Mangaluru", risk: "low" as const },
      ],
    },
    {
      label: "Rajasthan",
      risk: "low" as const,
      children: [
        { label: "Jaipur", risk: "medium" as const },
        { label: "Udaipur", risk: "low" as const },
      ],
    },
  ],
};

const riskColors = {
  high: "text-risk-high",
  medium: "text-risk-medium",
  low: "text-risk-low",
};

interface TreeNodeData {
  label: string;
  risk?: "high" | "medium" | "low";
  children?: TreeNodeData[];
}

const TreeNode = ({ label, risk, children, depth = 0 }: TreeNodeData & { depth?: number }) => (
  <motion.div
    initial={{ opacity: 0, x: -10 }}
    whileInView={{ opacity: 1, x: 0 }}
    viewport={{ once: true }}
    transition={{ delay: depth * 0.1 }}
    className="ml-6"
  >
    <div className="flex items-center gap-2 py-2">
      {depth > 0 && <div className="w-4 border-t border-slate-200" />}
      <span className={`text-sm font-semibold ${risk ? riskColors[risk] : "text-slate-900"}`}>
        {label}
      </span>
      {risk && (
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${riskColors[risk]} ${riskColors[risk].replace("text-", "bg-").replace("-500", "-50")}`}>
          {risk}
        </span>
      )}
    </div>
    {children && (
      <div className="border-l border-slate-200 ml-1">
        {children.map((child) => (
          <TreeNode key={child.label} {...child} depth={depth + 1} />
        ))}
      </div>
    )}
  </motion.div>
);

interface DistrictData {
  District: string;
  "Crime Count": number;
}

interface HotspotResults {
  High: DistrictData[];
  Medium: DistrictData[];
  Low: DistrictData[];
  state: string;
}

interface TreeVisualizationProps {
  results: HotspotResults | null;
}

const TreeVisualization = ({ results }: TreeVisualizationProps) => {
  const IndiaNode: TreeNodeData = {
    label: "India",
    children: results ? [
      {
        label: results.state,
        children: [
          {
            label: "High Risk Districts",
            risk: "high",
            children: results.High.map(d => ({ label: d.District, risk: "high" as const }))
          },
          {
            label: "Medium Risk Districts",
            risk: "medium",
            children: results.Medium.map(d => ({ label: d.District, risk: "medium" as const }))
          },
          {
            label: "Low Risk Districts",
            risk: "low",
            children: results.Low.map(d => ({ label: d.District, risk: "low" as const }))
          }
        ]
      }
    ] : []
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="p-8 rounded-3xl bg-white border border-slate-100 shadow-sm min-h-[400px]"
    >
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center">
          <GitBranch className="w-6 h-6 text-slate-400" />
        </div>
        <h3 className="text-2xl font-bold text-slate-900">Risk Classification Tree</h3>
      </div>
      
      {!results ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
          <GitBranch className="w-10 h-10 mb-4 opacity-20" />
          <p className="text-sm font-medium">Analyze hotspots to view classification tree</p>
        </div>
      ) : (
        <div className="bg-slate-50/50 p-6 rounded-2xl border border-slate-50 overflow-x-auto">
          <TreeNode label={IndiaNode.label} children={IndiaNode.children} />
        </div>
      )}
    </motion.div>
  );
};

export default TreeVisualization;
