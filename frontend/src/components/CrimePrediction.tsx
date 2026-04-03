import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, ChevronDown, Loader2 } from "lucide-react";
import { toast } from "sonner";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const SelectField = ({ label, value, onChange, options, placeholder, disabled }: {
  label: string; value: string; onChange: (v: string) => void; options: string[]; placeholder: string; disabled?: boolean;
}) => (
  <div>
    <label className="block text-sm font-medium text-slate-600 mb-2">{label}</label>
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full bg-slate-50 border border-slate-100 text-slate-900 px-4 py-3 rounded-xl appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <option value="" className="bg-white text-slate-900">{placeholder}</option>
        {options.map((o) => (
          <option key={o} value={o} className="bg-white text-slate-900">{o}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
    </div>
  </div>
);

const CrimePrediction = () => {
  const [states, setStates] = useState<string[]>([]);
  const [stateDistrictMap, setStateDistrictMap] = useState<Record<string, string[]>>({});
  const [categories, setCategories] = useState<string[]>([]);
  
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");
  const [year, setYear] = useState("2024");
  const [category, setCategory] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/config`);
        if (!response.ok) throw new Error("Failed to fetch configuration");
        const data = await response.json();
        console.log("Prediction Config Loaded:", data);
        setStates(data.states || []);
        setStateDistrictMap(data.state_district_map || {});
        setCategories(data.crimes || []);
        
        if (!data.states || data.states.length === 0) {
          console.warn("No states found in API configuration");
        }
      } catch (error) {
        console.error("Config fetch error:", error);
        toast.error("Failed to load application configuration. Please ensure background server is running.");
      } finally {
        setConfigLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handlePredict = async () => {
    if (!state || !district || !category) {
      toast.error("Please select State, District, and Crime Category");
      return;
    }
    
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state,
          district,
          year: parseInt(year),
          crime: category
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || "Prediction failed");
      }
      
      setResult(data.prediction);
      toast.success("Prediction generated successfully!");
    } catch (error: any) {
      console.error("Prediction error:", error);
      toast.error(error.message || "An error occurred during prediction");
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
      <div className="flex items-center gap-4 mb-10">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center">
          <Brain className="w-6 h-6 text-blue-600" />
        </div>
        <h3 className="text-2xl font-bold text-slate-900">Crime Prediction</h3>
      </div>

      <div className="grid sm:grid-cols-2 gap-6 mb-8">
        <SelectField 
          label="State" 
          value={state} 
          onChange={(v) => { setState(v); setDistrict(""); }} 
          options={states} 
          placeholder={configLoading ? "Loading..." : "Select State"} 
          disabled={configLoading}
        />
        <SelectField 
          label="District" 
          value={district} 
          onChange={setDistrict} 
          options={state ? stateDistrictMap[state] || [] : []} 
          placeholder="Select District" 
          disabled={!state}
        />
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-2">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="w-full bg-slate-50 border border-slate-100 text-slate-900 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-medium"
            min="2013"
            max="2035"
          />
        </div>
        <SelectField 
          label="Crime Category" 
          value={category} 
          onChange={setCategory} 
          options={categories} 
          placeholder="Select Category" 
          disabled={configLoading}
        />
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={handlePredict}
        disabled={loading || configLoading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-xl shadow-lg shadow-blue-500/20 transition-all disabled:opacity-70 flex items-center justify-center gap-2 mb-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing Trends...
          </>
        ) : (
          "Predict Crime"
        )}
      </motion.button>

      {result && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-8 p-8 rounded-2xl bg-blue-50/50 border border-blue-100 text-center"
        >
          <p className="text-blue-900 font-mono text-xl font-bold">{result}</p>
          <p className="text-blue-600/60 text-xs mt-2 font-medium uppercase tracking-wider">Forecasted Instances</p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default CrimePrediction;
