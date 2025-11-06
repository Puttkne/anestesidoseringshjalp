
import React, { useState } from 'react';
import type { CalculationResult } from '../types';
import { Card } from './Card';

interface DoseResultsProps {
    result: CalculationResult | null;
    isLoading: boolean;
}

const InfoIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
);

const BreakdownItem: React.FC<{ label: string; value: string | number; unit?: string;}> = ({ label, value, unit }) => (
    <div className="flex justify-between text-sm py-1.5 border-b border-slate-700/50">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-slate-200">{value} {unit}</span>
    </div>
);


export const DoseResults: React.FC<DoseResultsProps> = ({ result, isLoading }) => {
    const [showBreakdown, setShowBreakdown] = useState(false);

    const renderContent = () => {
        if (isLoading) {
            return <div className="text-center text-slate-400">Beräknar...</div>;
        }
        if (!result) {
            return <div className="text-center text-slate-400">Ange patientdata för att se rekommendation.</div>;
        }
        return (
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
                    <div className="p-4 bg-slate-700/50 rounded-lg">
                        <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">Regelbaserad dos</h3>
                        <p className="text-4xl font-bold text-white my-2">{result.ruleBasedDose.toFixed(2)} <span className="text-2xl font-normal text-slate-300">mg</span></p>
                        <p className="text-xs text-slate-400">Oxykodon</p>
                    </div>
                    <div className="p-4 bg-slate-700/50 rounded-lg border border-dashed border-slate-600">
                        <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider">ML Modell (2nd Opinion)</h3>
                         <p className="text-4xl font-bold text-white my-2">{result.mlDose.toFixed(2)} <span className="text-2xl font-normal text-slate-300">mg</span></p>
                         <p className="text-xs text-slate-400">Oxykodon</p>
                    </div>
                </div>

                 <div className="grid grid-cols-3 gap-2 text-center text-sm p-2 bg-slate-900/40 rounded-md">
                    <div>
                        <span className="text-slate-400">BMI</span>
                        <p className="font-mono text-white">{result.bmi.toFixed(1)}</p>
                    </div>
                    <div>
                        <span className="text-slate-400">IBW</span>
                        <p className="font-mono text-white">{result.ibw.toFixed(1)} <span className="text-xs text-slate-500">kg</span></p>
                    </div>
                    <div>
                        <span className="text-slate-400">ABW</span>
                        <p className="font-mono text-white">{result.abw.toFixed(1)} <span className="text-xs text-slate-500">kg</span></p>
                    </div>
                </div>

                <div>
                    <button
                        onClick={() => setShowBreakdown(!showBreakdown)}
                        className="text-sm text-cyan-400 hover:text-cyan-300"
                    >
                        {showBreakdown ? 'Dölj' : 'Visa'} beräkningsdetaljer
                    </button>
                    {showBreakdown && result.breakdown && (
                        <div className="mt-4 p-4 bg-slate-900/50 rounded-lg space-y-1">
                            <BreakdownItem label="Bas-MME (ingrepp)" value={result.breakdown.baseMME.toFixed(2)} unit="mg" />
                            <BreakdownItem label="Åldersfaktor" value={result.breakdown.ageFactor.toFixed(2)} />
                            <BreakdownItem label="ASA-faktor" value={result.breakdown.asaFactor.toFixed(2)} />
                            <BreakdownItem label="Opioidtolerant-faktor" value={result.breakdown.opioidFactor.toFixed(2)} />
                             <BreakdownItem label="Njurfunktionsfaktor" value={result.breakdown.renalFactor.toFixed(2)} />
                            <BreakdownItem label="MME före adjuvanter" value={result.breakdown.mmeBeforeAdjuvants.toFixed(2)} unit="mg" />
                            <BreakdownItem label="Adjuvant-reduktion" value={(-result.breakdown.adjuvantReduction).toFixed(2)} unit="mg" />
                             <div className="flex justify-between text-sm py-2 font-bold border-t-2 border-slate-600 mt-2">
                                <span className="text-slate-300">Slutgiltig MME</span>
                                <span className="font-mono text-cyan-400">{result.breakdown.finalMME.toFixed(2)} mg</span>
                            </div>
                        </div>
                    )}
                </div>
                <div className="text-xs text-slate-500 p-3 bg-slate-800/50 rounded-md">
                    <InfoIcon />
                    Detta är ett beslutsstöd. Dosen måste alltid bedömas och justeras av ansvarig kliniker baserat på patientens individuella behov och kliniska bild.
                </div>
            </div>
        );
    };

    return (
        <Card title="Dosrekommendation">
            {renderContent()}
        </Card>
    );
};
