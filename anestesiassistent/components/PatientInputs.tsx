
import React from 'react';
import type { Patient } from '../types';
import { Card } from './Card';
import { InputSlider } from './InputSlider';
import { ASA_CLASSES } from '../constants';

interface PatientInputsProps {
    patient: Patient;
    setPatient: (patient: Patient) => void;
}

const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
    </svg>
);

const RulerIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm5 2a1 1 0 00-1 1v8a1 1 0 102 0V6a1 1 0 00-1-1zm5-2a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
);


export const PatientInputs: React.FC<PatientInputsProps> = ({ patient, setPatient }) => {

    const handleChange = <K extends keyof Patient,>(key: K, value: Patient[K]) => {
        setPatient({ ...patient, [key]: value });
    };

    return (
        <Card title="Patientinformation">
            <div className="space-y-6">
                <InputSlider
                    label="Ålder"
                    unit="år"
                    value={patient.age}
                    onChange={(v) => handleChange('age', v)}
                    min={0}
                    max={120}
                    step={1}
                />
                <InputSlider
                    label="Vikt"
                    unit="kg"
                    value={patient.weight}
                    onChange={(v) => handleChange('weight', v)}
                    min={10}
                    max={200}
                    step={1}
                />
                <InputSlider
                    label="Längd"
                    unit="cm"
                    value={patient.height}
                    onChange={(v) => handleChange('height', v)}
                    min={100}
                    max={220}
                    step={1}
                />
                <div>
                    <label htmlFor="asa" className="block text-sm font-medium text-slate-300 mb-2">ASA-klass</label>
                    <select
                        id="asa"
                        value={patient.asa}
                        onChange={(e) => handleChange('asa', Number(e.target.value))}
                        className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                    >
                        {ASA_CLASSES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                </div>
                <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
                    <span className="font-medium text-slate-300">Opioidtolerant</span>
                    <label htmlFor="opioid-toggle" className="inline-flex relative items-center cursor-pointer">
                        <input type="checkbox" id="opioid-toggle" className="sr-only peer"
                            checked={patient.isOpioidTolerant}
                            onChange={(e) => handleChange('isOpioidTolerant', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-focus:ring-4 peer-focus:ring-cyan-800 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                    </label>
                </div>
            </div>
        </Card>
    );
};
