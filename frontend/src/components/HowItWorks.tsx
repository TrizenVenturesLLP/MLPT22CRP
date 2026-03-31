import { motion } from "framer-motion";

const steps = [
  {
    number: "1",
    title: "Select Region",
    description: "Simply choose your state and district from the comprehensive IPC-based dataset dashboard.",
  },
  {
    number: "2",
    title: "AI Trend Analysis",
    description: "Our ensemble models (RF + K-Means) process temporal patterns and lag features instantly.",
  },
  {
    number: "3",
    title: "View & Act",
    description: "Get the future crime counts and risk levels to optimize law enforcement resource allocation.",
  },
];

const HowItWorks = () => {
  return (
    <section className="py-20 px-4 bg-slate-50/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">How It Works</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            A seamless three-step process to bridge the language gap.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-8 rounded-2xl bg-white border border-slate-100 shadow-sm"
            >
              <div className="text-blue-600 text-4xl font-bold mb-6 opacity-40">
                {step.number}
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">{step.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
