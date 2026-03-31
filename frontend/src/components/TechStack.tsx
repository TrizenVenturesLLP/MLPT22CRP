import { motion } from "framer-motion";

const TechStack = () => {
  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">Technology Stack</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Built with industry-leading tools and custom AI architectures.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 p-12 bg-slate-50/50 rounded-3xl border border-slate-100">
          <div className="text-center md:text-left">
            <h3 className="text-purple-600 font-bold mb-4">AI Models</h3>
            <ul className="space-y-2 text-slate-600 text-sm">
              <li>RandomForest Regressor</li>
              <li>K-Means Clustering</li>
              <li>Recursive Analysis</li>
            </ul>
          </div>
          <div className="text-center md:text-left">
            <h3 className="text-purple-600 font-bold mb-4">Frontend</h3>
            <ul className="space-y-2 text-slate-600 text-sm">
              <li>React + Vite</li>
              <li>Tailwind CSS</li>
              <li>Framer Motion</li>
            </ul>
          </div>
          <div className="text-center md:text-left">
            <h3 className="text-purple-600 font-bold mb-4">Backend</h3>
            <ul className="space-y-2 text-slate-600 text-sm">
              <li>Python 3.8+</li>
              <li>Flask Framework</li>
              <li>Scikit-Learn</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TechStack;
