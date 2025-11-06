
import React from 'react';
import { Card } from './Card';
import { PROCEDURES, ADJUVANTS } from '../constants';
import type { Procedure, Adjuvant } from '../types';

interface ProcedureInputsProps {
    selectedProcedureId: string;
    setSelectedProcedureId: (id: string) => void;
    selectedAdjuvantIds: string[];
    setSelectedAdjuvantIds: (ids: string[]) => void;
}

export const ProcedureInputs: React.FC<ProcedureInputsProps> = ({
    selectedProcedureId,
    setSelectedProcedureId,
    selectedAdjuvantIds,
    setSelectedAdjuvantIds
}) => {
    
    const handleAdjuvantChange = (adjuvantId: string) => {
        const newSelection = selectedAdjuvantIds.includes(adjuvantId)
            ? selectedAdjuvantIds.filter(id => id !== adjuvantId)
            : [...selectedAdjuvantIds, adjuvantId];
        setSelectedAdjuvantIds(newSelection);
    };

    return (
        <Card title="Ingrepp & Läkemedel">
            <div className="space-y-6">
                <div>
                    <label htmlFor="procedure" className="block text-sm font-medium text-slate-300 mb-2">Kirurgiskt Ingrepp</label>
                    <select
                        id="procedure"
                        value={selectedProcedureId}
                        onChange={(e) => setSelectedProcedureId(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                    >
                        {PROCEDURES.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                </div>
                <div>
                    <h3 className="text-sm font-medium text-slate-300 mb-2">Valda Adjuvanter</h3>
                    <div className="grid grid-cols-2 gap-3">
                        {ADJUVANTS.map(adjuvant => (
                            <label key={adjuvant.id} className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors duration-200 ${selectedAdjuvantIds.includes(adjuvant.id) ? 'bg-cyan-500/20 border-cyan-500' : 'bg-slate-700/50 border-slate-600'} border`}>
                                <input
                                    type="checkbox"
                                    checked={selectedAdjuvantIds.includes(adjuvant.id)}
                                    onChange={() => handleAdjuvantChange(adjuvant.id)}
                                    className="h-4 w-4 rounded border-slate-500 text-cyan-600 focus:ring-cyan-500 bg-slate-800"
                                />
                                <span className="text-sm font-medium text-slate-200">{adjuvant.name}</span>
                            </label>
                        ))}
                    </div>
                </div>
            </div>
        </Card>
    );
};
