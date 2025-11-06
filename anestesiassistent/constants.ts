
import type { Procedure, Adjuvant, PainProfile } from './types';

export const ASA_CLASSES: { value: number; label: string }[] = [
    { value: 1, label: 'ASA 1: Normal frisk patient' },
    { value: 2, label: 'ASA 2: Mild systemsjukdom' },
    { value: 3, label: 'ASA 3: Allvarlig systemsjukdom' },
    { value: 4, label: 'ASA 4: Livshotande systemsjukdom' },
    { value: 5, label: 'ASA 5: Moribund patient' },
];

export const SPECIALTIES: string[] = ["Ortopedi", "Kirurgi", "Urologi", "Gynekologi"];

export const PROCEDURES: Procedure[] = [
    { id: 'knee_replacement', name: 'Knäprotes', specialty: 'Ortopedi', baseMME: 25, painProfile: { somatic: 9, visceral: 2, neuropathic: 4 } },
    { id: 'hip_replacement', name: 'Höftprotes', specialty: 'Ortopedi', baseMME: 22, painProfile: { somatic: 8, visceral: 3, neuropathic: 3 } },
    { id: 'lap_chole', name: 'Laparoskopisk kolecystektomi', specialty: 'Kirurgi', baseMME: 18, painProfile: { somatic: 4, visceral: 8, neuropathic: 2 } },
    { id: 'appendectomy', name: 'Appendektomi', specialty: 'Kirurgi', baseMME: 15, painProfile: { somatic: 5, visceral: 7, neuropathic: 1 } },
    { id: 'lumbar_fusion', name: 'Ländryggsfusion', specialty: 'Ortopedi', baseMME: 30, painProfile: { somatic: 7, visceral: 2, neuropathic: 9 } },
    { id: 'prostatectomy', name: 'Prostatektomi', specialty: 'Urologi', baseMME: 20, painProfile: { somatic: 3, visceral: 8, neuropathic: 6 } },
];

const defaultPainProfile: PainProfile = { somatic: 5, visceral: 5, neuropathic: 5 };

export const ADJUVANTS: Adjuvant[] = [
    { id: 'nsaid', name: 'NSAID', type: 'select', options: ['Ibuprofen', 'Ketorolac', 'Celecoxib'], potencyPercent: 0.15, painProfile: { somatic: 8, visceral: 5, neuropathic: 2 } },
    { id: 'paracetamol', name: 'Paracetamol', type: 'checkbox', potencyPercent: 0.10, painProfile: { somatic: 6, visceral: 6, neuropathic: 3 } },
    { id: 'catapressan', name: 'Catapressan', type: 'number', unit: 'µg', potencyPercent: 0.20, painProfile: { somatic: 4, visceral: 7, neuropathic: 6 } },
    { id: 'ketamine', name: 'Ketamin', type: 'number', unit: 'mg', potencyPercent: 0.30, painProfile: { somatic: 7, visceral: 4, neuropathic: 9 } },
    { id: 'lidokain', name: 'Lidokain', type: 'number', unit: 'mg', potencyPercent: 0.18, painProfile: { somatic: 6, visceral: 2, neuropathic: 7 } },
    { id: 'betapred', name: 'Betapred', type: 'checkbox', potencyPercent: 0.05, painProfile: defaultPainProfile },
    { id: 'droperidol', name: 'Droperidol', type: 'checkbox', potencyPercent: 0.0, painProfile: defaultPainProfile },
    { id: 'infiltration', name: 'Infiltration', type: 'checkbox', potencyPercent: 0.25, painProfile: { somatic: 9, visceral: 2, neuropathic: 4 } },
    { id: 'sevoflurane', name: 'Sevofluran > 2 MAC-timmar', type: 'checkbox', potencyPercent: 0.10, painProfile: defaultPainProfile },
];


export const REFERENCE_WEIGHT_KG = 70;
export const ADJUVANT_SAFETY_LIMIT_FACTOR = 0.3;
