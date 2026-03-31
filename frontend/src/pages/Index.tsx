import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import HowItWorks from "@/components/HowItWorks";
import TechStack from "@/components/TechStack";
import Footer from "@/components/Footer";
import { motion } from "framer-motion";
import { Brain, Flame } from "lucide-react";

const navCards = [
  {
    icon: Brain,
    title: "Crime Prediction",
    description: "Predict future crime trends at district level using AI models",
    path: "/crime-prediction",
    colorClass: "text-blue-600",
    glowClass: "hover:shadow-blue-500/10",
  },
  {
    icon: Flame,
    title: "Hotspot Detection",
    description: "Identify high-risk zones and classify districts by threat level",
    path: "/hotspot-detection",
    colorClass: "text-purple-600",
    glowClass: "hover:shadow-purple-500/10",
  },
];

import Navbar from "@/components/Navbar";

const Index = () => {
  const navigate = useNavigate();
  const toolsRef = useRef<HTMLDivElement>(null);

  const scrollToTools = () => {
    toolsRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-white">
      <Navbar onScrollToTools={scrollToTools} />

      <HeroSection onGetStarted={scrollToTools} />
      <div id="features"><FeaturesSection /></div>
      <div id="how-it-works"><HowItWorks /></div>
      
      {/* Analytics Tools Selection */}
      <section ref={toolsRef} className="py-24 px-4 bg-slate-50/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Analytics Tools</h2>
            <p className="text-slate-600 max-w-lg mx-auto">
              Select a module to get started with crime intelligence analysis
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-8">
            {navCards.map((card, i) => (
              <motion.button
                key={card.title}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -8 }}
                onClick={() => navigate(card.path)}
                className={`p-8 rounded-3xl bg-white border border-slate-100 text-left shadow-sm hover:shadow-xl transition-all group ${card.glowClass}`}
              >
                <div className={`w-14 h-14 rounded-2xl bg-slate-50 flex items-center justify-center mb-6 group-hover:bg-blue-50 transition-colors`}>
                  <card.icon className={`w-7 h-7 ${card.colorClass}`} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-3">{card.title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed mb-6">{card.description}</p>
                <div className={`text-sm font-bold ${card.colorClass} flex items-center gap-2`}>
                  Open Module
                  <div className="w-5 h-5 rounded-full bg-current opacity-10 group-hover:opacity-20 transition-opacity" />
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      <div id="tech-stack"><TechStack /></div>
      <Footer />
    </div>
  );
};

export default Index;
