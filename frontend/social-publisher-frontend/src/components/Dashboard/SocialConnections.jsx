import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Facebook, 
  Instagram, 
  Linkedin, 
  Twitter, 
  Music,
  CheckCircle, 
  XCircle,
  ExternalLink,
  Unlink
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const SocialConnections = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const socialPlatforms = [
    {
      id: 'facebook',
      name: 'Facebook',
      icon: Facebook,
      color: 'bg-blue-600',
      description: 'Pubblica su pagine Facebook'
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: Instagram,
      color: 'bg-gradient-to-r from-purple-500 to-pink-500',
      description: 'Condividi foto e video su Instagram'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: Linkedin,
      color: 'bg-blue-700',
      description: 'Condividi contenuti professionali'
    },
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: Twitter,
      color: 'bg-black',
      description: 'Pubblica tweet e thread'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: Music,
      color: 'bg-black',
      description: 'Carica video su TikTok'
    }
  ];

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/social/tokens`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data);
      } else {
        setError('Errore nel caricamento delle connessioni');
      }
    } catch (error) {
      setError('Errore di rete');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platform) => {
    try {
      const response = await fetch(`${API_BASE_URL}/social/connect/${platform}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Apri la finestra di autorizzazione OAuth
        window.open(data.auth_url, '_blank', 'width=600,height=600');
        
        // Ascolta per il completamento dell'autorizzazione
        const checkConnection = setInterval(() => {
          fetchConnections();
        }, 2000);

        // Ferma il controllo dopo 2 minuti
        setTimeout(() => {
          clearInterval(checkConnection);
        }, 120000);
      } else {
        setError(`Errore nella connessione a ${platform}`);
      }
    } catch (error) {
      setError('Errore di rete');
    }
  };

  const handleDisconnect = async (platform) => {
    if (!confirm(`Sei sicuro di voler disconnettere ${platform}?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/social/disconnect/${platform}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        fetchConnections();
      } else {
        setError(`Errore nella disconnessione da ${platform}`);
      }
    } catch (error) {
      setError('Errore di rete');
    }
  };

  const isConnected = (platformId) => {
    return connections.some(conn => conn.platform === platformId && conn.is_active);
  };

  const getConnection = (platformId) => {
    return connections.find(conn => conn.platform === platformId && conn.is_active);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Connessioni Social</CardTitle>
          <CardDescription>Caricamento...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ExternalLink className="h-5 w-5" />
          Connessioni Social
        </CardTitle>
        <CardDescription>
          Connetti i tuoi account social per iniziare a pubblicare contenuti
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {socialPlatforms.map((platform) => {
            const connected = isConnected(platform.id);
            const connection = getConnection(platform.id);
            const Icon = platform.icon;

            return (
              <div
                key={platform.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${platform.color} text-white`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{platform.name}</h3>
                      {connected ? (
                        <Badge variant="success" className="bg-green-100 text-green-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Connesso
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <XCircle className="h-3 w-3 mr-1" />
                          Non connesso
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {platform.description}
                    </p>
                    {connected && connection?.platform_username && (
                      <p className="text-xs text-muted-foreground">
                        Account: {connection.platform_username}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {connected ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnect(platform.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Unlink className="h-4 w-4 mr-1" />
                      Disconnetti
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => handleConnect(platform.id)}
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Connetti
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">💡 Suggerimento</h4>
          <p className="text-sm text-blue-800">
            Connetti almeno una piattaforma social per iniziare a pubblicare i tuoi contenuti. 
            Puoi sempre aggiungere o rimuovere connessioni in seguito.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default SocialConnections;

