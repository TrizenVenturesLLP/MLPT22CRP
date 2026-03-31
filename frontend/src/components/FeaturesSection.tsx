import { motion } from "framer-motion";
import { Search, Globe, Volume2 } from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Smart Forecasting",
    description: "Powered by RandomForest, our AI converts historical data into clear, predictive crime trends for any district.",
    iconBg: "bg-amber-50",
    iconColor: "text-amber-500",
  },
  {
    icon: Globe,
    title: "Regional Hotspots",
    description: "Identify threat levels across India using hybrid K-Means clustering and regional severity thresholds.",
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
  },
  {
    icon: Volume2,
    title: "Live Analytics",
    description: "Get real-time feedback on safety metrics and trend classifications exactly when they are needed.",
    iconBg: "bg-slate-50",
    iconColor: "text-slate-400",
  },
];

const FeaturesSection = () => {
  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">Key Features</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Advanced capabilities for accurate and rapid communication.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -5 }}
              className="p-8 rounded-2xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all"
            >
              <div className={`w-12 h-12 rounded-xl ${feature.iconBg} flex items-center justify-center mb-6`}>
                <feature.icon className={`w-6 h-6 ${feature.iconColor}`} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
