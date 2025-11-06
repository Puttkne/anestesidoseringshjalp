import { useState } from "react";
import { Login } from "@/components/Login";
import { DashboardHeader } from "@/components/DashboardHeader";
import { DosingCalculator } from "@/components/DosingCalculator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill, BarChart3, Brain, PlusCircle, Settings } from "lucide-react";

const Index = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  const handleLogin = (id: string, admin: boolean) => {
    setUserId(id);
    setIsAdmin(admin);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserId("");
    setIsAdmin(false);
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userId={userId} isAdmin={isAdmin} onLogout={handleLogout} />
      
      <main className="container mx-auto">
        <Tabs defaultValue="dosing" className="w-full">
          <div className="border-b bg-card sticky top-0 z-10 shadow-sm">
            <TabsList className="w-full justify-start h-auto p-0 bg-transparent rounded-none">
              <TabsTrigger value="dosing" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">
                <Pill className="w-4 h-4 mr-2" />
                Dosering & Dosrekommendation
              </TabsTrigger>
              <TabsTrigger value="history" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">
                <BarChart3 className="w-4 h-4 mr-2" />
                Historik & Statistik
              </TabsTrigger>
              <TabsTrigger value="learning" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">
                <Brain className="w-4 h-4 mr-2" />
                Inlärning & Modeller
              </TabsTrigger>
              <TabsTrigger value="procedures" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">
                <PlusCircle className="w-4 h-4 mr-2" />
                Hantera Ingrepp
              </TabsTrigger>
              {isAdmin && (
                <TabsTrigger value="admin" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">
                  <Settings className="w-4 h-4 mr-2" />
                  Admin
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          <TabsContent value="dosing" className="mt-0">
            <DosingCalculator />
          </TabsContent>

          <TabsContent value="history" className="p-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Historik & Statistik</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Fallhistorik och statistik kommer visas här.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="learning" className="p-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Inlärning & Modeller</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Modellstatus och inlärningsdata kommer visas här.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="procedures" className="p-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Hantera Ingrepp</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Lägg till och hantera kirurgiska ingrepp här.</p>
              </CardContent>
            </Card>
          </TabsContent>

          {isAdmin && (
            <TabsContent value="admin" className="p-4">
              <Card className="shadow-card">
                <CardHeader>
                  <CardTitle>Admin Panel</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">Admin-funktioner för användarhantering och systeminställningar.</p>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
