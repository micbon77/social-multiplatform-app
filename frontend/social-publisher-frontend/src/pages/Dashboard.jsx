import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, User, Settings } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SocialConnections from '../components/Dashboard/SocialConnections';
import PostForm from '../components/Dashboard/PostForm';

const Dashboard = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Social Multiplatform Publisher
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <User className="h-4 w-4" />
                <span>Ciao, {user?.username}</span>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Esci</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Post Form */}
          <div className="lg:col-span-2 space-y-6">
            <PostForm />
            
            {/* Recent Posts Card - Placeholder */}
            <Card>
              <CardHeader>
                <CardTitle>Post Recenti</CardTitle>
                <CardDescription>
                  I tuoi ultimi post pubblicati
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  <p>Nessun post pubblicato ancora.</p>
                  <p className="text-sm mt-2">I tuoi post appariranno qui dopo la pubblicazione.</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Social Connections & Stats */}
          <div className="space-y-6">
            <SocialConnections />
            
            {/* Quick Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle>Statistiche Rapide</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Post pubblicati oggi</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Post questa settimana</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Piattaforme connesse</span>
                    <span className="font-medium">-</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tips Card */}
            <Card>
              <CardHeader>
                <CardTitle>💡 Suggerimenti</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="font-medium text-blue-900">Ottimizza i tuoi contenuti</p>
                    <p className="text-blue-800 mt-1">
                      Adatta il tuo messaggio per ogni piattaforma considerando i limiti di caratteri.
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="font-medium text-green-900">Pianifica in anticipo</p>
                    <p className="text-green-800 mt-1">
                      Usa la funzione di programmazione per pubblicare nei momenti migliori.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

