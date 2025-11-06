
import React from 'react';
import { User, LogOut, FileText, Clock, Book, Syringe, Plus, Minus } from 'lucide-react';

interface Props {
  username: string;
  isAdmin: boolean;
  onLogout: () => void;
}

export const Dashboard: React.FC<Props> = ({ username, isAdmin, onLogout }) => {
  const [formData, setFormData] = React.useState({
    age: 50,
    weight: 70,
    height: 175,
    gender: '',
    asaClass: '',
    surgeryType: 'Elektivt',
    specialty: '',
    procedure: '',
    operationTimeHours: 0,
    operationTimeMinutes: 0,
    paracetamol: false,
    nsaid: false,
    betapred: false,
    klonidin: false,
    esketamin: false,
    lidokain: false,
    vas: 0,
    awakeness: '',
    breathingDepression: false,
    naloxon: false,
    postOpOpioid: false,
    updateTime: 4,
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="bg-white border-b px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <div className="bg-primary p-2 rounded-full">
              <Syringe className="text-white h-6 w-6" />
            </div>
            <h1 className="text-xl font-bold text-foreground">Anestesi-assistent</h1>
            <span className="text-sm text-muted-foreground">v1.0 Beta</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Inloggad: <span className="font-semibold text-foreground">{username}</span></span>
            <button onClick={onLogout} className="flex items-center text-sm text-muted-foreground hover:text-foreground">
              <LogOut className="mr-2 h-4 w-4" />
              Logga ut
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 p-8">
        <div className="flex gap-8 mb-8">
            <button className="pb-2 border-b-2 border-primary text-primary font-semibold flex items-center"><FileText className="mr-2 h-4 w-4"/>Dosering</button>
            <button className="pb-2 border-b-2 border-transparent text-muted-foreground hover:text-foreground flex items-center"><Clock className="mr-2 h-4 w-4"/>Historik</button>
            <button className="pb-2 border-b-2 border-transparent text-muted-foreground hover:text-foreground flex items-center"><Book className="mr-2 h-4 w-4"/>Utbildning</button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-8">
            {/* Patient Card */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4 flex items-center"><User className="mr-2 h-5 w-5 text-primary"/>Patient</h2>
              <div className="space-y-4">
                {renderNumberInput("Ålder", "age", "år", 0, 120, formData.age)}
                {renderNumberInput("Vikt (kg)", "weight", "kg", 0, 200, formData.weight)}
                {renderNumberInput("Längd (cm)", "height", "cm", 0, 250, formData.height)}
                <div className="grid grid-cols-2 gap-4">
                  {renderSelect("Kön", "gender", "Välj kön", ["Man", "Kvinna"])}
                  {renderSelect("ASA-klass", "asaClass", "Välj ASA", ["1", "2", "3", "4"])}
                </div>
              </div>
            </div>

            {/* Givna Opioider Card */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4 flex items-center"><Syringe className="mr-2 h-5 w-5 text-primary"/>Givna Opioider</h2>
              {/* Add opioid inputs here */}
            </div>
          </div>

          <div className="space-y-8">
            {/* Ingrepp Card */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4 flex items-center"><FileText className="mr-2 h-5 w-5 text-primary"/>Ingrepp</h2>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <button className={`flex-1 py-2 rounded-md ${formData.surgeryType === 'Elektivt' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-800'}`} onClick={() => handleInputChange('surgeryType', 'Elektivt')}>Elektivt</button>
                  <button className={`flex-1 py-2 rounded-md ${formData.surgeryType === 'Akut' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-800'}`} onClick={() => handleInputChange('surgeryType', 'Akut')}>Akut</button>
                </div>
                {renderSelect("Specialitet", "specialty", "Välj specialitet", ["Ortopedi", "Allmänkirurgi", "Gynekologi", "Urologi"])}
                {renderSelect("Typ av ingrepp", "procedure", "Välj ingrepp", ["Knäplastik", "Höftplastik", "Artroskopi"])}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Operationstid</label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1">{renderTimeInput("Timmar", "operationTimeHours")}</div>
                    <div className="flex-1">{renderTimeInput("Minuter", "operationTimeMinutes")}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Adjuvanter Card */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4 flex items-center"><Plus className="mr-2 h-5 w-5 text-primary"/>Adjuvanter</h2>
              <div className="grid grid-cols-2 gap-4">
                {renderCheckbox("Paracetamol", "paracetamol")}
                {renderCheckbox("Klonidin", "klonidin")}
                {renderCheckbox("NSAID", "nsaid")}
                {renderCheckbox("Esketamin", "esketamin")}
                {renderCheckbox("Betapred", "betapred")}
                {renderCheckbox("Lidokain", "lidokain")}
              </div>
            </div>
          </div>
        </div>

        {/* Doseringsrekommendation Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mt-8">
          <h2 className="text-lg font-semibold mb-4 flex items-center"><FileText className="mr-2 h-5 w-5 text-primary"/>Doseringsrekommendation</h2>
          <button className="w-full bg-primary text-white py-3 rounded-md">Beräkna Rekommendation</button>
          <div className="text-center text-muted-foreground mt-4">
            Fyll i patientdata och klicka på "Beräkna Rekommendation" för att få dosförslag
          </div>
        </div>

        {/* Logga Utfall Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mt-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center"><Clock className="mr-2 h-5 w-5 text-primary"/>Logga Utfall</h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">ID: 8:2</span>
              <button className="flex items-center text-sm text-muted-foreground hover:text-foreground border rounded-md px-3 py-1.5"><FileText className="mr-2 h-4 w-4"/>Spara temporärt</button>
            </div>
          </div>
          <div className="space-y-4">
            {renderNumberInput("VAS-smärta postoperativt (0-10)", "vas", "", 0, 10, formData.vas)}
            <div className="grid grid-cols-2 gap-4">
              {renderSelect("Vakenhetsgrad", "awakeness", "Välj vakenhetsgrad", ["Vaken", "Trött", "Sovande"])}
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="breathingDepression" checked={formData.breathingDepression} onChange={(e) => handleInputChange('breathingDepression', e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"/>
                <label htmlFor="breathingDepression" className="text-sm font-medium">Andningsdeprimering</label>
              </div>
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="naloxon" checked={formData.naloxon} onChange={(e) => handleInputChange('naloxon', e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"/>
                <label htmlFor="naloxon" className="text-sm font-medium">Naloxon</label>
              </div>
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="postOpOpioid" checked={formData.postOpOpioid} onChange={(e) => handleInputChange('postOpOpioid', e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"/>
                <label htmlFor="postOpOpioid" className="text-sm font-medium">Postoperativ opioid</label>
              </div>
            </div>
            {renderNumberInput("Tid för uppdatering efter opslut: 4 h", "updateTime", "h", 0, 24, formData.updateTime)}
          </div>
        </div>
      </main>
    </div>
  );

  function renderNumberInput(label: string, field: keyof typeof formData, unit: string, min: number, max: number, value: number) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">{label}</label>
        <div className="flex items-center gap-2">
            <input
              type="number"
              value={value}
              onChange={(e) => handleInputChange(field, e.target.value)}
              className="w-20 py-2 text-center border rounded-md"
            />
            <span className="text-muted-foreground text-sm">{unit}</span>
          <div className="flex-1 h-2 bg-gray-200 rounded-full"> <div className="h-2 bg-primary rounded-full" style={{width: `${(value/max)*100}%`}}></div></div>
          <button className="border rounded-md p-2" onClick={() => handleInputChange(field, Math.min(max, value + 1))}><Plus className="h-4 w-4" /></button>
        </div>
      </div>
    );
  }

  function renderSelect(label: string, field: keyof typeof formData, placeholder: string, options: string[]) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">{label}</label>
        <select  value={formData[field]} onChange={(e) => handleInputChange(field, e.target.value)} className="w-full border rounded-md p-2">
            <option value="" disabled>{placeholder}</option>
            {options.map(option => <option key={option} value={option}>{option}</option>)}
        </select>
      </div>
    );
  }

  function renderTimeInput(label: string, field: keyof typeof formData) {
    return (
      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">{label}</label>
        <div className="flex items-center border rounded-md">
          <button className="p-2 border-r"><Minus className="h-4 w-4"/></button>
          <input
            type="number"
            value={formData[field]}
            onChange={(e) => handleInputChange(field, e.target.value)}
            className="w-full py-1 text-center bg-transparent border-none focus:ring-0"
          />
          <button className="p-2 border-l"><Plus className="h-4 w-4"/></button>
        </div>
      </div>
    );
  }

  function renderCheckbox(label: string, field: keyof typeof formData) {
    return (
      <div className="flex items-center space-x-2">
        <input type="checkbox" id={field} checked={formData[field]} onChange={(e) => handleInputChange(field, e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"/>
        <label htmlFor={field} className="text-sm font-medium">{label}</label>
      </div>
    );
  }
};
