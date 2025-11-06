
import React from 'react';

interface InputSliderProps {
    label: string;
    unit: string;
    value: number;
    min: number;
    max: number;
    step: number;
    onChange: (value: number) => void;
    icon?: React.ReactNode;
}

export const InputSlider: React.FC<InputSliderProps> = ({ label, unit, value, min, max, step, onChange, icon }) => {
    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(Number(e.target.value));
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const numValue = Number(e.target.value);
        if (!isNaN(numValue) && numValue >= min && numValue <= max) {
            onChange(numValue);
        }
    };
    
    return (
        <div className="space-y-2">
            <label className="flex items-center text-sm font-medium text-slate-300">
                {icon && <span className="mr-2">{icon}</span>}
                {label}
            </label>
            <div className="flex items-center space-x-4">
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={handleSliderChange}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
                <div className="flex items-center bg-slate-900 border border-slate-600 rounded-md">
                    <input
                        type="number"
                        value={value}
                        onChange={handleInputChange}
                        className="w-20 bg-transparent text-center font-semibold text-white focus:outline-none"
                        min={min}
                        max={max}
                        step={step}
                    />
                    <span className="pr-3 text-slate-400 text-sm">{unit}</span>
                </div>
            </div>
        </div>
    );
};
