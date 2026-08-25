import React from 'react';
import { Check } from 'lucide-react';

interface StepperProps {
  currentStep: number;
  steps: string[];
}

export const Stepper: React.FC<StepperProps> = ({ currentStep, steps }) => {
  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between max-w-3xl mx-auto px-4">
        {steps.map((label, index) => {
          const stepNum = index + 1;
          const isCompleted = stepNum < currentStep;
          const isCurrent = stepNum === currentStep;

          return (
            <div key={label} className="flex items-center space-x-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  isCompleted
                    ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
                    : isCurrent
                    ? 'bg-sky-500 text-white ring-4 ring-sky-500/20 glow-blue'
                    : 'bg-slate-800 text-slate-500 border border-slate-700'
                }`}
              >
                {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : stepNum}
              </div>
              <span
                className={`hidden sm:inline text-xs font-medium ${
                  isCurrent ? 'text-white font-semibold' : isCompleted ? 'text-slate-300' : 'text-slate-500'
                }`}
              >
                {label}
              </span>
              {index < steps.length - 1 && (
                <div
                  className={`hidden md:block w-8 lg:w-16 h-0.5 transition-all duration-300 ${
                    stepNum < currentStep ? 'bg-emerald-500' : 'bg-slate-800'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
