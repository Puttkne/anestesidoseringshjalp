
import React from 'react';
import type { Outcome } from '../types';
import { Card } from './Card';
import { InputSlider } from './InputSlider';

interface OutcomeLoggerProps {
    outcome: Outcome;
    setOutcome: (outcome: Outcome) => void;
    recommendedDose: number;
}

export const OutcomeLogger: React.FC<OutcomeLoggerProps> = ({ outcome, setOutcome, recommendedDose }) => {

    const handleChange = <K extends keyof Outcome,>(key: K, value: Outcome[K]) => {
        setOutcome({ ...outcome, [key]: value });
    };

    const handleSave = () => {
        // In a real application, this would send data to the backend.
        alert(`Sparat utfall:\nRek. dos: ${recommendedDose} mg\nGivet: ${outcome.givenDose} mg\nVAS: ${outcome.vas}\nRescue: ${outcome.uvaDose} mg\nVakenhet: ${outcome.wakefulness}\nBiverkningar: ${outcome.sideEffects ? 'Ja' : 'Nej'}`);
    };

    return (
        <Card title="Logga Utfall">
            <div className="space-y-6">
                <InputSlider
                    label="Administrerad dos (Oxykodon)"
                    unit="mg"
                    value={outcome.givenDose}
                    onChange={(v) => handleChange('givenDose', v)}
                    min={0}
                    max={50}
                    step={0.25}
                />
                 <InputSlider
                    label="Högsta VAS (post-op)"
                    unit=""
                    value={outcome.vas}
                    onChange={(v) => handleChange('vas', v)}
                    min={0}
                    max={10}
                    step={1}
                />
                 <InputSlider
                    label="Extra rescue-dos (UVA)"
                    unit="mg"
                    value={outcome.uvaDose}
                    onChange={(v) => handleChange('uvaDose', v)}
                    min={0}
                    max={20}
                    step={1}
                />
                 <InputSlider
                    label="Patientens vakenhetsgrad (RASS)"
                    unit=""
                    value={outcome.wakefulness}
                    onChange={(v) => handleChange('wakefulness', v)}
                    min={-5}
                    max={4}
                    step={1}
                />
                <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
                    <span className="font-medium text-slate-300">Biverkningar (t.ex. PONV, andningsdep.)</span>
                     <label htmlFor="side-effect-toggle" className="inline-flex relative items-center cursor-pointer">
                        <input type="checkbox" id="side-effect-toggle" className="sr-only peer"
                            checked={outcome.sideEffects}
                            onChange={(e) => handleChange('sideEffects', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-focus:ring-4 peer-focus:ring-cyan-800 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                    </label>
                </div>
                <button
                    onClick={handleSave}
                    className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200"
                >
                    ✅ Uppdatera Fall (komplett)
                </button>
            </div>
        </Card>
    );
};
