// src/pages/auth/TwoFactorStep.tsx
import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '@/store/auth.store';
import { toast } from 'sonner';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ShieldCheck } from 'lucide-react';

interface TwoFactorStepProps {
  onSuccess: () => void;
}

export function TwoFactorStep({ onSuccess }: TwoFactorStepProps) {
  const { login2FA, cancelTwoFactor, isLoading } = useAuthStore();
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState<string | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string) => {
    // Только цифры
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError(null);

    // Автофокус на следующее поле
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Автоматическая отправка при заполнении всех 6 цифр
    if (value && index === 5) {
      const fullCode = newCode.join('');
      if (fullCode.length === 6) {
        handleSubmit(fullCode);
      }
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 0) return;

    const newCode = [...code];
    for (let i = 0; i < 6; i++) {
      newCode[i] = pasted[i] || '';
    }
    setCode(newCode);

    if (pasted.length === 6) {
      handleSubmit(pasted);
    } else {
      inputRefs.current[Math.min(pasted.length, 5)]?.focus();
    }
  };

  const handleSubmit = async (fullCode?: string) => {
    const totpCode = fullCode || code.join('');
    if (totpCode.length !== 6) {
      setError('Введите 6-значный код');
      return;
    }

    try {
      await login2FA(totpCode);
      onSuccess();
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Неверный код';
      setError(message);
      toast.error(message);
      // Очищаем поля
      setCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    }
  };

  const handleCancel = () => {
    cancelTwoFactor();
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
          <ShieldCheck className="h-6 w-6 text-blue-600" />
        </div>
        <CardTitle>Двухфакторная аутентификация</CardTitle>
        <CardDescription>
          Введите 6-значный код из приложения-аутентификатора
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center gap-2" onPaste={handlePaste}>
          {code.map((digit, index) => (
            <input
              key={index}
              ref={(el) => { inputRefs.current[index] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className={`
                w-12 h-14 text-center text-2xl font-semibold
                border-2 rounded-lg outline-none transition-colors
                ${error
                  ? 'border-red-400 focus:border-red-500'
                  : 'border-gray-300 focus:border-blue-500'
                }
              `}
            />
          ))}
        </div>

        {error && (
          <p className="mt-3 text-center text-sm text-red-600">{error}</p>
        )}
      </CardContent>
      <CardFooter className="flex flex-col gap-3">
        <Button
          onClick={() => handleSubmit()}
          disabled={isLoading || code.join('').length !== 6}
          className="w-full"
        >
          {isLoading ? 'Проверка...' : 'Подтвердить'}
        </Button>
        <Button variant="ghost" onClick={handleCancel} className="w-full">
          Назад к входу
        </Button>
      </CardFooter>
    </Card>
  );
}