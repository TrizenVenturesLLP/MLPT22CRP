import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Flame, AlertTriangle, Shield, ChevronDown, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface DistrictData {
  District: string;
  "Crime Count": number;
  lat: number;
  lng: number;
}

interface HotspotResults {
  High: DistrictData[];
  Medium: DistrictData[];
  Low: DistrictData[];
  ranges: {
    High: string;
    Medium: string;
    Low: string;
  };
  message: string;
}

const RiskCard = ({ level, data, icon: Icon, borderClass, glowClass, dotColor, label, range }: {
  level: string; data: DistrictData[]; icon: React.ElementType; borderClass: string; glowClass: string; dotColor: string; label: string; range?: string;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -4 }}
    className={`p-6 rounded-2xl bg-white border border-slate-100 shadow-sm transition-all`}
  >
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${dotColor.replace("text-", "bg-").replace("-500", "-50")}`}>
          <Icon className={`w-4 h-4 ${dotColor}`} />
        </div>
        <h4 className="font-bold text-slate-900">{label}</h4>
      </div>
      {range && <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50 px-2 py-1 rounded-md">{range}</span>}
    </div>
    <div className="space-y-3 max-h-48 overflow-y-auto pr-2 scrollbar-thin">
      {data.map((d) => (
        <div key={d.District} className="flex items-center justify-between group">
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${dotColor.replace("text-", "bg-")}`} />
            <span className="text-sm font-medium text-slate-600">{d.District}</span>
          </div>
          <span className="text-[10px] font-bold text-slate-400 tabular-nums">{Math.round(d["Crime Count"])}</span>
        </div>
      ))}
      {data.length === 0 && (
        <div className="text-center py-6 text-xs text-slate-400 italic bg-slate-50/50 rounded-xl">
          No districts in this category
        </div>
      )}
    </div>
  </motion.div>
);

interface HotspotDetectionProps {
  onResult?: (result: HotspotResults & { state: string }) => void;
}

const HotspotDetection = ({ onResult }: HotspotDetectionProps) => {
  const [states, setStates] = useState<string[]>([]);
  const [state, setState] = useState("");
  const [startYear, setStartYear] = useState("2015");
  const [endYear, setEndYear] = useState("2024");
  
  const [loading, setLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);
  const [result, setResult] = useState<HotspotResults | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch("/api/config");
        if (!response.ok) throw new Error("Failed to fetch configuration");
        const data = await response.json();
        setStates(data.states);
      } catch (error) {
        console.error("Config fetch error:", error);
        toast.error("Failed to load application configuration.");
      } finally {
        setConfigLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleDetect = async () => {
    if (!state) {
      toast.error("Please select a State");
      return;
    }
    
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch("/api/hotspots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state,
          start_year: parseInt(startYear),
          end_year: parseInt(endYear)
        })
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Hotspot detection failed");
      
      setResult(data);
      if (onResult) {
        onResult({ ...data, state });
      }
      toast.success("Hotspot analysis complete!");
    } catch (error: any) {
      console.error("Hotspot error:", error);
      toast.error(error.message || "An error occurred during hotspot detection");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="p-8 rounded-3xl bg-white border border-slate-100 shadow-sm"
    >
      <div className="flex items-center justify-between mb-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center">
            <Flame className="w-6 h-6 text-amber-500" />
          </div>
          <h3 className="text-2xl font-bold text-slate-900">Hotspot Detection</h3>
        </div>
        {result && (
          <span className="px-4 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-bold text-blue-600 transition-all animate-in fade-in slide-in-from-right-2">
            {result.message}
          </span>
        )}
      </div>

      <div className="grid sm:grid-cols-3 gap-6 mb-8">
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-2">State</label>
          <div className="relative">
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              disabled={configLoading}
              className="w-full bg-slate-50 border border-slate-100 text-slate-900 px-4 py-3 rounded-xl appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all font-medium"
            >
              <option value="" className="bg-white text-slate-900">{configLoading ? "Loading..." : "Select State"}</option>
              {states.map((s) => (
                <option key={s} value={s} className="bg-white text-slate-900">{s}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-2">Start Year</label>
          <input 
            type="number" 
            value={startYear} 
            onChange={(e) => setStartYear(e.target.value)} 
            className="w-full bg-slate-50 border border-slate-100 text-slate-900 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
            min="2001"
            max="2035"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-2">End Year</label>
          <input 
            type="number" 
            value={endYear} 
            onChange={(e) => setEndYear(e.target.value)} 
            className="w-full bg-slate-50 border border-slate-100 text-slate-900 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
            min="2001"
            max="2035"
          />
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={handleDetect}
        disabled={loading || configLoading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-xl shadow-lg shadow-blue-500/20 transition-all mb-8 disabled:opacity-70 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Clustering Data...
          </>
        ) : (
          "Detect Hotspots"
        )}
      </motion.button>

      {result && (
        <div className="grid md:grid-cols-3 gap-6">
          <RiskCard level="high" data={result.High} range={result.ranges.High} icon={AlertTriangle} borderClass="risk-border-high" glowClass="glow-red" dotColor="text-red-500" label="High Risk" />
          <RiskCard level="medium" data={result.Medium} range={result.ranges.Medium} icon={AlertTriangle} borderClass="risk-border-medium" glowClass="glow-amber" dotColor="text-amber-500" label="Medium Risk" />
          <RiskCard level="low" data={result.Low} range={result.ranges.Low} icon={Shield} borderClass="risk-border-low" glowClass="glow-green" dotColor="text-emerald-500" label="Low Risk" />
        </div>
      )}
    </motion.div>
  );
};

export default HotspotDetection;
