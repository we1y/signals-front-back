'use client'

import { Button } from "@/components/ui/common/button";
import { Input } from "@/components/ui/common/input";
import { Label } from "@/components/ui/common/label";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { balanceService } from "@/services/balance.service";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import VirtualKeyboard from "@/components/ui/custom/VirtualKeyboard";

export default function Send() {
  const [inputValue, setInputValue] = useState<string>("");
  const queryClient = useQueryClient();
  const router = useRouter();
  const [keyboard, setKeyboard] = useState<boolean>(false);

  const t = useTranslations("SendDrawer");

  const mutation = useMutation({
    mutationKey: ['transfer to main'],
    mutationFn: async (amount: number) => {
        try {
            const response = await balanceService.transferToMain(amount);
            if (!response) {
                throw new Error("No response received");
            }
            return response;
        } catch (error) {
            throw error;
        }
    },
    onError: () => {
        queryClient.invalidateQueries();
        router.push(`/failed?message=${encodeURIComponent("Недостаточно средств для перевода с торгового баланса")}`);
    },
    onSuccess: () => {
        queryClient.invalidateQueries();
        router.push(`/success?message=${encodeURIComponent("Средства успешно переведены")}`);
    }
});
  
    const tranferToMain = () => {
      if (inputValue && parseFloat(inputValue) > 0) {
        mutation.mutate(parseFloat(inputValue))
      }
    }

    const handleKeyPress = (key: string) => {
      setInputValue((prev) => {
        const newValue = prev + key;
        return newValue;
      });
    };
    
    const handleDelete = () => {
      setInputValue((prev) => prev.slice(0, -1));
    };

  return (
        <div className='space-y-4 m-4'>
            <div>
              <Label className="text-black">{t("label")}</Label>
              <Input 
                type="text" 
                placeholder={t("inputplaceholder")} 
                onChange={(e) => setInputValue(e.target.value)}
                onFocus={(e) => e.target.blur()}
                value={inputValue}
                readOnly
                onClick={() => setKeyboard(!keyboard)}
                />
            </div>
            {keyboard ? <VirtualKeyboard onKeyPress={handleKeyPress} onDelete={handleDelete}/> : ''}
            <Button onClick={tranferToMain} className="w-full bg-primary text-primary-foreground hover:bg-primary">{t("button")}</Button>
        </div>
  )
}