import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Send, 
  Image, 
  Calendar,
  Facebook, 
  Instagram, 
  Linkedin, 
  Twitter, 
  Music,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const PostForm = () => {
  const [content, setContent] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  const { token } = useAuth();
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const socialPlatforms = [
    {
      id: 'facebook',
      name: 'Facebook',
      icon: Facebook,
      color: 'text-blue-600',
      maxLength: 63206
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: Instagram,
      color: 'text-pink-600',
      maxLength: 2200
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: Linkedin,
      color: 'text-blue-700',
      maxLength: 3000
    },
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: Twitter,
      color: 'text-black',
      maxLength: 280
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: Music,
      color: 'text-black',
      maxLength: 2200
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
        setConnections(data.filter(conn => conn.is_active));
      }
    } catch (error) {
      console.error('Error fetching connections:', error);
    }
  };

  const handlePlatformToggle = (platformId) => {
    setSelectedPlatforms(prev => 
      prev.includes(platformId)
        ? prev.filter(id => id !== platformId)
        : [...prev, platformId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!content.trim()) {
      setError('Il contenuto del post non può essere vuoto');
      return;
    }

    if (selectedPlatforms.length === 0) {
      setError('Seleziona almeno una piattaforma');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/posts/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: content.trim(),
          platforms: selectedPlatforms,
          media_urls: []
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setContent('');
        setSelectedPlatforms([]);
      } else {
        setError(data.detail || 'Errore nella pubblicazione del post');
      }
    } catch (error) {
      setError('Errore di rete');
    } finally {
      setLoading(false);
    }
  };

  const getAvailablePlatforms = () => {
    const connectedPlatformIds = connections.map(conn => conn.platform);
    return socialPlatforms.filter(platform => 
      connectedPlatformIds.includes(platform.id)
    );
  };

  const getCharacterLimit = () => {
    if (selectedPlatforms.length === 0) return null;
    
    const limits = selectedPlatforms.map(platformId => {
      const platform = socialPlatforms.find(p => p.id === platformId);
      return platform ? platform.maxLength : Infinity;
    });
    
    return Math.min(...limits);
  };

  const characterLimit = getCharacterLimit();
  const remainingChars = characterLimit ? characterLimit - content.length : null;
  const isOverLimit = remainingChars !== null && remainingChars < 0;

  const availablePlatforms = getAvailablePlatforms();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Crea Nuovo Post
        </CardTitle>
        <CardDescription>
          Scrivi il tuo contenuto e seleziona le piattaforme dove pubblicarlo
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              <div className="font-medium mb-2">Post pubblicato con successo!</div>
              <div className="space-y-1">
                {result.results?.map((res, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    {res.status === 'success' ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertCircle className="h-3 w-3 text-red-600" />
                    )}
                    <span className="capitalize">{res.platform}</span>
                    <span>-</span>
                    <span>{res.status === 'success' ? 'Pubblicato' : 'Errore'}</span>
                  </div>
                ))}
              </div>
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Contenuto del Post
            </label>
            <Textarea
              placeholder="Scrivi qui il tuo post..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className={`min-h-32 resize-none ${isOverLimit ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {remainingChars !== null && (
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">
                  Limite caratteri per le piattaforme selezionate
                </span>
                <span className={isOverLimit ? 'text-red-500' : 'text-muted-foreground'}>
                  {remainingChars} caratteri rimanenti
                </span>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium">
              Seleziona Piattaforme
            </label>
            
            {availablePlatforms.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Nessuna piattaforma connessa. Connetti almeno una piattaforma social per pubblicare contenuti.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {availablePlatforms.map((platform) => {
                  const Icon = platform.icon;
                  const isSelected = selectedPlatforms.includes(platform.id);
                  
                  return (
                    <div
                      key={platform.id}
                      className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        isSelected 
                          ? 'border-primary bg-primary/5' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handlePlatformToggle(platform.id)}
                    >
                      <Checkbox
                        checked={isSelected}
                        onChange={() => handlePlatformToggle(platform.id)}
                        disabled={loading}
                      />
                      <Icon className={`h-5 w-5 ${platform.color}`} />
                      <div className="flex-1">
                        <span className="font-medium">{platform.name}</span>
                        <div className="text-xs text-muted-foreground">
                          Max {platform.maxLength.toLocaleString()} caratteri
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <Button
              type="submit"
              disabled={loading || availablePlatforms.length === 0 || selectedPlatforms.length === 0 || !content.trim() || isOverLimit}
              className="flex-1"
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loading ? 'Pubblicazione in corso...' : 'Pubblica Ora'}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              disabled={loading}
              className="px-6"
            >
              <Calendar className="h-4 w-4 mr-2" />
              Programma
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default PostForm;

