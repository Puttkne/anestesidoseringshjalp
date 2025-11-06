
import type { Patient, Procedure, Adjuvant, CalculationResult, PainProfile } from '../types';
import { ADJUVANTS, REFERENCE_WEIGHT_KG, ADJUVANT_SAFETY_LIMIT_FACTOR } from '../constants';

// Helper to calculate Ideal Body Weight (Devine formula)
const calculateIBW = (heightCm: number, isMale: boolean): number => {
    const heightInches = heightCm / 2.54;
    if (heightInches <= 60) return isMale ? 50 : 45.5;
    return (isMale ? 50 : 45.5) + 2.3 * (heightInches - 60);
};

// Helper to calculate Adjusted Body Weight
const calculateABW = (actualWeight: number, ibw: number): number => {
    if (actualWeight <= ibw) return actualWeight;
    return ibw + 0.4 * (actualWeight - ibw);
};

// Helper to calculate BMI
const calculateBMI = (weightKg: number, heightCm: number): number => {
    if (heightCm === 0) return 0;
    const heightM = heightCm / 100;
    return weightKg / (heightM * heightM);
};


// Helper to calculate mismatch penalty between two pain profiles
const calculateMismatchPenalty = (procProfile: PainProfile, adjProfile: PainProfile): number => {
    const procTotal = procProfile.somatic + procProfile.visceral + procProfile.neuropathic;
    const adjTotal = adjProfile.somatic + adjProfile.visceral + adjProfile.neuropathic;
    
    if (procTotal === 0 || adjTotal === 0) return 1.0;

    const procNorm = { s: procProfile.somatic / procTotal, v: procProfile.visceral / procTotal, n: procProfile.neuropathic / procTotal };
    const adjNorm = { s: adjProfile.somatic / adjTotal, v: adjProfile.visceral / adjTotal, n: adjProfile.neuropathic / adjTotal };

    const diff = Math.abs(procNorm.s - adjNorm.s) + Math.abs(procNorm.v - adjNorm.v) + Math.abs(procNorm.n - adjNorm.n);
    return 1.0 - (diff / 2) * 0.5; // Max 50% penalty for mismatch
};


export const calculateDose = (patient: Patient, procedure: Procedure, selectedAdjuvantIds: string[]): CalculationResult => {
    // 1. Initial MME from procedure
    let mme = procedure.baseMME;
    const breakdown = {
        baseMME: procedure.baseMME,
        ageFactor: 1.0,
        asaFactor: 1.0,
        opioidFactor: 1.0,
        renalFactor: 1.0,
        adjuvantReduction: 0,
        mmeBeforeAdjuvants: 0,
        finalMME: 0
    };

    // 2. Patient factors
    if (patient.age > 65) {
        breakdown.ageFactor = Math.max(0.4, Math.exp((65 - patient.age) / 20));
        mme *= breakdown.ageFactor;
    }
    
    if (patient.asa === 3) breakdown.asaFactor = 1.1;
    if (patient.asa >= 4) breakdown.asaFactor = 1.2;
    mme *= breakdown.asaFactor;

    if (patient.isOpioidTolerant) {
        breakdown.opioidFactor = 1.8;
        mme *= breakdown.opioidFactor;
    }

    if (patient.impairedRenalFunction) {
        breakdown.renalFactor = 0.8;
        mme *= breakdown.renalFactor;
    }
    
    const mmeBeforeAdjuvants = mme;
    breakdown.mmeBeforeAdjuvants = mmeBeforeAdjuvants;

    // 3. Adjuvant Calculation
    let totalReduction = 0;
    const selectedAdjuvants = ADJUVANTS.filter(adj => selectedAdjuvantIds.includes(adj.id));

    selectedAdjuvants.forEach(adjuvant => {
        const mismatchPenalty = calculateMismatchPenalty(procedure.painProfile, adjuvant.painProfile);
        const reduction = mmeBeforeAdjuvants * adjuvant.potencyPercent * mismatchPenalty;
        totalReduction += reduction;
    });

    const maxReduction = mmeBeforeAdjuvants * (1 - ADJUVANT_SAFETY_LIMIT_FACTOR);
    totalReduction = Math.min(totalReduction, maxReduction);
    
    breakdown.adjuvantReduction = totalReduction;
    mme -= totalReduction;
    
    // 4. Weight Calculation & Adjustment
    const isMale = patient.gender === 'male';
    const ibw = calculateIBW(patient.height, isMale);
    const abw = calculateABW(patient.weight, ibw);
    const bmi = calculateBMI(patient.weight, patient.height);
    
    mme *= (abw / REFERENCE_WEIGHT_KG);

    // 5. Finalize dose
    const finalMME = Math.max(0, mme);
    breakdown.finalMME = finalMME;
    
    let ruleBasedDose = Math.round((finalMME / 0.5) * 4) / 4; // 1 MME = 0.5mg Oxycodone IV

    let mlDose = ruleBasedDose * 0.9;
    mlDose = Math.round(mlDose * 4) / 4;

    return { ruleBasedDose, mlDose, bmi, ibw, abw, breakdown };
};
