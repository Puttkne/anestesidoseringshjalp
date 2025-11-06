
export interface Patient {
    age: number;
    gender: 'male' | 'female';
    weight: number;
    height: number;
    asa: number;
    isOpioidTolerant: boolean;
    lowPainThreshold: boolean;
    impairedRenalFunction: boolean; // GFR < 35
}

export interface TemporalDose {
    id: string;
    drug: string;
    dose: number;
    time: string; // e.g., "-00:30"
}

export interface PainProfile {
    somatic: number;
    visceral: number;
    neuropathic: number;
}

export interface Procedure {
    id: string;
    name: string;
    specialty: string;
    baseMME: number;
    painProfile: PainProfile;
}

export interface Adjuvant {
    id: string;
    name: string;
    type: 'checkbox' | 'number' | 'select';
    options?: string[];
    unit?: string;
    potencyPercent: number;
    painProfile: PainProfile;
}

export interface CalculationResult {
    ruleBasedDose: number;
    mlDose: number;
    bmi: number;
    ibw: number;
    abw: number;
    breakdown: {
        baseMME: number;
        ageFactor: number;
        asaFactor: number;
        opioidFactor: number;
        renalFactor: number;
        adjuvantReduction: number;
        mmeBeforeAdjuvants: number;
        finalMME: number;
    };
}

export interface Outcome {
    givenDose: number;
    vas: number;
    uvaDose: number;
    wakefulness: number;
    sideEffects: boolean;
}


export interface HistoricalCase {
    id: string;
    date: string;
    procedure: string;
    givenDose: number;
    vas: number;
    user: string;
    isComplete: boolean;
}
